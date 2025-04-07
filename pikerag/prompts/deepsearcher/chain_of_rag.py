# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Dict, List, Tuple, Any
import json
from pikerag.prompts import BaseContentParser, CommunicationProtocol, MessageTemplate
from pikerag.utils.json_parser import parse_json_v2
from pikerag.workflows.deepsearcher.vector_db import RetrievalResult
from pikerag.prompts.deepsearcher.agent_protocols import (
    api_selection_protocol,
    rag_router_protocol,
)


# 后续查询生成模板
followup_query_template = MessageTemplate(
    template=[
        ("system", "You are using a search tool to answer the main query by iteratively searching the database."),
        ("user", """
You are using a search tool to answer the main query by iteratively searching the database. Given the following intermediate queries and answers, generate a new simple follow-up question that can help answer the main query. You may rephrase or decompose the main query when previous answers are not helpful. Ask simple follow-up questions only as the search tool may not understand complex questions.

## Previous intermediate queries and answers
{intermediate_context_str}

## Main query to answer
{content}

Respond with a simple follow-up question that will help answer the main query, do not explain yourself or output anything else.
""".strip()),
    ],
    input_variables=["content", "intermediate_context_str"],
)

class FollowupQueryParser(BaseContentParser):
    def encode(
        self, content: str, intermediate_context: List[str] = [], **kwargs,
    ) -> Tuple[str, dict]:
        return content, {
            "intermediate_context_str": "\n".join(intermediate_context) if intermediate_context else "",
        }

    def decode(self, content: str, **kwargs) -> Dict[str, str]:
        # 取</think>之后的内容
        if "</think>" in content:
            content = content.split("</think>")[1]
        return content.strip()

# 中间答案生成模板
intermediate_api_answer_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant that generates answers based on provided documents or API calls."),
        ("user", """
Given the following documents and available APIs, determine whether to use documents or call an API to answer the query. 

## Available APIs
{available_apis_str}

## Documents
{retrieved_documents_str}

## Query
{content}

First, decide whether to use documents or call an API:
1. If the documents contain sufficient information, use those to generate an answer
2. If an API call would be more appropriate, select the API and specify required parameters

Respond in JSON format with the following structure:
{{
  "use_api": true/false,
  "api_selection": {{
    "selected_api_index": 0,  // Only include if use_api is true
    "parameters": {{}}  // Only include if use_api is true
  }},
  "answer": "Your concise answer based on documents or indicating an API will be called"
}}

If documents don't contain useful information and no API is suitable, respond with "No relevant information found" in the answer field.
""".strip()),
    ],
    input_variables=["content", "retrieved_documents_str", "available_apis_str"],
)

class IntermediateAPIAnswerParser(BaseContentParser):
    def encode(
        self, content: str, retrieved_documents: List[RetrievalResult] = [],
        available_apis: List[Dict[str, Any]] = [], text_window_splitter: bool = True, **kwargs,
    ) -> Tuple[str, dict]:
        formatted_documents = self._format_retrieved_results(retrieved_documents, text_window_splitter)
        formatted_apis = self._format_available_apis(available_apis)
        return content, {
            "retrieved_documents_str": formatted_documents,
            "available_apis_str": formatted_apis,
        }

    def decode(self, content: str, **kwargs) -> Dict[str, Any]:
        #try:
            # 尝试解析 JSON
            result = parse_json_v2(content)

            # 构建返回结果
            response = {}

            # 处理 use_api 字段
            if "use_api" in result:
                response["use_api"] = bool(result["use_api"])

                # 处理 API 选择
                if response["use_api"] and "api_selection" in result:
                    api_selection = result["api_selection"]
                    if isinstance(api_selection, dict):
                        response["selected_api_index"] = api_selection.get("selected_api_index", -1)
                        response["parameters"] = api_selection.get("parameters", {})
            else:
                # 默认不使用 API
                response["use_api"] = False

            # 添加回答内容
            response["intermediate_answer"] = result.get("answer", content.strip())

            return response
        #except Exception as e:
        #    print(f"[IntermediateAnswerParser] Content: {content}\nException: {e}")
            # 如果解析失败，返回原始内容
        #    return {"use_api": False, "intermediate_answer": content.strip()}
    
    def _format_retrieved_results(self, retrieved_results: List[RetrievalResult], text_window_splitter: bool = True) -> str:
        formatted_documents = []
        for i, result in enumerate(retrieved_results):
            text = result
            formatted_documents.append(f"<Document {i}>\n{text}\n<\Document {i}>")
        return "\n".join(formatted_documents)

    def _format_available_apis(self, available_apis: List[Dict[str, Any]]) -> str:
        formatted_apis = []
        for i, api in enumerate(available_apis):
            api_str = f"<API {i}>\n"
            if "name" in api:
                api_str += f"Name: {api['name']}\n"
            if "description" in api:
                api_str += f"Description: {api['description']}\n"
            if "endpoint" in api:
                api_str += f"Endpoint: {api['endpoint']}\n"
            if "method" in api:
                api_str += f"Method: {api['method']}\n"
            if "parameters" in api:
                api_str += f"Parameters: {api['parameters']}\n"
            api_str += f"</API {i}>"
            formatted_apis.append(api_str)
        return "\n".join(formatted_apis)


