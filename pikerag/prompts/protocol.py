# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from dataclasses import dataclass
from typing import Any, Dict, List

from pikerag.prompts.base_parser import BaseContentParser
from pikerag.prompts.message_template import MessageTemplate


@dataclass
class CommunicationProtocol:
    template: MessageTemplate
    parser: BaseContentParser

    def template_partial(self, **kwargs) -> List[str]:
        """Partially fill in the template placeholders to update the template.

        Args:
            **kwargs: the key, value pairs for the partially fill in variables.

        Returns:
            List[str]: the remaining input variables needed to fill in for the updated template.
        """
        self.template = self.template.partial(**kwargs)
        return self.template.input_variables

    def process_input(self, content: str, **kwargs) -> List[Dict[str, str]]:
        """Fill in the placeholders in the message template to form an input message list.

        Args:
            content (str): the main content for encoding.
            kwargs (dict): the optional key-value pairs that may be used for encoding.

        Returns:
            List[Dict[str, str]]: the formatted message list for LLM chat.
        """
        encoded_content, encoded_dict = self.parser.encode(content, **kwargs)
        return self.template.format(content=encoded_content, **kwargs, **encoded_dict)

    def parse_output(self, content: str, **kwargs) -> Any:
        """Let the parser to decode the response content.

        Args:
            content (str): the main content for parsing.
            kwargs (dict): the optional key-value pairs that may be used for parsing.

        Returns:
            Any: value(s) returned by the parser, the return value types varied according to different applications.
        """
        return self.parser.decode(content, **kwargs)
