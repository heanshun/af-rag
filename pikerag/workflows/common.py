# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import dataclasses
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

from pikerag.utils.normalizer import normalize_answer, normalize_mask


@dataclass
class BaseQaData:
    question: str
    metadata: dict = field(default_factory=lambda: {})

    answer_metric_scores: Dict[str, float] = field(default_factory=lambda: {})
    answer_metadata: dict = field(default_factory=lambda: {})

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)

    @abstractmethod
    def update_answer(self, answer: Union[List[str], str]) -> None:
        raise NotImplementedError

    def update_answer_meta(self, meta_name: str, meta_value: Any) -> None:
        self.answer_metadata[meta_name] = meta_value


@dataclass
class MultipleChoiceQaData(BaseQaData):
    options: Dict[str, str] = field(default_factory=lambda: {})
    answer_mask_labels: List[str] = field(default_factory=lambda: [])

    answer_masks: List[str] = field(default_factory=lambda: [])

    def __post_init__(self) -> None:
        self.answer_mask_labels = sorted([normalize_mask(mask) for mask in self.answer_mask_labels])
        self.options = {normalize_mask(mask): option.strip() for mask, option in self.options.items()}
        return

    def update_answer(self, answer: Union[List[str], str]) -> None:
        if isinstance(answer, str):
            self.answer_masks = [normalize_mask(answer)]
        else:
            self.answer_masks = sorted([normalize_mask(mask) for mask in answer])
        return


@dataclass
class GenerationQaData(BaseQaData):
    answer_labels: List[str] = field(default_factory=lambda: [])

    answer: str = field(default_factory=lambda: "")

    def __post_init__(self) -> None:
        self.answer_labels = [normalize_answer(answer) for answer in self.answer_labels]
        return

    def update_answer(self, answer: str) -> None:
        self.answer = normalize_answer(answer)
        return
