"""Test Agent: generates unit tests for a function using its real callers
as context, runs them, and repairs failures in a feedback loop.

Grounded in: Schaefer, Nadi, Eghbali & Tip, "An Empirical Evaluation of
Using Large Language Models for Automated Unit Test Generation" (TestPilot,
arXiv:2302.06527) -- generate from signature + implementation + usage
examples, then use error-aware re-prompting to repair failures. This is
the same generate -> run -> repair shape, implemented here as a plain
Python loop (also expressible as a LangGraph cycle -- see
orchestrator/graph.py).
"""

import os
import re
import subprocess
import sys
import tempfile

from llm.client import chat

TEST_GEN_SYSTEM_PROMPT = (
    "You write pytest unit tests. Output ONLY a single Python code block "
    "containing valid pytest test functions -- no prose before or after. "
    "Import the function under test with a plain `from <module> import <name>` "
    "statement. Cover at least one normal case and one edge case."
)


def _extract_code_block(text):
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def generate_tests(code_graph, func_node, error_feedback=None):
    ctx = code_graph.context_for(func_node)
    module = ctx["qualname"].rsplit(".", 1)[0]
    func_name = ctx["qualname"].rsplit(".", 1)[-1]

    prompt = (
        f"Module: {module}\n"
        f"Function under test: {func_name}\n"
        f"Source:\n{ctx['source']}\n\n"
        f"Called by (for realistic usage patterns): {ctx['callers'] or '(none)'}\n"
    )
    if error_feedback:
        prompt += f"\nThe previous test attempt failed with this error, fix it:\n{error_feedback}\n"

    response = chat(prompt, system=TEST_GEN_SYSTEM_PROMPT, max_tokens=600)
    return _extract_code_block(response)


def run_tests(test_code, repo_path):
    """Writes test_code to a temp file inside repo_path (so relative
    imports resolve) and runs pytest against just that file."""
    fd, test_path = tempfile.mkstemp(suffix="_argus_test.py", dir=repo_path)
    os.close(fd)
    try:
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "-q"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        passed = result.returncode == 0
        return {"passed": passed, "output": (result.stdout + result.stderr)[-3000:]}
    finally:
        if os.path.exists(test_path):
            os.remove(test_path)


def generate_and_repair(code_graph, func_node, repo_path, max_retries=2):
    error_feedback = None
    attempts = []

    for attempt in range(max_retries + 1):
        test_code = generate_tests(code_graph, func_node, error_feedback=error_feedback)
        result = run_tests(test_code, repo_path)
        attempts.append({"attempt": attempt + 1, "test_code": test_code, "result": result})

        if result["passed"]:
            break
        error_feedback = result["output"]

    final = attempts[-1]
    return {
        "function": func_node.replace("func:", ""),
        "passed": final["result"]["passed"],
        "attempts_used": len(attempts),
        "final_test_code": final["test_code"],
        "final_output": final["result"]["output"],
        "history": attempts,
    }
