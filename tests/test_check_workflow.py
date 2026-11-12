import tempfile
import unittest

from helpers import VALID_FULL, VALID_LIGHT, run_checker


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

    @unittest.expectedFailure
    def test_bare_na_agent_steps_fails(self):
        """P7: a bare n/a on Agent steps inside workflow should fail."""
        text = VALID_FULL.replace(
            "Agent steps inside workflow: n/a: no agent steps",
            "Agent steps inside workflow: n/a",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    @unittest.expectedFailure
    def test_light_no_tools_allows_zero_no_tool_tests(self):
        """P4: a design with no tools should not need No-tool tests."""
        text = VALID_LIGHT.replace("No-tool tests: 2", "No-tool tests: 0")
        text = text.replace(
            "## 2. Position on the spectrum",
            "## 2. Position on the spectrum\nTools used: none",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 0, output)

    @unittest.expectedFailure
    def test_ticked_guardrail_with_not_run_text_fails(self):
        """P11: a ticked guardrail whose text says it was not run should fail."""
        text = VALID_FULL.replace(
            "- [x] 1. Stop condition on every loop; background processes can be killed",
            "- [x] 1. robot test has not been run",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)

    @unittest.expectedFailure
    def test_guardrail_numbers_must_be_exact(self):
        """P11: guardrails numbered 1-19 plus 21 should fail."""
        text = VALID_FULL.replace(
            "- [n/a: one call per email] 20. Interrupted task resumes from a checkpoint without repeating unsafe actions",
            "- [n/a: one call per email] 21. Interrupted task resumes from a checkpoint without repeating unsafe actions",
        )
        code, output = run_checker(text)
        self.assertEqual(code, 1, output)


if __name__ == "__main__":
    unittest.main()
