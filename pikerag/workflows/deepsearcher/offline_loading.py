import os
from typing import List, Union

from tqdm import tqdm

# from deepsearcher.configuration import embedding_model, vector_db, file_loader
from pikerag.workflows.deepsearcher import configuration
from pikerag.workflows.deepsearcher.loader.splitter import split_docs_to_chunks


def load_from_local_files(
    paths_or_directory: Union[str, List[str]],
    collection_name: str = None,
    collection_description: str = None,
    force_new_collection: bool = False,
    chunk_size=1500,
    chunk_overlap=100,
):
    vector_db = configuration.vector_db
    if collection_name is None:
        collection_name = vector_db.default_collection
    collection_name = collection_name.replace(" ", "_").replace("-", "_")
    embedding_model = configuration.embedding_model
    file_loader = configuration.file_loader
    print("vector_db:", vector_db)
    vector_db.init_collection(
        dim=embedding_model.dimension,
        collection=collection_name,
        description=collection_description,
        force_new_collection=force_new_collection,
    )
    if isinstance(paths_or_directory, str):
        paths_or_directory = [paths_or_directory]
    all_docs = []
    for path in tqdm(paths_or_directory, desc="Loading files"):
        if os.path.isdir(path):
            docs = file_loader.load_directory(path)
        else:
            docs = file_loader.load_file(path)
        all_docs.extend(docs)
    # print("Splitting docs to chunks...")
    chunks = split_docs_to_chunks(
        all_docs,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = embedding_model.embed_chunks(chunks)
    vector_db.insert_data(collection=collection_name, chunks=chunks)


def load_from_website(
    urls: Union[str, List[str]],
    collection_name: str = None,
    collection_description: str = None,
    force_new_collection: bool = False,
    **crawl_kwargs,
):
    if isinstance(urls, str):
        urls = [urls]
    vector_db = configuration.vector_db
    embedding_model = configuration.embedding_model
    web_crawler = configuration.web_crawler

    vector_db.init_collection(
        dim=embedding_model.dimension,
        collection=collection_name,
        description=collection_description,
        force_new_collection=force_new_collection,
    )

    all_docs = []
    for url in tqdm(urls, desc="Loading from websites"):
        docs = web_crawler.crawl_url(url, **crawl_kwargs)
        all_docs.extend(docs)

    chunks = split_docs_to_chunks(all_docs)
    chunks = embedding_model.embed_chunks(chunks)
    vector_db.insert_data(collection=collection_name, chunks=chunks)
