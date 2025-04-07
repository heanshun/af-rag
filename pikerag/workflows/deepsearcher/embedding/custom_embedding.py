from typing import List, Union
from .base import BaseEmbedding

class CustomEmbedding(BaseEmbedding):
    def __init__(self, embedding_function, dimension, **kwargs):
        super().__init__()
        self._dimension = dimension  # 使用下划线前缀来存储私有属性
        self.embedding_function = embedding_function
        self.kwargs = kwargs

    @property
    def dimension(self):
        return self._dimension  # 返回私有属性值

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将文档列表转换为向量列表
        """
        embeddings = []
        for text in texts:  # 因为不支持批处理，所以逐个处理
            embedding = self.embedding_function(text)
            embeddings.append(embedding)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        将单个查询文本转换为向量
        """
        return self.embedding_function(text) 