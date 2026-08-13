"""Planning utilities for the agent."""

from __future__ import annotations

from typing import List

from llm import LLM

PLAN_SYSTEM_PROMPT = """You are a research planning assistant. Given a research goal,
break it into 3-6 concrete, ordered sub-tasks that, if completed, would fully answer
the goal. Return ONLY a numbered list, one sub-task per line. Be specific — each
sub-task should map to one search query or one calculation, not a vague theme."""


def make_plan(llm: LLM, goal: str) -> List[str]:
    raw = llm.complete(
        system=PLAN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Research goal: {goal}"}],
    )
    tasks: List[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        cleaned = line.lstrip("0123456789.) ").strip()
        if cleaned:
            tasks.append(cleaned)
    if not tasks:
        return [f"Research the topic: {goal}", f"Summarize the main findings for: {goal}"]
    return tasks
