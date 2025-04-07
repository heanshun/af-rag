# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List, Literal, Tuple

import jsonlines
import pickle
from langchain_core.documents import Document

from pikerag.workflows.common import GenerationQaData


# Used in tagging
def load_chunks_from_jsonl(jsonl_chunk_path: str) -> List[Document]:
    with jsonlines.open(jsonl_chunk_path, "r") as reader:
        chunk_dicts = [obj for obj in reader]

    chunks: List[Document] = [
        Document(
            page_content=chunk_dict["content"],
            metadata={"chunk_id": chunk_dict["chunk_id"], "title": chunk_dict["title"]},
        )
        for chunk_dict in chunk_dicts
    ]
    return chunks


# Used in tagging
def save_chunks_to_jsonl(tagged_chunks: List[Document], dump_path: str) -> None:
    with jsonlines.open(dump_path, "w") as writer:
        for chunk in tagged_chunks:
            chunk_dict = chunk.metadata
            chunk_dict["content"] = chunk.page_content
            writer.write(chunk_dict)
    return


# Used in tagging
def load_chunks_from_pkl(filepath: str) -> List[Document]:
    with open(filepath, "rb") as fin:
        chunks = pickle.load(fin)
    return chunks


# Used in tagging
def save_chunks_to_pkl(chunks: List[Document], filepath: str) -> None:
    with open(filepath, "wb") as fout:
        pickle.dump(chunks, fout)
    return


# Used in QA
def load_testing_suite(filepath: str) -> List[GenerationQaData]:
    testing_suite = []
    with jsonlines.open(filepath, "r") as reader:
        for qa in reader:
            # TODO: update GenerationQaData definition
            metadata = qa["metadata"]
            metadata["id"] = qa["id"]
            metadata["question_type"] = qa["question_type"]
            testing_suite.append(
                GenerationQaData(
                    question=qa["question"],
                    answer_labels=[str(label) for label in qa["answer_labels"]],
                    metadata=qa["metadata"],
                )
            )
    return testing_suite


# Used in QA
def load_ids_and_chunks(filepath: str, atom_tag: str="atom_questions") -> Tuple[List[str], List[Document]]:
    chunk_ids: List[str] = []
    chunk_docs: List[Document] = []
    with jsonlines.open(filepath, "r") as reader:
        for chunk_dict in reader:
            chunk_ids.append(chunk_dict["chunk_id"])
            chunk_docs.append(
                Document(
                    # TODO: check whether to use "content" only of the concatenate of "title" and "content"
                    page_content=chunk_dict["content"],
                    # page_content=f"Title: {chunk_dict['title']}. Content: {chunk_dict['content']}",
                    metadata={
                        "id": chunk_dict["chunk_id"],
                        "title": chunk_dict["title"],
                        f"{atom_tag}_str": "\n".join(chunk_dict[atom_tag])  # TODO: allow missing
                    }
                )
            )
    return chunk_ids, chunk_docs

def load_empty_ids_and_chunks(filepath: str, atom_tag: str="atom_questions") -> Tuple[List[str], List[Document]]:
    return [], []

# Used in QA
def load_ids_and_atoms(filepath: str, atom_tag: str) -> Tuple[Literal[None], List[Document]]:
    atom_docs: List[Document] = []
    with jsonlines.open(filepath, "r") as reader:
        for chunk_dict in reader:
            for atom in chunk_dict[atom_tag]:
                atom = atom.strip()
                if len(atom) > 0:
                    atom_docs.append(
                        Document(page_content=atom, metadata={"source_chunk_id": chunk_dict["chunk_id"]})
                    )
    return None, atom_docs
