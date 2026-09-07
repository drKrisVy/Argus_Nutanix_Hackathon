"""Reviewer Agent: reviews a function using its real callers/callees as
context, not just the diff text in isolation.

Grounded in: Icoz & Biricik, "Context-Aware Code Review Automation: A
Retrieval-Augmented Approach" (Applied Sciences 16(4), 2026). That paper
retrieves similar past review comments via a vector DB and routes by diff
category. This demo skips the vector DB (no review history exists yet for
a brand-new repo) and substitutes the code graph's structural context --
callers, callees, module -- as the retrieval signal instead. Swapping in
real historical-review retrieval is the natural upgrade path.
"""

from llm.client import chat

REVIEW_SYSTEM_PROMPT = (
    "You are a precise, senior code reviewer. Review the given function using "
    "the provided context about its callers and callees. Point out concrete "
    "bugs, edge cases, and risks. Be specific and reference line-level details "
    "from the source. Do not restate the code back verbatim. Keep it under 200 words."
)


def review_function(code_graph, func_node):
    ctx = code_graph.context_for(func_node)

    prompt = (
        f"Function: {ctx['qualname']}\n"
        f"Arguments: {ctx['args']}\n"
        f"Docstring: {ctx['docstring'] or '(none)'}\n\n"
        f"Source:\n{ctx['source']}\n\n"
        f"Called by: {ctx['callers'] or '(nothing in this repo)'}\n"
        f"Calls: {ctx['callees'] or '(nothing tracked)'}\n\n"
        "Review this function."
    )
    review_text = chat(prompt, system=REVIEW_SYSTEM_PROMPT, max_tokens=400)
    return {
        "function": ctx["qualname"],
        "review": review_text,
        "context_used": {"callers": ctx["callers"], "callees": ctx["callees"]},
    }
