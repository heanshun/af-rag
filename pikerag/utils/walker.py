# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
from pathlib import Path
from typing import List, Tuple


def list_files_recursively(directory: str, extensions: List[str]=None) -> List[Tuple[str, str]]:
    """Return a list of (filename, filepath) for files in the given directory recursively.

    Args:
        directory (str): the directory to walk through.
        extensions (List[str]): the target file extensions to visit if set. None if targeting at all file extensions.
    Defaults to None.

    Returns:
        List[Tuple[str, str]]: a list of (filename, filepath) tuples that meet the extension condition.
    """
    name_path_list: List[Tuple[str, str]] = []
    for root, _, files in os.walk(directory):
        for filename in files:
            if extensions is None or Path(filename).suffix[1:] in extensions:
                name_path_list.append((filename, os.path.join(root, filename)))
    return name_path_list
