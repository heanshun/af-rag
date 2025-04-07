import json

import requests


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

def get_embeddings_m3(message):
    import os
    if "HTTP_PROXY" in os.environ and "HTTPS_PROXY" in os.environ:
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)

    print(f'message = {message}')

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