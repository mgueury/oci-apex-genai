"""Loading logic for loading documents from a directory."""
import logging
from pathlib import Path
from typing import List, Type, Union
import apex
import config

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
from langchain_community.document_loaders import BSHTMLLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_community.document_loaders import PyPDFLoader

FILE_LOADER_TYPE = Union[
    Type[UnstructuredFileLoader], Type[TextLoader], Type[BSHTMLLoader]
]
logger = logging.getLogger(__name__)


def _is_visible(p: Path) -> bool:
    parts = p.parts
    for _p in parts:
        if _p.startswith("."):
            return False
    return True


class MyDirectoryLoader(BaseLoader):
    """Loading logic for loading documents from a directory."""

    def __init__(
        self,
        path: str,
        glob: str = "**/[!.]*",
        silent_errors: bool = False,
        load_hidden: bool = False,
        loader_cls: FILE_LOADER_TYPE = UnstructuredFileLoader,
        pdfloader_cls: FILE_LOADER_TYPE = PyPDFLoader,
        loader_kwargs: Union[dict, None] = None,
        recursive: bool = False,
        show_progress: bool = False,
    ):
        """Initialize with path to directory and how to glob over it."""
        if loader_kwargs is None:
            loader_kwargs = {}
        self.path = path
        self.glob = glob
        self.load_hidden = load_hidden
        self.loader_cls = loader_cls
        # HACK 1 - (temporary) dedicated class for pdf files
        self.pdfloader_cls = pdfloader_cls
        self.loader_kwargs = loader_kwargs
        self.silent_errors = silent_errors
        self.recursive = recursive
        self.show_progress = show_progress

    def load(self, connection) -> List[Document]:
        """Load documents."""
        p = Path(self.path)
        docs = []
        items = list(p.rglob(self.glob) if self.recursive else p.glob(self.glob))

        pbar = None
        if self.show_progress:
            try:
                from tqdm import tqdm

                pbar = tqdm(total=len(items))
            except ImportError as e:
                logger.warning(
                    "To log the progress of DirectoryLoader you need to install tqdm, "
                    "`pip install tqdm`"
                )
                if self.silent_errors:
                    logger.warning(e)
                else:
                    raise e

        for i in items:
            if i.is_file():
                if _is_visible(i.relative_to(p)) or self.load_hidden:
                    try:
                        # HACK 2 - only send pdf filess to `PyPDFLoader` (default) until `UnstructuredFileLoader` is fixed
                        if i.name.endswith('.pdf'):
                            sub_docs = self.pdfloader_cls(str(i), **self.loader_kwargs).load()
                        else:
                            sub_docs = self.loader_cls(str(i), **self.loader_kwargs).load()
                        print( sub_docs )
                        if config.ORACLE_USERNAME=='apex_app':
                            sub_docs = apex.apexInsertSubDocs( connection, sub_docs )    
                        docs.extend(sub_docs)
                    except Exception as e:
                        if self.silent_errors:
                            logger.warning(e)
                        else:
                            raise e
                    finally:
                        if pbar:
                            pbar.update(1)

        if pbar:
            pbar.close()

        return docs