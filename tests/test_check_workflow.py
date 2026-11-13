import re
import tempfile
import unittest

from helpers import REPO_ROOT, VALID_FULL, VALID_LIGHT, run_checker


def with_tools(text):
    """Turn the no-tools full fixture into a read-only-tool fixture."""
    text = text.replace(
        "| none | read-only | no tools in this design |",
        "| search | read-only | validates the query before calling |",
    )
    text = text.replace(
        "Robot test: n/a: no tools",
        "Robot test: tool names and descriptions are distinct",
    )
    for number in (7, 8, 9):
        text = text.replace(f"- [n/a: no tools] {number}.", f"- [x] {number}.")
    return text


def with_agent_step(text):
    """Turn the no-agent full fixture into a workflow with one agent step."""
    return text.replace(
        "Evidence: n/a: no agent used; fixed workflow\n"
        "Agent steps inside workflow: n/a: no agent steps",
        "Evidence: measured: rules only 70%, agent step 91% on 20 tasks\n"
        "Agent steps inside workflow: triage agent picks tools and stops after 3 actions",
    )


def with_override(text):
    """Use the override path: unmeasured evidence plus a logged user override."""
    text = with_agent_step(text)
    text = text.replace(
        "Evidence: measured: rules only 70%, agent step 91% on 20 tasks",
        "Evidence: n/a: user accepted the evidence risk",
    )
    text = text.replace("Override: n/a: none", "Override: evidence requirement")
    text = text.replace(
        "- 2026-11-13: chose position workflow. Reason: measured rules-only failure. Decided by: user",
        "- 2026-11-13: user override: evidence requirement. Reason: accepted risk. Decided by: user\n"
        "- 2026-11-13: chose position workflow. Reason: measured rules-only failure. Decided by: user",
    )
    return text


