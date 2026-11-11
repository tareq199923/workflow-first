# workflow-first

![workflow-first: plain code, workflow, single agent and multi-agent, with a checkpoint between each step. Below, the skill interviews you, writes WORKFLOW.md, runs the checker, and prints OK or FAIL.](assets/workflow-first-overview.svg)

`workflow-first` is an agent skill that helps you decide how to build an AI-powered project before you build it. It interviews you, writes a `WORKFLOW.md` design document from your own answers, and a plain-Python script checks that document.

The skill is built around one rule: **start as far left as you can, and move right only when the simpler design has been measured to fail.**

```
plain code  ->  workflow  ->  single agent  ->  multi-agent
```

## Status

**Status: pre-release (v0.x). Evals in progress. Tested on a small number of runs with GLM 5.3 Flash.**

- The checker was tested: a known-good document prints `OK`, and a deliberately broken one gives exactly two `FAIL:` lines.
- All agent tests so far used GLM 5.3 Flash.

## The idea

"Should I use an agent?" is not a yes-or-no question. It is a position on a spectrum: how much control do you write in code, and how much do you leave to the model at run time? Each step to the right gives more flexibility, but costs more, puts more into the model's context, and is harder to debug.

For every step in your design, the skill asks one question: **who decides what happens next?**

| Design | Who decides the next step |
| --- | --- |
| Plain code | Code |
| Workflow | You, in code, before it runs |
| Single agent | The model, choosing from paths and tools you defined |
| Multi-agent | Depends on the pattern: you (sequential), a classifier (dispatcher), or the models at run time (supervisor, peer-to-peer) |

Designs are compared on the same columns: context, reliability, cost, latency and adaptability. These are guidance, not laws. The skill says so, and asks you to measure your own system.

## What it does

The skill runs an interview, one question at a time:

1. **Goal:** what a correct result looks like.
2. **Position:** walks a decision guide from plain code upward and stops at the first "yes". It also asks who the users are and what a wrong answer costs.
3. **Arrows:** for each step, whether code, a classifier or a model decides what happens next.
4. **Models and tools:** model choice, and tool design (clear names, read-only vs read-write, MCP and skills).
5. **Knowledge, memory and context:** whether you need RAG or memory, and how context stays small.
6. **Routes** (routers and dispatchers only): constrained labels and a "confused, ask the user" route.
7. **Stop conditions, errors and recovery:** limits, what happens when one is hit, and error behavior.
8. **Guardrails:** a 20-item checklist. Each item is ticked or marked n/a with a reason.
9. **Evals:** pass/fail test tasks (20 to 50 for the full template, 10 or more for the light one).
10. **Measurements:** a baseline first. Before moving right, both designs run on the same tasks, more than once.

It then writes `WORKFLOW.md` from your answers, runs the checker, and fixes failures by going back to you.

**It does not invent answers.** If it prepares a proposed answer (for example from your existing code or README), it presents it as a proposal, and only what you confirm goes into `WORKFLOW.md`. If it cannot ask questions (a headless run), it leaves unanswered fields as placeholders and reports the open questions.

### Rules it applies

- No supervisor for dependent steps, FAQ bots or coding agents. Peer-to-peer is a last resort.
- Every loop needs a stop condition. Every agent system needs an error behavior ("return an error, not a half-finished answer") and something independent that verifies results.
- Plain code is preferred for validation gates and for aggregation.
- Reflection needs an external signal (tests, compiler, API error, human check), not a long self-critique prompt.
- Retrieved text and tool output are treated as data, not instructions.
- Moving right needs written evidence. If you want something fancier than the evidence supports, the skill tells you which rule it breaks, shows the cheaper option, and records your decision in the decision log.

## When it is used

Use it when you start an AI-powered project, feature or automation (LLM, agent, tool calling, MCP, memory, RAG), when you ask things like "should I use an agent?", "design the workflow", "draw the arrows" or "which pattern?", when you want to move an existing design to a more complex pattern, or when you need to fix checker failures or edit an existing `WORKFLOW.md`.

## Templates

- **Light** (`templates/WORKFLOW-light.md`): 7 sections, for small, low-stakes projects that are plain code or a workflow. The checker rejects it if the position is an agent or a model decides any step.
- **Full** (`templates/WORKFLOW.md`): 14 sections, for anything with an agent, tools that change things, memory or RAG, routing, or real users depending on it.

`templates/WORKFLOW-light.example.md` is a filled-in light file that passes the checker.

## The checker

`scripts/check_workflow.py` validates a `WORKFLOW.md`. It requires Python 3 only, with no extra packages.

```
py scripts\check_workflow.py WORKFLOW.md
py scripts\check_workflow.py --early WORKFLOW.md
```

It prints `OK` and exits 0 when the document passes, and prints `FAIL:` lines when it does not. If `py` is not found, use `python` or `python3`.

`--early` is for the start of a project. Eval counts and the measurements table become warnings. Evidence for an agent design, stop conditions and every other rule are still enforced.

The checker also catches contradictions, for example a guardrail ticked while another section says n/a.

## Install

Copy the whole `workflow-first` folder into your agent's skills folder, for example `.opencode\skills\workflow-first\`. Other agents may use a different folder. This repository does not claim support for any agent that is not named here.

## Folder layout

```
workflow-first/
  SKILL.md                      the skill itself (instructions for the agent)
  references/                   guides the skill reads while running
    anti-patterns.md
    build-order.md
    context-memory-rag.md
    decision-guide.md
    evals.md
    glossary.md
    guardrails.md
    scorecard.md
    tool-design.md
  scripts/
    check_workflow.py           the checker
  templates/
    WORKFLOW.md                 full template (14 sections)
    WORKFLOW-light.md           light template (7 sections)
    WORKFLOW-light.example.md   a filled-in light file that passes the checker
    eval-task.yaml              template for one eval task
  assets/
    workflow-first-overview.svg the diagram at the top of this README
```

## License

MIT. See `LICENSE`.
