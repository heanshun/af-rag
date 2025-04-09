import json

import requests


def get_other(prompt):
    data = {
        "messages": prompt
    }
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
    }
    parsed_data = requests.post('http://36.103.234.63:5000/gpt', data=data, headers=headers)
    print(f'get_other 返回: {parsed_data.text}')
    response = parsed_data.text
    print(f'返回 ===================== {response}')
    return response


 # http://36.103.234.63:5000/gpt
def get_filed(question, filed):
    prompt = f"""<<SYS>>你是一个通过问题找到与问题相关字段的工具AI，你的作用是从通过问题找到与问题有关的字段,只返回字段名<</SYS>>
    问题：{question}
    
    字段: {filed}
    """
    get_other(prompt)

