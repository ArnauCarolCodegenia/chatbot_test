"""
Sequential workflow agent.

SequentialAgent runs its sub_agents one after another in the declared order.
Each sub-agent can read state written by the previous one via context.state.

Use output_key on each sub-agent to automatically save its final response
into session state so the next step can access it.

Example flow (rename agents for your use-case):
  Step 1 — research_agent  → saves findings to state["research"]
  Step 2 — analysis_agent  → reads state["research"], saves to state["analysis"]
  Step 3 — report_agent    → reads state["analysis"], produces final output
"""

import os

from google.adk.agents import LlmAgent, SequentialAgent


def _make_step(name: str, instruction: str, output_key: str) -> LlmAgent:
    return LlmAgent(
        name=name,
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description=f"Sequential step: {name}",
        instruction=instruction,
        output_key=output_key,
    )


STEP1_INSTRUCTION = """
You are the RESEARCH step of a pipeline.
Analyse the user's request and summarise the key facts or requirements.
Be concise — the next step will act on your summary.
Save your output as a plain text summary.
"""

STEP2_INSTRUCTION = """
You are the ANALYSIS step of a pipeline.
You will receive research notes in the session state under the key 'research_output'.
Identify the main conclusions, risks, and recommendations.
"""

STEP3_INSTRUCTION = """
You are the REPORT step of a pipeline.
Synthesise the analysis in state['analysis_output'] into a clear, structured final report
with sections: Summary, Findings, Recommendations.
"""


def build_sequential_agent() -> SequentialAgent:
    step1 = _make_step("research_step",  STEP1_INSTRUCTION,  "research_output")
    step2 = _make_step("analysis_step",  STEP2_INSTRUCTION,  "analysis_output")
    step3 = _make_step("report_step",    STEP3_INSTRUCTION,  "report_output")

    return SequentialAgent(
        name="sequential_agent",
        description="Multi-step sequential pipeline: research → analysis → report.",
        sub_agents=[step1, step2, step3],
    )
