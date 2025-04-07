# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import importlib
import os
from typing import Dict, List

import numpy as np
import pandas as pd
from tabulate import tabulate

from pikerag.utils.logger import Logger
from pikerag.workflows.common import BaseQaData
from pikerag.workflows.evaluation.metrics.base import BaseMetric


class Evaluator:
    def __init__(
        self, evaluator_config: dict, num_rounds: int, num_data: int, log_dir: str,
        main_logger: Logger=None, name: str="",
        **kwargs,
    ) -> None:
        self._evaluator_config: dict = evaluator_config
        self._num_rounds: int = num_rounds
        self._num_data: int = num_data
        self._log_dir: str = log_dir
        self._main_logger = main_logger
        self._name = "Evaluator" + f" {name}" if name is not None else ""

        self._metrics: List[BaseMetric] = []
        self._metrics_by_name: Dict[str, BaseMetric] = {}

        self._init_metrics(**kwargs)

        self._start_report()

    def _init_metrics(self, **kwargs) -> None:
        metric_class_list: List[BaseMetric] = []

        # Step 1: Get pre-defined metrics in PIKE-RAG
        metric_module = importlib.import_module("pikerag.workflows.evaluation.metrics")
        for metric_name in self._evaluator_config.get("metrics", []):
            metric_class = getattr(metric_module, metric_name)
            metric_class_list.append(metric_class)

        # Step 2: Get custom metrics
        metric_configs = self._evaluator_config.get("custom_metrics", [])
        if not isinstance(metric_configs, list):
            metric_configs = [metric_configs]
        for metric_config in metric_configs:
            assert "module_path" in metric_config, "module_path not defined"
            assert "class_name" in metric_config, "class_name not defined"
            metric_module = importlib.import_module(metric_config["module_path"])
            class_names = metric_config["class_name"]
            if not isinstance(class_names, list):
                class_names = [class_names]
            for metric_name in class_names:
                metric_class = getattr(metric_module, metric_name)
                metric_class_list.append(metric_class)

        # Initialize metric instances
        for metric_class in metric_class_list:
            metric = metric_class(
                num_rounds=self._num_rounds,
                num_data=self._num_data,
                main_logger=self._main_logger,
                **kwargs,
            )
            self._metrics.append(metric)
            self._metrics_by_name[metric.name] = metric

        return

    def on_round_test_start(self, round_id: str) -> None:
        for metric in self._metrics:
            metric.on_round_test_start(round_id)

    def on_round_test_end(self, round_id: str) -> None:
        for metric in self._metrics:
            metric.on_round_test_end(round_id)
        self._round_report(round_id)

    def update_round_metrics(self, qa: BaseQaData) -> None:
        for metric in self._metrics:
            metric.step_update(qa)

    def on_test_end(self) -> None:
        for metric in self._metrics:
            metric.on_test_end()

        self._evaluation_report()
        self._dump_metrics()

    def _start_report(self) -> None:
        metric_names: List[str] = [metric.name for metric in self._metrics]
        msg = f"Evaluator initialized with {metric_names}."

        if self._main_logger is not None:
            self._main_logger.info(msg, tag=self._name)
        else:
            print(msg)

    def _round_report(self, round_id: str) -> None:
        if len(self._metrics) == 0:
            return

        metric_reports = []
        for metric in self._metrics:
            metric_reports.append([metric.name, metric.round_report()])
        report_table = tabulate(metric_reports, headers=["Metric", "Score"])

        msg = f"{round_id}: {len(self._metrics)} metrics over {self._num_data} test data:\n\n{report_table}\n"
        if self._main_logger is not None:
            self._main_logger.info(msg, tag=self._name)
        else:
            print(msg)

    def _evaluation_report(self) -> None:
        if len(self._metrics) == 0 or self._num_rounds == 0:
            return

        evaluation_reports = []
        for metric in self._metrics:
            evaluation_reports.append([metric.name] + list(metric.evaluation_report()))
        report_table = tabulate(evaluation_reports, headers=["Metric", "Avg.", "Min", "Max", "Std."])

        msg = f"{len(self._metrics)} Evaluation Metrics over {self._num_rounds} rounds:\n\n{report_table}\n"
        if self._main_logger is not None:
            self._main_logger.info(msg, tag=self._name)
        else:
            print(msg)

    def _dump_metrics(self) -> None:
        if len(self._metrics) == 0 or self._num_rounds == 0:
            return

        data = {"Round": [1 + i for i in range(self._num_rounds)] + ["Average"]}
        for metric in self._metrics:
            data[metric.name] = [
                metric._round_scores[i] for i in range(self._num_rounds)
            ] + [np.mean(metric._round_scores)]

        df_metrics = pd.DataFrame(data)
        df_metrics.to_csv(os.path.join(self._log_dir, f"{self._name}_metrics.csv"), index=False)
