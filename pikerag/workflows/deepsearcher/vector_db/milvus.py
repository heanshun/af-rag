from typing import List, Optional, Union

import numpy as np
from pymilvus import DataType, MilvusClient

from pikerag.workflows.deepsearcher.loader.splitter import Chunk
from pikerag.workflows.deepsearcher.tools import log
from pikerag.workflows.deepsearcher.vector_db.base import BaseVectorDB, CollectionInfo, RetrievalResult


class Milvus(BaseVectorDB):
    """Milvus class is a subclass of DB class."""

    client: MilvusClient = None

    def __init__(
        self,
        default_collection: str = "deepsearcher",
        uri: str = "http://localhost:19530",
        token: str = "root:Milvus",
        db: str = "default",
    ):
        super().__init__(default_collection)
        self.default_collection = default_collection
        self.client = MilvusClient(uri=uri, token=token, db_name=db, timeout=30)

    def init_collection(
        self,
        dim: int,
        collection: Optional[str] = "deepsearcher",
        description: Optional[str] = "",
        force_new_collection: bool = False,
        text_max_length: int = 65_535,
        reference_max_length: int = 2048,
        metric_type: str = "L2",
        *args,
        **kwargs,
    ):
        if not collection:
            collection = self.default_collection
        if description is None:
            description = ""
        try:
            has_collection = self.client.has_collection(collection, timeout=5)
            if force_new_collection and has_collection:
                self.client.drop_collection(collection)
            elif has_collection:
                return
            schema = self.client.create_schema(
                enable_dynamic_field=False, auto_id=True, description=description
            )
            schema.add_field("id", DataType.INT64, is_primary=True)
            schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=dim)
            schema.add_field("text", DataType.VARCHAR, max_length=text_max_length)
            schema.add_field("reference", DataType.VARCHAR, max_length=reference_max_length)
            schema.add_field("metadata", DataType.JSON)
            index_params = self.client.prepare_index_params()
            index_params.add_index(field_name="embedding", metric_type=metric_type)
            self.client.create_collection(
                collection,
                schema=schema,
                index_params=index_params,
                consistency_level="Strong",
            )
            log.color_print(f"create collection [{collection}] successfully")
        except Exception as e:
            log.critical(f"fail to init db for milvus, error info: {e}")

    def insert_data(
        self,
        collection: Optional[str],
        chunks: List[Chunk],
        batch_size: int = 256,
        *args,
        **kwargs,
    ):
        if not collection:
            collection = self.default_collection
        texts = [chunk.text for chunk in chunks]
        references = [chunk.reference for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks]

        datas = [
            {
                "embedding": embedding,
                "text": text,
                "reference": reference,
                "metadata": metadata,
            }
            for embedding, text, reference, metadata in zip(
                embeddings, texts, references, metadatas
            )
        ]
        batch_datas = [datas[i : i + batch_size] for i in range(0, len(datas), batch_size)]
        try:
            for batch_data in batch_datas:
                self.client.insert(collection_name=collection, data=batch_data)
        except Exception as e:
            log.critical(f"fail to insert data, error info: {e}")

    def search_data(
        self,
        collection: Optional[str],
        vector: Union[np.array, List[float]],
        top_k: int = 5,
        *args,
        **kwargs,
    ) -> List[RetrievalResult]:
        if not collection:
            collection = self.default_collection
        try:
            search_results = self.client.search(
                collection_name=collection,
                data=[vector],
                limit=top_k,
                output_fields=["*"],
                timeout=10,
            )

            return [
                RetrievalResult(
                    embedding=b["entity"]["embedding"],
                    text=b["entity"]["text"],
                    reference=b["entity"]["reference"],
                    score=b["distance"],
                    metadata=b["entity"]["metadata"],
                )
                for a in search_results
                for b in a
            ]
        except Exception as e:
            log.critical(f"fail to search data, error info: {e}")
            return []

    def list_collections(self, *args, **kwargs) -> List[CollectionInfo]:
        collection_infos = []
        try:
            collections = self.client.list_collections()
            for collection in collections:
                description = self.client.describe_collection(collection)
                collection_infos.append(
                    CollectionInfo(
                        collection_name=collection,
                        description=description["description"],
                    )
                )
        except Exception as e:
            log.critical(f"fail to list collections, error info: {e}")
        return collection_infos

    def clear_db(self, collection: str = "deepsearcher", *args, **kwargs):
        if not collection:
            collection = self.default_collection
        try:
            self.client.drop_collection(collection)
        except Exception as e:
            log.warning(f"fail to clear db, error info: {e}")
