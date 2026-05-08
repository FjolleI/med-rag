"""Live smoke test: ingest a doc, query it, hit real Pinecone + OpenAI.

Run from the repo root:  python scripts/smoke_real.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


async def main() -> None:
    from app.services import get_llm_router, get_vector_store, is_mock_mode

    print(f"mock_mode={is_mock_mode()}")
    if is_mock_mode():
        print("  (one or more API keys still placeholders — flip them in .env)")

    vs = await get_vector_store()
    print(f"vector_store={type(vs).__name__}")

    llm = await get_llm_router()
    print(f"llm_router={type(llm).__name__}")

    print("\n[1/3] ingesting a doc...")
    await vs.add_document(
        "smoke-001",
        "Type 2 diabetes is a chronic condition that affects how the body "
        "metabolizes glucose. First-line treatment combines lifestyle changes "
        "with metformin.",
        {"title": "Diabetes Overview"},
    )
    print("    ok")

    print("\n[2/3] semantic search...")
    hits = await vs.search("How is diabetes treated?", top_k=3)
    for h in hits:
        print(f"    {h['id']}  score={h['score']:.3f}  text={h['text'][:80]!r}")

    print("\n[3/3] LLM answer...")
    answer = await llm.query("How is type 2 diabetes treated?", hits)
    print("    provider:", answer.get("provider"), "model:", answer.get("model"))
    print("    response:")
    for line in (answer.get("response") or "").splitlines():
        print(f"      {line}")
    tokens = answer.get("tokens_used", {})
    if tokens:
        print(f"    tokens: prompt={tokens.get('prompt', '?')} completion={tokens.get('completion', '?')}")

    print("\nall good.")


if __name__ == "__main__":
    asyncio.run(main())
