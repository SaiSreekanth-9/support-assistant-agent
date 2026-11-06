"""The support assistant agent loop.

Flow: classify intent -> ticket-status requests go straight to the
``check_ticket_status`` tool -> everything else searches the knowledge
base with ``search_kb`` -> if the best retrieval score is below the
escalation threshold, the question is escalated (a ticket is created
automatically) instead of answering from nothing -> otherwise a grounded
answer is composed from the retrieved chunks, with citations.

Demo mode (no ``OPENAI_API_KEY``) is rule-based + extractive: the answer is
built from sentences in the retrieved chunks. With a key set, the answer
is refined by an LLM (see ``src/llm.py``) — still grounded in the same
retrieved chunks.
"""
import re

from src.config import settings
from src.retrieval import TfIdfRetriever, tokenize
from src.tools import check_ticket_status, create_ticket, init_tools, search_kb

INTENT_KEYWORDS = {
    "password_reset": {
        "password", "reset", "forgot", "locked", "lockout", "login",
        "log in", "sign in", "signin", "credentials", "mfa",
        "authenticator",
    },
    "vpn_access": {
        "vpn", "remote access", "connect to the office", "office network",
        "globalprotect", "vpn-101",
    },
    "expense": {
        "expense", "reimburse", "reimbursement", "receipt", "expensehub",
        "travel cost", "meal", "mileage", "per diem",
    },
    "ticket_status": {
        "ticket", "status of", "sup-", "my request", "check my",
    },
}

TICKET_ID_RE = re.compile(r"SUP-\d+", re.IGNORECASE)


def classify_intent(question: str) -> str:
    """Rule-based intent classification (used in demo mode)."""
    text = question.lower()
    if TICKET_ID_RE.search(text) or "ticket" in text:
        return "ticket_status"
    for intent, keywords in INTENT_KEYWORDS.items():
        if intent == "ticket_status":
            continue
        if any(kw in text for kw in keywords):
            return intent
    return "out_of_scope"


def _extractive_answer(question: str, chunks: list[dict]) -> str:
    """Build an answer from the most relevant sentences in the chunks."""
    query_tokens = set(tokenize(question))
    scored: list[tuple[int, str, str]] = []
    for chunk in chunks:
        for sentence in re.split(r"(?<=[.!?])\s+", chunk["text"]):
            sentence = sentence.strip()
            if not sentence:
                continue
            overlap = len(query_tokens & set(tokenize(sentence)))
            scored.append((overlap, sentence, chunk["source"]))
    scored.sort(key=lambda s: s[0], reverse=True)
    # Keep sentences that share at least one query term, up to 3, in
    # retrieval order; fall back to the top chunk's first sentences.
    picked = [s for s in scored if s[0] > 0][:3]
    if not picked:
        picked = [(0, s, c) for s, c in
                  [(sent, chunks[0]["source"]) for sent in
                   re.split(r"(?<=[.!?])\s+", chunks[0]["text"])[:2]]]
    sources = sorted({source for _, _, source in picked})
    body = " ".join(sentence for _, sentence, _ in picked)
    citations = " ".join(f"[{s}]" for s in sources)
    return f"{body} {citations}"


class SupportAssistant:
    """Agentic internal support assistant (RAG + tools + escalation)."""

    def __init__(self):
        self.retriever = TfIdfRetriever(settings.docs_dir)
        init_tools(self.retriever)

    def ask(self, question: str) -> dict:
        """Answer one question. Returns a result dict for the CLI."""
        question = question.strip()
        intent = classify_intent(question)

        if intent == "ticket_status":
            match = TICKET_ID_RE.search(question)
            if not match:
                return {
                    "intent": intent, "answer": (
                        "I can check a ticket's status if you give me its "
                        "ticket ID (for example SUP-1001). What is the ticket ID?"
                    ),
                    "sources": [], "score": 0.0, "escalated": False,
                    "ticket": None,
                }
            ticket = check_ticket_status(match.group(0))
            if ticket is None:
                return {
                    "intent": intent, "answer": (
                        f"I could not find ticket {match.group(0).upper()} in "
                        "the ticket store. Please check the ID and try again."
                    ),
                    "sources": [], "score": 0.0, "escalated": False,
                    "ticket": None,
                }
            return {
                "intent": intent, "answer": (
                    f"Ticket {ticket['id']} — \"{ticket['title']}\" — "
                    f"is currently: {ticket['status']}."
                ),
                "sources": [], "score": 1.0, "escalated": False,
                "ticket": ticket,
            }

        results = search_kb(question)
        best_score = results[0]["score"] if results else 0.0
        sources = sorted({r["source"] for r in results})

        if best_score < settings.escalation_threshold:
            ticket = create_ticket(
                title=f"Escalated question: {question[:80]}",
                description=(
                    "The support assistant could not find a grounded answer "
                    f"in the knowledge base (best retrieval score "
                    f"{best_score:.2f}, threshold "
                    f"{settings.escalation_threshold:.2f}).\n\n"
                    f"Question: {question}"
                ),
            )
            return {
                "intent": intent, "answer": (
                    "I couldn't find an answer to that in the internal "
                    "knowledge base, so I won't guess. I've escalated it to "
                    "the IT help desk as ticket "
                    f"{ticket['id']} — someone will follow up with you."
                ),
                "sources": [], "score": best_score, "escalated": True,
                "ticket": ticket,
            }

        if settings.demo_mode:
            answer = _extractive_answer(question, results)
        else:
            from src.llm import refine_answer

            answer = refine_answer(question, results, model=settings.chat_model)

        return {
            "intent": intent, "answer": answer, "sources": sources,
            "score": best_score, "escalated": False, "ticket": None,
        }
