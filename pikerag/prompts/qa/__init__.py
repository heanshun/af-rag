# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pikerag.prompts.qa.generation import (
    generation_qa_protocol, generation_qa_template, generation_qa_with_reference_protocol,
    generation_qa_with_reference_template, GenerationQaParser,
)
from pikerag.prompts.qa.multiple_choice import (
    multiple_choice_qa_protocol, multiple_choice_qa_template, multiple_choice_qa_with_reference_and_review_protocol,
    multiple_choice_qa_with_reference_and_review_template, multiple_choice_qa_with_reference_protocol,
    multiple_choice_qa_with_reference_template, MultipleChoiceQaParser, MultipleChoiceQaWithReferenceParser,
)

__all__ = [
    "generation_qa_protocol", "generation_qa_template",
    "generation_qa_with_reference_protocol", "generation_qa_with_reference_template",
    "GenerationQaParser",
    "multiple_choice_qa_protocol", "multiple_choice_qa_template",
    "multiple_choice_qa_with_reference_and_review_protocol", "multiple_choice_qa_with_reference_and_review_template",
    "multiple_choice_qa_with_reference_protocol", "multiple_choice_qa_with_reference_template",
    "MultipleChoiceQaParser", "MultipleChoiceQaWithReferenceParser",
]
