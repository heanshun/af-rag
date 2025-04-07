# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import traceback
from typing import Tuple

from bs4 import BeautifulSoup

from pikerag.prompts.base_parser import BaseContentParser
from pikerag.utils.lxml_parser import get_soup_from_content


class LinedText:
    def __init__(self, text: str) -> None:
        self.text = text
        self.lines = text.split("\n")
        self.max_line_number = len(self.lines) - 1

    @property
    def lined_text(self):
        return "\n".join([f"Line {i} \t {line}" for i, line in enumerate(self.lines)])

    def get_lines_text(self, start_line: int, end_line: int) -> Tuple[str, str]:
        return "\n".join(self.lines[start_line:end_line])


class ResplitParser(BaseContentParser):
    def __init__(self) -> None:
        self._encoded = False

    def encode(self, content: str, **kwargs) -> Tuple[str, dict]:
        self.text = content
        self.lined_text = LinedText(self.text)
        self._encoded = True
        return self.lined_text.lined_text, {"max_line_number": self.lined_text.max_line_number}

    def decode(self, content: str, **kwargs) -> Tuple[str, str, str, int]:
        assert self._encoded is True

        try:
            soup: BeautifulSoup = get_soup_from_content(content, tag="result")
            assert soup is not None, f"Designed tag not exist in response, please refine prompt"

            chunk_soups = soup.find_all("chunk")
            assert len(chunk_soups) == 2, f"There should be exactly 2 chunks in response, Please refine prompt"

            first_chunk_endline_str: str = chunk_soups[0].find("endline").text
            if (
                len(first_chunk_endline_str) == 0
                or "not applicable" in first_chunk_endline_str.lower()  # TODO: update the prompt to limit the output
                or "not included" in first_chunk_endline_str.lower()
            ):
                first_chunk = ""
                dropped_len = 0
            else:
                first_chunk_endline = int(first_chunk_endline_str)
                first_chunk = self.lined_text.get_lines_text(0, first_chunk_endline + 1)
                first_chunk_start_pos = self.text.find(first_chunk)
                assert first_chunk_start_pos != -1, f"first chunk not exist?"
                dropped_len = first_chunk_start_pos + len(first_chunk)

            first_chunk_summary = chunk_soups[0].find("summary").text
            second_chunk_summary = chunk_soups[1].find("summary").text


        except Exception as e:
            print("Content:")
            print(content)
            print("Input Text:")
            print(self.lined_text.lined_text)
            print("Exception:")
            print(e)
            traceback.print_exc()
            exit(0)

        return first_chunk, first_chunk_summary, second_chunk_summary, dropped_len
