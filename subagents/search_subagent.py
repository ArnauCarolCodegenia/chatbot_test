"""
Search subagent — level-2 agent under normal_agent.

Specialises in:
  - Fetching and parsing content from URLs
  - Web research and source citation
  - Returning well-structured retrieval results

The parent (normal_agent) delegates to this agent when the user's query
requires real-time information from the web or a specific URL.

Tools available:
  - fetch_url         → retrieve text from any public URL
  - get_current_datetime → timestamp results with today's date

Activate google_search by uncommenting it once you configure:
  GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID in .env
"""

import os

from google.adk.agents import LlmAgent

from tools.common_tools import fetch_url, get_current_datetime
from callbacks.action_callbacks import before_tool_log_cb, after_tool_log_cb

# Uncomment once search credentials are configured:
# from google.adk.tools import google_search

SEARCH_SUBAGENT_INSTRUCTION = """
You are a specialised web research agent. Your only job is to retrieve and
present information from external sources.

Behaviour:
1. Identify the most relevant URL(s) for the user's query.
2. Call fetch_url for each URL (max 3 URLs per query).
3. Extract only the relevant information — ignore navigation, ads, footers.
4. Cite every fact with its source URL in the format [Source: <url>].
5. Return a concise, factual summary. Do NOT add opinions or elaboration.
6. If no useful content is found, say so clearly.

Do not answer from memory — always retrieve fresh content.
"""


def build_search_subagent() -> LlmAgent:
    return LlmAgent(
        name="search_subagent",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description=(
            "Specialised retrieval agent. Fetches and summarises web content "
            "from URLs. Delegate to this agent for any query requiring live "
            "web data or content from a specific URL."
        ),
        instruction=SEARCH_SUBAGENT_INSTRUCTION,
        tools=[
            fetch_url,
            get_current_datetime,
            # google_search,   # Uncomment for Google Search grounding
        ],
        before_tool_callback=before_tool_log_cb,
        after_tool_callback=after_tool_log_cb,
    )
