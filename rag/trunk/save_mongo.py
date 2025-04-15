from datetime import datetime
from typing import Dict, Any
from rag.trunk.markdown import DocNode, split_document
from rag.trunk.api.api_json import process_api_json
import pymongo
from bson import ObjectId
from work_tool import insert_message_to_collection
from vectorapi.embeddings import get_embeddings_m3
from vectorapi.milvus import delete_data
import json

def node_to_dict(node: DocNode, doc_id: str, vector_space: str, parent_id: ObjectId = None,) -> Dict[Any, Any]:
    """
    将DocNode转换为MongoDB文档格式
    """
    # api vector_content 不为空，则表示是api的节点
    if node.vector_content is not None:
        vector_id = insert_message_to_collection(node.vector_content, vector_space, content = node.content, embedding_func=get_embeddings_m3)
        
    # 获取节点内容的向量ID
    if node.vector_content is None:
        vector_id = insert_message_to_collection(node.content, vector_space, embedding_func=get_embeddings_m3)

    node_dict = {
        "doc_id": doc_id,           # 原始文档ID
        "content": node.content,     # 节点内容
        "level": node.level,         # 节点层级
        "parent_id": parent_id,      # 父节点ID
        "vector_id": vector_id,      # 向量ID
        "type": node.type,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    return node_dict

def create_mongo_uri(
    host: str = "localhost",
    port: int = 27017,
    username: str = None,
    password: str = None,
    auth_db: str = "admin"
) -> str:
    """
    创建MongoDB连接URI
    """
    if username and password:
        return f"mongodb://{username}:{password}@{host}:{port}/?authSource={auth_db}"
    return f"mongodb://{host}:{port}/"

def save_doc_tree_to_mongodb(
    root: DocNode,
    doc_name: str,
    vector_space: str = "rag_collection",
    host: str = "localhost",
    port: int = 27017,
    username: str = None,
    password: str = None,
    auth_db: str = "admin",
    db_name: str = "documents"
) -> str:
    """
    将文档树保存到MongoDB
    如果文档名已存在，则先删除旧文档再保存新文档
    返回文档ID
    """
    # 创建MongoDB连接URI
    mongo_uri = create_mongo_uri(host, port, username, password, auth_db)
    
    # 连接MongoDB
    client = pymongo.MongoClient(mongo_uri)
    db = client[db_name]
    
    # 创建集合（如果不存在）
    docs_collection = db.documents
    nodes_collection = db.document_nodes
    
    try:
        # 检查文档是否已存在
        existing_doc = docs_collection.find_one({"name": doc_name})
        if existing_doc:
            # 删除已存在的文档及其节点
            delete_success = delete_document_by_name(
                    doc_name,
                    username=username,
                    password=password,
                    host=host,
                    port=port,
                    auth_db=auth_db,
                    db_name=db_name
                )
            if not delete_success:
                raise Exception(f"删除文档 '{doc_name}' 失败")
                    
        # 1. 保存文档元信息
        doc_info = {
            "name": doc_name,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": "processed"
        }
        doc_result = docs_collection.insert_one(doc_info)
        doc_id = str(doc_result.inserted_id)
        
        # 2. 使用BFS遍历并保存所有节点
        nodes_to_process = [(root, None)]  # (node, parent_id)
        while nodes_to_process:
            current_node, parent_id = nodes_to_process.pop(0)
            
            # 转换并保存当前节点
            node_dict = node_to_dict(current_node, doc_id, vector_space, parent_id)
            result = nodes_collection.insert_one(node_dict)
            current_id = result.inserted_id
            
            # 将子节点添加到处理队列
            for child in current_node.children:
                nodes_to_process.append((child, current_id))
        
        # 3. 修改索引创建方式，添加vector_id索引
        nodes_collection.drop_indexes()  # 删除所有现有索引
        nodes_collection.create_index([("doc_id", 1)])
        nodes_collection.create_index([("content", 1)])  # 为content创建普通索引
        nodes_collection.create_index([("level", 1)])
        nodes_collection.create_index([("parent_id", 1)])
        nodes_collection.create_index([("vector_id", 1)])  # 为vector_id创建索引
        
        return doc_id
    
    finally:
        client.close()

def query_document_content(
    query: str,
    doc_name: str = None,
    host: str = "localhost",
    port: int = 27017,
    username: str = None,
    password: str = None,
    auth_db: str = "admin",
    db_name: str = "documents"
) -> list:
    """
    检索文档内容
    Args:
        query: 搜索关键词
        doc_name: 可选的文档名，如果提供则只在指定文档中搜索
    """
    # 创建MongoDB连接URI
    mongo_uri = create_mongo_uri(host, port, username, password, auth_db)
    
    client = pymongo.MongoClient(mongo_uri)
    db = client[db_name]
    
    try:
        # 使用正则表达式进行搜索
        search_condition = {
            "content": {"$regex": query, "$options": "i"}  # i 选项表示不区分大小写
        }
        
        # 如果指定了文档名，先查找对应的文档ID
        if doc_name:
            doc = db.documents.find_one({"name": doc_name})
            if doc:
                search_condition["doc_id"] = str(doc["_id"])
            else:
                return []
        
        # 使用正则表达式搜索
        results = db.document_nodes.find(search_condition)
        
        # 处理结果
        processed_results = []
        for result in results:
            # 获取上下文（父节点和同级相邻节点）
            context = get_node_context(db, result)
            processed_results.append({
                "content": result["content"],
                "level": result["level"],
                "type": result["type"],
                "context": context,
                "doc_id": result["doc_id"]
            })
        
        return processed_results
    
    finally:
        client.close()

def get_node_context(db, node: Dict) -> Dict:
    """
    获取节点的上下文信息
    """
    context = {
        "parent": None,
        "siblings": []
    }
    
    # 获取父节点
    if node.get("parent_id"):
        parent = db.document_nodes.find_one({"_id": node["parent_id"]})
        if parent:
            context["parent"] = {
                "content": parent["content"],
                "type": parent["type"]
            }
    
    # 获取同级相邻节点
    siblings = db.document_nodes.find({
        "parent_id": node["parent_id"],
        "doc_id": node["doc_id"],
        "_id": {"$ne": node["_id"]}
    }).limit(2)
    
    context["siblings"] = [{
        "content": sib["content"],
        "type": sib["type"]
    } for sib in siblings]
    
    return context

def delete_document_by_name(
    doc_name: str,
    vector_space: str = "rag_collection",
    host: str = "localhost",
    port: int = 27017,
    username: str = None,
    password: str = None,
    auth_db: str = "admin",
    db_name: str = "documents"
) -> bool:
    """
    根据文档名删除文档及其所有节点
    Args:
        doc_name: 要删除的文档名称
    Returns:
        bool: 删除成功返回True，文档不存在返回False
    """
    # 创建MongoDB连接URI
    mongo_uri = create_mongo_uri(host, port, username, password, auth_db)
    
    client = pymongo.MongoClient(mongo_uri)
    db = client[db_name]
    
    try:
        # 查找文档
        doc = db.documents.find_one({"name": doc_name})
        if not doc:
            return False
            
        doc_id = str(doc["_id"])
        
        # 获取所有相关节点的vector_id
        nodes = db.document_nodes.find({"doc_id": doc_id})
        vector_ids = [node["vector_id"] for node in nodes if "vector_id" in node]
        
        # 删除向量库中的向量
        if vector_ids:
            delete_data(vector_space, vector_ids)
        
        # 删除所有相关节点
        db.document_nodes.delete_many({"doc_id": doc_id})
        
        # 删除文档本身
        db.documents.delete_one({"_id": doc["_id"]})
        
        return True
        
    finally:
        client.close()
