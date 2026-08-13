"""Two-tier memory for the agent."""

from __future__ import annotations

import json
import os
from typing import Dict, List

LONG_TERM_PATH = "memory_store.json"


class Memory:
    def __init__(self) -> None:
        self.short_term: Dict[str, str] = {}
        self.long_term: List[dict] = self._load_long_term()

    def _load_long_term(self) -> List[dict]:
        if os.path.exists(LONG_TERM_PATH):
            with open(LONG_TERM_PATH, encoding="utf-8") as handle:
                return json.load(handle)
        return []

    def _save_long_term(self) -> None:
        with open(LONG_TERM_PATH, "w", encoding="utf-8") as handle:
            json.dump(self.long_term, handle, indent=2)

    def record(self, task: str, finding: str) -> None:
        self.short_term[task] = finding
        self.long_term.append({"task": task, "finding": finding})
        self._save_long_term()

    def recall(self, query: str, top_k: int = 3) -> List[str]:
        query_words = set(query.lower().split())

        def score(entry: dict) -> int:
            entry_words = set(entry["task"].lower().split())
            return len(query_words & entry_words)

        ranked = sorted(self.long_term, key=score, reverse=True)
        return [entry["finding"] for entry in ranked[:top_k] if score(entry) > 0]

    def scratchpad_text(self) -> str:
        return "\n".join(f"- {task}: {finding}" for task, finding in self.short_term.items())
