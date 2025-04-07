import json

import requests


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

