from abc import ABC
from typing import List

from langchain_core.documents import Document


class BaseCrawler(ABC):
    def __init__(self, **kwargs):
        pass

    def crawl_url(self, url: str, **crawl_kwargs) -> List[Document]:
        pass
        # Return a list of Document objects which contain the markdown format information of the website
        # In the metadata, it's recommended to include the reference to the url.
        # e.g.
        # return [Document(page_content=..., metadata={"reference": "www.abc.com/page1.html"})]
