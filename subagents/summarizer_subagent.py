"""
Summarizer subagent — level-2 agent under normal_agent.

Specialises in:
  - Condensing long texts into structured summaries
  - Extracting key points, action items, and decisions
  - Converting unstructured content into bullet lists or tables
  - Adjusting verbosity to user-specified length (short / medium / detailed)

The parent (normal_agent) delegates here when the user wants to summarise,
extract highlights from, or restructure a piece of text or a document.

No external tools needed — this agent works purely with the context passed
to it plus the LLM's language capabilities.
"""

import os

from google.adk.agents import LlmAgent

from tools.common_tools import get_current_datetime

SUMMARIZER_SUBAGENT_INSTRUCTION = """
You are a specialised summarisation and extraction agent.

Given any text or document passed to you, produce one of the following
based on the user's request:

1. SUMMARY (default)
   - 3-5 bullet points covering the most important ideas.
   - One sentence of overall conclusion.

2. KEY POINTS
   - Numbered list of concrete facts, figures, or findings.
   - Include direct quotes for notable statements.

3. ACTION ITEMS
   - Bullet list of tasks, owners (if mentioned), and deadlines.
   - Separate "decided" from "to-do".

4. TABLE
   - Extract structured data into a markdown table when the input contains
     comparable entities (e.g. features, options, people).

5. DETAILED (when explicitly requested)
   - Section-by-section breakdown with headers.
   - Preserve all significant detail.

Rules:
- Never add information not present in the source text.
- Adapt output length to the user's instruction (short / medium / detailed).
- Always indicate the source if a title or URL is provided.
- Use today's date (from get_current_datetime) when stamping summaries.
"""


def build_summarizer_subagent() -> LlmAgent:
    return LlmAgent(
        name="summarizer_subagent",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description=(
            "Specialised summarisation agent. Condenses long texts into bullet "
            "summaries, key-point lists, action items, or markdown tables. "
            "Delegate to this agent when the user wants to summarise, extract, "
            "or restructure any body of text."
        ),
        instruction=SUMMARIZER_SUBAGENT_INSTRUCTION,
        tools=[get_current_datetime],
    )
