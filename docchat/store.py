"""Persistence + the live retrieval index.

Documents and their chunks live in SQLite so uploads survive restarts. The BM25
index is held in memory and (re)built from all chunks on startup and whenever a
document is added or removed.
"""
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import config, ingest
from .index import BM25Index

_index = BM25Index()
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    filename   TEXT NOT NULL,
    pages      INTEGER NOT NULL DEFAULT 0,
    source     TEXT NOT NULL DEFAULT 'sample',   -- 'sample' | 'upload'
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      INTEGER NOT NULL REFERENCES documents(id),
    page        INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text        TEXT NOT NULL
);
"""


def init(seed: bool = True) -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        count = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()["c"]
    if seed and not count:
        _seed_samples()
    rebuild_index()


def reset() -> None:
    with connect() as conn:
        conn.executescript("DROP TABLE IF EXISTS chunks; DROP TABLE IF EXISTS documents;")
    init(seed=True)


# --- documents & chunks -------------------------------------------------------

def add_document(*, name: str, filename: str, pdf_path: str,
                 source: str = "upload") -> dict:
    """Ingest a PDF on disk into the store and rebuild the index."""
    chunks, pages = ingest.extract_chunks(pdf_path)
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO documents (name, filename, pages, source, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, filename, pages, source, _now()),
        )
        doc_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO chunks (doc_id, page, chunk_index, text) VALUES (?, ?, ?, ?)",
            [(doc_id, c.page, c.chunk_index, c.text) for c in chunks],
        )
    rebuild_index()
    return {"id": doc_id, "name": name, "pages": pages, "n_chunks": len(chunks)}


def list_documents() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT d.*, (SELECT COUNT(*) FROM chunks c WHERE c.doc_id = d.id) "
            "AS n_chunks FROM documents d ORDER BY d.id"
        ).fetchall()
    return [dict(r) for r in rows]


def get_document(doc_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    return dict(row) if row else None


def _all_chunk_records() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT c.id, c.doc_id, c.page, c.chunk_index, c.text, d.name AS doc_name "
            "FROM chunks c JOIN documents d ON d.id = c.doc_id ORDER BY c.id"
        ).fetchall()
    return [dict(r) for r in rows]


# --- index --------------------------------------------------------------------

def rebuild_index() -> int:
    records = _all_chunk_records()
    with _lock:
        _index.build(records)
    return len(records)


def search(query: str, top_k: int | None = None) -> list[dict]:
    with _lock:
        return _index.search(query, top_k or config.TOP_K)


def chunk_count() -> int:
    with _lock:
        return len(_index.records)


# --- seed ---------------------------------------------------------------------

def _seed_samples() -> None:
    """Ingest the bundled, obviously-fictional sample PDFs."""
    if not config.SAMPLE_DIR.exists():
        return
    for pdf in sorted(config.SAMPLE_DIR.glob("*.pdf")):
        name = _pretty_name(pdf)
        add_document(name=name, filename=pdf.name, pdf_path=str(pdf),
                     source="sample")


def _pretty_name(pdf: Path) -> str:
    stem = pdf.stem.replace("_", " ").replace("-", " ")
    return stem.title()
