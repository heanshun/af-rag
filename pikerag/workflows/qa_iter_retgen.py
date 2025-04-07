# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Dict, List

import jsonlines
from tqdm import tqdm

from pikerag.workflows.common import BaseQaData
from pikerag.workflows.evaluation.evaluator import Evaluator
from pikerag.workflows.qa import QaWorkflow


class QaIterRetgenWorkflow(QaWorkflow):
    def __init__(self, yaml_config: Dict) -> None:
        workflow_configs: dict = yaml_config["workflow"].get("args", {})
        self._num_iteration: int = workflow_configs.get("num_iters", 5)

        super().__init__(yaml_config)

    def _init_evaluator(self) -> None:
        evaluator_config: dict = self._yaml_config.get("evaluator", {})

        self._evaluator_list = [
            Evaluator(
                evaluator_config=evaluator_config,
                num_rounds=self._yaml_config["test_rounds"],
                num_data=self._num_test,
                log_dir=self._yaml_config["log_dir"],
                main_logger=self._logger,
                name=f"Iter-{i + 1}",
            )
            for i in range(self._num_iteration)
        ]

        self._evaluator = self._evaluator_list[-1]

    def _iter_answer(self, qa: BaseQaData, question_idx: int, answers: List[str], rationales: List[str]) -> dict:
        query = f"{rationales[-1]} So the final answer is {answers[-1]}"

        chunks: List[str] = self._retriever.retrieve_contents_by_query(query, retrieve_id=f"Q{question_idx:03}")
        messages = self._qa_protocol.process_input(content=qa.question, references=chunks, **qa.as_dict())

        response = self._client.generate_content_with_messages(messages, **self.llm_config)
        output_dict: dict = self._qa_protocol.parse_output(response, **qa.as_dict())

        if "response" not in output_dict:
            output_dict["response"] = response

        if "reference_chunks" not in output_dict:
            output_dict["reference_chunks"] = chunks

        return output_dict

    def run(self) -> None:
        fout_list = [
            jsonlines.open(self._yaml_config["test_jsonl_path"][:-6] + f"_iter{i + 1}.jsonl", "w")
            for i in range(self._num_iteration)
        ]

        for round_idx in range(self._yaml_config["test_rounds"]):
            round_id: str = f"Round{round_idx}"
            self._update_llm_cache(round_idx)

            for evaluator in self._evaluator_list:
                evaluator.on_round_test_start(round_id)

            question_idx: int = 0
            pbar = tqdm(self._testing_suite, desc=f"[{self._yaml_config['experiment_name']}] Round {round_idx}")
            for qa in pbar:
                answers: List[str] = []
                rationales: List[str] = []
                responses: List[str] = []
                references: List[List[str]] = []

                # First Iteration
                output_dict: dict = self.answer(qa, question_idx)
                # Later Iteration
                for iter in range(self._num_iteration):
                    for key in ["answer", "rationale", "response", "reference_chunks"]:
                        assert key in output_dict, f"`{key}` should be included in output_dict"
                    answers.append(output_dict["answer"])
                    rationales.append(output_dict["rationale"])
                    responses.append(output_dict["response"])
                    references.append(output_dict["reference_chunks"])

                    if iter == self._num_iteration - 1:
                        break

                    output_dict = self._iter_answer(qa, question_idx, answers, rationales)

                for iter in range(self._num_iteration):
                    qa.answer_metadata[f"Iter-{iter + 1}"] = {
                        "answer": answers[iter],
                        "rationale": rationales[iter],
                        "response": responses[iter],
                        "references": references[iter],
                    }

                    qa.update_answer(answers[iter])
                    self._evaluator_list[iter].update_round_metrics(qa)
                    fout_list[iter].write(qa.as_dict())

                self._update_qas_metrics_table(qa)
                question_idx += 1
                self._update_pbar_desc(pbar, round_idx=round_idx, count=question_idx)

            for evaluator in self._evaluator_list:
                evaluator.on_round_test_end(round_id)

        for evaluator in self._evaluator_list:
            evaluator.on_test_end()

        for fout in fout_list:
            fout.close()
