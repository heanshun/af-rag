# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from abc import abstractmethod
from typing import List, Tuple, Union

import numpy as np

from pikerag.utils.logger import Logger
from pikerag.workflows.common import BaseQaData, GenerationQaData, MultipleChoiceQaData


class BaseMetric:
    name: str = "Base"

    def __init__(self, num_rounds: int, num_data: int, main_logger: Logger=None, **kwargs) -> None:
        self._num_rounds: int = num_rounds
        self._num_data: int = num_data
        self._main_logger: Logger = main_logger

        self._round_scores: List[float] = []

    def on_round_test_start(self, round_id: str) -> None:
        self._round_total_score: float = 0

    def on_round_test_end(self, round_id: str) -> None:
        self._round_scores.append(self._round_total_score / self._num_data)

    @abstractmethod
    def _scoring_generation_qa(self, qa: GenerationQaData) -> Union[float, int]:
        raise NotImplementedError

    @abstractmethod
    def _scoring_multiple_choice_qa(self, qa: MultipleChoiceQaData) -> Union[float, int]:
        raise NotImplementedError

    def _scoring_qa(self, qa: BaseQaData) -> Union[float, int]:
        if isinstance(qa, GenerationQaData):
            return self._scoring_generation_qa(qa)
        elif isinstance(qa, MultipleChoiceQaData):
            return self._scoring_multiple_choice_qa(qa)
        else:
            raise ValueError(f"Unrecognized QA data type: {type(qa)}")

    def step_update(self, qa: BaseQaData) -> None:
        score = self._scoring_qa(qa)
        qa.answer_metric_scores[self.name] = score
        self._round_total_score += score

    def on_test_end(self) -> None:
        pass

    def _easy_reading_score_format(self, score: float) -> str:
        return f"{score:.2%}"

    def round_report(self) -> str:
        return self._easy_reading_score_format(self._round_scores[-1])

    def evaluation_report(self) -> Tuple[str, str, str, str]:
        return (
            self._easy_reading_score_format(np.mean(self._round_scores)),
            self._easy_reading_score_format(min(self._round_scores)),
            self._easy_reading_score_format(max(self._round_scores)),
            f"{np.std(self._round_scores):.5}"
        )
