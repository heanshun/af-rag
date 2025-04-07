# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List, Tuple

from bs4 import BeautifulSoup

from pikerag.prompts import BaseContentParser, CommunicationProtocol, MessageTemplate
from pikerag.utils.lxml_parser import get_soup_from_content


written_phrase_mapping_template = MessageTemplate(
    template=[
        ("system", "You are a helpful assistant good at {knowledge_domain} that can help people {task_direction}."),
        ("user", """
# Task
You will be provided with a {oral_phrase} and a list of {written_phrases}, please think step by step to find out the relevant written phrases for the spoken phrase if any exists. Then output them in the specific format.

# Output format
The output should strictly follow the format below, do not add any redundant information.

<result>
  <thinking>Your thinking for the given content.</thinking>
  <phrases>
    <phrase>Relevant written phrase 1</phrase>
    <phrase>Relevant written phrase 2</phrase>
    ... Please output all relevant written phrases in the given list. Leave it empty if no one relevant.
  </phrases>
</result>

# Spoken phrase
{content}

# Candidate written phrases
{candidates}

# Thinking and answer
""".strip()),
    ],
    input_variables=["knowledge_domain", "task_direction", "oral_phrase", "written_phrases", "content", "candidates"],
)


class WrittenPhraseMappingParser(BaseContentParser):
    def decode(self, content: str, **kwargs) -> Tuple[str, List[str]]:
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
                print(f"[TagMappingParser] Content skipped due to the absence of <phrases>: {content}")

        else:
            # TODO: add logger for Parser?
            print(f"[TagMappingParser] Content skipped due to the absence of <result>: {content}")

        # NOTE: thinking not returned to let the return value compatible with LLMPoweredTagger.
        return thinking, phrases


written_phrase_mapping_protocol = CommunicationProtocol(
    template=written_phrase_mapping_template,
    parser=WrittenPhraseMappingParser(),
)
