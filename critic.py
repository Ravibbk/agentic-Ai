"""Self-critique support for the agent."""

from __future__ import annotations

from typing import Tuple

from llm import LLM

CRITIC_SYSTEM_PROMPT = """You are a strict editor. Given a research goal and a draft
report, score the draft from 1-10 on: completeness, accuracy of reasoning, and
whether it directly answers the goal. Respond in exactly this format:

SCORE: <number>
FEEDBACK: <one or two sentences on what's missing or weak, or "none" if score is 9-10>
"""


def critique(llm: LLM, goal: str, draft: str) -> Tuple[int, str]:
    raw = llm.complete(
        system=CRITIC_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Goal: {goal}\n\nDraft:\n{draft}"}],
    )
    score, feedback = 5, "Could not parse critic output."
    for line in raw.splitlines():
        if line.upper().startswith("SCORE:"):
            try:
                score = int("".join(character for character in line if character.isdigit()))
            except ValueError:
                pass
        if line.upper().startswith("FEEDBACK:"):
            feedback = line.split(":", 1)[1].strip()
    return score, feedback
