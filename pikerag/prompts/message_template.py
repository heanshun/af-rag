# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations
from string import Formatter
from typing import Dict, List, Tuple, Union, Callable

from pydantic import BaseModel, model_validator


formatter = Formatter()


class MessageTemplate(BaseModel):
    """A message template for a language model.

    Args:
        template (List[Tuple[str, str]]): each tuple in the template list consists two elements: the first one is the
            role of this message; the second one is a f-string style content.
        input_variables (Union[List[str], None]): the input variables needs to be fill in when finalizing the messages with the given
            template. It must correspond to the f-string style contents in the template. Input variable list would be
            automatically inferred based on the template if None is given. But it is always recommended to provide it by
            yourself. Defaults to None.
        partial_variables (Dict[str, Union[str, Callable[[], str]]]): no need to provide when initializing a message
            template by yourself. Defaults to {}.

    Example:
        .. code-block:: python

            from pikerag.llm_client.prompts import MessageTemplate

            # Initialize a message template with the template (and input variable list).
            message_template = MessageTemplate(
                template=[
                    ("system", "You are a helpful AI assistant."),
                    ("user", "This may be a {placeholder1} demonstration from user"),
                    ("assistant", "This may be a {placeholder2} demonstration from assistant"),
                    ("user", "You may finalize your {placeholder3} question here"),
                ],
                # It's allowable to provide only template when initializing an instance,
                # But it always recommended to list the input variables by yourself.
                input_variables=["placeholder1", "placeholder2", "placeholder3"],
            )

            # Partially fill in the placeholder1 and placeholder2.
            message_template = message_prompt.partial(placeholder1="demo question", placeholder2="demo answer")

            # Finalize the messages with the remaining variables provided.
            messages = message_template.format(placeholder3="your question")

    """
    template: List[Tuple[str, str]]

    input_variables: List[str] = None

    partial_variables: Dict[str, Union[str, Callable[[], str]]] = {}

    @model_validator(mode="after")
    def validate_input_variables(self) -> MessageTemplate:
        input_variables_in_template = sorted(
            {
                field_name
                for _, content_template in self.template
                for _, field_name, _, _ in formatter.parse(content_template)
                if field_name is not None
            }
        )

        if self.input_variables is None:
            self.input_variables = list(input_variables_in_template)

        else:
            input_variable_set = set(self.input_variables)
            partial_variable_set = set(self.partial_variables.keys())
            parsed_variable_set = set(input_variables_in_template)
            for variable in parsed_variable_set:
                assert variable in input_variable_set or variable in partial_variable_set, (
                    f"{variable} in template but not shown in input variables list!"
                )
            for variable in input_variable_set:
                assert variable in parsed_variable_set, (
                    f"{variable} in input variable list but cannot found in template!"
                )

        return self

    def partial(self, **kwargs: Union[str, Callable[[], str]]) -> MessageTemplate:
        """Return a partial of this message template."""
        prompt_dict = self.__dict__.copy()
        prompt_dict["input_variables"] = list(set(self.input_variables).difference(kwargs))
        prompt_dict["partial_variables"] = {**self.partial_variables, **kwargs}
        return type(self)(**prompt_dict)

    def _merge_partial_and_user_variables(self, **kwargs: Union[str, Callable[[], str]]) -> Dict[str, str]:
        partial_kwargs = {
            k: v if isinstance(v, str) else v()
            for k, v in self.partial_variables.items()
        }
        return {**partial_kwargs, **kwargs}

    def format(self, **kwargs) -> List[Dict[str, str]]:
        """Format the messages template into a list of finalized messages.

        Args:
            **kwargs: keyword arguments to use for filling in template variables in all the template messages in this
                messages template.

        Returns:
            List[Dict[str, str]]: list of formatted messages, each message contains the role and the content.
        """
        kwargs = self._merge_partial_and_user_variables(**kwargs)
        result: List[Dict[str, str]] = [
            {
                "role": role,
                "content": formatter.format(content, **kwargs),
            }
            for role, content in self.template
        ]
        return result
