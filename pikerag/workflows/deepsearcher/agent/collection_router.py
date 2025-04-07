from typing import List, Tuple

from pikerag.workflows.deepsearcher.agent.base import BaseAgent
from pikerag.workflows.deepsearcher.llm.base import BaseLLM
from pikerag.workflows.deepsearcher.tools import log
from pikerag.workflows.deepsearcher.vector_db.base import BaseVectorDB

COLLECTION_ROUTE_PROMPT = """
I provide you with collection_name(s) and corresponding collection_description(s). Please select the collection names that may be related to the question and return a python list of str. If there is no collection related to the question, you can return an empty list.

"QUESTION": {question}
"COLLECTION_INFO": {collection_info}

When you return, you can ONLY return a python list of str, WITHOUT any other additional content. Your selected collection name list is:
"""


class CollectionRouter(BaseAgent):
    def __init__(self, llm: BaseLLM, vector_db: BaseVectorDB, **kwargs):
        self.llm = llm
        self.vector_db = vector_db
        self.all_collections = [
            collection_info.collection_name for collection_info in self.vector_db.list_collections()
        ]

    def invoke(self, query: str, **kwargs) -> Tuple[List[str], int]:
        consume_tokens = 0
        collection_infos = self.vector_db.list_collections()
        vector_db_search_prompt = COLLECTION_ROUTE_PROMPT.format(
            question=query,
            collection_info=[
                {
                    "collection_name": collection_info.collection_name,
                    "collection_description": collection_info.description,
                }
                for collection_info in collection_infos
            ],
        )
        chat_response = self.llm.chat(
            messages=[{"role": "user", "content": vector_db_search_prompt}]
        )
        selected_collections = self.llm.literal_eval(chat_response.content)
        consume_tokens += chat_response.total_tokens

        for collection_info in collection_infos:
            # If a collection description is not provided, use the query as the search query
            if not collection_info.description:
                selected_collections.append(collection_info.collection_name)
            # If the default collection exists, use the query as the search query
            if self.vector_db.default_collection == collection_info.collection_name:
                selected_collections.append(collection_info.collection_name)
        selected_collections = list(set(selected_collections))
        log.color_print(
            f"<think> Perform search [{query}] on the vector DB collections: {selected_collections} </think>\n"
        )
        return selected_collections, consume_tokens
