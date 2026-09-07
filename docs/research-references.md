# Research References

Six papers, one per major design decision in Argus, plus a note on the
one deliberate engineering substitution (tree-sitter -> `ast`).

## 1. Live Codebase Memory (shared graph substrate)

**Codebase-Memory: Tree-Sitter-Based Knowledge Graphs for LLM Code
Exploration via MCP** -- Martin Vogel, Falk Meyer-Eschenbach, Severin
Kohler, Elias Grunewald, Felix Balzer (2026). arXiv:2603.27277
https://arxiv.org/abs/2603.27277

Builds a persistent knowledge graph of a codebase using tree-sitter (66
languages) plus call-graph traversal, impact analysis, and community
discovery, exposed via the Model Context Protocol (MCP). Across 31
real-world repos: 90% fewer tokens and 2.1x fewer tool calls than
file-exploration agents, at 83% vs. 92% answer quality.

**What Argus actually does differently, and why:** `codebase_memory/`
uses Python's standard-library `ast` module instead of tree-sitter. The
underlying idea is identical -- parse once, build a persistent graph
(here: a `networkx.DiGraph` of modules, functions, calls, and imports),
and let every agent query that graph instead of re-reading/re-grepping
files. The substitution is a pragmatic one for a Python-only demo: `ast`
ships with Python, needs no native bindings or per-language grammar
packages, and was verified working end-to-end in `tests/`. Tree-sitter is
the correct choice the moment this needs to support more than one
language, since `ast` is Python-specific -- that's the noted upgrade path.

## 2. Architect Agent (structural + LLM-described diagrams)

**Collaborative LLM Agents for C4 Software Architecture Design
Automation** -- Kamil Szczepanik, Jaroslaw A. Chudziak. arXiv:2510.22787,
accepted at HICSS-59 (2026). https://arxiv.org/abs/2510.22787

Multiple role-specialized LLM agents collaborate to produce C4 model
views (Context / Container / Component) automatically, evaluated with
structural rules plus an LLM-as-judge across five systems and four LLMs.

**What Argus does:** `agents/architect_agent.py` builds the diagram's
*structure* deterministically straight from the code graph (which
functions call which modules) -- this is more reliable than asking an LLM
to invent structure it might get wrong -- and uses the LLM only for what
it's actually good at: writing a one-line, plain-English description of
each module's responsibility.

## 3. Reviewer Agent (structural context instead of retrieval)

**Context-Aware Code Review Automation: A Retrieval-Augmented
Approach** -- Busra Icoz, Goksel Biricik. Applied Sciences 16(4), 2026.
https://www.mdpi.com/2076-3417/16/4/1875

Retrieves the top-k most similar historical review comments (via a vector
DB), classifies the diff into a category, and routes it to a specialized
review strategy. Reported +13.2% improvement over zero-shot baselines.

**What Argus does differently, and why:** `agents/reviewer_agent.py`
skips the vector DB -- a brand-new demo repo has no review history to
retrieve from -- and substitutes the code graph's structural context
(the function's real callers and callees) as the grounding signal
instead. Wiring in real historical-review retrieval once a team has PR
history is the natural upgrade path.

## 4. Test Agent (generate -> run -> repair)

**TestPilot: An Empirical Evaluation of Using Large Language Models for
Automated Unit Test Generation** -- Max Schafer, Sarah Nadi, Aryaz
Eghbali, Frank Tip (2023). arXiv:2302.06527.
https://arxiv.org/abs/2302.06527

Generates tests from function signature + implementation + usage
examples, with error-aware re-prompting to repair failing tests. Achieved
70.2% median statement coverage / 52.8% branch coverage on 1,684
real-world JS functions.

**What Argus does:** `agents/test_agent.py` implements the same
generate -> run -> repair shape against real `pytest` execution (not
simulated), and the loop is additionally expressed as an actual LangGraph
cycle in `orchestrator/graph.py` (`test_generate` <-> `test_run`), rather
than only as a plain Python `while` loop.

## 5. Performance Agent (static heuristic today, learned model tomorrow)

**Performance Prediction for Large Systems via Text-to-Text Regression**
("Regression Language Models") -- Yash Akhauri, Xingyou Song, Google
Research / Google DeepMind (2025). arXiv:2506.21718.
https://arxiv.org/abs/2506.21718

Shows a model can read a *text description* of a system/configuration and
directly output a numeric performance metric (they predict MIPS per
compute unit on Google's Borg infrastructure) -- no hand-engineered
features, no full execution required.

**What Argus does, honestly:** `agents/performance_agent.py` is a static
heuristic -- cyclomatic complexity, loop-nesting depth, fan-out, computed
via `ast` -- because training a real regression model needs historical CI
benchmark data this demo repo doesn't have. It correctly flags the
intentionally-seeded O(n^2) duplicate check in `data/sample_repo/orders.py`
as medium risk (verified in `tests/test_performance_agent.py`). The
roadmap -- explicitly not built here -- is training a text-to-text
regression model on real CI history, per this paper.

## 6. The overall shape: multi-agent SE assistants + LangGraph

**LLM-Based Multi-Agent Systems for Software Engineering: Literature
Review, Vision and the Road Ahead** -- Junda He, Christoph Treude, David
Lo, Singapore Management University (2024). arXiv:2404.04834.
https://arxiv.org/abs/2404.04834

Systematic review of 71 studies on LLM multi-agent systems across the
SDLC, cataloguing agent roles and finding these systems do well on
moderately complex tasks but struggle on deep logical reasoning.

**What Argus does:** narrow, single-purpose agents (Architect / Reviewer
/ Test / Performance / Explainer), each grounded in the same code graph,
coordinated by a thin orchestrator -- concretely implemented as a
**LangGraph** `StateGraph` (`orchestrator/graph.py`): one node per agent,
a shared `AgentState`, a conditional edge for routing by intent, and a
cyclic edge for the Test Agent's repair loop. LangGraph is an engineering
tooling choice, not a research paper, but it's the direct implementation
of the coordination layer this review argues the class of system needs.
