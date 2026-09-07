"""Query layer over the code graph so agents don't touch networkx directly."""


class CodeGraph:
    def __init__(self, g):
        self.g = g

    @classmethod
    def from_repo(cls, repo_path):
        from codebase_memory.graph_builder import build_graph
        return cls(build_graph(repo_path))

    def functions(self):
        return [n for n, d in self.g.nodes(data=True) if d.get("kind") == "function"]

    def modules(self):
        return [n for n, d in self.g.nodes(data=True) if d.get("kind") == "module"]

    def node(self, node_id):
        return dict(self.g.nodes[node_id]) if node_id in self.g else None

    def find_function(self, name):
        """Find a function node by short name or qualified name."""
        if f"func:{name}" in self.g:
            return f"func:{name}"
        matches = [n for n in self.functions() if n.endswith(f".{name}") or n == f"func:{name}"]
        return matches[0] if matches else None

    def callers_of(self, func_node):
        return [u for u, v, d in self.g.in_edges(func_node, data=True) if d.get("kind") == "calls"]

    def callees_of(self, func_node):
        return [v for u, v, d in self.g.out_edges(func_node, data=True) if d.get("kind") == "calls"]

    def module_of(self, func_node):
        data = self.node(func_node)
        return f"module:{data['module']}" if data else None

    def functions_in_module(self, module_node):
        return [v for u, v, d in self.g.out_edges(module_node, data=True) if d.get("kind") == "defines"]

    def imports_of(self, module_node):
        return [v for u, v, d in self.g.out_edges(module_node, data=True) if d.get("kind") == "imports"]

    def context_for(self, func_node):
        """Everything an agent typically needs about one function."""
        data = self.node(func_node) or {}
        return {
            "qualname": func_node.replace("func:", ""),
            "source": data.get("source", ""),
            "docstring": data.get("docstring", ""),
            "args": data.get("args", []),
            "callers": [c.replace("func:", "") for c in self.callers_of(func_node)],
            "callees": [c.replace("func:", "") for c in self.callees_of(func_node)],
        }

    def summary(self):
        return {
            "modules": len(self.modules()),
            "functions": len(self.functions()),
            "calls": len([1 for _, _, d in self.g.edges(data=True) if d.get("kind") == "calls"]),
            "imports": len([1 for _, _, d in self.g.edges(data=True) if d.get("kind") == "imports"]),
        }
