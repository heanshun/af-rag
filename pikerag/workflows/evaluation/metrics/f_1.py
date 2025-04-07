# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from collections import Counter

from pikerag.workflows.common import GenerationQaData
from pikerag.workflows.evaluation.metrics.base import BaseMetric


class F1(BaseMetric):
    name: str = "F1"

    def _scoring_generation_qa(self, qa: GenerationQaData) -> float:
        f1_score: float = 0.0
        answer_tokens = qa.answer.split()
        for answer_label in qa.answer_labels:
            label_tokens = answer_label.split()
            common = Counter(answer_tokens) & Counter(label_tokens)
            num_same = sum(common.values())
            if num_same == 0:
                continue
            precision = 1.0 * num_same / len(answer_tokens)
            recall = 1.0 * num_same / len(label_tokens)
            f1 = (2 * precision * recall) / (precision + recall)
            f1_score = max(f1_score, f1)

        return f1_score
