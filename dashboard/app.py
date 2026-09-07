"""Argus dashboard: one Streamlit screen showing all five agents against
the demo repo. Run with:  streamlit run dashboard/app.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

REPO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_repo")
sys.path.insert(0, REPO_PATH)

from codebase_memory.graph_store import CodeGraph
from agents import architect_agent, reviewer_agent, performance_agent, explainer_agent, test_agent

st.set_page_config(page_title="Argus", layout="wide")
st.title("Argus -- Living Engineering Co-Pilot")
st.caption("Demo target: data/sample_repo (a tiny order-processing service)")

if not os.environ.get("GROQ_API_KEY"):
    st.warning(
        "GROQ_API_KEY is not set. Copy .env.example to .env and add your key -- "
        "the Reviewer, Explainer, and Test agents need it. The Performance "
        "Agent's static scoring and the Architect Agent's diagram structure "
        "work without it."
    )


@st.cache_resource
def load_graph():
    return CodeGraph.from_repo(REPO_PATH)


code_graph = load_graph()
function_names = sorted(f.replace("func:", "") for f in code_graph.functions())

with st.sidebar:
    st.subheader("Live Codebase Memory")
    st.json(code_graph.summary())
    if st.button("Rebuild graph"):
        load_graph.clear()
        st.rerun()

tab_arch, tab_review, tab_test, tab_perf, tab_ask = st.tabs(
    ["Architecture", "Review", "Tests", "Performance", "Ask Argus"]
)

with tab_arch:
    st.subheader("Architect Agent")
    use_llm = st.checkbox("Use LLM for module descriptions", value=True, key="arch_llm")
    if st.button("Generate diagram"):
        with st.spinner("Building diagram..."):
            result = architect_agent.generate_c4_diagram(code_graph, use_llm=use_llm)
        st.code(result["mermaid"], language="text")
        st.caption("Paste this into https://mermaid.live to render it, or a Markdown file on GitHub.")
        st.write("**Module descriptions:**")
        for mod, desc in result["descriptions"].items():
            st.markdown(f"- `{mod}`: {desc}")

with tab_review:
    st.subheader("Reviewer Agent")
    target = st.selectbox("Function to review", function_names, key="review_target")
    if st.button("Review"):
        with st.spinner("Reviewing..."):
            node = code_graph.find_function(target)
            result = reviewer_agent.review_function(code_graph, node)
        st.write(result["review"])
        st.caption(f"Context used -- callers: {result['context_used']['callers']}, "
                   f"callees: {result['context_used']['callees']}")

with tab_test:
    st.subheader("Test Agent")
    target_t = st.selectbox("Function to generate tests for", function_names, key="test_target")
    retries = st.slider("Max repair retries", 0, 3, 2)
    if st.button("Generate & run tests"):
        with st.spinner("Generating and running tests..."):
            node = code_graph.find_function(target_t)
            result = test_agent.generate_and_repair(code_graph, node, REPO_PATH, max_retries=retries)
        st.write(f"**Passed:** {result['passed']} (attempts used: {result['attempts_used']})")
        st.code(result["final_test_code"], language="python")
        with st.expander("pytest output"):
            st.text(result["final_output"])

with tab_perf:
    st.subheader("Performance Agent")
    target_p = st.selectbox("Function to score", function_names, key="perf_target")
    use_llm_p = st.checkbox("Use LLM for the explanation sentence", value=True, key="perf_llm")
    if st.button("Assess risk"):
        node = code_graph.find_function(target_p)
        result = performance_agent.assess(code_graph, node, use_llm=use_llm_p)
        badge = {"low": "green", "medium": "orange", "high": "red"}[result["risk"]]
        st.markdown(f"**Risk:** :{badge}[{result['risk'].upper()}]")
        st.write(result["explanation"])
        st.json(result["features"])

with tab_ask:
    st.subheader("Explainer Agent")
    question = st.text_input("Ask a question about the codebase", "what does create_order do?")
    if st.button("Ask"):
        with st.spinner("Thinking..."):
            result = explainer_agent.answer(question, code_graph)
        st.write(result["answer"])
        st.caption(f"Grounded on: {result['grounded_on'] or '(repo-wide summary, no specific function matched)'}")
