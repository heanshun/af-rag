# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import rouge

from pikerag.utils.logger import Logger
from pikerag.workflows.common import GenerationQaData
from pikerag.workflows.evaluation.metrics.base import BaseMetric


class Rouge(BaseMetric):
    name: str = "Rouge"

    def __init__(self, num_rounds: int, num_data: int, main_logger: Logger = None, **kwargs) -> None:
        super().__init__(num_rounds, num_data, main_logger, **kwargs)

        self._rouge = rouge.Rouge()

    def _scoring_qa(self, qa: GenerationQaData) -> float:
        assert isinstance(qa, GenerationQaData), f"Rouge can only applied to GenerationQaData, but {type(qa)} provided"

        rouge_score: float = 0.0
        for answer_label in qa.answer_labels:
            scores: dict = self._rouge.get_scores(qa.answer, answer_label, avg=True)
            rouge_score = max(rouge_score, scores["rouge-1"]["f"])

        return rouge_score
