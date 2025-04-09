import importlib

import requests
import json
import time

from autogpt.token_counter import count_string_tokens
from colorama import Fore, init

# GPT API 地址
API_URL = "http://36.103.234.58:8000"

def get_chat(messages, history=[] ):

    count = count_string_tokens(messages, 'gpt-3.5-turbo-0301')
    max_tokens = 2048-count

    if max_tokens < 20:
        print(f'''请求失败, token超限''')
        return f"请求失败, token超限"
    # 定义请求的数据
    data = {
        "prompt": messages,
        "temperature": 0.0,
        "max_length": max_tokens,
        "history": history
    }
    # 发送请求
    response = requests.post(API_URL, json=data)
    # 检查请求是否成功
    if response.status_code == 200:
        content = json.loads(response.text)
        print(f'返回content = {content}')
        # 打印去掉 'choices' 后的关键信息
        return content['response']
    else:
        print(f'''请求失败，状态码：{response.status_code}，错误信息：{response.text}''')
        return f"请求失败, 状态码：{response.status_code}"


