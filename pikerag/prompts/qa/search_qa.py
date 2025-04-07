# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Dict, List, Tuple
from pikerag.prompts import BaseContentParser, CommunicationProtocol, MessageTemplate


search_qa_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant on question answering with search capabilities."),
        ("user", """Answer the given question. \
You must conduct reasoning inside <think> and </think> first every time you get new information. \
After reasoning, if you find you lack some knowledge, you can call a search engine by <search> query </search> and it will return the top searched results between <information> and </information>. \
You can search as many times as your want. \
If you find no further external knowledge needed, you can directly provide the answer inside <answer> and </answer>, without detailed illustrations. For example, <answer> Beijing </answer>. Question: {content}\n
""".strip()),
    ],
    input_variables=["content"],
)


class SearchQaParser(BaseContentParser):
    def encode(
        self, content: str, **kwargs
    ) -> Tuple[str, dict]:
        return content, {}

    def decode(self, content: str, **kwargs) -> Dict[str, str]:
        # Extract the final answer from the <answer> tags
        try:
            import re
            answer_pattern = r"<answer>(.*?)</answer>"
            think_pattern = r"<think>(.*?)</think>"
            
            answer_match = re.search(answer_pattern, content, re.DOTALL)
            think_matches = re.findall(think_pattern, content, re.DOTALL)
            
            answer = answer_match.group(1).strip() if answer_match else "No answer provided"
            rationale = " ".join([think.strip() for think in think_matches])
            
            return {
                "answer": answer,
                "rationale": rationale
            }
        except Exception as e:
            print(f"[SearchQaParser] Content: {content}\nException: {e}")
            return {
                "answer": "parsing error",
                "rationale": "parsing error"
            }


search_qa_protocol = CommunicationProtocol(
    template=search_qa_template,
    parser=SearchQaParser(),
) 