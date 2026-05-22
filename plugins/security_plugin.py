"""
Security plugin — applies global guardrails to ALL agents in the runner.

Plugins run BEFORE agent-level callbacks, making them the first line of defence.
Use them for policies that must apply universally regardless of which agent
processes the request.

Registered in main.py:
    runner = Runner(agent=root_agent, plugins=[SecurityPlugin()])
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_BLOCKED_PATTERNS = re.compile(
    r"(?i)\b("
    r"union\s+select|drop\s+(table|database)"
    r"|exec\s*\(|xp_cmdshell"
    r"|<script|javascript:"
    r"|ignore (all |previous |prior )?(instructions?|rules?|prompts?)"
    r")\b"
)

_SENSITIVE_OUTPUT_PATTERNS = re.compile(
    r"(?i)(password\s*[:=]\s*\S+|api.?key\s*[:=]\s*\S+|secret\s*[:=]\s*\S+)"
)


class SecurityPlugin:
    """
    Global security plugin.

    Hooks:
      before_model: blocks dangerous patterns in user input.
      after_model:  redacts accidental credential leakage in model output.
      before_tool:  logs every tool call with user_id for audit trail.
      on_tool_error: alerts on auth/permission errors.
    """

    async def before_model_callback(self, callback_context, llm_request):
        from google.adk.models import LlmResponse
        from google.adk import types

        text = _flatten_request(llm_request)
        if _BLOCKED_PATTERNS.search(text):
            logger.warning(
                "[PLUGIN:SECURITY] Blocked request | agent=%s | session=%s",
                callback_context.agent_name,
                callback_context.session_id,
            )
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="This request has been blocked by the security policy.")],
                )
            )
        return None

    async def after_model_callback(self, callback_context, llm_response):
        from google.adk.models import LlmResponse
        from google.adk import types

        try:
            text = llm_response.content.parts[0].text or ""
        except Exception:
            return None

        if _SENSITIVE_OUTPUT_PATTERNS.search(text):
            logger.warning("[PLUGIN:SECURITY] Sensitive data in model output — redacting.")
            redacted = _SENSITIVE_OUTPUT_PATTERNS.sub("[REDACTED]", text)
            return LlmResponse(
                content=types.Content(role="model", parts=[types.Part(text=redacted)])
            )
        return None

    async def before_tool_callback(self, callback_context, tool, args, tool_context):
        logger.info(
            "[PLUGIN:AUDIT] tool=%s | agent=%s | session=%s",
            tool.name,
            callback_context.agent_name,
            callback_context.session_id,
        )
        return None

    async def on_tool_error_callback(self, callback_context, tool, args, tool_context, error):
        if any(kw in str(error).lower() for kw in ("unauthorized", "forbidden", "permission")):
            logger.error(
                "[PLUGIN:SECURITY] Unauthorized tool error | tool=%s | session=%s | error=%s",
                tool.name,
                callback_context.session_id,
                error,
            )


def _flatten_request(llm_request) -> str:
    try:
        parts = []
        for content in (llm_request.contents or []):
            for part in (content.parts or []):
                if hasattr(part, "text") and part.text:
                    parts.append(part.text)
        return " ".join(parts)
    except Exception:
        return ""
