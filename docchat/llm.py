"""The FULL-version LLM path — used ONLY when an API key is configured.

In the demo this module is never invoked (config.LLM_ENABLED is False), so the
`anthropic` / `openai` packages are not even required to run DocChat. When a key
is present, the retrieved chunks are formatted into a grounded prompt and sent
to the provider for a natural-language answer.
"""
from . import config


def _format_context(hits: list[dict]) -> str:
    blocks = []
    for h in hits:
        blocks.append(
            f"[{h['doc_name']} · p.{h['page']} · chunk {h['chunk_index']}]\n{h['text']}"
        )
    return "\n\n".join(blocks)


def build_prompt(question: str, hits: list[dict]) -> str:
    context = _format_context(hits)
    return (
        "Answer the question using ONLY the context below. Cite the document and "
        "page for each fact. If the answer isn't in the context, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )


def generate_answer(question: str, hits: list[dict]) -> str:  # pragma: no cover
    """Call the configured provider. Requires the relevant SDK + API key."""
    provider = config.llm_provider()
    prompt = build_prompt(question, hits)

    if provider == "anthropic":
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # noqa: F841
            raise SystemExit('pip install anthropic to use the Anthropic LLM path.')
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in resp.content
                       if getattr(block, "type", None) == "text").strip()

    if provider == "openai":
        try:
            from openai import OpenAI
        except ImportError as exc:  # noqa: F841
            raise SystemExit("pip install openai to use the OpenAI LLM path.")
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()

    raise RuntimeError("no LLM provider configured")
