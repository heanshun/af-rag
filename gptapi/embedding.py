import ast

from gptapi.api import embedding

def send_info_to_embedding(info):
    """
    给 http://xxx/embedding 发送给定信息

    参数：
    info：要发送的信息

    返回值：
    无

    功能要求：
    调用storeapi模块的save_entity函数，将info保存到后台服务中。
    """

    # 定义请求的数据
    data = {
        "messages": info
    }

    # 发送请求
    content = embedding(data)
    output_list = ast.literal_eval(str(content))
    return output_list
