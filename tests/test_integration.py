"""End-to-end tests for the workflow and eval checkers working on one project."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, VALID_FULL, VALID_LIGHT


CHECK_WORKFLOW = REPO_ROOT / "scripts" / "check_workflow.py"
CHECK_EVALS = REPO_ROOT / "scripts" / "check_evals.py"


def make_eval_files(light=False):
    """Build a complete, count-consistent eval set for a valid fixture."""
    groups = (
        ["no-tool"] * 2 + ["model-error", "destructive"] + ["other"] * 8
        if light
        else ["no-tool"] * 3
        + ["tool-error"] * 2
        + ["model-error", "destructive", "injection"]
        + ["other"] * 12
    )
    files = {}
    for number, group in enumerate(groups, start=1):
        task_id = f"task-{number:02d}"
        if group == "no-tool":
            expect = "  tools_allowed: []\n  tools_called: []\n"
        elif group in ("tool-error", "model-error"):
            expect = "  max_retries: 1\n  final_answer_says_failed: true\n"
        elif group in ("destructive", "injection"):
            expect = "  no_external_action: true\n"
        else:
            expect = "  answer_contains: [checked]\n"
        files[f"evals/{task_id}.yaml"] = (
            f"id: {task_id}\n"
            f"group: {group}\n"
            "seeded_from: synthetic\n"
            f'prompt: "Integration test task {number}"\n'
            "runs: 3\n"
            "expect:\n"
            f"{expect}"
        )
    return files


def write_project(root, workflow, eval_files=None, create_eval_dir=True):
    root.mkdir(parents=True, exist_ok=True)
    workflow_path = root / "WORKFLOW.md"
    workflow_path.write_text(workflow, encoding="utf-8")
    if create_eval_dir:
        (root / "evals").mkdir(exist_ok=True)
    for name, content in (eval_files or {}).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return workflow_path


def run_script(script, workflow_path, *args):
    return subprocess.run(
        [sys.executable, str(script), str(workflow_path), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def run_workflow(workflow, *args):
    with tempfile.TemporaryDirectory(prefix="workflow first integration ") as tmp:
        path = write_project(Path(tmp), workflow)
        result = run_script(CHECK_WORKFLOW, path, *args)
        return result.returncode, result.stdout + result.stderr


def run_evals(workflow, eval_files=None, create_eval_dir=True):
    with tempfile.TemporaryDirectory(prefix="workflow first integration ") as tmp:
        path = write_project(Path(tmp), workflow, eval_files, create_eval_dir)
        result = run_script(CHECK_EVALS, path)
        return result.returncode, result.stdout + result.stderr


def run_both(workflow, eval_files):
    with tempfile.TemporaryDirectory(prefix="workflow first integration ") as tmp:
        path = write_project(Path(tmp), workflow, eval_files)
        workflow_result = run_script(CHECK_WORKFLOW, path)
        eval_result = run_script(CHECK_EVALS, path)
        return (
            (workflow_result.returncode, workflow_result.stdout + workflow_result.stderr),
            (eval_result.returncode, eval_result.stdout + eval_result.stderr),
        )


class IntegrationTests(unittest.TestCase):
    # A complete project must satisfy both validators, not just each in isolation.
    def test_valid_full_project_passes_both_checkers(self):
        workflow_result, eval_result = run_both(VALID_FULL, make_eval_files())
        self.assertEqual(workflow_result[0], 0, workflow_result[1])
        self.assertEqual(eval_result[0], 0, eval_result[1])
        self.assertIn("OK:", eval_result[1])

    def test_valid_light_project_passes_both_checkers(self):
        workflow_result, eval_result = run_both(VALID_LIGHT, make_eval_files(light=True))
        self.assertEqual(workflow_result[0], 0, workflow_result[1])
        self.assertEqual(eval_result[0], 0, eval_result[1])
        self.assertIn("OK:", eval_result[1])

    # Each WORKFLOW.md mutation introduces exactly one defect.
    def test_bare_na_agent_steps_fails_in_project(self):
        workflow = VALID_FULL.replace(
            "Agent steps inside workflow: n/a: no agent steps",
            "Agent steps inside workflow: n/a",
        )
        code, output = run_workflow(workflow)
        self.assertEqual(code, 1, output)
        self.assertIn("Agent steps inside workflow", output)

    def test_ticked_guardrail_saying_not_run_fails_in_project(self):
        workflow = VALID_FULL.replace(
            "- [x] 1. Stop condition on every loop; background processes can be killed",
            "- [x] 1. Stop condition on every loop; it has not been run",
        )
        code, output = run_workflow(workflow)
        self.assertEqual(code, 1, output)
        self.assertIn("not done", output)

    def test_open_guardrail_fails_unless_allow_open_is_used(self):
        workflow = VALID_FULL.replace(
            "- [x] 1. Stop condition on every loop; background processes can be killed",
            "- [ ] 1. Stop condition on every loop; background processes can be killed",
        )
        code, output = run_workflow(workflow)
        self.assertEqual(code, 1, output)
        self.assertIn("open", output.lower())
        allowed_code, allowed_output = run_workflow(workflow, "--allow-open")
        self.assertEqual(allowed_code, 0, allowed_output)
        self.assertIn("WARN:", allowed_output)

    def test_missing_retry_budget_fails_in_project(self):
        workflow = VALID_FULL.replace("Retry budget: 2 retries per model call\n", "")
        code, output = run_workflow(workflow)
        self.assertEqual(code, 1, output)
        self.assertIn("Retry budget", output)

    def test_missing_full_overflow_handling_fails_in_project(self):
        workflow = VALID_FULL.replace(
            "Overflow handling: email 201+ waits for the next run; none are dropped.\n",
            "",
        )
        code, output = run_workflow(workflow)
        self.assertEqual(code, 1, output)
        self.assertIn("Overflow handling", output)

    def test_missing_light_overflow_handling_fails_in_project(self):
        workflow = VALID_LIGHT.replace(
            "Overflow handling: tickets over a limit wait for the next run; none are dropped.\n",
            "",
        )
        code, output = run_workflow(workflow)
        self.assertEqual(code, 1, output)
        self.assertIn("Overflow handling", output)

    def test_agent_position_without_evidence_fails_in_project(self):
        workflow = VALID_FULL.replace(
            "Evidence: n/a: no agent used; fixed workflow",
            "Evidence: n/a: no evidence gathered",
        ).replace(
            "Agent steps inside workflow: n/a: no agent steps",
            "Agent steps inside workflow: triage agent chooses a route",
        )
        code, output = run_workflow(workflow)
        self.assertEqual(code, 1, output)
        self.assertIn("Evidence", output)

    # Each eval-project mutation changes one property while retaining the project.
    def test_missing_eval_folder_fails_in_project(self):
        code, output = run_evals(VALID_LIGHT, {}, create_eval_dir=False)
        self.assertEqual(code, 1, output)
        self.assertIn("Eval folder not found", output)

    def test_empty_eval_folder_fails_in_project(self):
        code, output = run_evals(VALID_LIGHT, {})
        self.assertEqual(code, 1, output)
        self.assertIn("No .yaml or .yml", output)

    def test_eval_count_mismatch_fails_in_project(self):
        workflow = VALID_LIGHT.replace("Eval tasks: 12", "Eval tasks: 11")
        code, output = run_evals(workflow, make_eval_files(light=True))
        self.assertEqual(code, 1, output)
        self.assertIn("'Eval tasks' says 11", output)

    def test_no_tool_count_mismatch_fails_in_project(self):
        workflow = VALID_LIGHT.replace("No-tool tests: 2", "No-tool tests: 1")
        code, output = run_evals(workflow, make_eval_files(light=True))
        self.assertEqual(code, 1, output)
        self.assertIn("'No-tool tests' says 1", output)

    def test_duplicate_eval_id_fails_in_project(self):
        files = make_eval_files(light=True)
        files["evals/task-02.yaml"] = files["evals/task-02.yaml"].replace(
            "id: task-02", "id: task-01"
        )
        code, output = run_evals(VALID_LIGHT, files)
        self.assertEqual(code, 1, output)
        self.assertIn("duplicate id 'task-01'", output)

    def test_bad_eval_provenance_fails_in_project(self):
        files = make_eval_files(light=True)
        files["evals/task-01.yaml"] = files["evals/task-01.yaml"].replace(
            "seeded_from: synthetic", "seeded_from: guesswork"
        )
        code, output = run_evals(VALID_LIGHT, files)
        self.assertEqual(code, 1, output)
        self.assertIn("seeded_from", output)

    def test_eval_retries_over_budget_fails_in_project(self):
        files = make_eval_files(light=True)
        files["evals/task-03.yaml"] = files["evals/task-03.yaml"].replace(
            "max_retries: 1", "max_retries: 3"
        )
        code, output = run_evals(VALID_LIGHT, files)
        self.assertEqual(code, 1, output)
        self.assertIn("exceeds Retry budget", output)

    def test_injection_task_without_no_external_action_fails_in_project(self):
        files = make_eval_files(light=True)
        files["evals/task-04.yaml"] = files["evals/task-04.yaml"].replace(
            "group: destructive", "group: injection"
        ).replace("  no_external_action: true\n", "  treated_as_data: true\n")
        code, output = run_evals(VALID_LIGHT, files)
        self.assertEqual(code, 1, output)
        self.assertIn("group 'injection' requires 'expect.no_external_action: true'", output)

    def test_routing_task_without_route_fails_in_project(self):
        files = make_eval_files(light=True)
        files["evals/task-05.yaml"] = files["evals/task-05.yaml"].replace(
            "group: other", "group: routing"
        )
        code, output = run_evals(VALID_LIGHT, files)
        self.assertEqual(code, 1, output)
        self.assertIn("group 'routing' requires 'expect.route'", output)


if __name__ == "__main__":
    unittest.main()
