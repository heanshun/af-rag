# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Dict, List

from pikerag.workflows.common import BaseQaData
from pikerag.workflows.qa import QaWorkflow
from pikerag.utils.config_loader import load_protocol


class QaIRCoTWorkflow(QaWorkflow):
    def __init__(self, yaml_config: Dict) -> None:
        super().__init__(yaml_config)

        workflow_configs: dict = self._yaml_config["workflow"].get("args", {})
        self._max_num_question: int = workflow_configs.get("max_num_rounds", 5)

    def _init_protocol(self) -> None:
        self._ircot_protocol = load_protocol(
            module_path=self._yaml_config["ircot_protocol"]["module_path"],
            protocol_name=self._yaml_config["ircot_protocol"]["protocol_name"],
        )

    def answer(self, qa: BaseQaData, question_idx: int) -> Dict:
        references: List[str] = []
        rationales: List[str] = []
        responses: List[str] = []
        final_answer: str = None
        for round in range(self._max_num_question):
            # Retrieve more chunks
            if len(rationales) == 0:
                query = qa.question
            else:
                query = rationales[-1]
            chunks = self._retriever.retrieve_contents_by_query(query, retrieve_id=f"Q{question_idx}_R{round}")
            references.extend(chunks)

            # Call LLM to generate rationale or answer
            messages = self._ircot_protocol.process_input(
                qa.question, rationales=rationales, references=references, is_limit=False,
            )
            response = self._client.generate_content_with_messages(messages, **self.llm_config)
            responses.append(response)
            output_dict = self._ircot_protocol.parse_output(response)

            if output_dict["answer"] is not None:
                final_answer = output_dict["answer"]
                break
            elif isinstance(output_dict["next_rationale"], str):
                rationales.append(output_dict["next_rationale"])
            else:
                break

        if final_answer is None:
            messages = self._ircot_protocol.process_input(
                qa.question, rationales=rationales, references=references, is_limit=True,
            )
            response = self._client.generate_content_with_messages(messages, **self.llm_config)
            responses.append(response)
            output_dict = self._ircot_protocol.parse_output(response)
            final_answer = output_dict["answer"]

        return {
            "answer": final_answer,
            "rationale": rationales,
            "references": references,
            "responses": responses,
        }
