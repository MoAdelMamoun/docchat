"""End-to-end smoke check of the DocChat RAG pipeline (no web server, no network).

Seeds the bundled sample PDFs, builds the BM25 index, and asserts that a few
questions retrieve the right document/page with a sensible extractive answer.
Uses a throwaway temp database.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DOCCHAT_DB_PATH"] = _tmp.name

from docchat import config, rag, store  # noqa: E402


def main():
    assert not config.LLM_ENABLED, "demo must run keyless (no API key)"
    store.init(seed=True)

    docs = store.list_documents()
    print("indexed documents:")
    for d in docs:
        print(f"  #{d['id']} {d['name']} — {d['pages']}p, {d['n_chunks']} chunks")
    assert len(docs) == 3, f"expected 3 sample docs, got {len(docs)}"
    assert store.chunk_count() > 10, "expected a healthy number of chunks"

    cases = [
        ("How many vacation days do employees get?", "handbook", "20 days"),
        ("How do I reset the Widget 3000?", "widget", "10 seconds"),
        ("What is the refund window?", "refund", "30 days"),
        ("How long is the Widget 3000 battery life?", "widget", "8 hours"),
    ]
    print("\nquestions:")
    for question, want_doc, want_text in cases:
        res = rag.answer_question(question)
        assert res["mode"] == "demo", "demo must use extractive mode"
        assert res["citations"], f"no citations for: {question}"
        top = res["citations"][0]
        print(f"\n  Q: {question}")
        print(f"     mode={res['mode']} top={top['document']} p{top['page']} "
              f"score={top['score']}")
        print(f"     A: {res['answer'][:120]}")
        assert want_doc.lower() in top["document"].lower(), \
            f"expected a {want_doc} citation, got {top['document']}"
        assert want_text.lower() in res["answer"].lower(), \
            f"expected {want_text!r} in answer: {res['answer']}"

    # Unknown question → honest 'not found', still demo mode.
    miss = rag.answer_question("What is the airspeed velocity of a swallow?")
    assert miss["mode"] == "demo"
    print("\n  miss-case answer:", miss["answer"][:80])

    print("\nOK: ingestion + BM25 retrieval + extractive answers healthy")
    Path(_tmp.name).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
