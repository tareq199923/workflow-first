# Eval task schema

This file is the normative schema for the files in `evals/`. `scripts/check_evals.py` enforces it, and `templates/eval-task.yaml` contains examples.

Each `.yaml` or `.yml` file may contain one or more YAML documents separated by `---`. Each document is one eval task.

## Required top-level keys

| Key | Type | Rule |
|---|---|---|
| `id` | string | Unique, non-empty, lowercase kebab-case (`my-task-name`). |
| `group` | string | One of the groups below. |
| `seeded_from` | string | One of `bug`, `user feedback`, `manual QA`, `synthetic`. |
| `prompt` | string | Non-empty. The task given to the system. |
| `runs` | integer | At least 2. More than once is the minimum; 3 is a good default. |
| `expect` | mapping | What a pass looks like. See the keys below. |

Optional keys: `setup` (how to arrange the environment) and `seed_ref` (a pointer to the real bug, feedback or QA case).

Unknown top-level keys produce a **warning**, not a failure.

## Groups

| Group | Use it when |
|---|---|
| `routing` | The system must pick the right route or label. |
| `tool-selection` | The system must pick the right read-only tool. |
| `no-tool` | The system must not call any tool. |
| `arg-validation` | A tool argument is missing or invalid, so the tool must not run. |
| `tool-error` | A tool times out or returns an error. |
| `model-error` | The model returns invalid output, or the API fails. |
| `abstain` | The correct behavior is to ask a human, ask the user, or not decide. |
| `memory` | The system must retrieve a saved decision or fact. |
| `context` | The system must keep the current goal and constraints available. |
| `checkpoint` | An interrupted task must resume from the last confirmed step. |
| `destructive` | The system is asked to delete or overwrite something. |
| `injection` | Retrieved text or tool output contains instructions. |
| `failover` | The primary provider fails and a fallback is configured. |
| `final-report` | A tool action fails and the final answer must not claim success. |
| `other` | A real case that does not fit the list. This produces a warning. |

### Group boundaries

- A **valid but wrong label** is `routing`, not `model-error`.
- An **invalid label**, a timeout, bad JSON, or an API failure is `model-error`.
- The correct behavior is to **send to a human / not decide** is `abstain`.

## `expect` keys

| Key | Type | Meaning |
|---|---|---|
| `route` | string | The route or label the system must choose. |
| `tools_allowed` | list | Tools the system is allowed to use. |
| `tools_called` | list | Tools the system must call. |
| `tools_called_not_in` | list | Tools the system must not call. |
| `max_tool_calls` | integer | The most tool calls allowed. |
| `answer_contains` | list | Strings the answer must contain. |
| `final_answer_says_failed` | boolean | The answer must say the action failed. |
| `confirmation_requested` | boolean | The system must ask for confirmation. |
| `files_deleted_before_confirmation` | integer | Files deleted before confirmation (must be 0). |
| `treated_as_data` | boolean | Retrieved text was treated as data, not instructions. |
| `no_external_action` | boolean | No external action (email, delete, purchase) happened. |
| `error_logged` | boolean | The failure was logged. |
| `max_retries` | integer | The most retries the system may use for this task. |

Unknown `expect` keys produce a **warning**, not a failure. A known key with the wrong type **fails**.

## Group rules

- `routing` requires `route`.
- `no-tool` requires `tools_allowed: []` and either `tools_called: []` or `max_tool_calls: 0`.
- `destructive` and `injection` require `no_external_action: true`.
- `max_retries` must be an integer of 0 or more and must not exceed the `Retry budget` in `WORKFLOW.md`.

## Counts checked against WORKFLOW.md

`check_evals.py` cross-checks these numbers:

| WORKFLOW.md field | Count in the eval files |
|---|---|
| `Eval tasks` | All tasks. |
| `No-tool tests` | Tasks with `group: no-tool`. |
| `Tool-error tests` | Tasks with `group: tool-error`. |
| `Model-error tests` | Tasks with `group: model-error`. |
| `Unsafe-request tests` | Tasks with `group: destructive` plus `group: injection`. |

Light mode reads these fields from section 6; full mode reads them from section 11.
