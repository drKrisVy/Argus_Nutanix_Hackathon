"""The Orchestrator: a LangGraph StateGraph.

Nodes: classify -> one of {architect, reviewer, performance, explainer,
test_generate <-> test_run}. Routing out of `classify` is a conditional
edge. The Test Agent's generate -> run -> repair loop is implemented here
as an actual cycle (test_generate -> test_run -> back to test_generate),
rather than a hand-rolled while loop, per the design in the README.

code_graph and repo_path are captured via closures rather than stored in
AgentState, since AgentState is meant to stay small and (eventually)
checkpointer-friendly.
"""

from langgraph.graph import StateGraph, START, END

from orchestrator.state import AgentState
from agents import architect_agent, reviewer_agent, performance_agent, explainer_agent, test_agent

MAX_TEST_RETRIES = 2


def _classify(state: AgentState) -> AgentState:
    text = state["request"].lower()
    if any(w in text for w in ("diagram", "architecture", "c4", "structure")):
        intent = "architect"
    elif any(w in text for w in ("review", "look at this diff", "check this change")):
        intent = "reviewer"
    elif any(w in text for w in ("test", "coverage", "unit test")):
        intent = "test"
    elif any(w in text for w in ("performance", "slow", "regression", "risk", "complexity")):
        intent = "performance"
    else:
        intent = "explainer"
    return {"intent": intent}


def _route(state: AgentState) -> str:
    return state["intent"]


def build_graph(code_graph, repo_path):
    def architect_node(state: AgentState) -> AgentState:
        result = architect_agent.generate_c4_diagram(code_graph)
        return {"output": {**state.get("output", {}), "architect": result}}

    def reviewer_node(state: AgentState) -> AgentState:
        func_node = code_graph.find_function(state["target_function"])
        result = reviewer_agent.review_function(code_graph, func_node)
        return {"output": {**state.get("output", {}), "reviewer": result}}

    def performance_node(state: AgentState) -> AgentState:
        func_node = code_graph.find_function(state["target_function"])
        result = performance_agent.assess(code_graph, func_node)
        return {"output": {**state.get("output", {}), "performance": result}}

    def explainer_node(state: AgentState) -> AgentState:
        result = explainer_agent.answer(state["request"], code_graph)
        return {"output": {**state.get("output", {}), "explainer": result}}

    def test_generate_node(state: AgentState) -> AgentState:
        func_node = code_graph.find_function(state["target_function"])
        prior = state.get("output", {}).get("test", {})
        error_feedback = prior.get("output") if prior and not prior.get("passed") else None
        test_code = test_agent.generate_tests(code_graph, func_node, error_feedback=error_feedback)
        current = state.get("output", {})
        current["test"] = {"test_code": test_code}
        return {"output": current}

    def test_run_node(state: AgentState) -> AgentState:
        test_code = state["output"]["test"]["test_code"]
        result = test_agent.run_tests(test_code, repo_path)
        current = state["output"]
        current["test"] = {**current["test"], "passed": result["passed"], "output": result["output"]}
        return {"output": current, "retry_count": state.get("retry_count", 0) + 1}

    def _test_retry_router(state: AgentState) -> str:
        passed = state["output"]["test"]["passed"]
        if passed or state.get("retry_count", 0) > MAX_TEST_RETRIES:
            return "done"
        return "retry"

    graph = StateGraph(AgentState)
    graph.add_node("classify", _classify)
    graph.add_node("architect", architect_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("performance", performance_node)
    graph.add_node("explainer", explainer_node)
    graph.add_node("test_generate", test_generate_node)
    graph.add_node("test_run", test_run_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        _route,
        {
            "architect": "architect",
            "reviewer": "reviewer",
            "performance": "performance",
            "explainer": "explainer",
            "test": "test_generate",
        },
    )
    graph.add_edge("architect", END)
    graph.add_edge("reviewer", END)
    graph.add_edge("performance", END)
    graph.add_edge("explainer", END)
    graph.add_edge("test_generate", "test_run")
    graph.add_conditional_edges(
        "test_run",
        _test_retry_router,
        {"retry": "test_generate", "done": END},
    )

    return graph.compile()


def run(code_graph, repo_path, request, target_function=None):
    app = build_graph(code_graph, repo_path)
    initial_state: AgentState = {
        "request": request,
        "target_function": target_function,
        "repo_path": repo_path,
        "retry_count": 0,
        "output": {},
    }
    return app.invoke(initial_state)
