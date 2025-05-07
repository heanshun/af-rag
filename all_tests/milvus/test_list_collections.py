import vectorapi.milvus as milvus
from pymilvus import DataType

def test_insert_data():
    result = milvus.list_collections()
    print(result)

test_insert_data()