"""Agent tools, exposed through a small registry.

Each tool is a real Python function. ``search_kb`` needs a retriever, which
is injected with :func:`init_tools` (the retriever is built once by the
agent). Tickets live in a JSON file (``data/tickets.json``) so created
tickets survive across CLI runs; the file is seeded with one sample ticket.
"""
import json
from pathlib import Path

from src.config import settings

TOOLS: dict[str, object] = {}

_retriever = None


def tool(name: str):
    """Register a function in the tool registry under ``name``."""
    def decorator(func):
        TOOLS[name] = func
        return func
    return decorator


def init_tools(retriever) -> None:
    """Inject the retriever used by ``search_kb``."""
    global _retriever
    _retriever = retriever


def _tickets_path() -> Path:
    return Path(settings.tickets_file)


def _load_tickets() -> list[dict]:
    path = _tickets_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_tickets(tickets: list[dict]) -> None:
    path = _tickets_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tickets, indent=2), encoding="utf-8")


def _next_ticket_id(tickets: list[dict]) -> str:
    numbers = [
        int(t["id"].split("-")[1]) for t in tickets
        if t.get("id", "").startswith("SUP-") and t["id"].split("-")[1].isdigit()
    ]
    return f"SUP-{max(numbers, default=1000) + 1}"


@tool("search_kb")
def search_kb(query: str, top_k: int | None = None) -> list[dict]:
    """Search the internal knowledge base; returns top-k chunks with scores."""
    if _retriever is None:
        raise RuntimeError("search_kb called before init_tools(retriever)")
    return _retriever.retrieve(query, top_k=top_k or settings.top_k)


@tool("create_ticket")
def create_ticket(title: str, description: str) -> dict:
    """Create a support ticket in the (mock) ticket store and return it."""
    tickets = _load_tickets()
    ticket = {
        "id": _next_ticket_id(tickets),
        "title": title,
        "description": description,
        "status": "Open",
        "created_by": "support-assistant-agent",
    }
    tickets.append(ticket)
    _save_tickets(tickets)
    return ticket


@tool("check_ticket_status")
def check_ticket_status(ticket_id: str) -> dict | None:
    """Look up a ticket by id; returns the ticket dict or None if unknown."""
    ticket_id = ticket_id.strip().upper()
    for ticket in _load_tickets():
        if ticket.get("id", "").upper() == ticket_id:
            return ticket
    return None
