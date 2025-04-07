# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Dict, List, Optional, Tuple

from pikerag.workflows.common import BaseQaData
from pikerag.workflows.qa import QaWorkflow
from pikerag.utils.config_loader import load_constant, load_protocol


class QaSelfAskWorkflow(QaWorkflow):
    def _init_protocol(self) -> None:
        self._self_ask_protocol = load_protocol(
            module_path=self._yaml_config["self_ask_protocol"]["module_path"],
            protocol_name=self._yaml_config["self_ask_protocol"]["protocol_name"],
        )
        self._intermediate_stop: str = load_constant(**self._yaml_config["self_ask_intermediate_stop"])

        print(f"Self-Ask Workflow initialized with stop `{self._intermediate_stop}`")

        self._followup_qa_protocol = load_protocol(
            module_path=self._yaml_config["followup_qa_protocol"]["module_path"],
            protocol_name=self._yaml_config["followup_qa_protocol"]["protocol_name"],
            partial_values=self._yaml_config["followup_qa_protocol"].get("template_partial", {}),
        )

    def _answer_followup_question(self, followup: str, retrieve_id: str) -> Tuple[str, List[str]]:
        chunks = self._retriever.retrieve_contents(followup, retrieve_id)
        messages = self._followup_qa_protocol.process_input(content=followup, references=chunks)
        response = self._client.generate_content_with_messages(messages, **self.llm_config)
        output_dict: dict = self._followup_qa_protocol.parse_output(response)
        return output_dict["answer"], chunks

    def _move_forward(
        self,
        question: str,
        followup_pairs: List[Tuple[str, str]],
        ask_followup: bool,
        ask_final: bool,
        stop: Optional[str],
    ) -> Tuple[Optional[str], Optional[str], str, str]:
        messages = self._self_ask_protocol.process_input(
            question,
            followup_pairs=followup_pairs,
            ask_followup=ask_followup,
            ask_final=ask_final,
        )
        response = self._client.generate_content_with_messages(
            messages,
            **self.llm_config,
            stop=stop,
        )
        final_answer, followup = self._self_ask_protocol.parse_output(response)
        return final_answer, followup, messages[-1]["content"], response

    def answer(self, qa: BaseQaData, question_idx: int) -> Dict:
        followup_pairs: List[Tuple[str, str]] = []
        followup_infos: List[dict] = []
        responses: List[list] = []

        final_answer, followup, messages, response = self._move_forward(
            qa.question, followup_pairs, ask_followup=True, ask_final=False, stop=self._intermediate_stop,
        )
        responses.append([messages, response])
        while final_answer is None and followup is not None:
            intermediate_answer, references = self._answer_followup_question(
                followup,
                f"Q{question_idx}-f{len(followup_pairs)}",
            )
            followup_pairs.append((followup, intermediate_answer))
            followup_infos.append(
                {
                    "question": followup,
                    "answer": intermediate_answer,
                    "references": references,
                }
            )
            final_answer, followup, messages, response = self._move_forward(
                qa.question, followup_pairs, ask_followup=True, ask_final=False, stop=self._intermediate_stop,
            )
            responses.append([messages, response])

        if final_answer is None:
            final_answer, _, messages, response = self._move_forward(
                qa.question, followup_pairs, ask_followup=False, ask_final=True, stop=None,
            )
            responses.append([messages, response])

        return {
            "answer": final_answer,
            "follow_ups": followup_infos,
            "responses": responses,
            "response": responses[-1][1],
        }
