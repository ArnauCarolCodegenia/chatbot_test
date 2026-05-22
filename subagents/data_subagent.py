"""
Data subagent — level-2 agent under multitool_agent.

Specialises in:
  - Parsing and analysing structured data (CSV, JSON, tables)
  - Computing statistics, aggregations, and comparisons
  - Generating formatted data outputs (markdown tables, JSON, CSV)
  - Creating PDF exports of data analysis results

The parent (multitool_agent) delegates here for anything data-heavy:
interpretation of numbers, transformation of datasets, or exporting
analysis results as a downloadable PDF artifact.

Tool available:
  - generate_pdf_tool → export the analysis as a PDF artifact
"""

import os

from google.adk.agents import LlmAgent

from tools.pdf_generator import generate_pdf_tool
from tools.common_tools import get_current_datetime
from callbacks.action_callbacks import before_tool_log_cb, after_tool_log_cb

DATA_SUBAGENT_INSTRUCTION = """
You are a specialised data analysis agent.

Given raw data (numbers, tables, JSON, CSV, or a description of data),
perform the requested analysis and return structured results.

Capabilities:
  1. STATISTICS   — mean, median, min, max, std dev, percentiles
  2. COMPARISON   — side-by-side comparison table of entities or options
  3. TREND        — identify patterns, growth rates, anomalies in a series
  4. AGGREGATION  — group-by summaries, totals, counts
  5. TRANSFORMATION — reformat data: CSV → table, JSON → readable text
  6. EXPORT       — call generate_pdf to save the analysis as a PDF artifact

Output format:
  - Lead with a one-sentence conclusion (the "so what").
  - Present data as markdown tables when comparing multiple items.
  - Show calculation steps for non-trivial maths.
  - End with a short "Insights" section (3 bullet points max).

When the user asks to export or save the analysis:
  1. Format the full analysis as clean plain text.
  2. Call generate_pdf with an appropriate title and filename.
  3. Tell the user the artifact name so they can download it.
"""


def build_data_subagent() -> LlmAgent:
    return LlmAgent(
        name="data_subagent",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description=(
            "Specialised data analysis agent. Computes statistics, comparisons, "
            "trends, and aggregations from structured data. Can export results "
            "as a PDF artifact. Delegate here for any data-heavy or analytical task."
        ),
        instruction=DATA_SUBAGENT_INSTRUCTION,
        tools=[
            generate_pdf_tool,
            get_current_datetime,
        ],
        before_tool_callback=before_tool_log_cb,
        after_tool_callback=after_tool_log_cb,
    )
