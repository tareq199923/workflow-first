# Build order and moving right

## Typical path
1. Deterministic code first (schemas, permissions, limits, error handling).
2. Add an LLM at a step where natural language helps. See where it fails.
3. If swapping to a stronger model does not help, put a single agent at that one step (a workflow with an agent inside).
4. Make one tool-use loop reliable before adding more agents.
5. Add structured task state and checkpoints.
6. Add retrieval only when information is too large or variable for context.
7. Add reflection only when there is a real evaluation signal.
8. Add a dispatcher when there are distinct request types with different execution needs.
9. Add specialist agents only when one agent's context or responsibilities are genuinely too large.
10. Add parallel agents only when tasks are independent or redundancy demonstrably helps.
11. Add a supervisor only when subtasks cannot be planned in advance.
12. Keep the eval suite running as the system changes. Tear down what stops helping (e.g. voting agents that always agree).

## When "move right" is proposed
- Ask for measurements (section 12), not impressions. Both designs, same tasks, more than once.
- Try the cheaper fixes in anti-patterns.md first.
- Move ONE step. Update Position, Evidence, Decision log. Re-run the checker.

## Honest limits
- Scorecards are guidance, not laws. Numbers (15x tokens, ~20% Self-Refine, 98-99% guardrails, 23% benchmark gap) are context-specific.
- Patterns combine: a workflow around an agent, a dispatcher before it, parallel checks inside it, gates between stages.
- More agents do not automatically mean better results; every handoff, call, tool and merge step is a possible failure point.
- Do not choose an architecture because it sounds advanced.
