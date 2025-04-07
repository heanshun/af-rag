# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List

from pikerag.llm_client.base import BaseLLMClient
from pikerag.utils.logger import Logger

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


def get_torch_dtype(type_str: str) -> torch.dtype:
    type_str = type_str.strip().lower()
    if type_str.startswith("torch."):
        type_str = type_str[6:]
    try:
        torch_dtype = getattr(torch, type_str)
        return torch_dtype
    except:
        raise ValueError(f"Unrecognized torch.dtype: {type_str}")


class HFMetaLlamaClient(BaseLLMClient):
    NAME = "HuggingFaceMetaLlamaClient"

    def __init__(
        self, location: str = None, auto_dump: bool = True, logger: Logger=None, llm_config: dict = None,
        max_attempt: int = 5, exponential_backoff_factor: int = None, unit_wait_time: int = 60, **kwargs,
    ) -> None:
        super().__init__(location, auto_dump, logger, max_attempt, exponential_backoff_factor, unit_wait_time, **kwargs)

        assert "model" in llm_config, "`model` should be provided in `llm_config` to initialize `HFMetaLlamaClient`!"
        self._model_id: str = llm_config["model"]
        self._init_agent(**kwargs)

    def _init_agent(self, **kwargs) -> None:
        self._tokenizer = AutoTokenizer.from_pretrained(self._model_id)

        if "torch_dtype" in kwargs:
            kwargs["torch_dtype"] = get_torch_dtype(kwargs["torch_dtype"])
        self._client = AutoModelForCausalLM.from_pretrained(self._model_id, **kwargs)

        return

    def _get_response_with_messages(self, messages: List[dict], **llm_config) -> str:
        llm_config.pop("model", None)
        # temperature must be positive, 1e-5 works same as 0
        llm_config["temperature"] = max(llm_config.get("temperature", 1e-5), 1e-5)

        response = None
        num_attempt: int = 0
        while num_attempt < self._max_attempt:
            try:
                input_ids = self._tokenizer.apply_chat_template(
                    messages,
                    add_generation_prompt=True,
                    return_tensors="pt",
                ).to(self._client.device)

                outputs = self._client.generate(
                    input_ids,
                    pad_token_id=self._tokenizer.eos_token_id,
                    **llm_config,
                )

                response = outputs[0][input_ids.shape[-1]:]

                break

            except Exception as e:
                self.warning(f"  Failed due to Exception: {e}")
                num_attempt += 1
                self._wait(num_attempt)
                self.warning(f"  Retrying...")

        return response

    def _get_content_from_response(self, response, messages: List[dict] = None) -> str:
        try:
            content = self._tokenizer.decode(response, skip_special_tokens=True)
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
