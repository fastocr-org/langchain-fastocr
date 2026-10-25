"""Document loader that reads scanned PDFs and images with FastOCR."""
import logging
from pathlib import Path
from typing import Any, Dict, Iterator, Literal, Optional, Sequence, Union

from fastocr_sdk import FastOCR
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from ._version import __version__

logger = logging.getLogger(__name__)

USER_AGENT = f"langchain-fastocr/{__version__}"
SUPPORTED_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")

PathLike = Union[str, Path]


class FastOCRLoader(BaseLoader):
    """Load scanned PDFs and images as LangChain documents, one document per file.

    Args:
        file_path: One path or a list of paths (PDF, PNG, JPG, JPEG, GIF, WebP or BMP).
        api_key: A FastOCR API key. Defaults to the FASTOCR_API_KEY environment variable.
        output: "text" returns the text. "pdf" also saves a searchable PDF beside each
            input file as <name>.searchable.pdf and records its path in the metadata.
        base_url: Overrides the API address. Defaults to FASTOCR_BASE_URL, then https://api.fastocr.org.
        timeout: Seconds to wait for each document to finish.

    Each document's metadata has source, file_name, fastocr_document_id, pages_billed and
    status. A "partial" status means the account ran out of API pages partway: the text
    covers only the processed pages and a warning is logged. A failed document raises the
    SDK's DocumentFailedError.
    """

    def __init__(
        self,
        file_path: Union[PathLike, Sequence[PathLike]],
        *,
        api_key: Optional[str] = None,
        output: Literal["text", "pdf"] = "text",
        base_url: Optional[str] = None,
        timeout: float = 300.0,
    ) -> None:
        if output not in ("text", "pdf"):
            raise ValueError("output must be 'text' or 'pdf'")
        paths = [file_path] if isinstance(file_path, (str, Path)) else list(file_path)
        self.paths = [Path(path).expanduser() for path in paths]
        for path in self.paths:
            if path.suffix.lower() not in SUPPORTED_SUFFIXES:
                raise ValueError(f"{path.name}: FastOCR accepts PDF, PNG, JPG, JPEG, GIF, WebP and BMP files")
        self.api_key = api_key
        self.output = output
        self.base_url = base_url
        self.timeout = timeout

    def lazy_load(self) -> Iterator[Document]:
        with self._client() as client:
            for path in self.paths:
                yield self._load_one(client, path)

    def _client(self) -> FastOCR:
        client = FastOCR(api_key=self.api_key, base_url=self.base_url)
        sdk_agent = client._http.headers.get("User-Agent", "")
        client._http.headers["User-Agent"] = f"{USER_AGENT} {sdk_agent}".strip()
        return client

    def _load_one(self, client: FastOCR, path: Path) -> Document:
        job = client.documents.process(path, timeout=self.timeout)
        if job.is_partial:
            logger.warning(
                "%s: only %s of %s pages were processed because the account ran out of API pages",
                path.name,
                job.pages_billed,
                job.pages_total,
            )
        metadata: Dict[str, Any] = {
            "source": str(path),
            "file_name": path.name,
            "fastocr_document_id": job.id,
            "pages_billed": job.pages_billed,
            "status": job.status,
        }
        text = client.documents.get_text(job.id)
        if self.output == "pdf":
            destination = path.with_name(f"{path.stem}.searchable.pdf")
            client.documents.download_searchable_pdf(job.id, destination)
            metadata["searchable_pdf_path"] = str(destination)
        return Document(page_content=text, metadata=metadata)
