# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from requests.exceptions import Timeout
import requests

import json
import os
import urllib.request
from typing import List

from pikerag.llm_client.base import BaseLLMClient
from pikerag.utils.logger import Logger

def llama3_replying(prompt, history=None, max_tokens=3000, temperature=0.2):
    if history is None:
        history = []
    api_url = 'http://192.168.50.179:8091/gpt'
    try:
        r = requests.post(
            api_url,
            json={
                "prompt": prompt,
                "history": history,
                "max_tokens": max_tokens,
                "top_p": 0.0,
                "temperature": temperature,
            },
            timeout=100  # 设置超时时间为10秒
        )
        # 正常处理响应...
    except Timeout:
        print(f"请求超时，程序退出。\n{['prompt']}\n")
        exit(1)  # 使用非零值退出，表示发生了错误

    content = r.text
    # 取</think>之后的内容
    if "</think>" in content:
        content = content.split("</think>")[1]
    return content.strip()

class CompanyLLMClient(BaseLLMClient):
    NAME = "CompanyLLMClient"

    def __init__(
        self, location: str = None, auto_dump: bool = True, logger: Logger=None,
        max_attempt: int = 5, exponential_backoff_factor: int = None, unit_wait_time: int = 60, **kwargs,
    ) -> None:
        super().__init__(location, auto_dump, logger, max_attempt, exponential_backoff_factor, unit_wait_time, **kwargs)
        self._init_agent(**kwargs)

    def _init_agent(self, **kwargs) -> None:
        # 从环境变量或配置中获取端点和API密钥
        endpoint_name = kwargs.get("endpoint_name", "COMPANY_LLM_ENDPOINT")
        self._endpoint = os.getenv(endpoint_name)
        assert self._endpoint, f"{endpoint_name} is not set!"

        api_key_name = kwargs.get("api_key_name", "COMPANY_LLM_API_KEY")
        self._api_key = os.getenv(api_key_name)
        assert self._api_key, f"{api_key_name} is not set!"

    def _wrap_header(self, **llm_config) -> dict:
        # 根据公司API要求构建请求头
        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._api_key}',
        }
        return header

    def _wrap_body(self, messages: List[dict], **llm_config) -> bytes:
        # 根据公司API要求构建请求体
        prompt = messages[-1]["content"]  # 获取最后一个用户的内容
        history = messages[:-1]  # 去掉最后一个用户的内容
        '''
        data = {
            "prompt": prompt,
            "history": history,
            "temperature": llm_config.get("temperature", 0.7),
            "max_tokens": llm_config.get("max_tokens", 1000),
            "model": llm_config.get("model", "default"),
            # 其他参数...
        }
        '''
        return (prompt, history)

    def _get_response_with_messages(self, messages: List[dict], **llm_config) -> bytes:
        print("进入取消息")
        response: bytes = None
        num_attempt: int = 0
#       while num_attempt < self._max_attempt:
#            try:
                # header = self._wrap_header(**llm_config)
                # body = self._wrap_body(messages, **llm_config)
                # req = urllib.request.Request(self._endpoint, body, header)
                # response = urllib.request.urlopen(req).read()
        (prompt, history) = self._wrap_body(messages, **llm_config)
        print(prompt)
        print(history)
        response = llama3_replying(prompt, history=history)
        print("llama response----------")
        print(response)
#                break
        '''
            except urllib.error.HTTPError as error:
                self.warning(f"  Failed due to Exception: {str(error.code)}")
                print(error.info())
                print(error.read().decode("utf8", 'ignore'))
                num_attempt += 1
                self._wait(num_attempt)
                self.warning(f"  Retrying...")
        '''
        return response

    def _get_content_from_response(self, response: bytes, messages: List[dict] = None) -> str:
        try:
            # 根据公司API的响应格式解析内容
            '''
            response_json = json.loads(response.decode('utf-8'))
            content = response_json.get("response", "")  # 假设响应中包含 "response" 字段
            
            if not content:
                warning_message = "Non-Content returned"
                self.warning(warning_message)
                self.debug(f"  -- Complete response: {response}")
                if messages is not None and len(messages) >= 1:
                    self.debug(f"  -- Last message: {messages[-1]}")
                content = ""
            '''
            content = response    
        except Exception as e:
            self.warning(f"Failed to parse response: {e}")
            content = ""

        return content 