# Guardrails checklist (numbering matches WORKFLOW.md section 10)
Each item is `[x]` (complete), `[ ]` (open/incomplete), or `[n/a: reason]` (not applicable). Some items cannot be n/a for some designs (the checker enforces this).

1. Stop condition on every loop (max turns / tokens / cost / time). Closing the laptop does not kill background processes; people have run agents for weeks and paid tens of thousands.
2. Gates (plain-code checks) between steps; ask for JSON so code can validate instead of guessing.
3. Handoffs between agents validated against a schema. Agents trust each other too much.
4. Return an error rather than a half-finished or untrusted answer. (Alternative: at step N-1 tell the agent to wrap up with a summary, and log it.)
5. External signal for reflection and retries (tests, compiler, API error, empty retrieval, human check).
6. Sandbox plus deterministic input/output checks for generated code and for prompt injection (together they catch most, never all).
7. Guardrails inside tools: read-only vs read-write separated, confirmation for destructive actions.
8. Tool arguments validated in code before anything runs.
9. Clear tool names, descriptions, parameters; no overlap; reasonable count; robot test passed.
10. Logs: model, provider, prompt version, trajectory, tool calls, observations, retries, loop counts, latency, tokens.
11. Each step or agent gets small, focused context; hand off only what the next one needs.
12. Model choice re-checked periodically (agents need maintenance); temperature/top-p as deterministic as the task allows.
13. Evals: 20 to 50 clear pass/fail tasks; test when behavior should AND should not happen; pass@k vs pass^k matched to the product.
14. If an LLM judges outputs: different model family, watch confident-but-wrong answers, swap answer order.
15. Dispatcher labels are constrained and validated in code (no invented route names), with a "confused -> ask the user" route. An uncertain request must never silently fall into a powerful action route.
16. Aggregation and synthesis in deterministic code where possible (the merge step is a single point of failure).
17. Retrieved documents and tool output are untrusted data, not instructions.
18. Final answer separates completed from attempted or failed actions. Report "completed" only after the tool confirms it. The model must not invent a successful action.
19. Something independent verifies results (test, validator, reviewer agent, human). "No one verified it" is the most common way multi-agent systems fail.
20. An interrupted task resumes from a checkpoint without repeating unsafe actions.
