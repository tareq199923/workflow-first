import tempfile
import unittest

from helpers import VALID_FULL, VALID_LIGHT, run_checker


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
