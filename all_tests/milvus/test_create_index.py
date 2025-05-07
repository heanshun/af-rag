import vectorapi.milvus as milvus

def test_create_index():
    collection_name = "rag_collection"

    result = milvus.create_index(collection_name)
    print(result)

test_create_index()