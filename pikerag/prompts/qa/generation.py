# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Dict, List, Tuple

from pikerag.prompts import BaseContentParser, CommunicationProtocol, MessageTemplate
from pikerag.utils.json_parser import parse_json_v2, parse_json


generation_qa_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant on question answering."),
        ("user", """
# Task
Your task is to give your answer to the given question.

# Output format
Your output should strictly follow the format below. Make sure your output parsable by json in Python.
{{
    "answer": <Your answer, format it as a string.>,
    "rationale": <Rationale behind your answer>
}}

# Question
{content}

Let's think step by step.
""".strip()),
    ],
    input_variables=["content"],
)


generation_qa_with_reference_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant on question answering."),
        ("user", """
# Task
Your task is to answer a question referring to a given context, if any.
For answering the Question at the end, you need to first read the articles, reports, or context provided, then give your final answer.

# Output format
Your output should strictly follow the format below. Make sure your output parsable by json in Python.
{{
    "answer": <Your Answer, format it as a string.>,
    "rationale": <rationale behind your choice>
}}

# Context, if any
{context_if_any}

# Question
{content}{yes_or_no_limit}

Let's think step by step.
""".strip()),
    ],
    input_variables=["content", "context_if_any", "yes_or_no_limit"],
)


class GenerationQaParser(BaseContentParser):
    def encode(
        self, content: str, references: List[str]=[], context_len_limit: int=80000, **kwargs,
    ) -> Tuple[str, dict]:
        # Construct `yes_or_no_limit` instruction.
        # TODO: update the logic when "question_type" enabled.
        answer_labels = kwargs.get("answer_labels", [])
        if len(answer_labels) == 1 and answer_labels[0] in ["yes", "no"]:
            yes_or_no_limit = """ Your answer shall be "Yes" or "No"."""
        else:
            yes_or_no_limit = ""

        # Construct reference contexts.
        if len(references) > 0:
            context_if_any = "Related context, reports, or articles: "
            for context in list(set(references)):
                context_if_any += f"\n{context}\n"
                if len(context_if_any) >= context_len_limit:
                    break
        else:
            context_if_any = ""

        return content, {
            "yes_or_no_limit": yes_or_no_limit,
            "context_if_any": context_if_any,
        }

    def decode(self, content: str, **kwargs) -> Dict[str, str]:
        try:
            output = parse_json(content)
        except Exception as e:
            print(f"[QaParser] Content: {content}\nException: {e}")

            try:
                output = parse_json_v2(content)
            except Exception as e2:
                print(f"  [QaParser] Exception: {e2}")

                return {  # TODO
                    "answer": "parsing error",
                    "rationale": "parsing error",
                }

        for key, value in output.items():
            output[key] = str(value)
        return output


generation_qa_protocol = CommunicationProtocol(
    template=generation_qa_template,
    parser=GenerationQaParser(),
)


generation_qa_with_reference_protocol = CommunicationProtocol(
    template=generation_qa_with_reference_template,
    parser=GenerationQaParser(),
)
