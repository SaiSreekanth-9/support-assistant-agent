# Support Assistant Agent — Agentic Internal Support Assistant

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/langchain-optional-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

An **agentic internal support assistant** that answers employee IT questions
from a small internal knowledge base, calls tools (knowledge-base search,
ticket creation, ticket status lookup), and **escalates honestly** when it
cannot ground an answer — instead of hallucinating one.

## Origin & honesty note

This is a **portfolio project inspired by** an experience on the author's
resume (an LLM-powered internal support assistant built as an intern). It
is **not** that employer's system: it was **not deployed at Eli Lilly or
any employer**, it contains **no real company data**, and it makes **no
claims about production usage, metrics, or dates**. All documents are
synthetic, written for the fictional company **Northwind Labs**, and the
ticket store is a mock JSON file. The project demonstrates the same
*patterns* — agentic workflows, tool calling, RAG with re-ranking-style
retrieval, and groundedness evaluation — on sample data only.

## Problem statement

Internal support teams drown in repeat questions (password resets, VPN
setup, expense policy) while LLM chatbots confidently invent answers to
things they don't know. This assistant pairs retrieval with an explicit
escalation rule: if the best retrieved chunk scores below a threshold, it
says so, files a ticket automatically, and hands the user a ticket ID.

## Features

- 🧭 **Intent classification** — rule-based in demo mode (`password_reset`,
  `vpn_access`, `expense`, `ticket_status`, `out_of_scope`); LLM mode can
  refine answers with ChatOpenAI
- 🔍 **TF-IDF retrieval** — standard-library only (`re`, `math`,
  `collections`), top-k=3, with source citations like `[vpn_access.md]`
- 🛡️ **Grounded answers** — answers are built only from retrieved chunks;
  below-threshold questions escalate instead of hallucinating
- 🧰 **Real tools** — a registry in `src/tools.py`: `search_kb`,
  `create_ticket`, `check_ticket_status` (mock ticket store in
  `data/tickets.json`)
- 🎫 **Low-confidence escalation** — automatically creates a ticket and
  returns its ID to the user
- 📊 **`evaluate` command** — fixed 6-question set; score = fraction where
  the top retrieved doc matches the expected doc; writes a markdown report
- ⚙️ **Demo mode needs no API key** — runs entirely on the standard library

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ User question│─────▶│   Classify   │─────▶│  ticket_     │
│              │      │   intent     │      │  status?     │
└──────────────┘      │ (rule-based) │      │  → check_    │
                      └──────┬───────┘      │  ticket_     │
                             │ else         │  status      │
                             ▼              └──────────────┘
                      ┌──────────────┐
                      │  search_kb   │
                      │  TF-IDF,     │
                      │  top-k = 3   │
                      └──────┬───────┘
                             │
                ┌────────────┴────────────┐
                │ best score < threshold? │
                ▼                         ▼
        ┌──────────────┐          ┌──────────────┐
        │  Escalate:   │          │  Grounded    │
        │  create_     │          │  answer from │
        │  ticket +    │          │  chunks      │
        │  ticket ID   │          │  + citations │
        └──────────────┘          │  (LLM refine│
                                  │   if key set)│
                                  └──────────────┘
```

**Flow:** `ask` classifies the intent. Ticket-status questions go straight
to the `check_ticket_status` tool. Everything else is retrieved with TF-IDF
over `data/sample_docs/`; a low best score triggers automatic escalation
via `create_ticket`, otherwise the answer is composed from the retrieved
chunks (extractively in demo mode, refined by GPT-4o-mini in LLM mode).

## Project structure

```
support-assistant-agent/
├── main.py                  # CLI: ask | chat | demo | evaluate
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py            # settings from env; dotenv optional
│   ├── retrieval.py         # TF-IDF indexer + retriever (stdlib only)
│   ├── tools.py             # tool registry: search_kb, create_ticket,
│   │                        #   check_ticket_status
│   ├── agent.py             # agent loop: classify -> tools -> answer/escalate
│   ├── llm.py               # optional LLM refinement (lazy import)
│   └── evaluate.py          # fixed question set -> markdown report
├── data/
│   ├── sample_docs/         # synthetic KB docs (fictional Northwind Labs)
│   │   ├── password_reset.md
│   │   ├── vpn_access.md
│   │   └── expense_policy.md
│   └── tickets.json         # mock ticket store (seeded with SUP-1001)
└── examples/
    ├── sample_outputs.md    # real demo + evaluate output
    └── eval_report.md       # generated by `python main.py evaluate`
```

## Installation

```bash
git clone <your-repo-url> support-assistant-agent
cd support-assistant-agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt   # only needed for LLM mode; demo mode needs nothing
cp .env.example .env   # leave OPENAI_API_KEY blank for demo mode
```

Demo mode runs with **no API key and no third-party packages** — just
Python 3.10+. To use LLM mode (ChatOpenAI answer refinement), install the
requirements and set `OPENAI_API_KEY` in `.env`.

## Usage

```bash
# Run the 4-question demo (password, VPN, expense, out-of-scope escalation)
python main.py demo

# Ask a single question
python main.py ask "How do I reset my password?"

# Check a ticket
python main.py ask "What is the status of ticket SUP-1001?"

# Chat interactively
python main.py chat

# Run the groundedness evaluation
python main.py evaluate
```

Example session:

```
Q1: How do I reset my password?
Intent: password_reset
Assistant: If you forgot your password or your account is locked, go to the
Northwind self-service password portal at password.northwind.example and
click "Forgot password". [password_reset.md]
(sources: password_reset.md; top score: 0.512)
```

## Configuration

All settings live in `.env` (see `.env.example`):

| Variable | Default | Meaning |
|---|---|---|
| `OPENAI_API_KEY` | *(empty)* | Leave blank for demo mode; set for LLM answer refinement |
| `CHAT_MODEL` | `gpt-4o-mini` | Chat model used in LLM mode only |
| `TOP_K` | `3` | Chunks retrieved per question |
| `ESCALATION_THRESHOLD` | `0.15` | Best TF-IDF score below this triggers escalation |
| `DOCS_DIR` | `data/sample_docs` | Knowledge-base directory |
| `TICKETS_FILE` | `data/tickets.json` | Mock ticket store |

## Sample outputs

See [examples/sample_outputs.md](examples/sample_outputs.md) for the real
`demo` and `evaluate` runs, including the out-of-scope escalation, and
[examples/eval_report.md](examples/eval_report.md) for the evaluation report.

## Limitations & future work

- TF-IDF is keyword retrieval — semantic (embedding) retrieval would handle
  paraphrases better; a re-ranker could improve top-1 accuracy further.
- Intent classification is rule-based in demo mode; an LLM classifier would
  generalise to new intents.
- The ticket store is a local JSON file, not a real ITSM integration
  (ServiceNow/Jira); no auth, no multi-user state.
- No conversation memory yet; each question is standalone.
- Planned: embedding retrieval + cross-encoder re-ranking, streaming
  responses, a Streamlit UI.

## License

MIT — see [LICENSE](LICENSE) (add one, e.g. via `gh repo create` template or choosealicense.com).
