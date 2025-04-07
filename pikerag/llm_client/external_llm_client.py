from requests.exceptions import Timeout
import requests
import json
from typing import List
from pikerag.llm_client.base import BaseLLMClient
from pikerag.utils.logger import Logger
import uuid

def get_data_from_response(r):
    try:
        response_json = json.loads(r.text)
        data = response_json.get("data", None)
        return data
    except json.JSONDecodeError:
        print("Error: Response is not a valid JSON")
        return None

def external_api_call(chat_id, model, prompt, user_message, timeout=100):
    api_url = 'http://192.168.50.67:31467/api/af-liuli/ai/syncChat'
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
        chat_id: str = "1", model: str = "qwen-turbo", **kwargs,
    ) -> None:
        super().__init__(location, auto_dump, logger, max_attempt, exponential_backoff_factor, unit_wait_time, **kwargs)
        self.chat_id = chat_id
        self.model = model

    def _wrap_body(self, messages: List[dict], **llm_config) -> tuple:
        print("llm_config = ", llm_config)
        prompt = llm_config.get("prompt", "")
        user_message = messages[-1]["content"] if messages else ""
        model = llm_config.get("model", self.model)
        return (self.chat_id, model, prompt, user_message)

    def _get_response_with_messages(self, messages: List[dict], **llm_config) -> bytes:
        chat_id, model, prompt, user_message = self._wrap_body(messages, **llm_config)
        response = external_api_call(
            chat_id=chat_id,
            model=model,
            prompt=prompt,
            user_message=user_message
        )
        return response

    def _get_content_from_response(self, response: bytes, messages: List[dict] = None) -> str:
        try:
            content = response
            if not content:
                warning_message = "未返回内容"
                self.warning(warning_message)
                self.debug(f"完整响应: {response}")
                if messages is not None and len(messages) >= 1:
                    self.debug(f"最后的消息: {messages[-1]}")
                content = ""
        except Exception as e:
            self.warning(f"解析响应失败: {e}")
            content = ""
        return content