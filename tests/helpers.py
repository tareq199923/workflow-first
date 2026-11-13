"""Shared helpers for the workflow-first checker tests (standard library only)."""
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "scripts" / "check_workflow.py"
EVALS_CHECKER = REPO_ROOT / "scripts" / "check_evals.py"


def run_checker(text, *args, cwd=None, python_flags=()):
    """Write text to a temp WORKFLOW.md, run the checker, return (exit_code, output)."""
    with tempfile.TemporaryDirectory(prefix="workflow first test ") as tmp:
        path = Path(tmp) / "WORKFLOW.md"
        path.write_text(text, encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, *python_flags, str(CHECKER), str(path), *args],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return completed.returncode, completed.stdout + completed.stderr


def run_evals(workflow_text, eval_files=None, *args, dirs=(), cwd=None, python_flags=()):
    """Write a temp project and run check_evals.py, return (exit_code, output).

    eval_files maps a path relative to the project root (for example
    "evals/task.yaml") to its text. dirs creates empty directories.
    """
    with tempfile.TemporaryDirectory(prefix="workflow first evals ") as tmp:
        root = Path(tmp)
        (root / "WORKFLOW.md").write_text(workflow_text, encoding="utf-8")
        for directory in dirs:
            (root / directory).mkdir(parents=True, exist_ok=True)
        for name, content in (eval_files or {}).items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, *python_flags, str(EVALS_CHECKER), str(root / "WORKFLOW.md"), *args],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return completed.returncode, completed.stdout + completed.stderr


# A full-mode email sorter: workflow + router, no tools, no agent step.
VALID_FULL = """# WORKFLOW: customer email sorter

## 1. Goal
Goal: Sort customer email into billing, support or sales.
Correct result looks like: every email gets one label, or goes to review.

## 2. Position on the spectrum
Position: workflow
Pattern: router
Why not further left: code cannot read free-text email intent.
Evidence: n/a: no agent used; fixed workflow
Agent steps inside workflow: n/a: no agent steps
Override: n/a: none

## 3. Arrows (who decides the next step)
Allowed values for "Decided by": code, classifier, model

| Step | Decided by | Notes |
|---|---|---|
| classify the email | classifier | one model call with fixed labels |
| apply the label | code | validates the label before writing |

## 4. Models
Prototype model: gpt-4o
Cheaper-model plan: try gpt-4o-mini after evals
Determinism settings: temperature 0
Re-check models on: 2026-12-01

## 5. Tools
| Tool | Read-only or read-write | Guardrail |
|---|---|---|
| none | read-only | no tools in this design |

Robot test: n/a: no tools
MCP or skills used: n/a: none used

## 6. Knowledge, memory and context
Retrieval (RAG): n/a: no external documents
Memory: n/a: one call per email
Context protection: each call gets only the email text
Handoff contents: n/a: single step

## 7. Routes (only for dispatcher / router)
Routes: table below

| Route | Meaning | Example input | Tools allowed |
|---|---|---|---|
| billing | money question | "my invoice is wrong" | none |
| support | product problem | "the app crashes" | none |
| sales | buying question | "can I get a quote" | none |
| needs review (ask the user) | unclear email | "hi" | none |

Ambiguous example and what happens: "hi" has no signal, so it goes to needs review.

## 8. Stop conditions
Max steps / turns: 5
Max tokens or cost: 2000 tokens
Timeout: 30s
When a limit is hit: return an error and send the email to manual review

## 9. Error behavior, reflection and recovery
On bad output or tool failure: return an error, not a half-finished label
On low confidence or unclear request: send to manual review
External signal for retries and reflection: schema check on the label
Resume plan: n/a: one call per email

## 10. Guardrails checklist
Mark each item [x] when complete, [ ] while open (incomplete), or [n/a: reason] when not applicable.
- [x] 1. Stop condition on every loop; background processes can be killed
- [x] 2. Gates (plain-code checks) between steps; JSON where code validates
- [n/a: not multi-agent] 3. Handoffs between agents validated against a schema
- [x] 4. Return an error rather than a half-finished or untrusted answer
- [n/a: no reflection loop] 5. External signal for reflection and retries
- [n/a: no generated code or RAG] 6. Sandbox plus deterministic input/output checks for generated code and prompt injection
- [n/a: no tools] 7. Guardrails inside tools: read-only vs read-write, confirmation for destructive actions
- [n/a: no tools] 8. Tool arguments validated in code before anything runs
- [n/a: no tools] 9. Clear tool names, descriptions, parameters; no overlap; robot test passed
- [x] 10. Logs: model, provider, prompt version, trajectory, tool calls, retries, loop counts, latency, tokens
- [x] 11. Small, focused context per step or agent
- [x] 12. Model choice re-checked periodically; determinism settings chosen
- [x] 13. Evals: 20 to 50 clear pass/fail tasks, both directions, pass@k vs pass^k chosen
- [n/a: no judge] 14. LLM-as-judge precautions (different family, watch confident-but-wrong, swap order)
- [x] 15. Dispatcher labels constrained and validated in code, with a "confused -> ask the user" route
- [n/a: no aggregation] 16. Aggregation and synthesis in deterministic code where possible
- [x] 17. Retrieved documents and tool output treated as untrusted data
- [x] 18. Final answer separates completed from attempted or failed; "completed" only after the tool confirms
- [x] 19. Something independent verifies results (test, validator, reviewer, human): "no one verified it" is the top failure
- [n/a: one call per email] 20. Interrupted task resumes from a checkpoint without repeating unsafe actions

## 11. Evals
Eval folder: evals/
Eval tasks: 20
Seeded from: user feedback and synthetic
No-tool tests: 3
Tool-error tests: 2
Model-error tests: 1
Unsafe-request tests: 2
Metric: pass^k, consistency matters
Run conditions: same model, provider and harness; 3 runs per task
Tracked: task success, invalid labels, latency, token cost, provider failures

## 12. Measurements (add up the columns)
Run the simpler design and the candidate on the same tasks, more than once.

| Design | Runs per task | Success rate | Avg cost or tokens | Avg latency | Notes |
|---|---|---|---|---|---|
| rules only | 3 | 70% | 0 | 1s | baseline |
| router | 3 | 91% | 2000 | 2s | candidate |

## 13. Move-right triggers
Measured results that would move the design one step right (after cheaper fixes are tried).
- pass rate < 90% over 3 runs after a stronger model also fails

## 14. Decision log
- 2026-11-13: chose position workflow. Reason: measured rules-only failure. Decided by: user
"""


# Copy of templates/WORKFLOW-light.example.md as a literal (it already passes).
VALID_LIGHT = """# WORKFLOW (light): support-ticket summarizer (EXAMPLE, delete this line when copying)
Mode: light

## 1. Goal
Goal: Summarize tickets.
Correct result looks like: Summary matches ticket.

## 2. Position on the spectrum
Position: workflow
Pattern: prompt chaining
Why not further left: Needs language understanding that code cannot do.
Tools used: none
Agent steps inside workflow: n/a: no agent steps

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
"""
