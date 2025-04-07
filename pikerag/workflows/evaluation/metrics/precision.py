# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from collections import Counter

from pikerag.workflows.common import BaseQaData, GenerationQaData, MultipleChoiceQaData
from pikerag.workflows.evaluation.metrics.base import BaseMetric


class Precision(BaseMetric):
    name: str = "Precision"

    def _scoring_generation_qa(self, qa: GenerationQaData) -> float:
        max_score: float = 0.0
        answer_tokens = qa.answer.split()
        if len(answer_tokens) == 0:
            return 0
        for answer_label in qa.answer_labels:
            label_tokens = answer_label.split()
            common = Counter(answer_tokens) & Counter(label_tokens)
            num_same = sum(common.values())
            precision = 1.0 * num_same / len(answer_tokens)
            if precision > max_score:
                max_score = precision
        return max_score

    def _scoring_multiple_choice_qa(self, qa: MultipleChoiceQaData) -> float:
        if len(qa.answer_masks) == 0:
            return 0
        num_correct = sum([int(ans in qa.answer_mask_labels) for ans in qa.answer_masks])
        return 1.0 * num_correct / len(qa.answer_masks)
