from typing import List, Optional, Tuple

from pikerag.workflows.deepsearcher.agent import RAGAgent
from pikerag.workflows.deepsearcher.llm.base import BaseLLM
from pikerag.workflows.deepsearcher.tools import log
from pikerag.workflows.deepsearcher.vector_db import RetrievalResult

RAG_ROUTER_PROMPT = """Given a list of agent indexes and corresponding descriptions, each agent has a specific function. 
Given a query, select only one agent that best matches the agent handling the query, and return the index without any other information.

## Question
{query}

## Agent Indexes and Descriptions
{description_str}

Only return one agent index number that best matches the agent handling the query:
"""


class RAGRouter(RAGAgent):
    def __init__(
        self,
        llm: BaseLLM,
        rag_agents: List[RAGAgent],
        agent_descriptions: Optional[List[str]] = None,
    ):
        self.llm = llm
        self.rag_agents = rag_agents
        self.agent_descriptions = agent_descriptions
        if not self.agent_descriptions:
            try:
                self.agent_descriptions = [
                    agent.__class__.__description__ for agent in self.rag_agents
                ]
            except Exception:
                raise AttributeError(
                    "Please provide agent descriptions or set __description__ attribute for each agent class."
                )

    def _route(self, query: str) -> Tuple[RAGAgent, int]:
        description_str = "\n".join(
            [f"[{i + 1}]: {description}" for i, description in enumerate(self.agent_descriptions)]
        )
        prompt = RAG_ROUTER_PROMPT.format(query=query, description_str=description_str)
        chat_response = self.llm.chat(messages=[{"role": "user", "content": prompt}])
        import re

        # 提取整数
        match = re.search(r'\d+', chat_response.content)

        if match:
            selected_agent_index = int(match.group()) - 1
        else:
            raise ValueError(f"无法从 chat_response.content 提取有效的整数: {chat_response.content}")
        
        selected_agent = self.rag_agents[selected_agent_index]
        log.color_print(
            f"<think> Select agent [{selected_agent.__class__.__name__}] to answer the query [{query}] </think>\n"
        )
        return self.rag_agents[selected_agent_index], chat_response.total_tokens

    def retrieve(self, query: str, **kwargs) -> Tuple[List[RetrievalResult], int, dict]:
        agent, n_token_router = self._route(query)
        retrieved_results, n_token_retrieval, metadata = agent.retrieve(query, **kwargs)
        return retrieved_results, n_token_router + n_token_retrieval, metadata

    def query(self, query: str, **kwargs) -> Tuple[str, List[RetrievalResult], int]:
        agent, n_token_router = self._route(query)
        answer, retrieved_results, n_token_retrieval = agent.query(query, **kwargs)
        return answer, retrieved_results, n_token_router + n_token_retrieval
