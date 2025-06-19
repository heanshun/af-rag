# Licensed under the MIT license.
import json
import math
from functools import partial
from typing import List, Dict, Any, Optional
import pymongo
from bson import ObjectId

from pikerag.knowledge_retrievers.base_qa_retriever import BaseQaRetriever
from pikerag.utils.config_loader import load_callable
from pikerag.utils.logger import Logger
from pikerag.workflows.common import BaseQaData
from vectorapi.embeddings import get_embeddings_aliyun, get_embedding
from vectorapi.milvus import search_similar_content
from pikerag.knowledge_retrievers.search_internet_baidu import baidu_search, resolve_baidu_url, extract_web_content

def get_messages_info(message, collection_name, limit=30, threshold=None, embedding_func=get_embedding):
    # 获取message的向量表示
    vectors = embedding_func(message)
    results = search_similar_content(collection_name, [vectors], limit)
    result = []

    # 处理搜索结果
    for query_res in results:
        for hit in query_res:
            # 获取结果的ID和距离
            entity_id = hit.id
            distance = hit.distance

            # 将距离转换为相似度（假设使用cosine距离）
            similarity = 1 - distance
            
            # 如果设置了阈值，则只返回相似度大于阈值的结果
            if threshold is not None and similarity < threshold:
                print(f"🔍 过滤低相似度结果: {similarity:.3f} < {threshold}")
                continue

            # 获取其他字段的值
            field1_value = hit.entity.get('content')
            result.append((entity_id, distance, field1_value))
        
    if len(result) == 0:
        print("⚠️ retrieve没有结果，启动联网搜索")
        # 调用联网搜索
        internet_results = baidu_search(message, max_results=3)
        for item in internet_results:
            print(f"📌 搜索到: {item['title']}")
                
            # 解析真实URL并提取网页内容
            real_url = resolve_baidu_url(item["url"])
            web_content = extract_web_content(real_url)
                
            if web_content:
                content_text = f"标题：{item['title']}\n链接：{real_url}\n内容：{web_content}"
                print(f"✅ 成功提取内容，长度: {len(web_content)}")
            else:
                content_text = f"标题：{item['title']}\n链接：{real_url}\n内容：无法提取网页内容"
                print(f"❌ 内容提取失败")
                
            # 将联网搜索结果添加到result中
            # 使用负数ID来标识联网搜索结果，距离设为0表示最相关
            result.append((-len(result)-1, 0.0, content_text))

    return result

