import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_repo"))

from codebase_memory.graph_store import CodeGraph
from orchestrator.graph import run
from agents import architect_agent, reviewer_agent, performance_agent, explainer_agent, test_agent

REPO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_repo")


def _patch_all_agents(monkeypatch, fake_chat):
    for module in (architect_agent, reviewer_agent, performance_agent, explainer_agent, test_agent):
        monkeypatch.setattr(module, "chat", fake_chat)


def test_architect_intent_routes_correctly(monkeypatch):
    _patch_all_agents(monkeypatch, lambda *a, **k: "a description")
    cg = CodeGraph.from_repo(REPO_PATH)
    result = run(cg, REPO_PATH, "show me the architecture diagram")
    assert "architect" in result["output"]
    assert "flowchart" in result["output"]["architect"]["mermaid"]


def test_performance_intent_routes_correctly(monkeypatch):
    _patch_all_agents(monkeypatch, lambda *a, **k: "explanation")
    cg = CodeGraph.from_repo(REPO_PATH)
    result = run(cg, REPO_PATH, "check performance risk", target_function="has_duplicate_items")
    assert result["output"]["performance"]["risk"] in ("medium", "high")


def test_test_agent_cycle_retries_on_failure_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake_chat(prompt, system=None, **kwargs):
        calls["n"] += 1
        if "failed with this error" in prompt:
            return (
                "```python\nfrom orders import has_duplicate_items\n\n"
                "def test_ok():\n    assert has_duplicate_items([('a', 1)]) is False\n```"
            )
        return "```python\nimport this_module_does_not_exist\n```"

    _patch_all_agents(monkeypatch, fake_chat)
    cg = CodeGraph.from_repo(REPO_PATH)
    result = run(cg, REPO_PATH, "generate tests", target_function="has_duplicate_items")

    assert result["output"]["test"]["passed"] is True
    assert result["retry_count"] >= 2