intermediate_answer_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant that generates answers based on provided documents."),
        ("user", """
Given the following documents, generate an appropriate answer for the query. DO NOT hallucinate any information, only use the provided documents to generate the answer. Respond "No relevant information found" if the documents do not contain useful information.

## Documents
{retrieved_documents_str}

## Query
{content}

Respond with a concise answer only, do not explain yourself or output anything else.
""".strip()),
    ],
    input_variables=["content", "retrieved_documents_str"],
)


class IntermediateAnswerParser(BaseContentParser):
    def encode(
            self, content: str, retrieved_documents: List[RetrievalResult] = [], text_window_splitter: bool = True,
            **kwargs,
    ) -> Tuple[str, dict]:
        formatted_documents = self._format_retrieved_results(retrieved_documents, text_window_splitter)
        return content, {
            "retrieved_documents_str": formatted_documents,
        }

    def decode(self, content: str, **kwargs) -> Dict[str, str]:
        # 取</think>之后的内容
        if "</think>" in content:
            content = content.split("</think>")[1]
        return content.strip()

    def _format_retrieved_results(self, retrieved_results: List[RetrievalResult],
                                  text_window_splitter: bool = True) -> str:
        formatted_documents = []
        for i, result in enumerate(retrieved_results):
            text = result
            formatted_documents.append(f"<Document {i}>\n{text}\n<\Document {i}>")
        return "\n".join(formatted_documents)


# 最终答案生成模板
final_answer_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant that generates final answers by combining relevant information."),
        ("user", """
Given the following intermediate queries and answers, generate a final answer for the main query by combining relevant information. Note that intermediate answers are generated by an LLM and may not always be accurate.

## Documents
{retrieved_documents_str}

## Intermediate queries and answers
{intermediate_context_str}

## Main query
{query}

Respond with an appropriate answer only, do not explain yourself or output anything else.
""".strip()),
    ],
    input_variables=["retrieved_documents_str", "intermediate_context_str", "query"],
)

class FinalAnswerParser(BaseContentParser):
    def encode(
        self, content: str, retrieved_documents: List[RetrievalResult] = [], 
        intermediate_context: List[str] = [], text_window_splitter: bool = True, **kwargs,
    ) -> Tuple[str, dict]:
        formatted_documents = self._format_retrieved_results(retrieved_documents, text_window_splitter)
        return "", {
            "query": content,
            "retrieved_documents_str": formatted_documents,
            "intermediate_context_str": "\n".join(intermediate_context) if intermediate_context else "",
        }

    def decode(self, content: str, **kwargs) -> Dict[str, str]:
        # 取</think>之后的内容
        if "</think>" in content:
            content = content.split("</think>")[1]
        return {"final_answer": content.strip()}
    
    def _format_retrieved_results(self, retrieved_results: List[RetrievalResult], text_window_splitter: bool = True) -> str:
        formatted_documents = []
        for i, result in enumerate(retrieved_results):
            text = result
            formatted_documents.append(f"<Document {i}>\n{text}\n<\Document {i}>")
        return "\n".join(formatted_documents)


# 反思提示模板（用于早期停止）
reflection_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant that judges whether there is enough information to answer a query."),
        ("user", """
Given the following intermediate queries and answers, judge whether you have enough information to answer the main query. If you believe you have enough information, respond with "Yes", otherwise respond with "No".

## Intermediate queries and answers
{intermediate_context_str}

## Main query
{content}

Respond with "Yes" or "No" only, do not explain yourself or output anything else.
""".strip()),
    ],
    input_variables=["intermediate_context_str", "content"],
)

class ReflectionParser(BaseContentParser):
    def encode(
        self, content: str, intermediate_context: List[str] = [], **kwargs,
    ) -> Tuple[str, dict]:
        return content, {
            "intermediate_context_str": "\n".join(intermediate_context) if intermediate_context else "",
        }

    def decode(self, content: str, **kwargs) -> Dict[str, bool]:
        # 直接返回内容，不需要解析JSON
        content = content.strip().lower()
        has_enough_info = "yes" in content
        return {"has_enough_info": has_enough_info}


