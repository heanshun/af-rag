import os
from typing import List

from openai._types import NOT_GIVEN

from pikerag.workflows.deepsearcher.embedding.base import BaseEmbedding

OPENAI_MODEL_DIM_MAP = {
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


class OpenAIEmbedding(BaseEmbedding):
    """
    https://platform.openai.com/docs/guides/embeddings/use-cases
    """

    def __init__(self, model: str = "text-embedding-ada-002", **kwargs):
        """

        Args:
            model_name (`str`):
                Can be one of the following:
                    'text-embedding-ada-002': No dimension needed, default is 1536,
                    'text-embedding-3-small': dimensions from 512 to 1536, default is 1536,
                    'text-embedding-3-large': dimensions from 1024 to 3072, default is 3072,
        """
        from openai import OpenAI

        if "api_key" in kwargs:
            api_key = kwargs.pop("api_key")
        else:
            api_key = os.getenv("OPENAI_API_KEY")
        if "model_name" in kwargs and (not model or model == "text-embedding-ada-002"):
            model = kwargs.pop("model_name")
        self.model = model
        self.client = OpenAI(api_key=api_key, **kwargs)

    def embed_query(self, text: str, dimensions=NOT_GIVEN) -> List[float]:
        # text = text.replace("\n", " ")
        return (
            self.client.embeddings.create(input=[text], model=self.model, dimensions=dimensions)
            .data[0]
            .embedding
        )

    def embed_documents(self, texts: List[str], dimensions=NOT_GIVEN) -> List[List[float]]:
        res = self.client.embeddings.create(input=texts, model=self.model, dimensions=dimensions)
        res = [r.embedding for r in res.data]
        return res

    @property
    def dimension(self) -> int:
        return OPENAI_MODEL_DIM_MAP[self.model]
