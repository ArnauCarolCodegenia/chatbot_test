"""
Writer subagent — level-2 agent under multitool_agent.

Specialises in:
  - Drafting structured documents (reports, proposals, emails, READMEs)
  - Following formatting conventions (markdown, plain text, HTML)
  - Adapting tone: professional, technical, casual, persuasive
  - Generating content in multiple languages

The parent (multitool_agent) delegates here when the user needs a polished
written output — especially before calling generate_pdf to export it.

Workflow tip: multitool_agent can call writer_subagent to produce the content,
then immediately call generate_pdf_tool on the result.
"""

import os

from google.adk.agents import LlmAgent

from tools.common_tools import get_current_datetime

WRITER_SUBAGENT_INSTRUCTION = """
You are a specialised professional writing agent.

Given a topic, brief, or raw notes, produce polished written content.

Document types you handle:
  - REPORT     — executive summary + sections + conclusion
  - PROPOSAL   — problem statement, solution, benefits, timeline, cost
  - EMAIL      — subject line + greeting + body + sign-off
  - README     — overview, installation, usage, contributing, license
  - ARTICLE    — intro hook, structured sections, conclusion CTA
  - SUMMARY    — condensed version of provided content
  - CUSTOM     — follow the user's exact structure instructions

Formatting rules:
  - Use markdown unless the user specifies plain text or HTML.
  - Headings: ## for sections, ### for subsections.
  - Bullet points for lists; numbered lists for sequential steps.
  - Bold (**text**) for key terms, not for decoration.

Tone options (default: professional):
  - professional: formal, objective, business-appropriate
  - technical:    precise, uses domain terminology, assumes expertise
  - casual:       friendly, conversational, accessible
  - persuasive:   benefit-led, action-oriented

Always include a date header using get_current_datetime.
Return ONLY the finished document — no meta-commentary.
"""


def build_writer_subagent() -> LlmAgent:
    return LlmAgent(
        name="writer_subagent",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description=(
            "Specialised writing agent. Drafts polished documents: reports, "
            "proposals, emails, READMEs, articles. Adapts tone and format on "
            "request. Delegate here whenever the user needs structured written "
            "output, especially before PDF export."
        ),
        instruction=WRITER_SUBAGENT_INSTRUCTION,
        tools=[get_current_datetime],
    )
