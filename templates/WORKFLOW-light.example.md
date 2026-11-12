# WORKFLOW (light): support-ticket summarizer (EXAMPLE, delete this line when copying)
Mode: light

## 1. Goal
Goal: Summarize tickets.
Correct result looks like: Summary matches ticket.

## 2. Position on the spectrum
Position: workflow
Pattern: prompt chaining
Why not further left: Needs language understanding that code cannot do.
Tools used: none
Agent steps inside workflow: n/a: none

## 3. Arrows (who decides the next step)
| Step | Decided by | Notes |
|---|---|---|
| check ticket text is not empty | code | gate before any LLM call |
| summarize ticket | code | one LLM call, JSON output |
| validate the JSON | code | gate; stop and return an error if invalid |

## 4. Limits and errors
Max steps / turns: 3
Max tokens or cost: 4000 tokens
Timeout: 30s
When a limit is hit: return an error
On bad output or tool failure: return an error

## 5. Core guardrails
- [x] 1. A limit on every LLM call chain or loop
- [x] 2. Gates (plain-code checks) between steps; JSON where code validates
- [x] 3. Return an error rather than a half-finished or untrusted answer
- [x] 4. Read-only and read-write tools separated; confirmation for destructive actions
- [x] 5. Retrieved text and tool output treated as untrusted data
- [x] 6. Logs: model, prompt version, tool calls, retries, latency, tokens
- [x] 7. Final answer separates completed from attempted or failed
- [x] 8. Something independent verifies results (test, validator, human)

## 6. Evals
Eval folder: evals/
Eval tasks: 12
Seeded from: user feedback and manual QA
No-tool tests: 2
Tool-error tests: 0
Model-error tests: 1
Unsafe-request tests: 1

## 7. Move-right trigger
- pass rate < 90% over 3 runs, or avg retries > 2, after trying a stronger model on the failing step
