from typing import List, Tuple

# from deepsearcher.configuration import vector_db, embedding_model, llm
from pikerag.workflows.deepsearcher import configuration
from pikerag.workflows.deepsearcher.vector_db.base import RetrievalResult


def query(original_query: str, max_iter: int = 3) -> Tuple[str, List[RetrievalResult], int]:
    default_searcher = configuration.default_searcher
    return default_searcher.query(original_query)


def retrieve(
    original_query: str, max_iter: int = 3
) -> Tuple[List[RetrievalResult], List[str], int]:
    default_searcher = configuration.default_searcher
    retrieved_results, consume_tokens, metadata = default_searcher.retrieve(original_query)
    return retrieved_results, [], consume_tokens


def naive_retrieve(query: str, collection: str = None, top_k=10) -> List[RetrievalResult]:
    naive_rag = configuration.naive_rag
    all_retrieved_results, consume_tokens, _ = naive_rag.retrieve(query)
    return all_retrieved_results


def naive_rag_query(
    query: str, collection: str = None, top_k=10
) -> Tuple[str, List[RetrievalResult]]:
    naive_rag = configuration.naive_rag
    answer, retrieved_results, consume_tokens = naive_rag.query(query)
    return answer, retrieved_results
