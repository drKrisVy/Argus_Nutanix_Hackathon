"""AST-based parser for the code graph.

Note on tree-sitter vs. ast: the research this project is grounded in
(Vogel et al., "Codebase-Memory", arXiv:2603.27277) uses tree-sitter so
the same approach works across ~66 languages. For this Python-only demo
we use the standard-library `ast` module instead: zero extra native
dependencies, guaranteed to run anywhere Python runs, and it gives us the
same information we need (functions, classes, calls, imports). Swapping
in tree-sitter adapters per language is the natural upgrade path if this
were extended beyond Python -- see docs/research-references.md.
"""

import ast
import os
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    qualname: str          # "module.func" or "module.Class.method"
    module: str
    name: str
    lineno: int
    end_lineno: int
    args: list
    docstring: str
    calls: list = field(default_factory=list)   # names called, unresolved
    source: str = ""


@dataclass
class ModuleInfo:
    name: str
    path: str
    imports: list = field(default_factory=list)   # imported module names
    functions: list = field(default_factory=list) # FunctionInfo.qualname
    classes: list = field(default_factory=list)


class _CallCollector(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        name = self._call_name(node.func)
        if name:
            self.calls.append(name)
        self.generic_visit(node)

    @staticmethod
    def _call_name(node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None


def _get_source_segment(source_lines, node):
    try:
        return "\n".join(source_lines[node.lineno - 1:node.end_lineno])
    except Exception:
        return ""


def parse_module(path, module_name):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    source_lines = source.splitlines()
    tree = ast.parse(source, filename=path)

    mod = ModuleInfo(name=module_name, path=path)
    functions = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod.imports.append(alias.name)
            else:
                if node.module:
                    mod.imports.append(node.module)

    def visit_functions(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                mod.classes.append(f"{module_name}.{child.name}")
                visit_functions(child, prefix=f"{child.name}.")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualname = f"{module_name}.{prefix}{child.name}"
                collector = _CallCollector()
                collector.visit(child)
                fn = FunctionInfo(
                    qualname=qualname,
                    module=module_name,
                    name=child.name,
                    lineno=child.lineno,
                    end_lineno=getattr(child, "end_lineno", child.lineno),
                    args=[a.arg for a in child.args.args],
                    docstring=ast.get_docstring(child) or "",
                    calls=collector.calls,
                    source=_get_source_segment(source_lines, child),
                )
                functions[qualname] = fn
                mod.functions.append(qualname)
                visit_functions(child, prefix=prefix)

    visit_functions(tree)
    return mod, functions


def parse_repo(repo_path):
    """Parse every .py file directly under repo_path (non-recursive is
    fine for the demo repo; this walks recursively for real use)."""
    modules = {}
    functions = {}
    for root, _dirs, files in os.walk(repo_path):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            module_name = os.path.splitext(fname)[0]
            path = os.path.join(root, fname)
            mod, fns = parse_module(path, module_name)
            modules[module_name] = mod
            functions.update(fns)
    return modules, functions
