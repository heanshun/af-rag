import vectorapi.milvus as milvus

def test_create_collection():
    collection_name = "rag_collection"
    dimension = 1024

    result = milvus.create_collection(collection_name, dimension)
    print(result)

test_create_collection()