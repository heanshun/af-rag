from langchain_core.embeddings import Embeddings
from typing import List
import requests
import json

def get_embeddings_m3(message):
    import os
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

class CustomAPIEmbeddings(Embeddings):
    def __init__(self, api_url: str, api_key: str = None, model_name: str = None, **kwargs):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # 使用列表推导式对每个文本调用get_embeddings_m3
        embeddings = [get_embeddings_m3(text) for text in texts]
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]