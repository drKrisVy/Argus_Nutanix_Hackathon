"""Explainer Agent: answers plain-English questions about the codebase by
pulling the relevant subgraph from Live Codebase Memory. This is the
onboarding/comprehension piece -- not a code generator.
"""

import re

from llm.client import chat

EXPLAIN_SYSTEM_PROMPT = (
    "You explain how a codebase works to an engineer using ONLY the structural "
    "facts given to you (functions, callers, callees, source). If the facts "
    "don't answer the question, say what's missing instead of guessing."
)


def _mentioned_functions(question, code_graph):
    found = []
    for func_node in code_graph.functions():
        name = func_node.replace("func:", "").split(".")[-1]
        if re.search(rf"\b{re.escape(name)}\b", question):
            found.append(func_node)
    return found


def answer(question, code_graph):
    mentioned = _mentioned_functions(question, code_graph)
    if not mentioned:
        # Fall back to a repo-wide summary so the agent still says something useful.
        summary = code_graph.summary()
        context = f"No specific function was named. Repo summary: {summary}."
    else:
        blocks = []
        for func_node in mentioned:
            ctx = code_graph.context_for(func_node)
            blocks.append(
                f"- {ctx['qualname']}(args={ctx['args']}): callers={ctx['callers']}, "
                f"callees={ctx['callees']}\n  source:\n{ctx['source']}"
            )
        context = "\n\n".join(blocks)

    prompt = f"Codebase facts:\n{context}\n\nQuestion: {question}"
    return {
        "question": question,
        "grounded_on": [m.replace("func:", "") for m in mentioned],
        "answer": chat(prompt, system=EXPLAIN_SYSTEM_PROMPT, max_tokens=350),
    }
