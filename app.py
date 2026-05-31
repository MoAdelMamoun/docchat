"""DocChat — FastAPI app.

Serves, all with ZERO config:
  • GET  /              → the chat UI (ask questions, see cited answers, doc list)
  • POST /api/ask       → RAG: retrieve + extractive answer (or LLM if a key is set)
  • GET  /api/documents → list indexed documents
  • POST /api/upload    → upload a PDF and chat with it (same keyless retrieval)

The demo path is keyless and offline (BM25 retrieval + extractive answer). The
LLM path runs only when an API key is configured.
"""
import shutil
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from docchat import config, rag, store

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "docchat" / "templates"))

app = FastAPI(title="DocChat", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(BASE / "docchat" / "static")),
          name="static")


@app.on_event("startup")
def _startup() -> None:
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    store.init(seed=True)


def _ctx(request: Request, **extra) -> dict:
    base = {
        "request": request,
        "demo_banner": config.DEMO_BANNER,
        "llm_enabled": config.LLM_ENABLED,
        "llm_provider": config.llm_provider(),
    }
    base.update(extra)
    return base


# --- UI -----------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def ui_chat(request: Request):
    docs = store.list_documents()
    return templates.TemplateResponse(
        request, "chat.html",
        _ctx(request, documents=docs, chunk_count=store.chunk_count()),
    )


@app.post("/reset")
def ui_reset():
    store.reset()
    return RedirectResponse("/", status_code=303)


# --- API ----------------------------------------------------------------------

@app.post("/api/ask")
async def api_ask(request: Request):
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001 - malformed/empty body
        return JSONResponse({"error": "request body must be JSON with a "
                                      "'question' field"}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "expected a JSON object"}, status_code=400)
    question = payload.get("question", "")
    result = rag.answer_question(question, top_k=payload.get("top_k"))
    return JSONResponse(result)


@app.get("/api/documents")
def api_documents():
    return {"documents": store.list_documents(),
            "chunk_count": store.chunk_count()}


@app.get("/api/documents/{doc_id}")
def api_document(doc_id: int):
    doc = store.get_document(doc_id)
    if doc is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return doc


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    name = file.filename or "upload.pdf"
    if not name.lower().endswith(".pdf"):
        return JSONResponse({"error": "only PDF files are supported"}, status_code=400)
    safe = "".join(c for c in name if c.isalnum() or c in "._- ").strip() or "upload.pdf"
    dest = config.UPLOAD_DIR / safe
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    try:
        info = store.add_document(
            name=Path(safe).stem.replace("_", " ").title(),
            filename=safe, pdf_path=str(dest), source="upload",
        )
    except Exception as exc:  # noqa: BLE001 - bad/unreadable PDF
        dest.unlink(missing_ok=True)
        return JSONResponse({"error": f"could not read PDF: {exc}"}, status_code=400)
    return JSONResponse({"ok": True, "document": info}, status_code=201)
