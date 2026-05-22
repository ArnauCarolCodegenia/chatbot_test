"""
Sub-agent as a Tool (AgentTool pattern).

AgentTool wraps an agent so it can be called like a regular tool from another
agent's tool list. The calling agent passes a natural-language task string;
the wrapped agent handles it and returns the result.

This is the recommended pattern when:
  - A specialised agent is complex and should be reused across multiple parents.
  - You want explicit tool-call semantics rather than automatic routing.

Difference from sub_agents=[]:
  sub_agents=[]: LLM can transfer control entirely (the sub-agent takes over).
  AgentTool:     LLM invokes it as a tool; the parent retains control after.
"""

import os

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool


def _build_specialist_agent() -> LlmAgent:
    """Internal specialist agent that can be wrapped as a tool."""
    return LlmAgent(
        name="specialist_agent",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description="A specialist agent capable of deep analysis on a given topic.",
        instruction="""
You are a specialist analyst. You receive a focused task and return a detailed,
structured analysis. Be thorough but concise. Return only the analysis, no preamble.
        """,
    )


def build_subagent_tool() -> AgentTool:
    """Return a callable AgentTool wrapping the specialist agent."""
    return AgentTool(agent=_build_specialist_agent())


"""
Additional AgentTool examples — uncomment as needed:

def build_code_review_tool() -> AgentTool:
    code_reviewer = LlmAgent(
        name="code_review_agent",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        instruction=\"\"\"
You are an expert code reviewer. Given a code snippet, identify:
- Bugs and logical errors
- Security vulnerabilities
- Performance issues
- Style and readability improvements
Return a numbered list of findings.
        \"\"\",
    )
    return AgentTool(agent=code_reviewer)


def build_translation_tool() -> AgentTool:
    translator = LlmAgent(
        name="translation_agent",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        instruction=\"\"\"
You are a professional translator. Translate the given text to the requested target language.
Preserve tone, formatting, and technical terms. Return only the translation.
        \"\"\",
    )
    return AgentTool(agent=translator)
"""
