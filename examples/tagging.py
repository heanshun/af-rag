# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import argparse
import os
import pathlib
import shutil
import yaml

from pikerag.utils.config_loader import load_dot_env
from pikerag.workflows.tagging import TaggingWorkflow


def load_yaml_config(config_path: str, args: argparse.Namespace) -> dict:
    with open(config_path, "r") as fin:
        yaml_config: dict = yaml.safe_load(fin)

    # .env file path
    if yaml_config["dotenv_path"] is None:
        repo_path: str = pathlib.Path(os.path.abspath(__file__)).parent.parent
        yaml_config["dotenv_path"] = os.path.join(repo_path, "env_configs/.env")

    # Create logging dir if not exists
    experiment_name = yaml_config["experiment_name"]
    log_dir = os.path.join(yaml_config["log_root_dir"], experiment_name)
    yaml_config["log_dir"] = log_dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    shutil.copy(config_path, log_dir)

    # LLM cache config
    if yaml_config["llm_client"]["cache_config"]["location_prefix"] is None:
        yaml_config["llm_client"]["cache_config"]["location_prefix"] = experiment_name

    # input doc extensions setting
    if "input_doc_setting" in yaml_config:
        input_doc_dir = yaml_config["input_doc_setting"]["doc_dir"]
        assert os.path.exists(input_doc_dir), f"Input doc dir {input_doc_dir} not exist!"
        if "extensions" not in yaml_config["input_doc_setting"]:
            yaml_config["input_doc_setting"]["extensions"] = None
        elif isinstance(yaml_config["input_doc_setting"]["extensions"], str):
            yaml_config["input_doc_setting"]["extensions"] = [yaml_config["input_doc_setting"]["extensions"]]

    return yaml_config


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=str, help="the path of the yaml config file you want to use")
    # TODO: add more options here, and let the ones in cmd line replace the ones in yaml file
    args = parser.parse_args()

    # Loading yaml config.
    yaml_config: dict = load_yaml_config(args.config, args)

    # Load environment variables from dot env file.
    load_dot_env(env_path=yaml_config["dotenv_path"])

    workflow = TaggingWorkflow(yaml_config)
    workflow.run()
