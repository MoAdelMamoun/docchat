"""Configuration for DocChat.

Everything has a safe default so the demo runs with ZERO config. The demo uses
keyless, offline retrieval (BM25) and an extractive answer — no API key, no
network, no model downloads. If (and only if) an LLM API key is present in the
environment, the FULL path is used instead: the retrieved context + question
are sent to the LLM for a natural-language answer.
"""
import os
from pathlib import Path

try:  # pragma: no cover - trivial
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # noqa: BLE001
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "sample_docs"
UPLOAD_DIR = Path(os.getenv("DOCCHAT_UPLOAD_DIR", str(BASE_DIR / "uploads")))
DB_PATH = os.getenv("DOCCHAT_DB_PATH", str(BASE_DIR / "docchat_demo.db"))

# Retrieval settings.
CHUNK_WORDS = 55           # ~words per chunk (small docs → finer, precise citations)
CHUNK_OVERLAP = 15         # word overlap between consecutive chunks
TOP_K = 4                  # chunks retrieved per question

# --- LLM (FULL version only) --------------------------------------------------
# The demo NEVER calls an LLM. These keys are read only if you set them; when
# both are empty (the default) DocChat stays in keyless extractive demo mode.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("DOCCHAT_ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
OPENAI_MODEL = os.getenv("DOCCHAT_OPENAI_MODEL", "gpt-4o-mini")


def llm_provider() -> str | None:
    """Which LLM provider (if any) is configured. None → keyless demo mode."""
    if ANTHROPIC_API_KEY:
        return "anthropic"
    if OPENAI_API_KEY:
        return "openai"
    return None


LLM_ENABLED = llm_provider() is not None

DEMO_BANNER = ("Demo — keyless retrieval, no LLM. Add an API key for full AI answers. "
               "All bundled documents are fictional.")
