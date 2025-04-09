from typing import List, Dict, Any
import pymongo
from bson import ObjectId
from auto.work_tool import get_messages_info
from vectorapi.embeddings import get_embeddings_m3

def create_mongo_uri(
    host: str = "localhost",
    port: int = 27017,
    username: str = None,
    password: str = None,
    auth_db: str = "admin"
) -> str:
    """创建MongoDB连接URI"""
    if username and password:
        return f"mongodb://{username}:{password}@{host}:{port}/?authSource={auth_db}"
    return f"mongodb://{host}:{port}/"

def search_markdown(
    query: str,
    top_k: int = 5,
    threshold = None,
    username: str = "admin",
    password: str = "Class123!",
    host: str = "192.168.50.67",
    port: int = 30429,
    auth_db: str = "admin",
    db_name: str = "documents"
) -> List[Dict[str, Any]]:
    """
    检索markdown文档内容
    
    Args:
        query: 查询内容
        top_k: 返回结果数量
        username: MongoDB用户名
        password: MongoDB密码
        host: MongoDB主机
        port: MongoDB端口
        auth_db: 认证数据库
        db_name: 目标数据库名称
        
    Returns:
        List[Dict]: 检索结果列表，每个结果包含以下字段：
            - doc_id: 文档ID
            - doc_name: 文档名称
            - matched_content: 匹配到的内容
            - node_type: 节点类型
            - level: 节点层级
            - siblings: 同级节点内容列表
            - parent: 父节点内容
    """
    # 从向量库获取相似内容的向量ID
    vector_results = get_messages_info(query, "rag_collection", limit=top_k, threshold=threshold, embedding_func=get_embeddings_m3)
    if not vector_results:
        return []
        
    # 连接MongoDB获取完整内容
    mongo_uri = create_mongo_uri(host, port, username, password, auth_db)
    client = pymongo.MongoClient(mongo_uri)
    db = client[db_name]
    
    try:
        results = []
        seen_parent_ids = set()  # 用于追踪已经处理过的父节点ID
        
        for vector_result in vector_results:
            vector_id = vector_result[0]
            node = db.document_nodes.find_one({"vector_id": vector_id})
            if not node:
                continue
                
            # 如果已经处理过具有相同父节点的内容，则跳过
            if node["parent_id"] and node["parent_id"] in seen_parent_ids:
                continue
            
            if node["parent_id"]:
                seen_parent_ids.add(node["parent_id"])
            
            # 获取同级节点（兄弟节点）
            siblings = list(db.document_nodes.find({
                "parent_id": node["parent_id"],
                "doc_id": node["doc_id"]
            }).sort("_id", 1))  # 按ID排序以保持原始顺序
            
            # 获取父节点信息
            parent = None
            if node["parent_id"]:
                parent = db.document_nodes.find_one({"_id": node["parent_id"]})
            
            # 组织返回结果
            result = {
                "doc_id": node["doc_id"],
                "matched_content": node["content"],
                "node_type": node["type"],
                "level": node["level"],
                "siblings": [sib["content"] for sib in siblings],
                "parent": parent["content"] if parent else None
            }
            
            # 获取文档名称
            doc = db.documents.find_one({"_id": ObjectId(node["doc_id"])})
            if doc:
                result["doc_name"] = doc["name"]
            
            results.append(result)
        
        return results
        
    finally:
        client.close()

if __name__ == "__main__":
    results = search_markdown(
        query="一个感叹句",
        top_k=5,
        threshold=0.5,
        username="admin",
        password="Class123!",
        host="192.168.50.67",
        port=30429
    )

    for result in results:
        print(f"文档: {result['doc_name']}")
        print(f"匹配内容: {result['matched_content']}")
        print(f"同级内容: {result['siblings']}")
        print(f"父节点: {result['parent']}")
        print("---")
