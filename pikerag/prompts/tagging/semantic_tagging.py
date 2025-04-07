# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List

from bs4 import BeautifulSoup

from pikerag.prompts import BaseContentParser, CommunicationProtocol, MessageTemplate
from pikerag.utils.lxml_parser import get_soup_from_content


semantic_tagging_template = MessageTemplate(
    template=[
        ("system", "You are a helpful assistant good at {knowledge_domain} that can help people {task_direction}."),
        ("user", """
# Task
Please read the content provided carefully, think step by step, then extract the {tag_semantic} phrases contained therein.

# Output format
The output should strictly follow the format below, do not add any redundant information.

<result>
  <thinking>Your thinking for the given content.</thinking>
  <phrases>
    <phrase>Extracted phrase 1</phrase>
    <phrase>Extracted phrase 2</phrase>
    <phrase>Extracted phrase 3</phrase>
    ... Please output an equal number of phrases based on the number of phrases contained in the content. Leave it empty if no phrase found.
  </phrases>
</result>

# Content
{content}

# Thinking and answer
""".strip()),
    ],
    input_variables=["knowledge_domain", "task_direction", "tag_semantic", "content"],
)


class SemanticTaggingParser(BaseContentParser):
    def decode(self, content: str, **kwargs) -> List[str]:
        thinking: str = ""
        phrases: List[str] = []

        result_soup: BeautifulSoup = get_soup_from_content(content=content, tag="result")
        if result_soup is not None:
            thinking_soup = result_soup.find("thinking")
            phrases_soup = result_soup.find("phrases")

            if thinking_soup is not None:
                thinking = thinking_soup.text.strip()

            if phrases_soup is not None:
                for phrase_soup in phrases_soup.find_all("phrase"):
                    phrase_str = phrase_soup.text.strip()
                    if len(phrase_str) > 0:
                        phrases.append(phrase_str)

            else:
                # TODO: add logger for Parser?
                print(f"[SemanticTagParser] Content skipped due to the absence of <phrases>: {content}")

        else:
            # TODO: add logger for Parser?
            print(f"[SemanticTagParser] Content skipped due to the absence of <result>: {content}")

        # NOTE: thinking not returned to let the return value compatible with LLMPoweredTagger.
        return phrases


semantic_tagging_protocol = CommunicationProtocol(
    template=semantic_tagging_template,
    parser=SemanticTaggingParser(),
)
