"""LangChain document loaders for the FastOCR Document OCR and Bank Statement APIs."""

from ._version import __version__
from .loader import FastOCRLoader
from .statements import FastOCRBankStatementLoader

__all__ = ["__version__", "FastOCRLoader", "FastOCRBankStatementLoader"]
