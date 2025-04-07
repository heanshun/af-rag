from abc import ABC, abstractmethod
from typing import List, Union

import numpy as np

from pikerag.workflows.deepsearcher.loader.splitter import Chunk


class RetrievalResult:
    def __init__(
        self,
        embedding: np.array,
        text: str,
        reference: str,
        metadata: dict,
        score: float = 0.0,
    ):
        self.embedding = embedding
        self.text = text
        self.reference = reference
        self.metadata = metadata
        self.score: float = score

    def __repr__(self):
        return f"RetrievalResult(score={self.score}, embedding={self.embedding}, text={self.text}, reference={self.reference}), metadata={self.metadata}"


def deduplicate_results(results: List[RetrievalResult]) -> List[RetrievalResult]:
    all_text_set = set()
    deduplicated_results = []
    for result in results:
        if result.text not in all_text_set:
            all_text_set.add(result.text)
            deduplicated_results.append(result)
    return deduplicated_results


class CollectionInfo:
    def __init__(self, collection_name: str, description: str):
        self.collection_name = collection_name
        self.description = description


class BaseVectorDB(ABC):
    def __init__(
        self,
        default_collection: str = "deepsearcher",
        *args,
        **kwargs,
    ):
        self.default_collection = default_collection

    @abstractmethod
    def init_collection(
        self,
        dim: int,
        collection: str,
        description: str,
        force_new_collection=False,
        *args,
        **kwargs,
    ):
        pass

    @abstractmethod
    def insert_data(self, collection: str, chunks: List[Chunk], *args, **kwargs):
        pass

    @abstractmethod
    def search_data(
        self, collection: str, vector: Union[np.array, List[float]], *args, **kwargs
    ) -> List[RetrievalResult]:
        pass

    def list_collections(self, *args, **kwargs) -> List[CollectionInfo]:
        pass

    @abstractmethod
    def clear_db(self, *args, **kwargs):
        pass
