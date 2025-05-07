import vectorapi.milvus as milvus
from pymilvus import connections

def test_create_collection():
    # 首先确保连接配置正确
    collection_name = "rag_collection2"
    dimension = 512

    result = milvus.create_collection(collection_name, dimension)
    print(result)

test_create_collection()