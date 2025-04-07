import numpy as np
from auto.work_tool import get_messages_info, insert_message_to_collection
from gptapi.embedding import send_info_to_embedding
from vectorapi.embeddings import get_embeddings
from vectorapi.milvus import create_collection, create_index, delete_collection
from vectorapi.translate import zh_en

# 计算两个向量之间的余弦相似度
def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    similarity = dot_product / (norm_vec1 * norm_vec2)
    return similarity

# 主函数，计算两个句子的相似度
def calculate_similarity(sentence1, sentence2, vector_func):
    # 获取两个句子的嵌入向量
    vec1 = vector_func(sentence1)
    vec2 = vector_func(sentence2)
    
    # 计算并返回它们的相似度
    return cosine_similarity(vec1, vec2)

def get_similar(question, to_en=False):
    if to_en:
        question = zh_en(question)
    result = get_messages_info(question, collection_name, limit=100, embedding_func=get_embeddings)
    return result

collection_name = "test_collection"

if __name__ == "__main__":
    delete_collection(collection_name)
    create_collection(collection_name, 384)
    create_index(collection_name)

    strings = ['通过何种途径获取的客户', '客户所属省份']
    en_strings = ['How to get customers', 'Customer province']
    t5_strings = ['What are the ways to get customers?', 'Provinces in which the client belongs']

    for item in strings:
        insert_message_to_collection(item, collection_name, content=item, embedding_func=get_embeddings)

    for item in en_strings:
        insert_message_to_collection(item, collection_name, content=item, embedding_func=get_embeddings)

    for item in t5_strings:
        insert_message_to_collection(item, collection_name, content=item, embedding_func=get_embeddings)
