# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import os
import sys


class Logger(logging.Logger):
    def __init__(
        self, name: str, level = logging.INFO,
        dump_mode: str = "w", dump_folder: str = "./", extension_name: str = "log",
    ) -> None:
        super().__init__(name, logging.NOTSET)

        # Create dump folder if not exist.
        if not os.path.exists(dump_folder):
            try:
                os.makedirs(dump_folder)
            except FileExistsError:
                logging.warning(
                    "Receive File Exist Error about creating dump folder for internal log. "
                    "It may be caused by multi-thread and it won't have any impact on logger dumps.",
                )
            except Exception as e:
                raise e

        # File handler
        filename = os.path.join(dump_folder, f"{name}.{extension_name}")
        fh = logging.FileHandler(filename=filename, mode=dump_mode, encoding="utf-8")
        fh.setLevel(logging.DEBUG)

        # Stdout handler
        stdout_level = os.environ.get("LOG_LEVEL") or level
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(stdout_level)

        self.addHandler(fh)
        self.addHandler(sh)

    def debug(self, msg, tag: str=None):
        if tag is not None:
            msg = f"[{tag}]\n" + msg
        super().debug(msg)

    def info(self, msg, tag: str=None):
        if tag is not None:
            msg = f"[{tag}]\n" + msg
        super().info(msg)

    def warning(self, msg, tag: str=None):
        if tag is not None:
            msg = f"[{tag}]\n" + msg
        super().warning(msg)

    def warn(self, msg, tag: str=None):
        if tag is not None:
            msg = f"[{tag}]\n" + msg
        super().warn(msg)

    def error(self, msg, tag: str=None):
        if tag is not None:
            msg = f"[{tag}]\n" + msg
        super().error(msg)

    def exception(self, msg, tag: str=None):
        if tag is not None:
            msg = f"[{tag}]\n" + msg
        super().exception(msg)

    def critical(self, msg, tag: str=None):
        if tag is not None:
            msg = f"[{tag}]\n" + msg
        super().critical(msg)


if __name__ == "__main__":
    logger = Logger(name="logger_test")
    logger.info("It is info")
    logger.debug("It is debug")
    logger.critical("It is critical")
    logger.error("It is error")