class CheckWorkflowTests(unittest.TestCase):
    def test_valid_full_passes(self):
        code, output = run_checker(VALID_FULL)
        self.assertEqual(code, 0, output)

    def test_valid_light_passes(self):
        code, output = run_checker(VALID_LIGHT)
        self.assertEqual(code, 0, output)

    def test_missing_goal_fails(self):
        text = VALID_FULL.replace("Goal: Sort customer email into billing, support or sales.\n", "")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    def test_works_from_other_cwd(self):
        with tempfile.TemporaryDirectory(prefix="workflow first cwd ") as tmp:
            code, output = run_checker(VALID_FULL, cwd=tmp)
        self.assertEqual(code, 0, output)

    def test_full_requires_retry_budget(self):
        text = VALID_FULL.replace("Retry budget: 2 retries per model call\n", "")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Retry budget", output)

    def test_light_requires_retry_budget(self):
        text = VALID_LIGHT.replace("Retry budget: 2 retries per model call\n", "")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Retry budget", output)

    def test_missing_overflow_handling_fails(self):
        text = VALID_FULL.replace(
            "Overflow handling: email 201+ waits for the next run; none are dropped.\n",
            "",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Overflow handling", output)

    def test_overflow_na_fails_when_limit_set(self):
        full = VALID_FULL.replace(
            "Overflow handling: email 201+ waits for the next run; none are dropped.",
            "Overflow handling: n/a: no overflow",
        )
        code, output = run_checker(full)
        self.assertEqual(code, 1, output)
        self.assertIn("Overflow handling", output)
        light = VALID_LIGHT.replace(
            "Overflow handling: tickets over a limit wait for the next run; none are dropped.",
            "Overflow handling: n/a: no overflow",
        )
        code, output = run_checker(light)
        self.assertEqual(code, 1, output)
        self.assertIn("Overflow handling", output)

    def test_bare_na_agent_steps_fails(self):
        """P7: a bare n/a on Agent steps inside workflow should fail."""
        text = VALID_FULL.replace(
            "Agent steps inside workflow: n/a: no agent steps",
            "Agent steps inside workflow: n/a",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    def test_light_no_tools_allows_zero_no_tool_tests(self):
        """P4: a design with no tools should not need No-tool tests."""
        text = VALID_LIGHT.replace("No-tool tests: 2", "No-tool tests: 0")
        code, output = run_checker(text)
        self.assertEqual(code, 0, output)

    def test_light_missing_tools_used_fails(self):
        text = VALID_LIGHT.replace("Tools used: none\n", "")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Tools used", output)

    def test_light_missing_model_error_tests_fails(self):
        text = VALID_LIGHT.replace("Model-error tests: 1\n", "")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Model-error tests", output)

    def test_full_missing_model_error_tests_fails(self):
        text = VALID_FULL.replace("Model-error tests: 1\n", "")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Model-error tests", output)

    def test_light_no_tools_requires_model_error_tests(self):
        text = VALID_LIGHT.replace("Model-error tests: 1", "Model-error tests: 0")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Model-error tests", output)

    def test_full_no_tools_requires_model_error_tests(self):
        text = VALID_FULL.replace("Model-error tests: 1", "Model-error tests: 0")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Model-error tests", output)

    def test_light_tools_present_requires_tool_error_tests(self):
        text = VALID_LIGHT.replace("Tools used: none", "Tools used: search")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Tool-error tests", output)

    def test_light_tools_present_requires_no_tool_tests(self):
        text = VALID_LIGHT.replace("Tools used: none", "Tools used: search")
        text = text.replace("No-tool tests: 2", "No-tool tests: 0")
        text = text.replace("Tool-error tests: 0", "Tool-error tests: 1")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("No-tool tests", output)

    def test_light_tools_present_allows_zero_model_error_tests(self):
        text = VALID_LIGHT.replace("Tools used: none", "Tools used: search")
        text = text.replace("Tool-error tests: 0", "Tool-error tests: 1")
        text = text.replace("Model-error tests: 1", "Model-error tests: 0")
        code, output = run_checker(text)
        self.assertEqual(code, 0, output)

    def test_light_zero_unsafe_request_tests_warns_but_passes(self):
        text = VALID_LIGHT.replace("Unsafe-request tests: 1", "Unsafe-request tests: 0")
        code, output = run_checker(text)
        self.assertEqual(code, 0, output)
        self.assertIn("WARN:", output)
        self.assertIn("Unsafe-request tests", output)

    def test_full_tools_present_allows_zero_model_error_tests(self):
        text = with_tools(VALID_FULL)
        text = text.replace("Model-error tests: 1", "Model-error tests: 0")
        code, output = run_checker(text)
        self.assertEqual(code, 0, output)

    def test_full_tools_present_requires_no_tool_tests(self):
        text = with_tools(VALID_FULL)
        text = text.replace("No-tool tests: 3", "No-tool tests: 0")
        text = text.replace("Model-error tests: 1", "Model-error tests: 0")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("No-tool tests", output)

    def test_full_tools_present_requires_tool_error_tests(self):
        text = with_tools(VALID_FULL)
        text = text.replace("Tool-error tests: 2", "Tool-error tests: 0")
        text = text.replace("Model-error tests: 1", "Model-error tests: 0")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Tool-error tests", output)

    def test_ticked_guardrail_with_not_run_text_fails(self):
        """P11: a ticked guardrail whose text says it was not run should fail."""
        text = VALID_FULL.replace(
            "- [x] 1. Stop condition on every loop; background processes can be killed",
            "- [x] 1. robot test has not been run",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    def test_guardrail_numbers_must_be_exact(self):
        """P11: guardrails numbered 1-19 plus 21 should fail."""
        text = VALID_FULL.replace(
            "- [n/a: one call per email] 20. Interrupted task resumes from a checkpoint without repeating unsafe actions",
            "- [n/a: one call per email] 21. Interrupted task resumes from a checkpoint without repeating unsafe actions",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    def test_incomplete_guardrail_reports_open_not_unchecked(self):
        text = VALID_FULL.replace(
            "- [x] 1. Stop condition on every loop; background processes can be killed",
            "- [ ] 1. Stop condition on every loop; background processes can be killed",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("OPEN: Section 10: item 1 is incomplete", output)
        self.assertNotIn("unchecked", output)

    def test_allow_open_returns_success_with_warning(self):
        text = VALID_FULL.replace(
            "- [x] 1. Stop condition on every loop; background processes can be killed",
            "- [ ] 1. Stop condition on every loop; background processes can be killed",
        )
        code, output = run_checker(text, "--allow-open")
        self.assertEqual(code, 0, output)
        self.assertIn("OPEN: Section 10: item 1 is incomplete", output)
        self.assertIn("WARN:", output)
        self.assertIn("draft", output.lower())

    def test_incomplete_light_guardrail_reports_open(self):
        text = VALID_LIGHT.replace(
            "- [x] 1. A limit on every LLM call chain or loop",
            "- [ ] 1. A limit on every LLM call chain or loop",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("OPEN: Section 5: item 1 is incomplete", output)
        self.assertNotIn("unchecked", output)

    def test_ticked_guardrail_with_incomplete_text_fails(self):
        text = VALID_FULL.replace(
            "- [x] 1. Stop condition on every loop; background processes can be killed",
            "- [x] 1. robot test is incomplete",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    def test_ticked_guardrail_normal_sentences_pass(self):
        text = VALID_FULL.replace(
            "- [x] 1. Stop condition on every loop; background processes can be killed",
            "- [x] 1. robot test run on all 3 tools",
        )
        text = text.replace(
            "- [x] 2. Gates (plain-code checks) between steps; JSON where code validates",
            "- [x] 2. ready to run in CI",
        )
        text = text.replace(
            "- [n/a: not multi-agent] 3. Handoffs between agents validated against a schema",
            "- [x] 3. all gates are done in code",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 0, output)

    def test_ticked_guardrail_pending_phrases_pass(self):
        """D2: pending / to run in CI / not yet executed are plans, not contradictions."""
        phrases = ("pending", "to run in CI", "not yet executed")
        fixtures = (
            ("full", VALID_FULL,
             "- [x] 1. Stop condition on every loop; background processes can be killed"),
            ("light", VALID_LIGHT,
             "- [x] 1. A limit on every LLM call chain or loop"),
        )
        for label, fixture, original in fixtures:
            for phrase in phrases:
                with self.subTest(mode=label, phrase=phrase):
                    text = fixture.replace(original, f"- [x] 1. robot test {phrase}")
                    code, output = run_checker(text)
                    self.assertEqual(code, 0, output)

    def test_light_guardrail_numbers_must_be_exact(self):
        text = VALID_LIGHT.replace(
            "- [x] 8. Something independent verifies results (test, validator, human)",
            "- [x] 9. Something independent verifies results (test, validator, human)",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("missing", output)
        self.assertIn("unexpected", output)

    def test_bare_na_agent_steps_fails_in_light(self):
        text = VALID_LIGHT.replace(
            "Agent steps inside workflow: n/a: no agent steps",
            "Agent steps inside workflow: n/a",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    def test_bare_na_evidence_fails(self):
        text = VALID_FULL.replace(
            "Evidence: n/a: no agent used; fixed workflow",
            "Evidence: n/a",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    def test_pattern_na_fails_above_plain_code(self):
        full = VALID_FULL.replace("Pattern: router", "Pattern: n/a")
        code, output = run_checker(full)
        self.assertEqual(code, 1, output)
        light = VALID_LIGHT.replace("Pattern: prompt chaining", "Pattern: n/a")
        code, output = run_checker(light)
        self.assertEqual(code, 1, output)

    def test_pattern_na_allowed_for_plain_code(self):
        text = VALID_LIGHT.replace("Position: workflow", "Position: plain-code")
        text = text.replace("Pattern: prompt chaining", "Pattern: n/a")
        text = text.replace(
            "Why not further left: Needs language understanding that code cannot do.",
            "Why not further left: n/a: plain code is enough",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 0, output)

    def test_plain_none_evidence_fails_for_agent(self):
        text = with_agent_step(VALID_FULL).replace(
            "Evidence: measured: rules only 70%, agent step 91% on 20 tasks",
            "Evidence: none",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    def test_it_was_slow_evidence_fails_for_agent(self):
        text = with_agent_step(VALID_FULL).replace(
            "Evidence: measured: rules only 70%, agent step 91% on 20 tasks",
            "Evidence: it was slow",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    def test_agent_step_with_measured_evidence_passes(self):
        code, output = run_checker(with_agent_step(VALID_FULL))
        self.assertEqual(code, 0, output)

    def test_override_with_date_and_log_passes_with_warning(self):
        code, output = run_checker(with_override(VALID_FULL))
        self.assertEqual(code, 0, output)
        self.assertIn("WARN: unmeasured design: user override recorded", output)

    def test_override_without_decision_log_fails(self):
        text = with_override(VALID_FULL).replace(
            "- 2026-11-13: user override: evidence requirement. Reason: accepted risk. Decided by: user\n",
            "",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("decision", output)

    def test_override_without_date_fails(self):
        text = with_override(VALID_FULL).replace(
            "- 2026-11-13: user override: evidence requirement.",
            "- user override: evidence requirement.",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("decision", output)

    def test_override_waives_section_12_measurements(self):
        text = with_override(VALID_FULL).replace(
            "| rules only | 3 | 70% | 0 | 1s | baseline |\n"
            "| router | 3 | 91% | 2000 | 2s | candidate |",
            "| rules only | 1 | 70% | 0 | 1s | one run only |",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 0, output)
        self.assertIn("user override recorded", output)

    def test_override_does_not_waive_eval_minimum(self):
        text = with_override(VALID_FULL)
        text = text.replace("Eval tasks: 20", "Eval tasks: 12")
        text = text.replace("- [x] 13.", "- [n/a: evals not finished] 13.")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("only 12 eval tasks", output)

    def test_early_mode_keeps_item13_contradiction(self):
        text = VALID_FULL.replace("Eval tasks: 20", "Eval tasks: 12")
        code, output = run_checker(text, "--early")
        self.assertEqual(code, 1, output)
        self.assertIn("item 13 is ticked", output)

    def test_early_mode_downgrades_eval_count_only(self):
        text = VALID_FULL.replace("Eval tasks: 20", "Eval tasks: 12")
        text = text.replace("- [x] 13.", "- [n/a: evals not finished] 13.")
        code, output = run_checker(text, "--early")
        self.assertEqual(code, 0, output)
        self.assertIn("only 12 eval tasks", output)

        text = text.replace("Model-error tests: 1", "Model-error tests: 0")
        code, output = run_checker(text, "--early")
        self.assertEqual(code, 0, output)
        self.assertIn(
            "WARN: Section 11: with an LLM and no tools, need at least 1 in 'Model-error tests'",
            output,
        )

        text = text.replace("Model-error tests: 0", "Model-error tests: n/a")
        code, output = run_checker(text, "--early")
        self.assertEqual(code, 1, output)
        self.assertIn("must be a number", output)

    def test_full_group_minimums_fail_without_early(self):
        tool_text = with_tools(VALID_FULL)
        for name, old, new in (
            ("No-tool tests", "No-tool tests: 3", "No-tool tests: 0"),
            ("Tool-error tests", "Tool-error tests: 2", "Tool-error tests: 0"),
            ("Unsafe-request tests", "Unsafe-request tests: 2", "Unsafe-request tests: 0"),
        ):
            with self.subTest(name=name):
                code, output = run_checker(tool_text.replace(old, new))
                self.assertEqual(code, 1, output)
                self.assertIn(name, output)

        text = VALID_FULL.replace("Model-error tests: 1", "Model-error tests: 0")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Model-error tests", output)

    def test_full_group_minimums_warn_with_early(self):
        text = with_tools(VALID_FULL)
        text = text.replace("Eval tasks: 20", "Eval tasks: 0")
        text = text.replace("No-tool tests: 3", "No-tool tests: 0")
        text = text.replace("Tool-error tests: 2", "Tool-error tests: 0")
        text = text.replace("Model-error tests: 1", "Model-error tests: 0")
        text = text.replace("Unsafe-request tests: 2", "Unsafe-request tests: 0")
        text = text.replace("- [x] 13.", "- [n/a: evals not written yet] 13.")
        code, output = run_checker(text, "--early")
        self.assertEqual(code, 0, output)
        self.assertIn("WARN: Section 11: only 0 eval tasks", output)
        self.assertIn("WARN: Section 11: need at least 1 in 'No-tool tests'", output)
        self.assertIn("WARN: Section 11: need at least 1 in 'Tool-error tests'", output)
        self.assertIn("WARN: Section 11: need at least 1 in 'Unsafe-request tests'", output)

        text = VALID_FULL.replace("Eval tasks: 20", "Eval tasks: 0")
        text = text.replace("No-tool tests: 3", "No-tool tests: 0")
        text = text.replace("Tool-error tests: 2", "Tool-error tests: 0")
        text = text.replace("Model-error tests: 1", "Model-error tests: 0")
        text = text.replace("Unsafe-request tests: 2", "Unsafe-request tests: 0")
        text = text.replace("- [x] 13.", "- [n/a: evals not written yet] 13.")
        code, output = run_checker(text, "--early")
        self.assertEqual(code, 0, output)
        self.assertIn(
            "WARN: Section 11: with an LLM and no tools, need at least 1 in 'Model-error tests'",
            output,
        )

    def test_light_group_minimums_fail_without_early(self):
        tool_text = VALID_LIGHT.replace("Tools used: none", "Tools used: search")

        text = tool_text.replace("No-tool tests: 2", "No-tool tests: 0")
        text = text.replace("Tool-error tests: 0", "Tool-error tests: 1")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("No-tool tests", output)

        text = tool_text.replace("No-tool tests: 2", "No-tool tests: 1")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Tool-error tests", output)

        text = VALID_LIGHT.replace("Model-error tests: 1", "Model-error tests: 0")
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)
        self.assertIn("Model-error tests", output)

    def test_light_group_minimums_warn_with_early(self):
        text = VALID_LIGHT.replace("Tools used: none", "Tools used: search")
        text = text.replace("Eval tasks: 12", "Eval tasks: 0")
        text = text.replace("No-tool tests: 2", "No-tool tests: 0")
        text = text.replace("Model-error tests: 1", "Model-error tests: 0")
        text = text.replace("Unsafe-request tests: 1", "Unsafe-request tests: 0")
        code, output = run_checker(text, "--early")
        self.assertEqual(code, 0, output)
        self.assertIn("WARN: Section 6: only 0 eval tasks", output)
        self.assertIn("WARN: Section 6: need at least 1 in 'No-tool tests'", output)
        self.assertIn("WARN: Section 6: need at least 1 in 'Tool-error tests'", output)
        self.assertIn("WARN: Section 6: 'Unsafe-request tests' is 0", output)

        text = VALID_LIGHT.replace("Eval tasks: 12", "Eval tasks: 0")
        text = text.replace("No-tool tests: 2", "No-tool tests: 0")
        text = text.replace("Model-error tests: 1", "Model-error tests: 0")
        text = text.replace("Unsafe-request tests: 1", "Unsafe-request tests: 0")
        code, output = run_checker(text, "--early")
        self.assertEqual(code, 0, output)
        self.assertIn(
            "WARN: Section 6: with an LLM and no tools, need at least 1 in 'Model-error tests'",
            output,
        )

    def test_skill_md_no_absolute_no_supervisor_wording(self):
        skill = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Do not recommend a supervisor for dependent steps, FAQ bots, or coding agents. "
            "Peer-to-peer is a last resort.",
            skill,
        )
        self.assertNotIn("No supervisor for dependent steps", skill)
        self.assertIn("Also fill the `Override` field.", skill)

    def test_skill_md_mentions_both_checkers(self):
        skill = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("check_workflow.py", skill)
        self.assertIn("check_evals.py", skill)
        self.assertIn("structure, not truth", skill)
        self.assertIn("--allow-open", skill)

    def test_no_provenance_text_in_template_fields(self):
        for name in ("WORKFLOW.md", "WORKFLOW-light.md", "WORKFLOW-light.example.md"):
            text = (REPO_ROOT / "templates" / name).read_text(encoding="utf-8")
            for line in text.splitlines():
                if not re.match(r"^\s*(?:[-*]\s+)?[A-Za-z][\w /()-]*\s*:", line):
                    continue
                value = re.sub(r"\bconfirmed step\b", "step", line, flags=re.I)
                self.assertNotRegex(
                    value,
                    r"\bconfirmed\b|\bdecided by user\b|\(user\)|\b\d{4}-\d{2}-\d{2}\b",
                    f"{name}: provenance text is not allowed in a field: {line}",
                )

    def test_check_workflow_runs_with_python_S(self):
        example = (REPO_ROOT / "templates" / "WORKFLOW-light.example.md").read_text(encoding="utf-8")
        code, output = run_checker(example, python_flags=("-S",))
        self.assertEqual(code, 0, output)


if __name__ == "__main__":
    unittest.main()
