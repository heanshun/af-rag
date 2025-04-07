# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pikerag.prompts.tagging.atom_question_tagging import (
    atom_question_tagging_protocol, atom_question_tagging_template, AtomQuestionParser,
)

from pikerag.prompts.tagging.semantic_tagging import (
    semantic_tagging_protocol, semantic_tagging_template, SemanticTaggingParser,
)

__all__ = [
    "semantic_tagging_protocol", "semantic_tagging_template", "SemanticTaggingParser",
    "atom_question_tagging_protocol", "atom_question_tagging_template", "AtomQuestionParser",
]
