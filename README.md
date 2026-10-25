<div align="center">

<a href="https://fastocr.org">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/fastocr-org/langchain-fastocr/main/docs/images/logo-dark.png">
    <img src="https://raw.githubusercontent.com/fastocr-org/langchain-fastocr/main/docs/images/logo-light.png" alt="FastOCR" width="200">
  </picture>
</a>

<h3>A LangChain document loader that reads scanned PDFs and images with FastOCR.</h3>

<p>
<a href="https://github.com/fastocr-org/langchain-fastocr/actions/workflows/ci.yml"><img src="https://github.com/fastocr-org/langchain-fastocr/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="https://pypi.org/project/langchain-fastocr/"><img src="https://img.shields.io/pypi/v/langchain-fastocr.svg?label=pypi" alt="PyPI"></a>
<a href="https://pypi.org/project/langchain-fastocr/"><img src="https://img.shields.io/pypi/pyversions/langchain-fastocr.svg" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
</p>

<p>
<a href="https://fastocr.org">Website</a> ·
<a href="https://fastocr.org/docs">Docs</a> ·
<a href="https://fastocr.org/developers/keys">Get an API key</a>
</p>

<img src="https://raw.githubusercontent.com/fastocr-org/langchain-fastocr/main/docs/images/readme-hero.gif" alt="FastOCR reads a scanned page in English, Arabic and Hindi and returns its text" width="800">

</div>

## Quickstart

```bash
pip install langchain-fastocr
export FASTOCR_API_KEY="your_api_key"
```

```python
from langchain_fastocr import FastOCRLoader

documents = FastOCRLoader("scanned_contract.pdf").load()
print(documents[0].page_content)
```

Python 3.10 or newer. The distribution is `langchain-fastocr` and the import is `langchain_fastocr`.

## What you get back

`FastOCRLoader` returns one `Document` per file.

| You get | Where |
|---|---|
| The text of the whole file | `page_content` |
| The file's path and name | `metadata["source"]`, `metadata["file_name"]` |
| The FastOCR document id | `metadata["fastocr_document_id"]` |
| Pages billed | `metadata["pages_billed"]` |
| `completed` or `partial` | `metadata["status"]` |
| A searchable PDF, with `output="pdf"` | saved as `<name>.searchable.pdf` beside the input; its path is in `metadata["searchable_pdf_path"]` |

If the account runs out of pages partway through a file, you still get the text of the pages that were processed, with `status` set to `partial` and a warning in the log. A document that fails raises the error from [`fastocr-sdk`](https://pypi.org/project/fastocr-sdk/) with its message and code.

## Languages and files

- 100+ languages, detected automatically. No language setting is needed.
- PDF files up to 1 GiB, and PNG, JPG, JPEG, GIF, WebP and BMP images up to 20 MiB. An image counts as one page.

## Get an API key and pages

Any signed-in FastOCR account can create an API key and start right away.

1. Sign in and create an API key in the [developer console](https://fastocr.org/developers/keys). You accept the [API terms](https://fastocr.org/api-terms) with your first key.
2. Set the key as `FASTOCR_API_KEY`, or pass `api_key=` to the loader.
3. When you need more than the free pages, buy a Page Pack on the [pricing page](https://fastocr.org/pricing?from=api#packs). Packs work on the website and in the API.

Every account gets 50 free pages a month, shared with PDFs on the website. An image sent to the API is one page.

## Examples

### RAG over scanned PDFs

```python
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_fastocr import FastOCRLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

documents = FastOCRLoader("scanned_contract.pdf").load()
chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(documents)

store = InMemoryVectorStore.from_documents(chunks, OpenAIEmbeddings())
for hit in store.as_retriever(search_kwargs={"k": 3}).invoke("When can the contract be terminated?"):
    print(hit.metadata["file_name"], hit.page_content[:200])
```

Each chunk keeps its file's metadata, so answers can cite the source file. This example also needs `pip install langchain-openai langchain-text-splitters numpy` and an OpenAI key; any other embeddings class works the same way.

### A folder of scans

```python
from pathlib import Path

from langchain_fastocr import FastOCRLoader

scans = sorted(p for p in Path("scans").iterdir() if p.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"})
for document in FastOCRLoader(scans).lazy_load():
    print(document.metadata["file_name"], document.metadata["pages_billed"])
```

`lazy_load()` yields each document as soon as its file is finished. The loader runs one file at a time.

### Searchable PDFs for an archive

```python
from langchain_fastocr import FastOCRLoader

documents = FastOCRLoader(["invoice-001.pdf", "invoice-002.pdf"], output="pdf").load()
for document in documents:
    print(document.metadata["searchable_pdf_path"])
```

Each searchable PDF is saved beside its input, as `invoice-001.searchable.pdf`. An existing file with that name is replaced. Index the text and keep the PDF.

## Options

| Argument | Default | Meaning |
|---|---|---|
| `file_path` | required | One path or a list of paths |
| `api_key` | `FASTOCR_API_KEY` | Your FastOCR API key |
| `output` | `"text"` | `"pdf"` also saves a searchable PDF beside each input |
| `base_url` | `FASTOCR_BASE_URL`, then `https://api.fastocr.org` | API address |
| `timeout` | `300.0` | Seconds to wait for each document |

## Support and license

Questions: support@fastocr.org. Bugs and requests: [GitHub issues](https://github.com/fastocr-org/langchain-fastocr/issues). MIT license; see [LICENSE](LICENSE).
