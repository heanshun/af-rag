import os
from typing import List

import requests

from pikerag.workflows.deepsearcher.embedding.base import BaseEmbedding

SILICONFLOW_MODEL_DIM_MAP = {
    "BAAI/bge-m3": 1024,
    "netease-youdao/bce-embedding-base_v1": 768,
    "BAAI/bge-large-zh-v1.5": 1024,
    "BAAI/bge-large-en-v1.5": 1024,
    "Pro/BAAI/bge-m3": 1024,  # paid model
}


class SiliconflowEmbedding(BaseEmbedding):
    """
    https://docs.siliconflow.cn/en/api-reference/embeddings/create-embeddings
    """

    def __init__(self, model="BAAI/bge-m3", **kwargs):
        if "model_name" in kwargs and (not model or model == "BAAI/bge-m3"):
            model = kwargs.pop("model_name")
        self.model = model
        if "api_key" in kwargs:
            api_key = kwargs.pop("api_key")
        else:
            api_key = os.getenv("SILICONFLOW_API_KEY")

        self.api_key = api_key

    def embed_query(self, text: str) -> List[float]:
        """
        input_type (`str`): "query" or "document" for retrieval case.
        """
        url = "https://api.siliconflow.cn/v1/embeddings"

        payload = {"model": self.model, "input": text, "encoding_format": "float"}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

    def embed_documents(self, texts: list[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]

    @property
    def dimension(self) -> int:
        return SILICONFLOW_MODEL_DIM_MAP[self.model]
