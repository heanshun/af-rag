# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import argparse
import importlib
import os
import pathlib
import shutil
import warnings
import yaml
from pikerag.workflows.common import BaseQaData

# TODO
warnings.filterwarnings("ignore", r".*TypedStorage is deprecated.*")
warnings.filterwarnings("ignore", r".*Relevance scores must be between 0 and 1.*")
warnings.filterwarnings("ignore", r".*No relevant docs were retrieved using the relevance score threshold 0.5.*")

from pikerag.utils.config_loader import load_dot_env
from pikerag.workflows.qa import QaWorkflow


def load_yaml_config(config_path: str, args: argparse.Namespace=None) -> dict:
    with open(config_path, "r", encoding='utf-8') as fin:
        yaml_config: dict = yaml.safe_load(fin)

    # Create logging dir if not exists
    experiment_name = yaml_config["experiment_name"]
    log_dir = os.path.join(yaml_config["log_root_dir"], experiment_name)
    yaml_config["log_dir"] = log_dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    shutil.copy(config_path, log_dir)

    # test jsonl file path
    if yaml_config["test_jsonl_filename"] is None:
        yaml_config["test_jsonl_filename"] = f"{experiment_name}.jsonl"
    yaml_config["test_jsonl_path"] = os.path.join(log_dir, yaml_config["test_jsonl_filename"])

    # LLM cache config
    if yaml_config["llm_client"]["cache_config"]["location_prefix"] is None:
        yaml_config["llm_client"]["cache_config"]["location_prefix"] = experiment_name

    return yaml_config


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=str, help="yaml配置文件的路径")
    args = parser.parse_args()

    # 加载yaml配置
    yaml_config: dict = load_yaml_config(args.config, args)

    # 加载环境变量
    load_dot_env(env_path=yaml_config.get("dotenv_path", None))

    # 动态导入QA Workflow类
    workflow_module = importlib.import_module(yaml_config["workflow"]["module_path"])
    workflow_class = getattr(workflow_module, yaml_config["workflow"]["class_name"])
    assert issubclass(workflow_class, QaWorkflow)
    workflow = workflow_class(yaml_config)

    print("请输入您的问题（输入'quit'或'exit'退出）：")
    while True:
        question = input("> ").strip()
        if question.lower() in ['quit', 'exit']:
            break
        if not question:
            continue
            
        qa = BaseQaData(question=question)
        result = workflow.answer(qa, 0)
        print("\n回答:", result)
        print("\n请输入下一个问题（输入'quit'或'exit'退出）：")
