# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Any, List, Sequence, Tuple

from tqdm import tqdm

from langchain_core.documents import Document, BaseDocumentTransformer

from pikerag.llm_client import BaseLLMClient
from pikerag.prompts import CommunicationProtocol
from pikerag.utils.logger import Logger


class LLMPoweredFilter(BaseDocumentTransformer):
    NAME = "LLMPoweredFilter"

    def __init__(
        self,
        llm_client: BaseLLMClient,
        filter_protocol: CommunicationProtocol,
        llm_config: dict = {},
        logger: Logger = None,
        **kwargs,
    ) -> None:
        super().__init__()

        self._llm_client = llm_client
        self._llm_config = llm_config

        self._filter_protocol: CommunicationProtocol = filter_protocol

        self.logger = logger

    def _get_filter_info(self, content: str, **metadata) -> Tuple[str, bool]:
        messages = self._filter_protocol.process_input(content, **metadata)

        # Call client for filtering info
        response = self._llm_client.generate_content_with_messages(messages=messages, **self._llm_config)

        return self._filter_protocol.parse_output(content=response, **metadata)

    # TODO: create new interface like "TextSplitter" for filtering?
    def transform_documents(self, documents: Sequence[Document], keep_unrelated: bool = False, **kwargs: Any) -> Sequence[Document]:
        ret_docs: List[Document] = []
        for idx, doc in tqdm(enumerate(documents), desc="Filtering Documents", total=len(documents)):
            content = doc.page_content
            metadata = doc.metadata

            filter_info, related = self._get_filter_info(content, **metadata)
            if self.logger is not None:
                self.logger.debug(
                    f"{idx + 1}/{len(documents)} document -- related? {related}, kept? {keep_unrelated or related}",
                    tag=self.NAME,
                )

            if not keep_unrelated and not related:
                continue

            # TODO: could there be multiple filter conditions? Set it as list of filter_info?
            metadata.update({"filter_info": filter_info, "related": related})
            ret_docs.append(doc)
        return ret_docs
