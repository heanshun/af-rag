import time

from colorama import Fore
from pymilvus import Milvus, DataType

host = 'localhost'
port = '19530'
client = Milvus(host=host, port=port)

def create_collection(collection_name, dimension):
    """
    创建集合及字段

    参数：
    - collection_name：集合名称
    - dimension：向量维度

    返回：
    - 无
    """
    collection_name = collection_name

    collection_schema = {
        "fields": [
            {"name": "id", "type": DataType.INT64, "is_primary": True, "auto_id": True},
            {"name": "vector", "type": DataType.FLOAT_VECTOR, "metric_type": "L2", "params": {"dim": dimension}},
            {"name": "content", "type": DataType.VARCHAR, "params": {"max_length": 2000}},
        ],
        "segment_row_limit": 4096,
    }

    client.create_collection(collection_name, collection_schema)

def delete_collection(collection_name):
    
    # 检查集合是否存在
    if client.has_collection(collection_name):
        # 删除集合
        client.drop_collection(collection_name)
        print(f"Collection '{collection_name}' has been deleted.")
    else:
        print(f"Collection '{collection_name}' does not exist.")

def insert_data(collection_name, vectors):
    """
    调用milvus插入数据

    参数：
    collection_name：要插入数据的集合名称
    vectors：要插入的向量数据，格式为二维列表，每个向量为一个列表

    返回值：
    无
    """
    result = client.insert(collection_name, vectors)
    return result.primary_keys

def search_similar_content(collection_name, query_vector, limit=30, output_fields=["content"]):
    """
    功能要求：
    调用milvus, 查询相似内容

    参数：
    - query_vector: 待查询的向量

    返回：
    - similar_content: 相似内容的列表
    """
    start_time = time.time()
    # 首先加载集合到内存
    client.load_collection(collection_name=collection_name)
    print("正在连接host: ", host, "port: ", port)

    # 设置查询参数
    search_params = {
        "metric_type": "L2",
        "params": {"nprobe": limit},
    }

    results = client.search(
        collection_name=collection_name,
        anns_field="vector",
        data=query_vector,
        param=search_params,
        output_fields=output_fields,
        limit=limit,
        partition_names=None,
        timeout=None
    )

    end_time = time.time()
    # 计算请求耗时，单位为毫秒
    elapsed_time = (end_time - start_time) * 1000

    print(Fore.GREEN + f"milvus开始时间：{start_time}，耗时： {elapsed_time} ms" + Fore.RESET)  # 打印绿色的结果，然后恢复正常颜色

    return results

def create_index(collection_name):
    """
    创建索引

    参数：
    collection_name：str，集合名称
    index_type：str，索引类型
    index_param：dict，索引参数

    返回：
    无
    """
    # 定义索引参数
    index_param = {
        "metric_type": "L2",  # 选择一个适合您数据的距离度量
        "index_type": "IVF_FLAT",  # 选择一个索引类型
        "params": {"nlist": 128}  # 设置索引参数
    }

    # 创建索引
    client.create_index(collection_name=collection_name, field_name="vector", params=index_param)

def execute_milvus_command(collection_name):
    """
    执行milvus命令

    参数：
    command (str): milvus命令

    返回：
    response (str): 命令执行结果
    """
    # 调用milvus执行命令
    has_index = client.has_index(collection_name=collection_name, field_name="vector")
    print(has_index)

def list_collections():
    has_index = client.list_collections()
    return has_index

def delete_data(collection_name, primary_keys):
    """
    调用milvus删除数据

    参数：
    collection_name：要删除数据的集合名称
    primary_keys：要删除的数据的主键列表

    返回值：
    无
    """
    keys_str = ','.join(str(key) for key in primary_keys)  # 将主键列表转换为字符串
    expr = f'id in [{keys_str}]'  # 构建查询表达式
    result = client.delete(collection_name, expr)
    return result
