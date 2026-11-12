#!/usr/bin/env python3
"""Validate eval files against WORKFLOW.md and references/eval-schema.md.

Usage: python check_evals.py WORKFLOW.md [--evals PATH]
Exit 0 = pass, 1 = failures, 2 = cannot run (missing PyYAML, bad usage).
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("FAIL: PyYAML is not installed. Run: pip install pyyaml")
    sys.exit(2)

from check_workflow import field, is_placeholder, section, to_int  # noqa: E402

GROUPS = {
    "routing",
    "tool-selection",
    "no-tool",
    "arg-validation",
    "tool-error",
    "model-error",
    "abstain",
    "memory",
    "context",
    "checkpoint",
    "destructive",
    "injection",
    "failover",
    "final-report",
    "other",
}
PROVENANCE = {"bug", "user feedback", "manual QA", "synthetic"}
REQUIRED_KEYS = ["id", "group", "seeded_from", "prompt", "runs", "expect"]
OPTIONAL_KEYS = {"setup", "seed_ref"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

EXPECT_TYPES = {
    "route": str,
    "tools_allowed": list,
    "tools_called": list,
    "tools_called_not_in": list,
    "max_tool_calls": int,
    "answer_contains": list,
    "final_answer_says_failed": bool,
    "confirmation_requested": bool,
    "files_deleted_before_confirmation": int,
    "treated_as_data": bool,
    "no_external_action": bool,
    "error_logged": bool,
    "max_retries": int,
}

COUNT_FIELDS = [
    ("Eval tasks", None),
    ("No-tool tests", "no-tool"),
    ("Tool-error tests", "tool-error"),
    ("Model-error tests", "model-error"),
    ("Unsafe-request tests", ("destructive", "injection")),
]


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def type_ok(value, expected):
    if expected is bool:
        return isinstance(value, bool)
    if expected is int:
        return is_int(value)
    if expected is list:
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    return isinstance(value, expected)


def type_name(expected):
    return {
        str: "a string",
        list: "a list of strings",
        int: "an integer",
        bool: "a boolean",
    }[expected]


def validate_expect(expect, fail, warns, filename, label):
    for key, value in expect.items():
        if not isinstance(key, str):
            warns.append(f"{filename}: task '{label}': expect key {key!r} is not a string (ignored)")
            continue
        expected = EXPECT_TYPES.get(key)
        if expected is None:
            warns.append(f"{filename}: task '{label}': unknown expect key '{key}' (ignored)")
            continue
        if not type_ok(value, expected):
            fail(f"'expect.{key}' must be {type_name(expected)}, got {value!r}")
            continue
        if expected is int:
            if value < 0:
                fail(f"'expect.{key}' must be 0 or more, got {value}")
            elif key == "files_deleted_before_confirmation" and value != 0:
                fail(f"'expect.{key}' must be 0, got {value}")


def validate_task(doc, filename, fails, warns):
    tid = doc.get("id")
    label = tid if isinstance(tid, str) and tid.strip() else "<no id>"

    def fail(message):
        fails.append(f"{filename}: task '{label}': {message}")

    for key in REQUIRED_KEYS:
        if key not in doc:
            fail(f"missing required key '{key}'")

    if "id" in doc:
        if not isinstance(tid, str) or not tid.strip():
            fail("'id' must be a non-empty string")
        elif not ID_RE.fullmatch(tid):
            fail(f"'id' must be lowercase kebab-case, got '{tid}'")

    group = doc.get("group")
    if "group" in doc:
        if not isinstance(group, str):
            fail("'group' must be a string")
        elif group not in GROUPS:
            fail(f"unknown group '{group}'")
        elif group == "other":
            warns.append(
                f"{filename}: task '{label}': group 'other' is a fallback; "
                "use a specific group when one fits"
            )

    seeded = doc.get("seeded_from")
    if "seeded_from" in doc:
        if not isinstance(seeded, str) or seeded not in PROVENANCE:
            fail(f"'seeded_from' must be one of {', '.join(sorted(PROVENANCE))}; got {seeded!r}")

    prompt = doc.get("prompt")
    if "prompt" in doc:
        if not isinstance(prompt, str) or not prompt.strip():
            fail("'prompt' must be a non-empty string")

    runs = doc.get("runs")
    if "runs" in doc:
        if not is_int(runs):
            fail(f"'runs' must be an integer, got {runs!r}")
        elif runs < 2:
            fail(f"'runs' must be at least 2, got {runs}")

    expect = doc.get("expect")
    if "expect" in doc:
        if not isinstance(expect, dict):
            fail("'expect' must be a mapping of keys to values")
        else:
            validate_expect(expect, fail, warns, filename, label)
            if group == "routing" and "route" not in expect:
                fail("group 'routing' requires 'expect.route'")
            if group == "no-tool":
                if expect.get("tools_allowed") != []:
                    fail("group 'no-tool' requires 'expect.tools_allowed: []'")
                if expect.get("tools_called") != [] and expect.get("max_tool_calls") != 0:
                    fail("group 'no-tool' requires 'expect.tools_called: []' or 'expect.max_tool_calls: 0'")
            if group in ("destructive", "injection") and expect.get("no_external_action") is not True:
                fail(f"group '{group}' requires 'expect.no_external_action: true'")

    for key in sorted(set(doc) - set(REQUIRED_KEYS) - OPTIONAL_KEYS):
        warns.append(f"{filename}: task '{label}': unknown top-level key '{key}' (ignored)")


def check_budget(text, tasks, fails, warns):
    users = []
    for filename, task in tasks:
        expect = task.get("expect")
        if isinstance(expect, dict) and is_int(expect.get("max_retries")):
            users.append((filename, task, expect["max_retries"]))
    if not users:
        return
    budget = to_int(field(text, "Retry budget"))
    if budget is None:
        warns.append("'Retry budget' is missing or not a number, so 'max_retries' values could not be checked.")
        return
    for filename, task, retries in users:
        if retries > budget:
            label = task.get("id") if isinstance(task.get("id"), str) else "<no id>"
            fails.append(
                f"{filename}: task '{label}': 'max_retries' {retries} exceeds Retry budget {budget}"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Validate eval files against WORKFLOW.md and references/eval-schema.md."
    )
    parser.add_argument("workflow", help="path to WORKFLOW.md")
    parser.add_argument("--evals", metavar="PATH", help="eval folder (default: Eval folder from WORKFLOW.md)")
    args = parser.parse_args()

    workflow_path = Path(args.workflow)
    try:
        text = workflow_path.read_text(encoding="utf-8-sig")
    except OSError as error:
        print(f"Cannot read file: {error}")
        return 2

    light = bool(re.search(r"^[ \t]*\**Mode\**\s*:\**\s*light\**\s*$", text, re.M | re.I))
    sec = 6 if light else 11
    block = section(text, sec)
    if not block:
        print(f"FAIL: Section {sec} not found in {workflow_path.name}.")
        return 1

    if args.evals:
        folder = Path(args.evals)
        if not folder.is_absolute():
            folder = Path.cwd() / folder
    else:
        value = field(block, "Eval folder")
        if is_placeholder(value):
            print(f"FAIL: Section {sec}: 'Eval folder' is missing or still a placeholder.")
            return 1
        folder = Path(value)
        if not folder.is_absolute():
            folder = workflow_path.resolve().parent / folder
    folder = folder.resolve()

    if not folder.exists():
        print(f"FAIL: Eval folder not found: {folder}")
        return 1
    if not folder.is_dir():
        print(f"FAIL: Eval folder is not a directory: {folder}")
        return 1

    files = sorted(
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in (".yaml", ".yml")
    )
    if not files:
        print(f"FAIL: No .yaml or .yml files in {folder}")
        return 1

    fails, warns = [], []
    tasks = []
    for path in files:
        try:
            documents = list(yaml.safe_load_all(path.read_text(encoding="utf-8-sig")))
        except (OSError, yaml.YAMLError) as error:
            fails.append(f"{path.name}: cannot read YAML: {error}")
            continue
        if not documents:
            fails.append(f"{path.name}: contains no eval task")
            continue
        found = 0
        for document in documents:
            if document is None:
                continue
            if not isinstance(document, dict):
                fails.append(
                    f"{path.name}: each YAML document must be a mapping, "
                    f"got {type(document).__name__}"
                )
                continue
            found += 1
            validate_task(document, path.name, fails, warns)
            tasks.append((path.name, document))
        if found == 0:
            fails.append(f"{path.name}: contains no eval task")

    seen = {}
    for filename, task in tasks:
        tid = task.get("id")
        if not isinstance(tid, str) or not tid.strip():
            continue
        if tid in seen:
            fails.append(f"duplicate id '{tid}' in {filename} (already used in {seen[tid]})")
        else:
            seen[tid] = filename

    check_budget(text, tasks, fails, warns)

    for name, groups in COUNT_FIELDS:
        expected = to_int(field(block, name))
        if expected is None:
            fails.append(
                f"Section {sec}: '{name}' is missing or not a number, "
                "so the count cannot be checked."
            )
            continue
        if groups is None:
            actual = len(tasks)
        elif isinstance(groups, tuple):
            actual = sum(1 for _, task in tasks if task.get("group") in groups)
        else:
            actual = sum(1 for _, task in tasks if task.get("group") == groups)
        if actual != expected:
            fails.append(
                f"Section {sec}: '{name}' says {expected}, but the eval files contain {actual}."
            )

    for warning in dict.fromkeys(warns):
        print("WARN:", warning)
    if fails:
        for failure in dict.fromkeys(fails):
            print("FAIL:", failure)
        print(f"\nNot ready: {len(set(fails))} problem(s).")
        return 1
    print(f"OK: {len(tasks)} eval task(s) match WORKFLOW.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
