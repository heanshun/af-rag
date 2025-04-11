import vectorapi.milvus as milvus

def test_delete_collection():
    collection_name = "rag_collection"
    result = milvus.delete_collection(collection_name)
    print(result)

test_delete_collection()