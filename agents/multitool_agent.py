"""
Multi-tool agent — level-1 agent under the orchestrator.

Handles tasks that need multiple tools or specialised output generation.
For content creation and data work it delegates down to its own subagents:

  multitool_agent
    ├── writer_subagent  → drafts reports, proposals, emails, READMEs
    └── data_subagent    → analyses data, computes stats, exports as PDF

Transfer mechanism:
  The LLM generates transfer_to_agent(agent_name='writer_subagent') or
  transfer_to_agent(agent_name='data_subagent') when appropriate.
  After the subagent finishes, control returns here.

To add more subagents: import and append to sub_agents=[].
Uncomment google_search and build_rag_tool() once credentials are configured.
"""

import os

from google.adk.agents import LlmAgent

from tools.common_tools import get_current_datetime, fetch_url
from tools.pdf_generator import generate_pdf_tool
from tools.subagent_tool import build_subagent_tool
from subagents.writer_subagent import build_writer_subagent
from subagents.data_subagent import build_data_subagent

# Uncomment after configuring GOOGLE_SEARCH_API_KEY / GOOGLE_SEARCH_ENGINE_ID:
# from google.adk.tools import google_search

# Uncomment after configuring Vertex AI RAG corpus:
# from rag.rag_config import build_rag_tool

MULTITOOL_INSTRUCTION = """
You are a capable assistant with access to multiple tools and specialised subagents.

Direct tools (call these yourself):
  - get_current_datetime  → today's date/time
  - fetch_url             → retrieve content from a specific URL
  - generate_pdf          → create a PDF artifact from title + text
  - specialist (AgentTool) → delegate a focused analysis task

Subagents (transfer control for these):
  - writer_subagent  → transfer here when the user needs a polished written
    document: report, proposal, email, README, article. The subagent will
    draft it; you can then optionally call generate_pdf on the result.
  - data_subagent    → transfer here for data analysis, statistics, comparisons,
    or when the user wants to export an analysis as a PDF.

Decision guide:
  Writing task     → transfer to writer_subagent
  Data / numbers   → transfer to data_subagent
  Fetch a URL      → use fetch_url directly
  Quick PDF export → use generate_pdf directly (skip writer_subagent for short content)
  Everything else  → use tools directly or answer from knowledge

Always prefer tools and subagents over making up information.
After a subagent returns, summarise the result for the user if needed.
"""


def build_multitool_agent() -> LlmAgent:
    return LlmAgent(
        name="multitool_agent",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description=(
            "Agent with multiple tools and two subagents. "
            "writer_subagent drafts polished documents; "
            "data_subagent handles data analysis and PDF export. "
            "Use for tasks requiring tool combinations or content generation."
        ),
        instruction=MULTITOOL_INSTRUCTION,
        tools=[
            get_current_datetime,
            fetch_url,
            generate_pdf_tool,
            build_subagent_tool(),
            # google_search,       # Uncomment for web search
            # build_rag_tool(),    # Uncomment for RAG retrieval
        ],
        sub_agents=[
            build_writer_subagent(),
            build_data_subagent(),
        ],
    )
