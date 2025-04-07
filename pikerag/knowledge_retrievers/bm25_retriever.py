# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from pikerag.knowledge_retrievers.base_qa_retriever import BaseQaRetriever
from pikerag.utils.config_loader import load_callable
from pikerag.workflows.common import BaseQaData


class BM25QaChunkRetriever(BaseQaRetriever):
    name: str = "BM25QaChunkRetriever"

    def __init__(self, retriever_config, log_dir, main_logger):
        super().__init__(retriever_config, log_dir, main_logger)

        self._init_retriever()

    def _init_retriever(self) -> None:
        assert "vector_store" in self._retriever_config, "vector_store must be defined in retriever part!"
        vector_store_config = self._retriever_config["vector_store"]

        loading_configs: dict = vector_store_config["id_document_loading"]
        ids, documents = load_callable(
            module_path=loading_configs["module_path"],
            name=loading_configs["func_name"],
        )(**loading_configs.get("args", {}))

        self._retrieve_k = self._retriever_config["retrieve_k"]
        self._bm25_retriever = BM25Retriever.from_documents(documents=documents, k=self._retrieve_k)
        return

    def retrieve_documents_by_query(self, query: str, retrieve_id: str="", **kwargs) -> List[Document]:
        return self._bm25_retriever.get_relevant_documents(query, **kwargs)

    def retrieve_contents_by_query(self, query: str, retrieve_id: str="", **kwargs) -> List[str]:
        docs: List[Document] = self.retrieve_documents_by_query(query, retrieve_id, **kwargs)
        return [doc.page_content for doc in docs]

    def retrieve_contents(self, qa: BaseQaData, retrieve_id: str="", **kwargs) -> List[str]:
        query = qa.question
        return self.retrieve_contents_by_query(query, retrieve_id, **kwargs)
