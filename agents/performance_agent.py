"""Performance Agent: static-heuristic risk scoring for a function, no
benchmark execution required.

Grounded in: Akhauri & Song, "Performance Prediction for Large Systems via
Text-to-Text Regression" (arXiv:2506.21718, Google DeepMind 2025) -- their
Regression Language Models predict a numeric performance outcome directly
from a text description of a system, with no hand-engineered features and
no full execution. This demo agent is the honest v1 of that idea: a
static-feature heuristic scorer, since training a real regression model
needs historical CI benchmark data this hackathon repo doesn't have yet.
The roadmap note in the README says so explicitly.
"""

import ast

from llm.client import chat, LLMError


class _ComplexityVisitor(ast.NodeVisitor):
    """Approximates cyclomatic complexity: +1 per branch/loop/boolean op."""

    def __init__(self):
        self.decision_points = 0
        self.max_loop_depth = 0
        self._current_loop_depth = 0

    def _enter_loop(self):
        self._current_loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self._current_loop_depth)

    def _exit_loop(self):
        self._current_loop_depth -= 1

    def visit_For(self, node):
        self.decision_points += 1
        self._enter_loop()
        self.generic_visit(node)
        self._exit_loop()

    def visit_While(self, node):
        self.decision_points += 1
        self._enter_loop()
        self.generic_visit(node)
        self._exit_loop()

    def visit_If(self, node):
        self.decision_points += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.decision_points += len(node.values) - 1
        self.generic_visit(node)


def extract_features(source_code, fan_out=0):
    tree = ast.parse(source_code)
    visitor = _ComplexityVisitor()
    visitor.visit(tree)
    return {
        "cyclomatic_complexity": 1 + visitor.decision_points,
        "max_loop_nesting_depth": visitor.max_loop_depth,
        "fan_out": fan_out,
        "lines_of_code": len(source_code.splitlines()),
    }


def score_risk(features):
    reasons = []
    score = 0

    if features["max_loop_nesting_depth"] >= 2:
        score += 2
        reasons.append(
            f"nested loops {features['max_loop_nesting_depth']} deep -- likely "
            f"O(n^{features['max_loop_nesting_depth']}) or worse over its input"
        )
    if features["cyclomatic_complexity"] >= 8:
        score += 1
        reasons.append(f"high cyclomatic complexity ({features['cyclomatic_complexity']})")
    if features["fan_out"] >= 5:
        score += 1
        reasons.append(f"high fan-out ({features['fan_out']} callees) -- broad blast radius if slow")

    label = "high" if score >= 3 else "medium" if score >= 1 else "low"
    return label, reasons


def explain_risk(qualname, label, reasons, use_llm=True):
    if not reasons:
        return "No static performance concerns detected."
    if use_llm:
        try:
            prompt = (
                f"Function {qualname} was flagged as '{label}' performance risk for these "
                f"reasons: {'; '.join(reasons)}. Write one plain-English sentence explaining "
                f"the likely real-world impact to a reviewer, without repeating the reasons verbatim."
            )
            return chat(prompt, max_tokens=80).strip()
        except LLMError:
            pass
    return "; ".join(reasons)


def assess(code_graph, func_node, use_llm=True):
    ctx = code_graph.context_for(func_node)
    features = extract_features(ctx["source"], fan_out=len(ctx["callees"]))
    label, reasons = score_risk(features)
    explanation = explain_risk(ctx["qualname"], label, reasons, use_llm=use_llm)
    return {
        "function": ctx["qualname"],
        "risk": label,
        "features": features,
        "reasons": reasons,
        "explanation": explanation,
    }
