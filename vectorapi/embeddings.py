import json
import requests
import os
from openai import OpenAI


def get_embeddings(message):
    data = {
        "message": message
    }
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
    }
    parsed_data = requests.post('http://192.168.50.179:4000/gpt', data=data, headers=headers)
    print(f'get_embeddings返回 ===================== {parsed_data}')

    json_data = json.loads(parsed_data.text)

    num_list = json_data['encoded_input']

    return num_list


def get_embeddings_chinese(message):
    data = {
        "message": message
    }
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
    }
    parsed_data = requests.post('http://192.168.50.179:9000/gpt', data=data, headers=headers)
    print(f'get_embeddings_chinese返回 ===================== {parsed_data}')

    # 去掉字符串两端的中括号
    s = parsed_data.text.strip("[]")

    # 用空格分割字符串，得到一个列表
    s_list = s.split()

    # 使用列表生成式，将列表中的每个元素转换为浮点数
    num_list = [float(i) for i in s_list]

    return num_list

def get_embeddings_bce(message):
    data = {
        "message": message
    }
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
    }
    parsed_data = requests.post('http://192.168.50.179:4001/gpt', data=data, headers=headers)
    print(f'get_embeddings_m3返回 ===================== {parsed_data}')

    # 去掉字符串两端的中括号
    json_data = json.loads(parsed_data.text)

    # 用空格分割字符串，得到一个列表
    num_list = json_data['encoded_input']

    # 使用列表生成式，将列表中的每个元素转换为浮点数
    # num_list = [float(i) for i in s_list]

    return num_list

def get_embeddings_m3(message):
    if "HTTP_PROXY" in os.environ and "HTTPS_PROXY" in os.environ:
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)

    data = {
        "message": message
    }
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
    }
    parsed_data = requests.post('http://192.168.50.179:4005/gpt', data=data, headers=headers)
    print(f'get_embeddings_m3返回 ===================== {parsed_data}')

    # 去掉字符串两端的中括号
    json_data = json.loads(parsed_data.text)

    # 用空格分割字符串，得到一个列表
    num_list = json_data['encoded_input']

    # 使用列表生成式，将列表中的每个元素转换为浮点数
    # num_list = [float(i) for i in s_list]

    return num_list

def get_embeddings_aliyun(message):
    # 创建1024维的零向量作为默认返回值
    default_vector = [0.0] * 1024
    
    # 如果是空字符串，返回零向量
    if not message.strip():
        print("空字符串，返回零向量")
        return default_vector
    
    # 移除代理设置（如果存在）
    if "HTTP_PROXY" in os.environ and "HTTPS_PROXY" in os.environ:
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)

    try:
        # 初始化OpenAI客户端
        client = OpenAI(
            api_key="sk-062f03efe4df47298433b72464c190ce",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # 调用embeddings API
        completion = client.embeddings.create(
            model="text-embedding-v3",
            input=message,
            dimensions=1024,
            encoding_format="float"
        )
        
        # 获取嵌入向量
        if completion and hasattr(completion, 'data') and completion.data:
            embeddings = completion.data[0].embedding
            return embeddings
        else:
            print("错误：API返回的嵌入向量为空")
            
    except Exception as e:
        print(f"调用阿里云API时发生错误: {str(e)}")


