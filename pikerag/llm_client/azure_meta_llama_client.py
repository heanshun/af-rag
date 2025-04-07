# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
import os
import urllib.request
from typing import List

from pikerag.llm_client.base import BaseLLMClient
from pikerag.utils.logger import Logger


class AzureMetaLlamaClient(BaseLLMClient):
    NAME = "AzureMetaLlamaClient"

    def __init__(
        self, location: str = None, auto_dump: bool = True, logger: Logger=None,
        max_attempt: int = 5, exponential_backoff_factor: int = None, unit_wait_time: int = 60, **kwargs,
    ) -> None:
        super().__init__(location, auto_dump, logger, max_attempt, exponential_backoff_factor, unit_wait_time, **kwargs)

        self._init_agent(**kwargs)

    def _init_agent(self, **kwargs) -> None:
        llama_endpoint_name = kwargs.get("llama_endpoint_name", None)
        if llama_endpoint_name is None:
            llama_endpoint_name = "LLAMA_ENDPOINT"
        self._endpoint = os.getenv(llama_endpoint_name)
        assert self._endpoint, "LLAMA_ENDPOINT is not set!"

        llama_key_name = kwargs.get("llama_key_name", None)
        if llama_key_name is None:
            llama_key_name = "LLAMA_API_KEY"
        self._api_key = os.getenv(llama_key_name)
        assert self._api_key, "LLAMA_API_KEY is not set!"

    def _wrap_header(self, **llm_config) -> dict:
        assert "model" in llm_config, f"`model` must be provided in `llm_config` to call AzureMetaLlamaClient!"
        header = {
            'Content-Type':'application/json',
            'Authorization':('Bearer '+ self._api_key),
            'azureml-model-deployment': llm_config["model"],
        }
        return header

    def _wrap_body(self, messages: List[dict], **llm_config) -> bytes:
        data = {
            "input_data": {
                "input_string": messages,
                "parameters": llm_config,
            }
        }
        body = str.encode(json.dumps(data))
        return body

    def _get_response_with_messages(self, messages: List[dict], **llm_config) -> bytes:
        response: bytes = None
        num_attempt: int = 0
        while num_attempt < self._max_attempt:
            try:
                header = self._wrap_header(**llm_config)
                body = self._wrap_body(messages, **llm_config)
                req = urllib.request.Request(self._endpoint, body, header)
                response = urllib.request.urlopen(req).read()
                break

            except urllib.error.HTTPError as error:
                self.warning(f"  Failed due to Exception: {str(error.code)}")
                print(error.info())
                print(error.read().decode("utf8", 'ignore'))
                num_attempt += 1
                self._wait(num_attempt)
                self.warning(f"  Retrying...")

        return response

    def _get_content_from_response(self, response: bytes, messages: List[dict] = None) -> str:
        try:
            content = json.loads(response.decode('utf-8'))["output"]
            if content is None:
                warning_message = f"Non-Content returned"

                self.warning(warning_message)
                self.debug(f"  -- Complete response: {response}")
                if messages is not None and len(messages) >= 1:
                    self.debug(f"  -- Last message: {messages[-1]}")

                content = ""
        except:
            content = ""

        return content
