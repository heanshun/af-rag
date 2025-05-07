import vectorapi.milvus as milvus

def test_delete_collection():
    collection_name = "rag_collection2"
    result = milvus.delete_collection(collection_name)
    print(result)

test_delete_collection()