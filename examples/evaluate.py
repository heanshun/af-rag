# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import argparse
import yaml

from pikerag.utils.config_loader import load_dot_env
from pikerag.workflows.evaluate import EvaluationWorkflow


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=str, help="the path of the yaml config file you want to use")
    args = parser.parse_args()

    with open(args.config, "r") as fin:
        yaml_config = yaml.safe_load(fin)

    load_dot_env(env_path=yaml_config.get("dotenv_path", None))

    workflow = EvaluationWorkflow(yaml_config)
    workflow.run()
