# workflow-first

`workflow-first` is an agent skill for designing AI-powered projects. It interviews you about the project, writes a `WORKFLOW.md` design document from your answers, and a plain-Python script checks that document.

## What it does

- Asks for your goal, then walks you through one rule: start as far left as possible, and move right only when the simpler design has been measured to fail.
  `plain code -> workflow -> single agent -> multi-agent`
- Asks who decides each next step (code, a classifier, or a model), what tools and memory are involved, what the limits and error behavior are, and which guardrails apply.
- Writes `WORKFLOW.md` from your own answers (a light or a full template), without filling in answers you did not give.
- Runs `scripts\check_workflow.py` on the result and sends failures back to you to fix.

## Status

**Status: pre-release (v0.x). Evals in progress. Tested on a small number of runs with one small model.**

- The checker was tested: a known-good document prints `OK`, and a deliberately broken one gives exactly two `FAIL:` lines.
- The newest `SKILL.md` rules have not been tested yet. These are the rules for handling "I don't know, you decide", what to write after a yes, and the updated description.
- All agent tests so far used one small model.

## Folder layout

```
workflow-first\
  SKILL.md                      the skill itself (instructions for the agent)
  references\                   guides the skill reads while running
    anti-patterns.md
    build-order.md
    context-memory-rag.md
    decision-guide.md
    evals.md
    glossary.md
    guardrails.md
    scorecard.md
    tool-design.md
  scripts\
    check_workflow.py           the checker
  templates\
    WORKFLOW.md                 full template (14 sections)
    WORKFLOW-light.md           light template (7 sections)
    WORKFLOW-light.example.md   a filled-in light file that passes the checker
    eval-task.yaml              template for one eval task
```

## Run the checker

Requires Python 3 only. No extra packages.

```
py scripts\check_workflow.py WORKFLOW.md
py scripts\check_workflow.py --early WORKFLOW.md
```

`--early` turns the eval-count and measurements-table checks into warnings. It is meant for the start of a project. All other rules are still enforced.

If `py` is not available, use `python` or `python3`.

## Install

Copy the whole `workflow-first` folder into your agent's skills folder, for example `.opencode\skills\workflow-first\`. Other agents may use a different folder. This repository does not claim support for any agent that is not named here.

## Known limitations

1. A guardrail line with no text after its number (like `- [x] 9.`) can make the checker's item regex swallow the next line.
2. The item 9 check only fails when "Robot test" says n/a.
3. The item 13 check only counts eval tasks.
4. The decision-log rule is deliberately narrow.

## License

See `LICENSE`.
