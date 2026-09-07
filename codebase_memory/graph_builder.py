"""Builds the code graph (networkx.DiGraph) from parsed modules/functions."""

import json
import networkx as nx

from codebase_memory.parser import parse_repo


def build_graph(repo_path):
    modules, functions = parse_repo(repo_path)
    g = nx.DiGraph()

    for mod_name, mod in modules.items():
        g.add_node(f"module:{mod_name}", kind="module", path=mod.path)

    for mod_name, mod in modules.items():
        for imported in mod.imports:
            target = f"module:{imported}"
            if target in g:
                g.add_edge(f"module:{mod_name}", target, kind="imports")

    for qualname, fn in functions.items():
        g.add_node(
            f"func:{qualname}",
            kind="function",
            module=fn.module,
            name=fn.name,
            lineno=fn.lineno,
            end_lineno=fn.end_lineno,
            args=fn.args,
            docstring=fn.docstring,
            source=fn.source,
        )
        g.add_edge(f"module:{fn.module}", f"func:{qualname}", kind="defines")

    # Resolve calls: match a called short name against known function
    # short names in this repo (good enough for a single small demo repo;
    # a real implementation would use import-aware scoping).
    by_short_name = {}
    for qualname in functions:
        short = qualname.rsplit(".", 1)[-1]
        by_short_name.setdefault(short, []).append(qualname)

    for qualname, fn in functions.items():
        for called in fn.calls:
            targets = by_short_name.get(called, [])
            for target in targets:
                if target != qualname:
                    g.add_edge(f"func:{qualname}", f"func:{target}", kind="calls")

    return g


def save_graph(g, path):
    data = nx.node_link_data(g, edges="edges")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_graph(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return nx.node_link_graph(data, directed=True, edges="edges")
