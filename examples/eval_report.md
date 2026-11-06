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
