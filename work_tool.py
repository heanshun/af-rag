# 需求：调用 milvus的def insert_data(collection_name, vectors) 函数，把给定信息及向量值插入 memory_collection 集合中

# 背景知识：
# milvus模块含有如下函数：
# - insert_data(collection_name, vectors)：将向量数据插入到指定的集合中。

# 解决方案：
# 导入milvus模块
import vectorapi.milvus as milvus
from pymilvus import DataType
from vectorapi.embeddings import get_embeddings_aliyun, get_embeddings_bge

# 定义函数insert_data_to_collection，接收collection_name和vectors两个参数
def insert_data_to_collection(messages, vectors):
    collection_name = "memory_collection"

    data = [
        {"name": "vector", "type": DataType.FLOAT_VECTOR, "values": [vectors]},
        {"name": "content", "type": DataType.VARCHAR, "values": [messages]},
    ]
    milvus.insert_data(collection_name, data)

def insert_message_to_collection(message, collection_name, content="", embedding_func = get_embeddings_bge):
    # 获取message的向量表示
    vectors = embedding_func(message)

    # 把信息序号添加到前面，以便获取时，能得到信息编号
    if content == "":
        content = message

    data = [
        {"name": "vector", "type": DataType.FLOAT_VECTOR, "values": [vectors]},
        {"name": "content", "type": DataType.VARCHAR, "values": [content]},
    ]
    result = milvus.insert_data(collection_name, data)
    return result[0]

def delete_data_from_collection(collection_name, primary_keys):
    """
    调用milvus删除数据

    参数：
    collection_name：要删除数据的集合名称
    primary_keys：要删除的数据对应的主键列表

    返回值：
    无
    """
    milvus.delete_data(collection_name, primary_keys)


def convert_to_entity_content(query_vector):
    """
    将milvus.search_similar_content的结果转换为entity.content的内容

    参数：
    - result: milvus.search_similar_content的结果，形如['["id: 444089649888493600, distance: 0.0, entity: {\'content\': \'Alice\'}", "id: 444089649888493634, distance: 23362.951171875, entity: {\'content\': \'memory_collection\'}", "id: 444089649888493617, distance: 24576.0, entity: {\'content\': \'bob is work\'}", "id: 444089649888493651, distance: 39964.2109375, entity: {\'content\': \'OA已经开始按配置方式进行开发了。\'}"]']

    返回：
    - entity.content的内容列表
    """
    results = milvus.search_similar_content("memory_collection", [query_vector])
    result = ""
    # 处理搜索结果
    for query_res in results:
        for topk_res in query_res:
            # 获取结果的ID和距离
            entity_id = topk_res.id
            # distance = topk_res.distance

            # 获取其他字段的值
            field1_value = topk_res.entity.get('content')
            result += f"- id: {entity_id}, content: {field1_value}\n"

    return result

def get_simple_messages(message, collection_name, threshold=0.1):
    # 获取message的向量表示
    vectors = embedding.send_info_to_embedding(message)
    results = milvus.search_similar_content(collection_name, [vectors], 1000)
    result = ""
    # 处理搜索结果
    for query_res in results:
        for topk_res in query_res:
            # 获取结果的ID和距离
            entity_id = topk_res.id
            distance = topk_res.distance
            # 只取距离小于阈值的结果
            if distance < threshold:
                # 获取其他字段的值
                field1_value = topk_res.entity.get('content')
                result += f"{field1_value}\n"

    return result

def get_messages_info(message, collection_name, limit=30, threshold=None, embedding_func = get_embeddings_bge):
    # 获取message的向量表示
    vectors = embedding_func(message)
    results = milvus.search_similar_content(collection_name, [vectors], limit)
    result = []
    # 处理搜索结果
    for query_res in results:
        for topk_res in query_res:
            # 获取结果的ID和距离
            entity_id = topk_res.id
            distance = topk_res.distance

            # 如果设置了阈值，则只返回距离小于阈值的结果
            if threshold is not None and distance >= threshold:
                continue

            # 获取其他字段的值
            field1_value = topk_res.entity.get('content')
            result.append((entity_id, distance, field1_value))

    return result
