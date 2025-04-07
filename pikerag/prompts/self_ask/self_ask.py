# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import re
from typing import Dict, List, Optional, Tuple

from pikerag.prompts import BaseContentParser, CommunicationProtocol, MessageTemplate


IntermediateStop: str = "Intermediate answer:"


self_ask_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant good at question-answering."),
        ("user", """
Question: Who lived longer, Muhammad Ali or Alan Turing?
Are follow up questions needed here: Yes.
Follow up: How old was Muhammad Ali when he died?
Intermediate answer: Muhammad Ali was 74 years old when he died.
Are follow up questions needed here: Yes.
Follow up: How old was Alan Turing when he died?
Intermediate answer: Alan Turing was 41 years old when he died.
Are follow up questions needed here: No.
So the final answer is: Muhammad Ali

Question: When was the founder of craigslist born?
Are follow up questions needed here: Yes.
Follow up: Who was the founder of craigslist?
Intermediate answer: Craigslist was founded by Craig Newmark.
Are follow up questions needed here: Yes.
Follow up: When was Craig Newmark born?
Intermediate answer: Craig Newmark was born on December 6, 1952.
Are follow up questions needed here: No.
So the final answer is: December 6, 1952

Question: Who was the maternal grandfather of George Washington?
Are follow up questions needed here: Yes.
Follow up: Who was the mother of George Washington?
Intermediate answer: The mother of George Washington was Mary Ball Washington.
Are follow up questions needed here: Yes.
Follow up: Who was the father of Mary Ball Washington?
Intermediate answer: The father of Mary Ball Washington was Joseph Ball.
Are follow up questions needed here: No.
So the final answer is: Joseph Ball

Question: Are both the directors of Jaws and Casino Royale from the same country?
Are follow up questions needed here: Yes.
Follow up: Who is the director of Jaws?
Intermediate answer: The director of Jaws is Steven Spielberg.
Are follow up questions needed here: Yes.
Follow up: Where is Steven Spielberg from?
Intermediate answer: The United States.
Are follow up questions needed here: Yes.
Follow up: Who is the director of Casino Royale?
Intermediate answer: The director of Casino Royale is Martin Campbell.
Are follow up questions needed here: Yes.
Follow up: Where is Martin Campbell from?
Intermediate answer: New Zealand.
Are follow up questions needed here: No.
So the final answer is: No

Question: {content}
{followup_context}
{asking_prefix}
""".strip()),
    ],
    input_variables=["content", "followup_context", "asking_prefix"],
)


class SelfAskParser(BaseContentParser):
    def __init__(self) -> None:
        self._final_answer_prefix = "Are follow up questions needed here: No.\nSo the final answer is: "
        self._final_answer_pattern = re.compile(r"So the final answer is:(.*)", re.DOTALL)
        self._follow_up_prefix = "Are follow up questions needed here: "
        self._follow_up_pattern = re.compile(r"Follow up:(.*)", re.DOTALL)

        self._ask_final: bool = False

    def encode(
        self, content: str, followup_pairs: List[Tuple[str, str]], ask_followup: bool, ask_final: bool, **kwargs,
    ) -> Tuple[str, Dict]:
        followup_context: str = "\n".join(
            [
                f"Are follow up questions needed here: Yes.\nFollow up: {q}\nIntermediate Answer: {a}"
                for q, a in followup_pairs
            ]
        )

        assert ask_followup != ask_final, f"There should be and should only be one `True` for `ask_followup` and `ask_final`"

        if len(followup_pairs) >= 5 and ask_followup is True:
            ask_followup = False
            ask_final = True

        self._ask_final = ask_final
        if ask_followup is True:
            asking_prefix = self._follow_up_prefix
        else:
            asking_prefix = self._final_answer_prefix

        return content, {
            "followup_context": followup_context,
            "asking_prefix": asking_prefix,
        }

    def decode(self, content: str,  **kwargs) -> Tuple[Optional[str], Optional[str]]:
        if isinstance(content, str):
            content = content.strip()

            if self._ask_final is False:
                follow_up_match = re.search(self._follow_up_pattern, content)
                if follow_up_match is not None:
                    follow_up = follow_up_match.group(1)
                    return None, follow_up

                final_answer_match = re.search(self._final_answer_pattern, content)
                if final_answer_match is not None:
                    final_answer = final_answer_match.group(1)
                    return final_answer, None

            else:
                return content, None

        return None, None


self_ask_protocol = CommunicationProtocol(
    template=self_ask_template,
    parser=SelfAskParser(),
)
