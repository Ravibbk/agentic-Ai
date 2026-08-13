# AutoResearcher — Autonomous Research & Report-Writing Agent

AutoResearcher is a **goal-driven, multi-step AI agent** that takes a high-level research
question (e.g. "Compare the environmental impact of EVs vs hydrogen vehicles") and
autonomously plans sub-tasks, calls external tools (web search, calculator, file writer),
verifies its own findings, and produces a cited markdown report — with **no human
in the loop between the initial prompt and the final output**.

Unlike a simple "prompt -> LLM -> answer" chatbot wrapper, this is a true **agentic
system**: it decides _what to do next_, _when it has enough information_, and
_when its own output is weak enough to redo_.

## Why this is "agentic" (not just a chatbot)

| Capability                     | How it's implemented                                                                                                          |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| **Planning**                   | The agent decomposes the goal into an ordered task list (`Planner`) before acting                                             |
| **Tool use**                   | It chooses between tools (web search, calculator, file writer) at runtime based on the sub-task                               |
| **Memory**                     | Short-term scratchpad (current run) + long-term memory (past findings, reusable across sessions)                              |
| **Reflection / self-critique** | After drafting, a `Critic` step scores the draft against the original goal and triggers a revision loop if it falls short     |
| **Autonomy loop**              | Runs a ReAct-style `Plan → Act → Observe → Reflect` loop until a stopping condition (goal satisfied or max iterations) is met |

## Architecture

```
User Goal
    │
    ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Planner   │────▶│  Agent Loop  │────▶│    Tools     │
│ (task list) │     │ (ReAct core) │◀────│ search/calc/ │
└─────────────┘     └──────┬───────┘     │ file writer  │
                            │             └─────────────┘
                            ▼
                     ┌──────────────┐
                     │    Memory    │  (short-term + long-term)
                     └──────┬───────┘
                            ▼
                     ┌──────────────┐
                     │    Critic    │──▶ revise if score < threshold
                     └──────┬───────┘
                            ▼
                    Final Report (.md)
```

## Files

- `src/agent.py` — the core agent loop (Plan → Act → Observe → Reflect)
- `src/planner.py` — breaks a goal into ordered sub-tasks
- `src/tools.py` — tool registry: web search, calculator, file writer
- `src/memory.py` — short-term + long-term (vector-style) memory
- `src/critic.py` — self-evaluation & revision trigger
- `src/llm.py` — thin wrapper around the Anthropic API (model-agnostic interface)
- `src/main.py` — entry point / CLI

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY and (optional) TAVILY_API_KEY
python src/main.py --goal "Compare EV vs hydrogen vehicle environmental impact"
```

## Example run

See `examples/sample_run.md` for a full trace: plan → tool calls → reflection →
revision → final report.

## Key engineering decisions

1. **Model-agnostic LLM wrapper** — swapping Claude for GPT-4 or a local model is a
   one-line change in `llm.py`.
2. **Stopping condition is explicit**, not "run forever" — prevents infinite tool-call
   loops and runaway API cost, a real failure mode in early agent frameworks.
3. **Reflection loop is bounded** (`MAX_REVISIONS = 2`) — self-critique without a cap
   can cause agents to loop indefinitely chasing marginal improvements.
4. **Tool calls are logged with token/cost metadata** — for observability, since
   uncontrolled agentic tool use is the #1 production cost risk.
