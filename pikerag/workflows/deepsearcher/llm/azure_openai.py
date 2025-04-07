from typing import Dict, List

from pikerag.workflows.deepsearcher.llm.base import BaseLLM, ChatResponse


class AzureOpenAI(BaseLLM):
    def __init__(
        self,
        model: str,
        azure_endpoint: str = None,
        api_key: str = None,
        api_version: str = None,
        **kwargs,
    ):
        self.model = model
        import os

        from openai import AzureOpenAI

        if azure_endpoint is None:
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if api_key is None:
            api_key = os.getenv("AZURE_OPENAI_KEY")
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
            **kwargs,
        )

    def chat(self, messages: List[Dict]) -> ChatResponse:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return ChatResponse(
            content=completion.choices[0].message.content,
            total_tokens=completion.usage.total_tokens,
        )
