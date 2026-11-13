# WORKFLOW: <project name>

## 1. Goal
Goal: <one or two sentences>
Correct result looks like: <how you know it worked>

## 2. Position on the spectrum
Position: <plain-code | workflow | single-agent | multi-agent>
Pattern: <e.g. prompt chaining, router, ReAct, dispatcher, sequential, supervisor>
Why not further left: <what the simpler option could not do; "n/a" only for plain-code>
Evidence: measured: <numbers from section 12> OR n/a: <reason> for workflow/plain-code; for an override leave this n/a and fill Override
Agent steps inside workflow: <"n/a: no agent steps" or list each step where a model picks its own actions, with its stop condition>
Override: <n/a: none, or the name of the rule the user overrode>

## 3. Arrows (who decides the next step)
Allowed values for "Decided by": code, classifier, model

| Step | Decided by | Notes |
|---|---|---|
| <step 1> | <code> | <notes> |

## 4. Models
Prototype model: <start with the most capable model on every step, or n/a: reason>
Cheaper-model plan: <which steps you will try cheaper models on, after evals, one step at a time>
Determinism settings: <ask the user for temperature / top-p, or "not set">
Re-check models on: <date or trigger, e.g. every new model release>

## 5. Tools
| Tool | Read-only or read-write | Guardrail |
|---|---|---|
| <tool> | <read-only> | <guardrail> |

Robot test: <if you only had the tool names and descriptions, could you always tell which to use? what did you find and fix>
MCP or skills used: <existing MCP servers, skills (with scripts), or "n/a: reason">

## 6. Knowledge, memory and context
Retrieval (RAG): <what is retrieved, chunking, re-ranker / duplicate removal, how sources are kept. Or "n/a: reason">
Memory: <short-term state; long-term: semantic / episodic / procedural; where stored; always loaded or on demand. Or "n/a: reason">
Context protection: <what goes into each model call; what is summarized, dropped or retrieved>
Handoff contents: <the small object passed between steps or agents. Or "n/a: reason">

## 7. Routes (only for dispatcher / router)
Routes: <"n/a: no router" or "table below">

| Route | Meaning | Example input | Tools allowed |
|---|---|---|---|
| <route> | <meaning> | <example> | <tools> |

Ambiguous example and what happens: <or n/a: reason>

## 8. Stop conditions
Max steps / turns: <number or "n/a: reason">
Max tokens or cost: <value or "n/a: reason">
Timeout: <value or "n/a: reason">
When a limit is hit: <return an error / wrap up with a summary and log it / other>

## 9. Error behavior, reflection and recovery
On bad output or tool failure: <default is return an error, not a half-finished answer>
On low confidence or unclear request: <ask the user / escalate to a human / n/a: reason>
External signal for retries and reflection: <test, compiler, API error, schema check, human check, or "n/a: reason">
Resume plan: <how an interrupted task continues from the last confirmed step without repeating unsafe actions, or "n/a: reason">

## 10. Guardrails checklist
Mark each item [x] when complete, [ ] while open (incomplete), or [n/a: reason] when not applicable.
- [ ] 1. Stop condition on every loop; background processes can be killed
- [ ] 2. Gates (plain-code checks) between steps; JSON where code validates
- [ ] 3. Handoffs between agents validated against a schema
- [ ] 4. Return an error rather than a half-finished or untrusted answer
- [ ] 5. External signal for reflection and retries
- [ ] 6. Sandbox plus deterministic input/output checks for generated code and prompt injection
- [ ] 7. Guardrails inside tools: read-only vs read-write, confirmation for destructive actions
- [ ] 8. Tool arguments validated in code before anything runs
- [ ] 9. Clear tool names, descriptions, parameters; no overlap; robot test passed
- [ ] 10. Logs: model, provider, prompt version, trajectory, tool calls, retries, loop counts, latency, tokens
- [ ] 11. Small, focused context per step or agent
- [ ] 12. Model choice re-checked periodically; determinism settings chosen
- [ ] 13. Evals: 20 to 50 clear pass/fail tasks, both directions, pass@k vs pass^k chosen
- [ ] 14. LLM-as-judge precautions (different family, watch confident-but-wrong, swap order)
- [ ] 15. Dispatcher labels constrained and validated in code, with a "confused -> ask the user" route
- [ ] 16. Aggregation and synthesis in deterministic code where possible
- [ ] 17. Retrieved documents and tool output treated as untrusted data
- [ ] 18. Final answer separates completed from attempted or failed; "completed" only after the tool confirms
- [ ] 19. Something independent verifies results (test, validator, reviewer, human): "no one verified it" is the top failure
- [ ] 20. Interrupted task resumes from a checkpoint without repeating unsafe actions

## 11. Evals
Eval folder: <path, e.g. evals/>
Eval tasks: <number, aim for 20 to 50>
Seeded from: <bug | user feedback | manual QA | synthetic>
No-tool tests: <number of tests where a tool must NOT be called; 0 if there are no tools>
Tool-error tests: <number; 0 if there are no tools>
Model-error tests: <number; at least 1 when the design has no tools>
Unsafe-request tests: <number; at least 1 for any design with an LLM>
Metric: <pass@k | pass^k | other, and why>
Run conditions: <model, provider, endpoint/harness, runs per task (more than once), kept the same when comparing>
Tracked: <task success, tool-selection accuracy, invalid-call rate, retries, latency, token cost, failures, recovery success>

## 12. Measurements (add up the columns)
Run the simpler design and the candidate on the same tasks, more than once.

| Design | Runs per task | Success rate | Avg cost or tokens | Avg latency | Notes |
|---|---|---|---|---|---|
| <design> | <3> | <pass rate> | <cost> | <latency> | <notes> |

## 13. Move-right triggers
Measured results that would move the design one step right (after cheaper fixes are tried).
- <trigger 1>

## 14. Decision log
- <date>: <decision, reason, who decided>
