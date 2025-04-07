# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pikerag.workflows.common import GenerationQaData, MultipleChoiceQaData
from pikerag.workflows.evaluation.metrics.base import BaseMetric


class ExactMatch(BaseMetric):
    name: str = "ExactMatch"

    def _scoring_generation_qa(self, qa: GenerationQaData) -> int:
        for answer_label in qa.answer_labels:
            if qa.answer == answer_label:
                return 1

        return 0

    def _scoring_multiple_choice_qa(self, qa: MultipleChoiceQaData) -> int:
        if len(qa.answer_masks) != len(qa.answer_mask_labels):
            return 0

        for mask_in_answer, mask_in_label in zip(qa.answer_masks, qa.answer_mask_labels):
            if mask_in_answer != mask_in_label:
                return 0

        return 1
