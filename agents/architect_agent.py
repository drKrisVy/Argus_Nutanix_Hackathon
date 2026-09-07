"""Architect Agent: generates a C4-style Mermaid diagram from the code graph.

Grounded in: Szczepanik & Chudziak, "Collaborative LLM Agents for C4
Software Architecture Design Automation" (arXiv:2510.22787, HICSS-59 2026).
That paper uses multiple role-specialized LLM agents to produce Context /
Container / Component views. This demo version builds the diagram's
*structure* deterministically from the graph (which is more reliable than
asking an LLM to invent structure it might get wrong) and uses the LLM
only to phrase short, plain-English descriptions of each module -- the
part an LLM is genuinely good at.
"""

from llm.client import chat, LLMError


def _mermaid_id(module_name):
    return module_name.replace(".", "_").replace("-", "_")


def build_container_diagram(code_graph):
    """Deterministic C4 Container-level view: one box per module, edges
    for cross-module calls."""
    lines = ["flowchart TB"]
    for module_node in code_graph.modules():
        mod_name = module_node.replace("module:", "")
        lines.append(f'    {_mermaid_id(mod_name)}["{mod_name}"]')

    seen_edges = set()
    for func_node in code_graph.functions():
        src_module = code_graph.node(func_node)["module"]
        for callee in code_graph.callees_of(func_node):
            dst_module = code_graph.node(callee)["module"]
            if dst_module != src_module:
                edge = (src_module, dst_module)
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    lines.append(f"    {_mermaid_id(src_module)} --> {_mermaid_id(dst_module)}")
    return "\n".join(lines)


def describe_modules(code_graph, use_llm=True):
    """One-line, plain-English description per module. Falls back to a
    structural description (function list) if no LLM key is configured."""
    descriptions = {}
    for module_node in code_graph.modules():
        mod_name = module_node.replace("module:", "")
        functions = [f.replace("func:", "").split(".")[-1] for f in code_graph.functions_in_module(module_node)]

        if use_llm:
            try:
                prompt = (
                    f"A Python module named '{mod_name}' defines these functions: "
                    f"{', '.join(functions)}. In one short sentence, describe this "
                    f"module's responsibility for a software architecture diagram."
                )
                descriptions[mod_name] = chat(prompt, max_tokens=60).strip()
                continue
            except LLMError:
                pass
        descriptions[mod_name] = f"Defines: {', '.join(functions)}"
    return descriptions


def generate_c4_diagram(code_graph, use_llm=True):
    diagram = build_container_diagram(code_graph)
    descriptions = describe_modules(code_graph, use_llm=use_llm)
    return {"mermaid": diagram, "descriptions": descriptions}
