"""
Parallel workflow agent.

ParallelAgent runs all its sub_agents concurrently and waits for all to finish
before returning. Each branch writes to a distinct state key so results don't
collide. A final aggregator agent synthesises the parallel results.

Use this pattern when sub-tasks are independent (e.g. fetching data from
several APIs at the same time, or generating multiple drafts in parallel).

Layout:
  ParallelAgent
    ├── branch_a_agent  (output_key="branch_a")
    ├── branch_b_agent  (output_key="branch_b")
    └── branch_c_agent  (output_key="branch_c")

After all branches finish, a SequentialAgent wraps the parallel step + an
aggregator so the final response is coherent.
"""

import os

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent


def _make_branch(name: str, instruction: str, output_key: str) -> LlmAgent:
    return LlmAgent(
        name=name,
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description=f"Parallel branch: {name}",
        instruction=instruction,
        output_key=output_key,
    )


BRANCH_A_INSTRUCTION = """
You are BRANCH A. Given the user's request, handle the FIRST perspective or subtask.
Be concise — write only your findings, they will be merged with other branches.
"""

BRANCH_B_INSTRUCTION = """
You are BRANCH B. Given the user's request, handle the SECOND perspective or subtask.
Be concise — write only your findings.
"""

BRANCH_C_INSTRUCTION = """
You are BRANCH C. Given the user's request, handle the THIRD perspective or subtask.
Be concise — write only your findings.
"""

AGGREGATOR_INSTRUCTION = """
You are the AGGREGATOR. Three parallel branches have analysed the user's request.
Their outputs are stored in session state:
  - state['branch_a']: Branch A findings
  - state['branch_b']: Branch B findings
  - state['branch_c']: Branch C findings

Synthesise all three into a single, coherent, well-structured response.
Do not repeat content — integrate and summarise.
"""


def build_parallel_agent() -> SequentialAgent:
    branch_a = _make_branch("branch_a_agent", BRANCH_A_INSTRUCTION, "branch_a")
    branch_b = _make_branch("branch_b_agent", BRANCH_B_INSTRUCTION, "branch_b")
    branch_c = _make_branch("branch_c_agent", BRANCH_C_INSTRUCTION, "branch_c")

    fan_out = ParallelAgent(
        name="parallel_fan_out",
        description="Run three independent analysis branches concurrently.",
        sub_agents=[branch_a, branch_b, branch_c],
    )

    aggregator = LlmAgent(
        name="aggregator_agent",
        model=os.getenv("DEFAULT_MODEL", "gemini-2.0-flash"),
        description="Merge parallel branch outputs into a single response.",
        instruction=AGGREGATOR_INSTRUCTION,
    )

    return SequentialAgent(
        name="parallel_agent",
        description="Fan-out parallel analysis followed by result aggregation.",
        sub_agents=[fan_out, aggregator],
    )
