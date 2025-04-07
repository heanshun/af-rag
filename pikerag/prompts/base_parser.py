# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Any, Tuple


class BaseContentParser:
    def __init__(self) -> None:
        pass

    def encode(self, content: str, **kwargs) -> Tuple[str, dict]:
        """The content encoding logic.

        Args:
            content (str): the main content for encoding.
            kwargs (dict): the optional key-value pairs that may be used for encoding.

        Returns:
            str: the encoded content.
            dict: any other information generated in the encoding process that may be used outside encoding.
        """
        return content, {}

    def decode(self, content: str, **kwargs) -> Any:
        return content
