"""
Action callbacks — observability and cross-cutting logic hooks attached to
agent and tool lifecycle events.

Return None from every callback here to preserve the default ADK behaviour.
Returning a non-None value from a model callback would override the response —
only do that intentionally (see security_callbacks.py for an example).

Lifecycle order:
  before_agent_callback
    before_model_callback  ← can short-circuit with LlmResponse
      (LLM call)
    after_model_callback   ← can modify LlmResponse
    before_tool_callback   ← can short-circuit with dict
      (tool execution)
    after_tool_callback    ← can modify tool result
  after_agent_callback
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


async def before_agent_cb(callback_context) -> None:
    """Log agent start and record invocation start time in state."""
    logger.info("[AGENT START] %s | session=%s", callback_context.agent_name, callback_context.session_id)
    callback_context.state["_agent_start_time"] = time.monotonic()


async def after_agent_cb(callback_context) -> None:
    """Log agent completion and elapsed time."""
    start = callback_context.state.pop("_agent_start_time", None)
    elapsed = f"{time.monotonic() - start:.2f}s" if start else "unknown"
    logger.info("[AGENT END]   %s | elapsed=%s", callback_context.agent_name, elapsed)


async def before_tool_log_cb(callback_context, tool, args, tool_context) -> None:
    """Log every tool invocation with its arguments."""
    logger.info(
        "[TOOL CALL]   tool=%s | agent=%s | args=%s",
        tool.name,
        callback_context.agent_name,
        {k: v for k, v in args.items() if k != "tool_context"},
    )


async def after_tool_log_cb(callback_context, tool, args, tool_context, tool_response) -> None:
    """Log tool result status."""
    status = tool_response.get("status", "?") if isinstance(tool_response, dict) else "non-dict"
    logger.info("[TOOL RESULT] tool=%s | status=%s", tool.name, status)


"""
Additional callback examples — uncomment as needed:

async def before_model_cache_cb(callback_context, llm_request):
    # Simple in-memory response cache keyed by last user message
    from google.adk.models import LlmResponse
    from google.adk import types
    import hashlib, json

    try:
        last_msg = llm_request.contents[-1].parts[-1].text or ""
    except Exception:
        return None

    cache_key = hashlib.md5(last_msg.encode()).hexdigest()
    cached = callback_context.state.get(f"_cache:{cache_key}")
    if cached:
        logger.info("[CACHE HIT] %s", cache_key[:8])
        return LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text=cached)])
        )
    callback_context.state["_pending_cache_key"] = cache_key
    return None


async def after_model_cache_cb(callback_context, llm_response):
    cache_key = callback_context.state.pop("_pending_cache_key", None)
    if cache_key:
        try:
            text = llm_response.content.parts[0].text or ""
            callback_context.state[f"_cache:{cache_key}"] = text
        except Exception:
            pass
    return None


async def before_tool_rate_limit_cb(callback_context, tool, args, tool_context):
    # Naive per-session rate limiter: max 20 tool calls per session
    import time
    count_key = "_tool_call_count"
    count = callback_context.state.get(count_key, 0) + 1
    callback_context.state[count_key] = count
    if count > 20:
        return {"status": "error", "message": "Tool call limit reached for this session."}
    return None
"""
