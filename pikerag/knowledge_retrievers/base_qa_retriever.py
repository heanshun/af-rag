# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List

from pikerag.utils.logger import Logger
from pikerag.workflows.common import BaseQaData


class BaseQaRetriever:
    def __init__(self, retriever_config: dict, log_dir: str, main_logger: Logger) -> None:
        self._retriever_config: dict = retriever_config
        self._log_dir: str = log_dir
        self._main_logger: Logger = main_logger

    def retrieve_contents_by_query(self, query: str, retrieve_id: str="", **kwargs) -> List[str]:
        return []

    def retrieve_contents(self, qa: BaseQaData, retrieve_id: str="", **kwargs) -> List[str]:
        return self.retrieve_contents_by_query(qa.question, retrieve_id, **kwargs)
