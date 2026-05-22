"""
Security callbacks — input validation and guardrails applied before every
LLM call. Return an LlmResponse to short-circuit the request; return None
to let it proceed normally.

Detects:
  - SQL injection patterns in user input
  - XSS / HTML injection
  - Prompt injection attempts
  - Personally Identifiable Information leakage (optional)

These are agent-level callbacks. For application-wide enforcement, use
SecurityPlugin in plugins/security_plugin.py instead (runs first).
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SQL injection patterns — covers classic, blind, time-based, and UNION attacks
# ---------------------------------------------------------------------------
_SQL_PATTERNS = re.compile(
    r"(?i)\b("
    r"union\s+select|select\s+\*|drop\s+table|drop\s+database"
    r"|insert\s+into|delete\s+from|update\s+\w+\s+set"
    r"|exec\s*\(|execute\s*\(|xp_cmdshell"
    r"|or\s+1\s*=\s*1|and\s+1\s*=\s*1"
    r"|--\s*$|;\s*--"
    r"|\/\*.*?\*\/"
    r")\b"
)

# ---------------------------------------------------------------------------
# XSS / HTML injection patterns
# ---------------------------------------------------------------------------
_XSS_PATTERNS = re.compile(
    r"(?i)(<script|</script|javascript:|on\w+\s*=|<iframe|<object|<embed|<svg)",
)

# ---------------------------------------------------------------------------
# Prompt injection / jailbreak patterns
# ---------------------------------------------------------------------------
_PROMPT_INJECTION_PATTERNS = re.compile(
    r"(?i)("
    r"ignore (previous|all|prior|above) (instructions?|prompts?|rules?)"
    r"|forget (everything|your instructions)"
    r"|you are now|act as (a )?(?:jailbreak|unrestricted|evil|dan)"
    r"|disregard (your )?(guidelines?|safety)"
    r")"
)


def _extract_text(llm_request) -> str:
    """Pull plain text from an LlmRequest for inspection."""
    try:
        parts = []
        for content in (llm_request.contents or []):
            for part in (content.parts or []):
                if hasattr(part, "text") and part.text:
                    parts.append(part.text)
        return " ".join(parts)
    except Exception:
        return ""


async def before_model_security_cb(callback_context, llm_request):
    """
    Inspect the assembled LLM request before it is sent to the model.

    - Blocks SQL injection, XSS, and prompt injection patterns.
    - Returns a blocking LlmResponse if a threat is detected.
    - Returns None to let the request proceed.
    """
    from google.adk.models import LlmResponse
    from google.adk import types

    text = _extract_text(llm_request)

    if _SQL_PATTERNS.search(text):
        logger.warning(
            "[SECURITY] SQL injection pattern detected in agent '%s'. Blocked.",
            callback_context.agent_name,
        )
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=(
                    "Your request contains patterns associated with SQL injection "
                    "and cannot be processed. Please rephrase your request."
                ))],
            )
        )

    if _XSS_PATTERNS.search(text):
        logger.warning(
            "[SECURITY] XSS pattern detected in agent '%s'. Blocked.",
            callback_context.agent_name,
        )
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=(
                    "Your request contains HTML/script content that cannot be processed."
                ))],
            )
        )

    if _PROMPT_INJECTION_PATTERNS.search(text):
        logger.warning(
            "[SECURITY] Prompt injection attempt detected in agent '%s'. Blocked.",
            callback_context.agent_name,
        )
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=(
                    "Your request attempts to override system instructions and cannot be processed."
                ))],
            )
        )

    return None  # All checks passed — proceed normally


"""
Optional PII detection callback — uncomment if needed:

import re as _re
_PII_PATTERNS = _re.compile(
    r"(?i)\\b(\\d{3}-\\d{2}-\\d{4}|\\d{16}|[A-Z]{2}\\d{6,9})\\b"  # SSN, credit card, passport
)

async def after_model_pii_cb(callback_context, llm_response):
    from google.adk import types
    from google.adk.models import LlmResponse
    text = ""
    try:
        for part in llm_response.content.parts:
            if hasattr(part, "text"):
                text += part.text or ""
    except Exception:
        pass
    if _PII_PATTERNS.search(text):
        logger.warning("[SECURITY] PII detected in model response — redacting.")
        redacted = _PII_PATTERNS.sub("[REDACTED]", text)
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=redacted)],
            )
        )
    return None
"""
