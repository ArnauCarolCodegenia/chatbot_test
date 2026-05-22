"""
Orchestrator agent — level-0 root agent.

Full 3-level hierarchy:

  Orchestrator  (level 0 — this file)
    ├── normal_agent       (level 1) → search_subagent, summarizer_subagent
    ├── multitool_agent    (level 1) → writer_subagent, data_subagent
    ├── sequential_agent   (level 1) → internal pipeline steps
    └── parallel_agent     (level 1) → concurrent branches + aggregator

Transfer mechanism:
  The LLM generates transfer_to_agent(agent_name='...') to hand off to a
  level-1 agent. That agent may in turn transfer to its own subagents.
  Control propagates back up the chain after each agent finishes.

To add a new level-1 agent: import it and append to sub_agents=[].
"""

import os

from google.adk.agents import LlmAgent

from agents.normal_agent import build_normal_agent
from agents.sequential_agent import build_sequential_agent
from agents.parallel_agent import build_parallel_agent
from agents.multitool_agent import build_multitool_agent
from callbacks.action_callbacks import before_agent_cb, after_agent_cb
from callbacks.security_callbacks import before_model_security_cb
from plugins.security_plugin import SecurityPlugin
from tools.common_tools import get_current_datetime


ORCHESTRATOR_INSTRUCTION = """
You are the root orchestrator of this assistant platform.
You sit at the top of a 3-level agent hierarchy:

  You (orchestrator)
    ├── normal_agent       — conversational Q&A, web search, summarisation
    │     ├── search_subagent      (retrieval / URL research)
    │     └── summarizer_subagent  (condensing / structuring text)
    ├── multitool_agent    — tools, document writing, data analysis, PDF export
    │     ├── writer_subagent      (reports, proposals, emails)
    │     └── data_subagent        (statistics, tables, data exports)
    ├── sequential_agent   — ordered multi-step pipelines (research→analysis→report)
    └── parallel_agent     — concurrent fan-out + aggregation

Your responsibilities:
1. Understand the user's intent precisely.
2. Transfer to the most appropriate level-1 agent — do not micromanage their work.
3. Handle only trivial conversational replies (greetings, clarifications) yourself.

Routing guide:
  Simple questions / chat       → normal_agent
  Web search / URL content      → normal_agent  (it will route to search_subagent)
  Summarise / extract / reformat → normal_agent (it will route to summarizer_subagent)
  Write a document / report     → multitool_agent (it will route to writer_subagent)
  Analyse data / export PDF     → multitool_agent (it will route to data_subagent)
  Multi-step ordered workflow   → sequential_agent
  Multiple independent tasks    → parallel_agent

When transferring, briefly tell the user what you are doing (one sentence).
If unsure, default to normal_agent.
"""


def build_orchestrator() -> LlmAgent:
    return LlmAgent(
        name="orchestrator",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description="Root orchestrator that routes requests to specialised agents.",
        instruction=ORCHESTRATOR_INSTRUCTION,
        tools=[get_current_datetime],
        sub_agents=[
            build_normal_agent(),
            build_multitool_agent(),
            build_sequential_agent(),
            build_parallel_agent(),
        ],
        before_agent_callback=before_agent_cb,
        after_agent_callback=after_agent_cb,
        before_model_callback=before_model_security_cb,
    )
