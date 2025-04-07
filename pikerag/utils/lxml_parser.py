# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional
from bs4 import BeautifulSoup


def get_soup_from_content(content: str, tag: str="result") -> Optional[BeautifulSoup]:
    start_pos = content.find(f"<{tag}>")
    end_pos = content.find(f"</{tag}>") + len(f"</{tag}>")
    if start_pos != -1 and end_pos != -1:
        soup = BeautifulSoup(content[start_pos:end_pos], "lxml")
        return soup
    return None
