"""Groundedness evaluation: fixed question set -> markdown report.

Score = fraction of questions where the top retrieved document matches the
expected source doc. Retrieval only — evaluation never creates tickets.
"""
from pathlib import Path

from src.config import settings
from src.retrieval import TfIdfRetriever

EVAL_SET = [
    ("How do I reset my password?", "password_reset.md"),
    ("I forgot my password and can't log in, what should I do?", "password_reset.md"),
    ("How do I set up VPN access?", "vpn_access.md"),
    ("How do I connect to the VPN from home?", "vpn_access.md"),
    ("How do I submit an expense report?", "expense_policy.md"),
    ("What is the expense reimbursement limit for meals?", "expense_policy.md"),
]

REPORT_PATH = Path("examples/eval_report.md")


def run_evaluation() -> Path:
    """Run the eval set, write the markdown report, return its path."""
    retriever = TfIdfRetriever(settings.docs_dir)
    rows = []
    correct = 0
    for question, expected in EVAL_SET:
        results = retriever.retrieve(question, top_k=settings.top_k)
        top = results[0]["source"] if results else "—"
        top_score = results[0]["score"] if results else 0.0
        ok = top == expected
        correct += int(ok)
        rows.append((question, expected, top, top_score, ok))

    score = correct / len(EVAL_SET) if EVAL_SET else 0.0
    lines = [
        "# Evaluation report",
        "",
        "Groundedness check: for each question, does the top retrieved "
        "document match the expected source doc?",
        "",
        f"**Score: {correct}/{len(EVAL_SET)} = {score:.2f}**",
        "",
        "| Question | Expected doc | Top retrieved doc | Top score | Match |",
        "|---|---|---|---|---|",
    ]
    for question, expected, top, top_score, ok in rows:
        lines.append(
            f"| {question} | {expected} | {top} | {top_score:.3f} | "
            f"{'✅' if ok else '❌'} |"
        )
    lines += [
        "",
        f"Retriever: TF-IDF (stdlib), top-k={settings.top_k}. "
        f"Escalation threshold: {settings.escalation_threshold}.",
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return REPORT_PATH
