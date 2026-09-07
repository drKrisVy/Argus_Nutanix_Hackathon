import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codebase_memory.graph_store import CodeGraph
from agents import performance_agent

REPO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_repo")


def test_flags_nested_loop_as_risky():
    cg = CodeGraph.from_repo(REPO_PATH)
    node = cg.find_function("has_duplicate_items")
    result = performance_agent.assess(cg, node, use_llm=False)
    assert result["risk"] in ("medium", "high")
    assert result["features"]["max_loop_nesting_depth"] == 2


def test_simple_function_is_low_risk():
    cg = CodeGraph.from_repo(REPO_PATH)
    node = cg.find_function("get_stock")
    result = performance_agent.assess(cg, node, use_llm=False)
    assert result["risk"] == "low"
    assert result["reasons"] == []


def test_extract_features_counts_complexity():
    source = "def f(x):\n    if x:\n        return 1\n    else:\n        return 2\n"
    features = performance_agent.extract_features(source)
    assert features["cyclomatic_complexity"] == 2
