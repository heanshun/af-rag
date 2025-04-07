# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Tuple

from pikerag.llm_client import AzureOpenAIClient
from pikerag.prompts import BaseContentParser, CommunicationProtocol, MessageTemplate
from pikerag.utils.logger import Logger
from pikerag.workflows.common import GenerationQaData
from pikerag.workflows.evaluation.metrics.base import BaseMetric


answer_judge_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant good at question answering and answer scoring."),
        ("user", """
# Task
Providing a question and its correct answer labels, your task is to analyze whether a given answer is correct or not. An answer is treated as correct if the meaning of any label is expressed in the answer. Redundant expression in answer is allowed.

# Question
{question}

# Correct Answer Labels
{labels}

# Answer that Require Judgment
{content}

Is the answer correct or not? You output should only be "Yes" or "No".
""".strip())
    ],
    input_variables=["question", "labels", "content"],
)


class AnswerJudgementParser(BaseContentParser):
    def encode(self, content: str, **kwargs) -> Tuple[str, dict]:
        qa = kwargs.get("qa", None)
        assert isinstance(qa, GenerationQaData)

        return content, {
            "question": qa.question,
            "labels": "\n".join(qa.answer_labels),
        }

    def decode(self, content: str, **kwargs) -> int:
        content = content.strip().lower()
        if content == "yes" or content == "yes.":
            return 1
        elif content == "no" or content == "no.":
            return 0
        else:
            print(f"Cannot parse judgement response: {content}")
            return 0.5


answer_judge_protocol = CommunicationProtocol(
    template=answer_judge_template,
    parser=AnswerJudgementParser(),
)


class LLM(BaseMetric):
    name: str = "LLM-Accuracy"

    def __init__(self, num_rounds: int, num_data: int, main_logger: Logger = None, **kwargs) -> None:
        super().__init__(num_rounds, num_data, main_logger, **kwargs)

        self._client: AzureOpenAIClient = AzureOpenAIClient(
            # TODO: enable kwargs for Metric initialization.
            location=kwargs.get("cache_location", None),
        )
        self._llm_config = {
            "model": kwargs.get("model", "gpt-4"),
            "temperature": kwargs.get("temperature", 0),
        }

    def _scoring_generation_qa(self, qa: GenerationQaData) -> float:
        messages = answer_judge_protocol.process_input(content=qa.answer, qa=qa)
        judgement = self._client.generate_content_with_messages(messages, **self._llm_config)
        score = answer_judge_protocol.parse_output(judgement)
        return score
