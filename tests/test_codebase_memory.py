import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codebase_memory.graph_store import CodeGraph

REPO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_repo")


def test_graph_has_expected_modules():
    cg = CodeGraph.from_repo(REPO_PATH)
    modules = {m.replace("module:", "") for m in cg.modules()}
    assert {"inventory", "orders", "pricing", "notifications", "main"} <= modules


def test_graph_resolves_cross_module_calls():
    cg = CodeGraph.from_repo(REPO_PATH)
    node = cg.find_function("create_order")
    callees = {c.replace("func:", "") for c in cg.callees_of(node)}
    assert "inventory.reserve_stock" in callees
    assert "pricing.calculate_total" in callees


def test_find_function_by_short_name():
    cg = CodeGraph.from_repo(REPO_PATH)
    assert cg.find_function("get_stock") == "func:inventory.get_stock"


def test_context_for_includes_callers_and_callees():
    cg = CodeGraph.from_repo(REPO_PATH)
    node = cg.find_function("reserve_stock")
    ctx = cg.context_for(node)
    assert "orders.create_order" in ctx["callers"]
    assert "inventory.get_stock" in ctx["callees"]
