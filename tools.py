"""Tool registry for the agent."""

from __future__ import annotations

import ast
import operator
import os
from typing import Dict

TOOLS: Dict[str, dict] = {}


def register(name: str, description: str):
    def decorator(fn):
        TOOLS[name] = {"fn": fn, "description": description}
        return fn

    return decorator


@register("web_search", "Search the web for up-to-date facts. Input: a query string.")
def web_search(query: str) -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return (
            f"[stub search result for '{query}'] "
            "No TAVILY_API_KEY set — plug in a real search API key to get live results."
        )

    from tavily import TavilyClient

    client = TavilyClient(api_key=api_key)
    results = client.search(query, max_results=5)
    return "\n".join(f"- {item['title']}: {item['content'][:200]}" for item in results["results"])


_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


@register("calculator", "Evaluate a numeric expression safely. Input: e.g. '12 * (3 + 4)'.")
def calculator(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval").body
        return str(_safe_eval(tree))
    except Exception as exc:
        return f"Error evaluating expression: {exc}"


@register("write_file", "Write text content to a local file. Input: 'path.md ||| content'.")
def write_file(payload: str) -> str:
    path, _, content = payload.partition("|||")
    path = path.strip()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content.strip())
    return f"Wrote {len(content)} chars to {path}"


def tool_descriptions() -> str:
    return "\n".join(f"- {name}: {entry['description']}" for name, entry in TOOLS.items())


def call_tool(name: str, arg: str) -> str:
    if name not in TOOLS:
        return f"Error: unknown tool '{name}'"
    return TOOLS[name]["fn"](arg)
