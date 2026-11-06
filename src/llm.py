"""Optional LLM answer refinement via LangChain + OpenAI.

This module is only imported when an ``OPENAI_API_KEY`` is set (LLM mode).
Demo mode never imports it, so the project runs with the standard library
alone. If the LangChain packages are missing in LLM mode, a clear error
tells the user to install ``requirements.txt``.
"""


def refine_answer(question: str, chunks: list[dict], model: str = "gpt-4o-mini") -> str:
    """Rewrite retrieved chunks into a grounded answer with citations.

    Raises RuntimeError with install instructions when langchain-openai
    is not available.
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "langchain-openai is not installed. Run: pip install -r requirements.txt"
        ) from exc

    context = "\n\n".join(
        f"[{c['source']}]\n{c['text']}" for c in chunks
    )
    prompt = (
        "You are an internal IT support assistant. Answer the user's question "
        "using ONLY the context below. If the context does not contain the "
        "answer, say you do not know. Cite sources like [vpn_access.md].\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    )
    llm = ChatOpenAI(model=model, temperature=0)
    return llm.invoke(prompt).content.strip()
