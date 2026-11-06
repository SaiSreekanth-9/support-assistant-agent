"""Support Assistant Agent — agentic internal support assistant (CLI).

Usage:
    python main.py ask "How do I reset my password?"
    python main.py chat            # interactive loop
    python main.py demo            # 4 canned questions, incl. an escalation
    python main.py evaluate        # groundedness eval -> examples/eval_report.md

Demo mode (no OPENAI_API_KEY) runs entirely on the standard library:
rule-based intent classification + TF-IDF retrieval + extractive answers.
With a key set, answers are refined by gpt-4o-mini via LangChain.
"""
import argparse
import sys

from src.agent import SupportAssistant

DEMO_QUESTIONS = [
    "How do I reset my password?",
    "How do I set up VPN access to work from home?",
    "How do I submit an expense report?",
    "What is the capital of France?",
]


def _print_result(result: dict) -> None:
    print(f"Intent: {result['intent']}")
    print(f"Assistant: {result['answer']}")
    if result["sources"]:
        print(f"(sources: {', '.join(result['sources'])}; "
              f"top score: {result['score']:.3f})")
    if result.get("ticket"):
        print(f"(ticket: {result['ticket']['id']})")


def cmd_ask(question: str) -> None:
    _print_result(SupportAssistant().ask(question))


def cmd_chat() -> None:
    assistant = SupportAssistant()
    print("Support Assistant ready. Ask about passwords, VPN, expenses, or "
          "ticket status (type 'exit' to quit).\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if question.lower() in {"exit", "quit"}:
            print("Bye!")
            break
        if not question:
            continue
        result = assistant.ask(question)
        print(f"\nAssistant: {result['answer']}")
        if result["sources"]:
            print(f"(sources: {', '.join(result['sources'])}; "
                  f"top score: {result['score']:.3f})")
        if result.get("ticket"):
            print(f"(ticket: {result['ticket']['id']})")
        print()


def cmd_demo() -> None:
    assistant = SupportAssistant()
    print("Support Assistant — demo run (demo mode: no API key needed)\n")
    for i, question in enumerate(DEMO_QUESTIONS, 1):
        print(f"Q{i}: {question}")
        _print_result(assistant.ask(question))
        print()


def cmd_evaluate() -> None:
    from src.evaluate import run_evaluation

    report_path = run_evaluation()
    print(report_path.read_text(encoding="utf-8"))
    print(f"Evaluation report written to {report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Agentic internal support assistant (RAG + tools + escalation).",
    )
    sub = parser.add_subparsers(dest="command")
    ask = sub.add_parser("ask", help="Ask a single question")
    ask.add_argument("question", nargs="+", help="The question to ask")
    sub.add_parser("chat", help="Interactive chat loop")
    sub.add_parser("demo", help="Run 4 canned demo questions")
    sub.add_parser("evaluate", help="Run the groundedness evaluation")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    if args.command == "ask":
        cmd_ask(" ".join(args.question))
    elif args.command == "chat":
        cmd_chat()
    elif args.command == "demo":
        cmd_demo()
    elif args.command == "evaluate":
        cmd_evaluate()


if __name__ == "__main__":
    main()
