import json
from typing import List

from langchain_core.documents import Document

from pikerag.workflows.deepsearcher.loader.file_loader.base import BaseLoader


class JsonFileLoader(BaseLoader):
    """load .json or .jsonl files"""

    def __init__(self, text_key: str):
        self.text_key = text_key

    def load_file(self, file_path: str) -> List[Document]:
        if file_path.endswith(".jsonl"):
            data_list: list[dict] = self._read_jsonl_file(file_path)
        else:
            data_list: list[dict] = self._read_json_file(file_path)
        documents = []
        for data_dict in data_list:
            page_content = data_dict.pop(self.text_key)
            data_dict.update({"reference": file_path})
            document = Document(page_content=page_content, metadata=data_dict)
            documents.append(document)
        return documents

    def _read_json_file(self, file_path: str) -> list[dict]:
        json_data = json.load(open(file_path))
        if not isinstance(json_data, list):
            raise ValueError("JSON file must contain a list of dictionaries.")
        return json_data

    def _read_jsonl_file(self, file_path: str) -> List[dict]:
        data_list = []
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    json_data = json.loads(line)
                    data_list.append(json_data)
                except json.JSONDecodeError:
                    print(f"Failed to decode line: {line}")
        return data_list

    @property
    def supported_file_types(self) -> List[str]:
        return ["txt", "md"]
