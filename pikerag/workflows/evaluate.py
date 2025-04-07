# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List

import jsonlines
from dacite import from_dict
from tqdm import tqdm

from pikerag.utils.logger import Logger
from pikerag.workflows.common import GenerationQaData
from pikerag.workflows.evaluation.evaluator import Evaluator


class EvaluationWorkflow:
    def __init__(self, yaml_config: dict) -> None:
        self._yaml_config: dict = yaml_config

        self._init_logger()

        self._load_result_jsonlines()

        self._init_evaluator()

    def _init_logger(self) -> None:
        self._logger: Logger = Logger(name="evaluation", dump_folder=self._yaml_config["log_dir"])

    def _load_result_jsonlines(self) -> None:
        filepath = self._yaml_config["result_path"]
        with jsonlines.open(filepath, "r") as reader:
            self._results: List[GenerationQaData] = [
                from_dict(GenerationQaData, data)
                for data in reader
            ]

    def _init_evaluator(self):
        evaluator_config: dict = self._yaml_config.get("evaluator", {})

        self._evaluator = Evaluator(
            evaluator_config=evaluator_config,
            num_rounds=self._yaml_config["test_rounds"],
            num_data=self._yaml_config["num_test_data"],
            log_dir=self._yaml_config["log_dir"],
            main_logger=self._logger,
        )
        return

    def run(self) -> None:
        with jsonlines.open(self._yaml_config["output_path"], "w") as writer:
            res_idx: int = 0
            for round_idx in range(self._yaml_config["test_rounds"]):
                round_id: str = f"Round{round_idx}"
                self._evaluator.on_round_test_start(round_id)
                for _ in tqdm(range(self._yaml_config["num_test_data"]), desc=f"Evaluation Round {round_idx}"):
                    qa = self._results[res_idx]
                    self._evaluator.update_round_metrics(qa)
                    writer.write(qa.as_dict())

                    res_idx += 1
                    if res_idx >= len(self._results):
                        break

                self._evaluator.on_round_test_end(round_id)
                if res_idx >= len(self._results):
                    break

            self._evaluator.on_test_end()
        return
