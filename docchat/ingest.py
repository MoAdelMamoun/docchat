"""PDF ingestion — extract text with pypdf, then chunk it page-by-page.

Each chunk keeps its source document and page number so retrieval can cite
exactly where an answer came from. Pure-Python, offline: no model downloads.
"""
import re
from dataclasses import dataclass

from pypdf import PdfReader

from . import config


@dataclass
class Chunk:
    page: int
    chunk_index: int
    text: str


def _clean(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _chunk_page(words: list[str], page: int, start_index: int,
                size: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    step = max(1, size - overlap)
    i = 0
    idx = start_index
    while i < len(words):
        window = words[i:i + size]
        if not window:
            break
        chunks.append(Chunk(page=page, chunk_index=idx, text=" ".join(window)))
        idx += 1
        if i + size >= len(words):
            break
        i += step
    return chunks


def extract_chunks(pdf_path: str, size: int | None = None,
                   overlap: int | None = None) -> tuple[list[Chunk], int]:
    """Return (chunks, page_count) for a PDF on disk."""
    size = size or config.CHUNK_WORDS
    overlap = overlap or config.CHUNK_OVERLAP
    reader = PdfReader(pdf_path)
    chunks: list[Chunk] = []
    next_index = 0
    for page_no, page in enumerate(reader.pages, start=1):
        text = _clean(page.extract_text() or "")
        if not text:
            continue
        words = text.split()
        page_chunks = _chunk_page(words, page_no, next_index, size, overlap)
        chunks.extend(page_chunks)
        next_index += len(page_chunks)
    return chunks, len(reader.pages)
