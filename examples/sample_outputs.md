# Sample outputs

> Real output from `python main.py demo` and `python main.py evaluate`,
> run in demo mode (no API key, standard library only). Ticket IDs reflect
> a fresh ticket store seeded with SUP-1001; running `demo` again will
> create the next ticket ID.

## Demo run — `python main.py demo`

```
Support Assistant — demo run (demo mode: no API key needed)

Q1: How do I reset my password?
Intent: password_reset
Assistant: If you are still locked out after 15 minutes, or you no longer have access
to the email address on file, contact the IT help desk at
helpdesk@northwind.example or extension 4357 and ask for a manual password
reset. If you forgot your password or your account is locked, go to the Northwind
self-service password portal at password.northwind.example and click
"Forgot password". The reset link expires after 30 minutes. [password_reset.md]
(sources: password_reset.md; top score: 0.361)

Q2: How do I set up VPN access to work from home?
Intent: vpn_access
Assistant: To work remotely, you need VPN access to the Northwind office network. First, request access by emailing vpn-requests@northwind.example with your
manager copied in. If you see
error code VPN-101, your access has expired and you need to re-request it
from vpn-requests@northwind.example. [vpn_access.md]
(sources: vpn_access.md; top score: 0.315)

Q3: How do I submit an expense report?
Intent: expense
Assistant: Submit expense reports in ExpenseHub within 30 days of the purchase date. Attach a receipt for every expense over $25. If you are unsure whether an expense is
covered, ask Finance at finance@northwind.example before you spend it. [expense_policy.md]
(sources: expense_policy.md; top score: 0.226)

Q4: What is the capital of France?
Intent: out_of_scope
Assistant: I couldn't find an answer to that in the internal knowledge base, so I won't guess. I've escalated it to the IT help desk as ticket SUP-1002 — someone will follow up with you.
(ticket: SUP-1002)
```

> Q4 demonstrates the escalation path: the question scores 0.00 against the
> knowledge base (below the 0.15 threshold), so the assistant refuses to
> guess and files ticket SUP-1002 automatically.

## Single question — `python main.py ask "What is the capital of France?"`

```
Intent: out_of_scope
Assistant: I couldn't find an answer to that in the internal knowledge base, so I won't guess. I've escalated it to the IT help desk as ticket SUP-1003 — someone will follow up with you.
(ticket: SUP-1003)
```

(The ticket ID is SUP-1003 here because the demo run above had already
created SUP-1002.)

## Ticket status — `python main.py ask "What is the status of ticket SUP-1001?"`

```
Intent: ticket_status
Assistant: Ticket SUP-1001 — "VPN access request for new laptop" — is currently: In Progress.
(ticket: SUP-1001)
```

## Evaluation — `python main.py evaluate`

```
# Evaluation report

Groundedness check: for each question, does the top retrieved document match the expected source doc?

**Score: 6/6 = 1.00**

| Question | Expected doc | Top retrieved doc | Top score | Match |
|---|---|---|---|---|
| How do I reset my password? | password_reset.md | password_reset.md | 0.361 | ✅ |
| I forgot my password and can't log in, what should I do? | password_reset.md | password_reset.md | 0.288 | ✅ |
| How do I set up VPN access? | vpn_access.md | vpn_access.md | 0.358 | ✅ |
| How do I connect to the VPN from home? | vpn_access.md | vpn_access.md | 0.206 | ✅ |
| How do I submit an expense report? | expense_policy.md | expense_policy.md | 0.226 | ✅ |
| What is the expense reimbursement limit for meals? | expense_policy.md | expense_policy.md | 0.172 | ✅ |

Retriever: TF-IDF (stdlib), top-k=3. Escalation threshold: 0.15.

Evaluation report written to examples/eval_report.md
```

Full report: [examples/eval_report.md](eval_report.md).
