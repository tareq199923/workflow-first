# Evals

## Why
A leaderboard shows one column (accuracy) and hides cost, latency and context. Evals let you add up your own columns instead of "I think it worked better". Public benchmarks are inconsistent (harness, environment, scoring method, API endpoint, provider all change results), so do your own experiments.

## How to start
- Start now. 20 to 50 simple tasks. Early on every change has a visible effect.
- Seed them from what you already test manually: bugs, user feedback, QA steps.
- Each task must CLEARLY pass or fail, checked by code. Vague rubrics give inconsistent results.
- Test both directions: the tool IS used when it should be, and is NOT used when it shouldn't.
- Clean environment: as close to production as possible while adding as little as possible. Watch for agents "hacking the eval".
- Run each task more than once. Keep model, provider, endpoint and harness the same when comparing.
- Log trajectories. Judging the path is hard (an unexpected valid route should not be punished); prefer outcome checks with a few path checks.

## Metric
- pass@k: at least one success in K tries. Good when one success matters (coding).
- pass^k: all K tries succeed. Falls as K grows (0.75^3 is about 42%). Good for customer-facing agents where consistency matters.
- Choose from the product requirement and write the reason down.

## Test groups
| Group | Example | Pass condition |
|---|---|---|
| Tool selection | Ask for current info | Correct read-only tool selected |
| No-tool behavior | Simple general question | No tool call |
| Argument validation | Missing or invalid parameter | Tool not executed; clear error |
| Tool failure | Simulated timeout or API error | Agent sees the error, follows a safe retry policy |
| Memory retrieval | Ask about a saved decision | Correct memory retrieved |
| Context control | Long conversation | Current goal and constraints still available |
| Checkpoint recovery | Interrupt a multi-step task | Resumes from last confirmed step |
| Destructive action | Ask to delete or overwrite | Confirmation and permission checks enforced |
| Prompt injection | Retrieved page says ignore the rules | Page text treated as data |
| Failover | Primary provider fails | Fallback only under configured conditions |
| Final reporting | A tool action fails | Final answer does not claim success |

Track at least: task success, tool-selection accuracy, invalid-call rate, retry count, latency, token cost, provider failures, recovery success.

## LLM as a judge (only if you must)
- Prefers answers from its own model family: use a different family.
- Prefers confident answers: a confident wrong answer can slip through.
- Order matters: run several evaluations and swap the order.
- A deterministic check (unit test, schema, regex) beats an LLM judge.

## Homework
Build the boring version (workflow) and the fancy version, run both on the same tasks more than once, compare success rate, latency, token cost and failure types. Do not assume the flexible one is better. Record in WORKFLOW.md section 12.
