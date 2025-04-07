# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Dict, List, Tuple, Any
import json
from pikerag.prompts import BaseContentParser, CommunicationProtocol, MessageTemplate
from pikerag.utils.json_parser import parse_json_v2, parse_json
from pikerag.workflows.deepsearcher.vector_db import RetrievalResult


# API选择模板
api_selection_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant that selects appropriate APIs or resources based on queries."),
        ("user", """
Given the following available APIs and resources, select the most appropriate one to answer the query and provide the required parameters in JSON format.

## Available APIs and Resources
{available_apis_str}

## Query
{content}

Respond with a JSON object containing:
1. "selected_api_index": the index of the selected API
2. "parameters": a JSON object with the required parameters

Example response:
{{"selected_api_index": 0, "parameters": {{"user_id": "123"}}}}

Respond with the JSON object only, do not explain yourself or output anything else.
""".strip()),
    ],
    input_variables=["content", "available_apis_str"],
)

class ApiSelectionParser(BaseContentParser):
    def encode(
        self, content: str, available_apis: List[Dict[str, Any]] = [], **kwargs,
    ) -> Tuple[str, dict]:
        formatted_apis = self._format_available_apis(available_apis)
        return content, {
            "available_apis_str": formatted_apis,
        }

    def decode(self, content: str, **kwargs) -> Dict[str, Any]:
        try:
            # 尝试解析JSON响应
            result = json.loads(content)
            if not isinstance(result, dict):
                return {"selected_api_index": -1, "parameters": {}}
            
            # 验证必要的字段
            if "selected_api_index" not in result or "parameters" not in result:
                return {"selected_api_index": -1, "parameters": {}}
            
            # 确保索引是整数
            try:
                result["selected_api_index"] = int(result["selected_api_index"])
            except (ValueError, TypeError):
                return {"selected_api_index": -1, "parameters": {}}
            
            return result
        except Exception as e:
            print(f"[ApiSelectionParser] Content: {content}\nException: {e}")
            return {"selected_api_index": -1, "parameters": {}}
    
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

api_selection_protocol = CommunicationProtocol(
    template=api_selection_template,
    parser=ApiSelectionParser(),
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
        try:
            # 尝试解析JSON响应
            result = json.loads(content)
            if not isinstance(result, dict):
                return {"selected_agent_index": -1}
            
            # 验证必要的字段
            if "selected_agent_index" not in result:
                return {"selected_agent_index": -1}
            
            # 确保索引是整数
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