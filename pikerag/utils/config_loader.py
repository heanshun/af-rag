# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import importlib
import os
import pathlib
from copy import deepcopy
from dotenv import load_dotenv
from typing import Any, Callable, Optional

from langchain_core.embeddings import Embeddings

from pikerag.prompts import CommunicationProtocol


def load_dot_env(env_path: Optional[str]) -> None:
    if env_path is None:
        repo_path: str = pathlib.Path(os.path.abspath(__file__)).parent.parent.parent
        env_path = os.path.join(repo_path, "env_configs/.env")

    # Load environment variables from dot env file
    load_success: bool = load_dotenv(env_path)
    assert load_success is True, f"Failed to load dot env file: {env_path}"
    return


def load_constant(module_path: str, variable_name: str) -> Any:
    target_module = importlib.import_module(module_path)
    target = getattr(target_module, variable_name)
    return target


def load_protocol(module_path: str, protocol_name: str, partial_values: dict={}) -> CommunicationProtocol:
    protocol_module = importlib.import_module(module_path)
    protocol: CommunicationProtocol = deepcopy(getattr(protocol_module, protocol_name))
    protocol.template_partial(**partial_values)
    return protocol


def load_callable(module_path: str, name: str) -> Callable:
    return load_constant(module_path, name)


def load_class(module_path: str, class_name: str, base_class=None) -> object:
    loaded_class = load_constant(module_path, class_name)
    if base_class is not None:
        assert issubclass(loaded_class, base_class), (
            f"Class expected to be sub-class of {base_class.name()} but {loaded_class.name()} loaded."
        )
    return loaded_class


def load_embedding_func(module_path: Optional[str]=None, class_name: Optional[str]=None, **kwargs) -> Embeddings:
    # Set to disable huggingface/tokenizers fork warning of deadlocks.
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    if module_path is None or class_name is None:
        from langchain_community.embeddings import SentenceTransformerEmbeddings
        embedding_class = SentenceTransformerEmbeddings
    else:
        embedding_class = load_callable(module_path, class_name)

    if "model_name" not in kwargs or kwargs["model_name"] is None:
        kwargs["model_name"] = "BAAI/bge-m3"

    embedding = embedding_class(**kwargs)
    return embedding
