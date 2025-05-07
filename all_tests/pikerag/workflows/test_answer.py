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


def load_questions() -> list:
    """加载预设的问题文件中的所有问题"""
    questions_file = "tests/pikerag/workflows/questions.txt"  # 将问题文件路径写死在代码中
    with open(questions_file, "r", encoding='utf-8') as f:
        questions = [line.strip() for line in f if line.strip()]
    return questions


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=str, help="the path of the yaml config file you want to use")
    parser.add_argument("question_id", type=int, help="要测试的问题编号（从0开始）")
    args = parser.parse_args()

    # Loading yaml config.
    yaml_config: dict = load_yaml_config(args.config, args)

    # Load environment variables from dot env file.
    load_dot_env(env_path=yaml_config.get("dotenv_path", None))

    # Dynamically import the QA Workflow class
    workflow_module = importlib.import_module(yaml_config["workflow"]["module_path"])
    workflow_class = getattr(workflow_module, yaml_config["workflow"]["class_name"])
    assert issubclass(workflow_class, QaWorkflow)
    workflow = workflow_class(yaml_config)

    # Load questions from file
    questions = load_questions()
    if args.question_id >= len(questions):
        raise ValueError(f"问题编号 {args.question_id} 超出范围，总共只有 {len(questions)} 个问题")
    
    question = questions[args.question_id]

    qa = BaseQaData(question=question)
    result = workflow.answer(qa, 0)
    print(f"问题 {args.question_id}: {question}")
    print("回答:", result)
