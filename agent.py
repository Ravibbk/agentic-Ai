"""Core ReAct-style agentic loop."""

from __future__ import annotations

import re
from typing import Tuple

from llm import LLM
from planner import make_plan
from memory import Memory
from tools import tool_descriptions, call_tool
from critic import critique

MAX_REVISIONS = 2
CRITIC_PASS_THRESHOLD = 8

ACT_SYSTEM_PROMPT = """You are a research agent working on one sub-task at a time.
Available tools:
{tools}

Given the sub-task, respond in exactly this format:
TOOL: <tool_name>
INPUT: <input to the tool>

If no tool is needed and you can answer directly from reasoning, use:
TOOL: none
INPUT: <your direct answer>
"""

DRAFT_SYSTEM_PROMPT = """You are a research report writer. Using the goal and the
collected findings below, write a clear, well-structured markdown report that
directly answers the goal. Cite findings inline where relevant."""


class ResearchAgent:
    def __init__(self) -> None:
        self.llm = LLM()
        self.memory = Memory()

    def _decide_action(self, task: str) -> Tuple[str, str]:
        raw = self.llm.complete(
            system=ACT_SYSTEM_PROMPT.format(tools=tool_descriptions()),
            messages=[{"role": "user", "content": f"Sub-task: {task}"}],
        )
        tool_match = re.search(r"TOOL:\s*(\S+)", raw)
        input_match = re.search(r"INPUT:\s*(.+)", raw, re.DOTALL)
        tool = tool_match.group(1).strip() if tool_match else "none"
        arg = input_match.group(1).strip() if input_match else ""
        return tool, arg

    def run(self, goal: str, verbose: bool = True) -> str:
        plan = make_plan(self.llm, goal)
        if verbose:
            print(f"\n[PLAN] {len(plan)} sub-tasks:")
            for i, task in enumerate(plan, 1):
                print(f"  {i}. {task}")

        prior = self.memory.recall(goal)
        if prior and verbose:
            print(f"\n[MEMORY] Recalled {len(prior)} relevant past finding(s).")

        for task in plan:
            tool, arg = self._decide_action(task)
            if verbose:
                print(f"\n[ACT] task='{task}' -> tool='{tool}' input='{arg[:80]}'")

            if tool == "none":
                result = arg
            else:
                result = call_tool(tool, arg)

            self.memory.record(task, result)
            if verbose:
                print(f"[OBSERVE] {result[:150]}")

        draft = self._draft_report(goal)

        for i in range(MAX_REVISIONS):
            score, feedback = critique(self.llm, goal, draft)
            if verbose:
                print(f"\n[CRITIC] round {i + 1}: score={score}/10 feedback='{feedback}'")
            if score >= CRITIC_PASS_THRESHOLD:
                break
            draft = self._draft_report(goal, revision_note=feedback)

        if verbose:
            print(f"\n[USAGE] {self.llm.usage_summary()}")
        return draft

    def _draft_report(self, goal: str, revision_note: str = "") -> str:
        findings = self.memory.scratchpad_text()
        prompt = f"Goal: {goal}\n\nFindings:\n{findings}"
        if revision_note:
            prompt += f"\n\nPrevious draft was scored too low. Fix this: {revision_note}"
        return self.llm.complete(
            system=DRAFT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