class MongoDBMixin:
    """MongoDB连接和操作的混入类"""
    
    def create_mongo_uri(
        self,
        host: str = "localhost",
        port: int = 27017,
        username: str = None,
        password: str = None,
        auth_db: str = "admin"
    ) -> str:
        """创建MongoDB连接URI
        
        Args:
            host: MongoDB主机地址
            port: MongoDB端口
            username: 用户名
            password: 密码
            auth_db: 认证数据库名
            
        Returns:
            str: MongoDB连接URI
        """
        if username and password:
            return f"mongodb://{username}:{password}@{host}:{port}/?authSource={auth_db}"
        return f"mongodb://{host}:{port}/"
        
    def _init_mongodb_mixin(self) -> None:
        """初始化MongoDB连接配置"""
        mongo_config = self._retriever_config.get("mongodb_setting", {})
        self.mongo_uri = self.create_mongo_uri(
            host=mongo_config.get("host", "localhost"),
            port=mongo_config.get("port", 27017),
            username=mongo_config.get("username"),
            password=mongo_config.get("password"),
            auth_db=mongo_config.get("auth_db", "admin")
        )
        self.db_name = mongo_config.get("db_name", "documents")
        self.client = None
        self._main_logger.info(
            msg=f"Initialized MongoDB connection with URI: {self.mongo_uri}",
            tag=self.name
        )
        
    def _get_db(self):
        """获取数据库连接"""
        if not self.client:
            self.client = pymongo.MongoClient(self.mongo_uri)
            self._main_logger.debug(
                msg="Created new MongoDB client connection",
                tag=self.name
            )
        return self.client[self.db_name]
        
    def _close_db(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            self.client = None
            self._main_logger.debug(
                msg="Closed MongoDB client connection",
                tag=self.name
            )


class QaMongoDBRetriever(BaseQaRetriever, MongoDBMixin):
    """基于MongoDB的文档检索器实现"""
    
    name: str = "QaMongoDBRetriever"
    
    def __init__(self, retriever_config: dict, log_dir: str, main_logger: Logger) -> None:
        """初始化检索器
        
        Args:
            retriever_config: 检索器配置
            log_dir: 日志目录
            main_logger: 主日志记录器
        """
        super().__init__(retriever_config, log_dir, main_logger)
        
        # 初始化检索参数
        self.retrieve_k = retriever_config.get("retrieve_k", 5)
        self.retrieve_score_threshold = retriever_config.get("retrieve_score_threshold", 1)
        self.embedding_func = eval(retriever_config.get("embedding_func", get_embedding))
        
        self._init_query_parser()
        self._init_mongodb_mixin()
        
    def _init_query_parser(self) -> None:
        """初始化查询解析器"""
        query_parser_config: dict = self._retriever_config.get("retrieval_query", None)
        
        if query_parser_config is None:
            self._main_logger.info(
                msg="`retrieval_query` not configured, using default embedding function",
                tag=self.name,
            )
            return
        else:
            parser_func = load_callable(
                module_path=query_parser_config["module_path"],
                name=query_parser_config["func_name"],
            )
            self._query_parser = partial(parser_func, **query_parser_config.get("args", {}))
    
    def _get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档信息"""
        db = self._get_db()
        doc = db.documents.find_one({"_id": ObjectId(doc_id)})
        if doc:
            self._main_logger.debug(
                msg=f"Retrieved document info for doc_id: {doc_id}",
                tag=self.name
            )
        else:
            self._main_logger.warning(
                msg=f"Document not found for doc_id: {doc_id}",
                tag=self.name
            )
        return doc
    
    def _get_node_content(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点内容"""
        db = self._get_db()
        node = db.document_nodes.find_one({"_id": node_id})
        if node:
            self._main_logger.debug(
                msg=f"Retrieved node content for node_id: {node_id}",
                tag=self.name
            )
        else:
            self._main_logger.warning(
                msg=f"Node not found for node_id: {node_id}",
                tag=self.name
            )
        return node
    
    def _get_siblings(self, parent_id: str, doc_id: str) -> List[Dict[str, Any]]:
        """获取同级节点"""
        db = self._get_db()
        siblings = list(db.document_nodes.find({
            "parent_id": parent_id,
            "doc_id": doc_id
        }).sort("_id", 1))
        self._main_logger.debug(
            msg=f"Retrieved {len(siblings)} siblings for parent_id: {parent_id}, doc_id: {doc_id}",
            tag=self.name
        )
        return siblings
            
    def retrieve_contents_by_query(self, query: str, retrieve_id: str = "") -> List[str]:
        """检索文档内容"""
        retrieve_k = self.retrieve_k
        threshold = self.retrieve_score_threshold

        self._main_logger.info(
            msg=f"Starting content retrieval for query: {query}",
            tag=self.name
        )
        
        # 从向量库获取相似内容的向量ID
        vector_results = get_messages_info(
            query, 
            "rag_collection2", 
            limit=retrieve_k,
            threshold=threshold,
            embedding_func=self.embedding_func
        )
        
        self._main_logger.debug(
            msg=f"Vector search returned {len(vector_results)} results: {json.dumps(vector_results, ensure_ascii=False)}",
            tag=self.name
        )
            
        try:
            db = self._get_db()
            results = []
            seen_parent_ids = set()

            for vector_result in vector_results:
                vector_id = vector_result[0]
                distance = vector_result[1]
                content = vector_result[2]
                
                self._main_logger.debug(
                    msg=f"Processing vector_id: {vector_id}, distance: {distance}, content: {content}",
                    tag=self.name
                )
                
                # 处理联网搜索结果（负数ID）
                if vector_id < 0:
                    self._main_logger.info(
                        msg=f"Processing internet search result with ID: {vector_id}",
                        tag=self.name
                    )
                    
                    # 解析联网搜索内容（格式：标题：xxx\n链接：xxx\n内容：xxx）
                    lines = content.split('\n')
                    title = ""
                    link = ""
                    web_content = ""
                    
                    for line in lines:
                        if line.startswith("标题："):
                            title = line.replace("标题：", "").strip()
                        elif line.startswith("链接："):
                            link = line.replace("链接：", "").strip()
                        elif line.startswith("内容："):
                            web_content = line.replace("内容：", "").strip()
                    
                    # 构造联网搜索结果
                    internet_content = {
                        "文档名": "互联网搜索结果",
                        "标题": title,
                        "doc_name": link,
                        "内容": web_content
                    }
                    results.append(str(internet_content))
                    continue
                
                # 处理本地数据库结果
                node = db.document_nodes.find_one({"vector_id": vector_id})
                if not node:
                    self._main_logger.warning(
                        msg=f"Node not found for vector_id: {vector_id}, content from vector store: {content}",
                        tag=self.name
                    )
                    continue
                
                if node["parent_id"] and node["parent_id"] in seen_parent_ids:
                    self._main_logger.debug(
                        msg=f"Skipping duplicate parent_id: {node['parent_id']}",
                        tag=self.name
                    )
                    continue
                
                if node["parent_id"]:
                    seen_parent_ids.add(node["parent_id"])
                
                # 如果节点类型为sentence，则获取同级节点、父节点和文档信息
                if node["type"] == "sentence":
                    # 获取同级节点
                    siblings = self._get_siblings(node["parent_id"], node["doc_id"])

                    # 获取父节点
                    parent = None
                    if node["parent_id"]:
                        parent = self._get_node_content(node["parent_id"])
                    
                    # 获取文档信息
                    doc = self._get_document_info(node["doc_id"])
                    
                    # 组织内容
                    content = {
                        "doc_id": node["doc_id"],
                        "doc_name": doc["name"] if doc else None,
                        "matched_content": node["content"],
                        "node_type": node["type"],
                        "level": node["level"],
                        "siblings": [sib["content"] for sib in siblings],
                        "parent": parent["content"] if parent else None
                    }
                #chapter节点  
                elif node["type"] == "chapter":
                    # 获取文档信息
                    doc = self._get_document_info(node["doc_id"])
                    
                    # 获取当前chapter的子节点（paragraphs）
                    paragraphs = self._get_siblings(node["_id"], node["doc_id"])
                    # 获取每个paragraph下的所有sentence
                    all_sentences = []
                    for para in paragraphs:
                        sentences = self._get_siblings(para["_id"], node["doc_id"])
                        all_sentences.extend([sent["content"] for sent in sentences])
                    if all_sentences:
                        content = {
                            "doc_id": node["doc_id"],
                            "doc_name": doc["name"] if doc else None,
                            "matched_content": node["content"],
                            "node_type": node["type"],
                            "level": node["level"],
                            "sentences": all_sentences
                        }
                # 非sentence和chapter节点
                else:
                    # 获取文档信息
                    doc = self._get_document_info(node["doc_id"])

                    content = {
                        "doc_id": node["doc_id"],
                        "doc_name": doc["name"] if doc else None,
                        "matched_content": node["content"],
                        "node_type": node["type"],
                        "level": node["level"]
                    }
                
                results.append(str(content))
            
            if len(results) > 0:
                self._main_logger.info(
                    msg=f"Successfully retrieved {len(results)} documents for query",
                    tag=self.name
                )
            else:
                self._main_logger.warning(
                    msg="No documents were retrieved after processing vector results",
                    tag=self.name
                )
                
            return results
            
        except Exception as e:
            self._main_logger.error(
                msg=f"Error during content retrieval: {str(e)}",
                tag=self.name
            )
            raise
        finally:
            self._close_db()


def create_mongo_uri(
    host: str = "localhost",
    port: int = 27017,
    username: str = None,
    password: str = None,
    auth_db: str = "admin"
) -> str:
    """创建MongoDB连接URI的独立函数
    
    Args:
        host: MongoDB主机地址
        port: MongoDB端口
        username: 用户名
        password: 密码
        auth_db: 认证数据库名
        
    Returns:
        str: MongoDB连接URI
    """
    if username and password:
        return f"mongodb://{username}:{password}@{host}:{port}/?authSource={auth_db}"
    return f"mongodb://{host}:{port}/" 