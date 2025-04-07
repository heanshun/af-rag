from abc import ABC
from typing import Any, List, Tuple

from pikerag.workflows.deepsearcher.vector_db import RetrievalResult


def describe_class(description):
    def decorator(cls):
        cls.__description__ = description
        return cls

    return decorator


class BaseAgent(ABC):
    def __init__(self, **kwargs):
        pass

    def invoke(self, query: str, **kwargs) -> Any:
        """
        Invoke the agent and return the result.
        Args:
            query: The query string.

        """


class RAGAgent(BaseAgent):
    def __init__(self, **kwargs):
        pass

    def retrieve(self, query: str, **kwargs) -> Tuple[List[RetrievalResult], int, dict]:
        """
        Retrieve document results from the knowledge base.

        Args:
            query: The query string.

        Returns:
            A tuple containing:
                - the retrieved results
                - the total number of token usages of the LLM
                - any additional metadata, which can be an empty dictionary
        """

    def query(self, query: str, **kwargs) -> Tuple[str, List[RetrievalResult], int]:
        """
        Query the agent and return the answer.

        Args:
            query: The query string.

        Returns:
            A tuple containing:
                - the result generated from LLM
                - the retrieved document results
                - the total number of token usages of the LLM
        """