# 获取支持文档模板
get_supported_docs_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant that selects documents supporting a Q-A pair."),
        ("user", """
Given the following documents, select the ones that are support the Q-A pair.

## Documents
{retrieved_documents_str}

## Q-A Pair
### Question
{content}
### Answer
{answer_str}

Respond with a python list of indices of the selected documents.
""".strip()),
    ],
    input_variables=["retrieved_documents_str", "content", "answer_str"],
)


class GetSupportedDocsParser(BaseContentParser):
    def encode(
        self, content: str, retrieved_documents: List[RetrievalResult] = [], 
        answer: str = "", text_window_splitter: bool = True, **kwargs,
    ) -> Tuple[str, dict]:
        formatted_documents = self._format_retrieved_results(retrieved_documents, text_window_splitter)
        return content, {
            "retrieved_documents_str": formatted_documents,
            "answer_str": answer,
        }

    def decode(self, content: str, **kwargs) -> Dict[str, Any]:
        # 取</think>之后的内容
        if "</think>" in content:
            content = content.split("</think>")[1]
        try:
            # 这里假设返回的是一个Python列表的字符串表示
            # 实际使用时，需要在调用方进行安全的eval
            return {"supported_doc_indices": content.strip()}
        except Exception as e:
            print(f"[GetSupportedDocsParser] Content: {content}\nException: {e}")
            return {"supported_doc_indices": "[]"}
    
    def _format_retrieved_results(self, retrieved_results: List[RetrievalResult], text_window_splitter: bool = True) -> str:
        formatted_documents = []
        for i, result in enumerate(retrieved_results):
            if text_window_splitter and "wider_text" in result.metadata:
                text = result.metadata["wider_text"]
            else:
                text = result.text
            formatted_documents.append(f"<Document {i}>\n{text}\n<\Document {i}>")
        return "\n".join(formatted_documents)


# 创建协议对象
followup_query_protocol = CommunicationProtocol(
    template=followup_query_template,
    parser=FollowupQueryParser(),
)

intermediate_answer_protocol = CommunicationProtocol(
    template=intermediate_answer_template,
    parser=IntermediateAnswerParser(),
)

intermediate_api_answer_protocol = CommunicationProtocol(
    template=intermediate_api_answer_template,
    parser=IntermediateAPIAnswerParser(),
)

final_answer_protocol = CommunicationProtocol(
    template=final_answer_template,
    parser=FinalAnswerParser(),
)

reflection_protocol = CommunicationProtocol(
    template=reflection_template,
    parser=ReflectionParser(),
)

get_supported_docs_protocol = CommunicationProtocol(
    template=get_supported_docs_template,
    parser=GetSupportedDocsParser(),
)

# RAG路由模板
rag_router_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant that selects the most appropriate agent to handle queries."),
        ("user", """
Given a list of agent indexes and corresponding descriptions, each agent has a specific function. 
Given a query, select only one agent that best matches the agent handling the query.

## Question
{content}

## Agent Indexes and Descriptions
{description_str}

Respond with a JSON object containing:
1. "selected_agent_index": the index of the selected agent (1-based index)

Example response:
{{"selected_agent_index": 1}}

Respond with the JSON object only, do not explain yourself or output anything else.
""".strip()),
    ],
    input_variables=["content", "description_str"],
)

class RagRouterParser(BaseContentParser):
    def encode(
        self, content: str, agent_descriptions: List[str] = [], **kwargs,
    ) -> Tuple[str, dict]:
        description_str = "\n".join(
            [f"[{i + 1}]: {description}" for i, description in enumerate(agent_descriptions)]
        )
        return content, {
            "description_str": description_str,
        }

    def decode(self, content: str, **kwargs) -> Dict[str, Any]:
        # 取</think>之后的内容
        if "</think>" in content:
            content = content.split("</think>")[1]
        try:
            result = json.loads(content)
            if not isinstance(result, dict):
                return {"selected_agent_index": -1}

            if "selected_agent_index" not in result:
                return {"selected_agent_index": -1}

            try:
                result["selected_agent_index"] = int(result["selected_agent_index"])
            except (ValueError, TypeError):
                return {"selected_agent_index": -1}
            
            return result
        except Exception as e:
            print(f"[RagRouterParser] Content: {content}\nException: {e}")
            return {"selected_agent_index": -1}

rag_router_protocol = CommunicationProtocol(
    template=rag_router_template,
    parser=RagRouterParser(),
) 