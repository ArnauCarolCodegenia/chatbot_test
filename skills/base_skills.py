"""
Skills — reusable instruction blocks that can be injected into any agent.

In ADK a "skill" is a named capability: a prompt fragment, a set of tools,
or both, that gives an agent a specialised behaviour without duplicating code.

Pattern: define skill dicts with 'instruction' and optional 'tools', then
merge them into an agent's instruction string and tool list at build time.

Usage example:
    from skills.base_skills import SKILLS

    agent = LlmAgent(
        instruction=SKILLS["summarisation"]["instruction"] + "\\n" + MY_INSTRUCTION,
        tools=[*SKILLS["summarisation"]["tools"], my_own_tool],
        ...
    )
"""

from tools.common_tools import get_current_datetime, fetch_url
from tools.pdf_generator import generate_pdf_tool

SKILLS: dict[str, dict] = {
    # ------------------------------------------------------------------
    # Summarisation skill
    # ------------------------------------------------------------------
    "summarisation": {
        "description": "Condense long texts into concise bullet summaries.",
        "instruction": """
SKILL — SUMMARISATION:
When asked to summarise, extract the 5 most important points as bullet items.
Use plain language. Include numbers/statistics when present. Max 150 words.
""",
        "tools": [],
    },

    # ------------------------------------------------------------------
    # Document generation skill
    # ------------------------------------------------------------------
    "document_generation": {
        "description": "Generate structured documents and export them as PDF artifacts.",
        "instruction": """
SKILL — DOCUMENT GENERATION:
When creating a report or document:
1. Draft clear sections: Introduction, Body (with subsections), Conclusion.
2. Use headings and bullet points for readability.
3. After drafting, call generate_pdf to save the document as a downloadable artifact.
4. Inform the user that the file is available in the artifacts panel.
""",
        "tools": [generate_pdf_tool],
    },

    # ------------------------------------------------------------------
    # Web research skill
    # ------------------------------------------------------------------
    "web_research": {
        "description": "Retrieve and synthesise information from URLs.",
        "instruction": """
SKILL — WEB RESEARCH:
When researching online:
1. Identify 1-3 authoritative URLs relevant to the question.
2. Use fetch_url to retrieve their content.
3. Cite sources inline using [Source: URL] notation.
4. Never fabricate URLs — only use ones retrieved via tools.
""",
        "tools": [fetch_url],
    },

    # ------------------------------------------------------------------
    # Temporal awareness skill
    # ------------------------------------------------------------------
    "temporal_awareness": {
        "description": "Always know the current date/time before answering time-sensitive queries.",
        "instruction": """
SKILL — TEMPORAL AWARENESS:
For any query involving dates, deadlines, or 'current' information:
1. Call get_current_datetime first to know today's date.
2. Use it as the reference point for relative expressions (yesterday, next week, etc.).
""",
        "tools": [get_current_datetime],
    },
}


"""
Additional skill templates — uncomment and fill in as needed:

SKILLS["customer_support"] = {
    "description": "Handle customer support queries with empathy and clarity.",
    "instruction": \"\"\"
SKILL — CUSTOMER SUPPORT:
- Greet the user warmly.
- Acknowledge the issue before attempting to solve it.
- Offer step-by-step solutions.
- Escalate if unable to resolve after two attempts.
\"\"\",
    "tools": [],
}

SKILLS["sql_query"] = {
    "description": "Translate natural language requests into safe SQL queries.",
    "instruction": \"\"\"
SKILL — SQL QUERY:
- Only generate SELECT queries unless explicitly asked for mutations.
- Always include a LIMIT clause (default LIMIT 100).
- Validate table/column names against the schema before executing.
- Explain the query in plain language before running it.
\"\"\",
    "tools": [],  # Add BigQueryToolset or custom DB tool here
}
"""
