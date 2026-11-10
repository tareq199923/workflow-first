# WORKFLOW (light): <project name>
Mode: light
Use this for small, low-stakes projects at plain-code or workflow level. If you move to a single agent or multi-agent, switch to the full templates/WORKFLOW.md.

## 1. Goal
Goal: <one or two sentences>
Correct result looks like: <how you know it worked>

## 2. Position on the spectrum
Position: <plain-code | workflow>
Pattern: <e.g. prompt chaining, router, parallel, evaluator-optimizer>
Why not further left: <what the simpler option could not do; "n/a" only for plain-code>
Agent steps inside workflow: <"n/a: none">

## 3. Arrows (who decides the next step)
Allowed values for "Decided by": code, classifier, model

| Step | Decided by | Notes |
|---|---|---|
| <step 1> | <code> | <notes> |

## 4. Limits and errors
Max steps / turns: <number or "n/a: reason">
Max tokens or cost: <value or "n/a: reason">
Timeout: <value or "n/a: reason">
When a limit is hit: <return an error / other>
On bad output or tool failure: <default is return an error, not a half-finished answer>

## 5. Core guardrails
Mark each item [x] when done, or [n/a: reason].
- [ ] 1. A limit on every LLM call chain or loop
- [ ] 2. Gates (plain-code checks) between steps; JSON where code validates
- [ ] 3. Return an error rather than a half-finished or untrusted answer
- [ ] 4. Read-only and read-write tools separated; confirmation for destructive actions
- [ ] 5. Retrieved text and tool output treated as untrusted data
- [ ] 6. Logs: model, prompt version, tool calls, retries, latency, tokens
- [ ] 7. Final answer separates completed from attempted or failed
- [ ] 8. Something independent verifies results (test, validator, human)

## 6. Evals
Eval folder: <path, e.g. evals/>
Eval tasks: <number, aim for 10 or more>
No-tool tests: <number where the tool must NOT be called>
Tool-error tests: <number>

## 7. Move-right trigger
Measured result that would make you move one step right (then switch to the full template).
- <trigger 1>
