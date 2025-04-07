# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import pickle
from typing import List, Literal, Tuple

from datasets import load_dataset, Dataset
from tqdm import tqdm

from langchain_core.documents import Document

from pikerag.utils.walker import list_files_recursively
from pikerag.workflows.common import MultipleChoiceQaData


def load_testing_suite(path: str="cais/mmlu", name: str="college_biology") -> List[MultipleChoiceQaData]:
    dataset: Dataset = load_dataset(path, name)["test"]
    testing_suite: List[dict] = []
    for qa in dataset:
        testing_suite.append(
            MultipleChoiceQaData(
                question=qa["question"],
                metadata={
                    "subject": qa["subject"],
                },
                options={
                    chr(ord('A') + i): choice
                    for i, choice in enumerate(qa["choices"])
                },
                answer_mask_labels=[chr(ord('A') + qa["answer"])],
            )
        )
    return testing_suite


def load_ids_and_chunks(chunk_file_dir: str) -> Tuple[Literal[None], List[Document]]:
    chunks: List[Document] = []
    chunk_idx: int = 0
    for doc_name, doc_path in tqdm(
        list_files_recursively(directory=chunk_file_dir, extensions=["pkl"]),
        desc="Loading Files",
    ):
        with open(doc_path, "rb") as fin:
            chunks_in_file: List[Document] = pickle.load(fin)

        for doc in chunks_in_file:
            doc.metadata.update(
                {
                    "filename": doc_name,
                    "chunk_idx": chunk_idx,
                }
            )
            chunk_idx += 1

        chunks.extend(chunks_in_file)

    return None, chunks


def load_sample_questions(path: str="cais/mmlu", name: str="college_biology") -> List[MultipleChoiceQaData]:
    """加载一组预定义的生物学样本测试题。
    
    Returns:
        List[MultipleChoiceQaData]: 包含预定义问题的列表
    """
    sample_questions = [
        {
            "question": "如果我迟到了20分钟，会受到什么处罚？",
            "choices": ["罚款20", "没处罚", "罚款30", "开除"],
            "answer": 0,  # C: 罚款30
            "subject": "cell_biology"
        },
        {
            "question": "光合作用主要发生在植物细胞的哪个细胞器中？",
            "choices": ["叶绿体", "线粒体", "内质网", "高尔基体"],
            "answer": 0,  # A: 叶绿体
            "subject": "plant_biology"
        }
    ]
    
    testing_suite = []
    for qa in sample_questions:
        testing_suite.append(
            MultipleChoiceQaData(
                question=qa["question"],
                metadata={
                    "subject": qa["subject"],
                },
                options={
                    chr(ord('A') + i): choice
                    for i, choice in enumerate(qa["choices"])
                },
                answer_mask_labels=[chr(ord('A') + qa["answer"])],
            )
        )
    return testing_suite
