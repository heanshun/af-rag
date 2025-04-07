from typing import List, Optional, Dict, Any
from .base import BaseLLM, ChatResponse

class CustomLLM(BaseLLM):
    def __init__(self, llm_function, max_tokens: int = 3000, temperature: float = 0.2):
        self.llm_function = llm_function
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        """
        生成回答
        """
        response = self.llm_function(
            prompt=prompt,
            history=history if history else [],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        return response

    def get_num_tokens(self, text: str) -> int:
        """
        获取文本的 token 数量（这里使用简单估算）
        """
        return len(text) // 4  # 粗略估计中文字符的 token 数

    def chat(self, messages: List[Dict]) -> Dict[str, Any]:
        """
        通过 generate 方法生成对话回复，并计算 token 数量
        """
        # 获取用户的最新消息作为 prompt
        prompt = messages[-1]["content"] if messages else ""

        # 调用 generate 方法获取生成的内容
        print(prompt)
        response_content = self.generate(prompt=prompt, history=messages[:-1])
        print("返回结果-----------")
        print(response_content)
        print("返回结果-----------")

        # 计算 token 数量
        total_tokens = self.get_num_tokens(response_content)

        return ChatResponse(
            content=response_content,
            total_tokens=total_tokens,
        )
