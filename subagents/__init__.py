"""
Subagents — level-2 specialised agents.

Hierarchy:
    Orchestrator
        ├── normal_agent
        │     ├── search_subagent     (retrieval / URL research)
        │     └── summarizer_subagent (condensing / structuring)
        └── multitool_agent
              ├── writer_subagent     (document / report writing)
              └── data_subagent       (analysis / PDF generation)

Transfer mechanism (sub_agents=[]):
  The parent LlmAgent calls transfer_to_agent(agent_name='...') to hand off.
  The subagent processes the request and returns; control comes back to the
  parent which can continue or pass the result up the chain.

Alternative (AgentTool):
  Wrap any subagent with AgentTool and put it in tools=[] instead.
  Use this when the parent needs to inspect the subagent's output before
  responding (e.g. validate, combine with other results).
  See tools/subagent_tool.py for an example.
"""

from subagents.search_subagent import build_search_subagent
from subagents.summarizer_subagent import build_summarizer_subagent
from subagents.writer_subagent import build_writer_subagent
from subagents.data_subagent import build_data_subagent

__all__ = [
    "build_search_subagent",
    "build_summarizer_subagent",
    "build_writer_subagent",
    "build_data_subagent",
]
