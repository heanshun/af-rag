from requests.exceptions import Timeout
import requests
import json
from typing import List
from pikerag.llm_client.base import BaseLLMClient
from pikerag.utils.logger import Logger
import os
from openai import OpenAI
import uuid

def get_data_from_response(r):
    try:
        response_json = json.loads(r.text)
        data = response_json.get("data", None)
        return data
    except json.JSONDecodeError:
        print("Error: Response is not a valid JSON")
        return None

def external_api_call(chat_id, model, prompt, user_message, api_url, timeout=100):
    print("请求内容：")
    print(user_message)
    try:
        r = requests.post(
            api_url,
            json={
                "chatId": uuid.uuid4().hex,
                "model": model,
                #"prompt": "",
                "userMessage": user_message
            },
            timeout=timeout
        )
        print(f'result = {r.text}')
        result = get_data_from_response(r)
        return result
    except Timeout:
        print(f"请求超时，程序退出。\n提问内容: {user_message}\n")
        exit(1)

class ExternalLLMClient(BaseLLMClient):
    NAME = "ExternalLLMClient"

    def __init__(
        self, location: str = None, auto_dump: bool = True, logger: Logger=None,
        max_attempt: int = 5, exponential_backoff_factor: int = None, unit_wait_time: int = 60, 
        chat_id: str = "1", model: str = "deepseek-r1", **kwargs,
    ) -> None:
        super().__init__(location, auto_dump, logger, max_attempt, exponential_backoff_factor, unit_wait_time, **kwargs)
        self.chat_id = chat_id
        self.model = model
        self.client = None

    def _init_client(self, api_key, api_url):
        if not self.client:
            print(f"初始化客户端，API URL: {api_url}")
            self.client = OpenAI(
                api_key=api_key,
                base_url=api_url
            )
            print("客户端初始化成功")

    def _wrap_body(self, messages: List[dict], **llm_config) -> tuple:
        api_key = llm_config.get("api_key", "")
        api_url = llm_config.get("api_url", "")
        model = llm_config.get("model", self.model)
        print(f"准备API调用，模型: {model}")
        self._init_client(api_key, api_url)
        return (messages, model)

    def _get_response_with_messages(self, messages: List[dict], **llm_config) -> bytes:
        messages, model = self._wrap_body(messages, **llm_config)
        try:
            print(f"发送消息: {messages}")
            completion = self.client.chat.completions.create(
                model=model,
                messages=[{"role": m["role"], "content": m["content"]} for m in messages]
            )
            print(f"API调用成功，返回结果: {completion.choices[0].message.content}")
            return completion.choices[0].message.content
        except Exception as e:
            self.warning(f"API调用失败: {e}")
            print(f"详细错误信息: {str(e)}")
            return ""

    def _get_content_from_response(self, response: bytes, messages: List[dict] = None) -> str:
        try:
            if not response:
                warning_message = "未返回内容"
                self.warning(warning_message)
                if messages is not None and len(messages) >= 1:
                    self.debug(f"最后的消息: {messages[-1]}")
                return ""
            return response
        except Exception as e:
            self.warning(f"解析响应失败: {e}")
            return ""