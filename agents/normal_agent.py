"""
Normal (general-purpose) LLM agent — level-1 agent under the orchestrator.

This agent handles conversational queries and single-step tasks directly.
For specialised subtasks it delegates down to its own subagents:

  normal_agent
    ├── search_subagent     → live web retrieval and URL research
    └── summarizer_subagent → condensing, structuring, extracting from text

Transfer mechanism:
  The LLM generates transfer_to_agent(agent_name='search_subagent') or
  transfer_to_agent(agent_name='summarizer_subagent') when appropriate.
  After the subagent finishes, control returns here.

To add more subagents: import and append to sub_agents=[].
"""

import os

from google.adk.agents import LlmAgent

from tools.common_tools import get_current_datetime, fetch_url
from callbacks.action_callbacks import before_tool_log_cb, after_tool_log_cb
from subagents.search_subagent import build_search_subagent
from subagents.summarizer_subagent import build_summarizer_subagent

# Uncomment to add web search grounding directly on this agent:
# from google.adk.tools import google_search

NORMAL_AGENT_INSTRUCTION = """
You are a helpful, concise assistant. Answer user questions accurately.
Use your available tools and subagents to provide the best response:

- get_current_datetime: when you need today's date or time
- fetch_url: to retrieve content from a specific URL
- search_subagent: delegate to this subagent for any query that requires
  web research, live data, or content from multiple URLs
- summarizer_subagent: delegate to this subagent when the user wants to
  summarise, extract key points, or restructure a body of text

Delegation rule:
  If the task is primarily about RETRIEVAL → transfer to search_subagent.
  If the task is primarily about SUMMARISING/STRUCTURING text → transfer to summarizer_subagent.
  For simple, direct questions → answer yourself using tools or knowledge.

If a task is complex, multi-step, or requires parallel work, escalate back
to the orchestrator by telling the user to rephrase for a workflow agent.
"""


def build_normal_agent() -> LlmAgent:
    return LlmAgent(
        name="normal_agent",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description=(
            "General-purpose assistant for conversational queries and simple tasks. "
            "Has two subagents: search_subagent (web retrieval) and "
            "summarizer_subagent (condensing/structuring text)."
        ),
        instruction=NORMAL_AGENT_INSTRUCTION,
        tools=[
            get_current_datetime,
            fetch_url,
            # google_search,   # Uncomment for live web search on this agent
        ],
        sub_agents=[
            build_search_subagent(),
            build_summarizer_subagent(),
        ],
        before_tool_callback=before_tool_log_cb,
        after_tool_callback=after_tool_log_cb,
    )
