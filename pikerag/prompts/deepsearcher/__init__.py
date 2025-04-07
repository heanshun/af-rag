# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pikerag.prompts.deepsearcher.chain_of_rag import (
    followup_query_protocol, followup_query_template,
    intermediate_answer_protocol, intermediate_answer_template,
    final_answer_protocol, final_answer_template,
    reflection_protocol, reflection_template,
    get_supported_docs_protocol, get_supported_docs_template,
    FollowupQueryParser, IntermediateAnswerParser, FinalAnswerParser,
    ReflectionParser, GetSupportedDocsParser,
)

__all__ = [
    "followup_query_protocol", "followup_query_template",
    "intermediate_answer_protocol", "intermediate_answer_template",
    "final_answer_protocol", "final_answer_template",
    "reflection_protocol", "reflection_template",
    "get_supported_docs_protocol", "get_supported_docs_template",
    "FollowupQueryParser", "IntermediateAnswerParser", "FinalAnswerParser",
    "ReflectionParser", "GetSupportedDocsParser",
] 