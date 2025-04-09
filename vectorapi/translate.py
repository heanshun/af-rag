import json

import requests
from gptapi.api import get_completion

def en_zh(message):
    data = {
        "message": message
    }
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
    }
    parsed_data = requests.post('http://192.168.50.179:7000/en_zh', data=data, headers=headers)
    print(f'en_zh返回 ===================== {parsed_data}')

    return parsed_data.text


def zh_en(message):
    data = {
        "message": message
    }
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
    }
    parsed_data = requests.post('http://192.168.50.179:7000/zh_en', data=data, headers=headers)
    print(f'zh_en返回 ===================== {parsed_data}')

    return parsed_data.text

def openai_zh_en(message):
    prompt = f"""
给下面数据库表名起个英文名，尽可能简洁明了：
{message}
"""
    result = get_completion(prompt, max_tokens=100, model="gpt-4-0125-preview")
    return result