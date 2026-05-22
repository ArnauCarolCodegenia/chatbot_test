"""
Logging plugin — structured observability across all agents.

Emits JSON-compatible log lines so they can be ingested by Cloud Logging,
Datadog, or any log aggregator. Tracks token usage per invocation.

Register alongside SecurityPlugin:
    runner = Runner(agent=root_agent, plugins=[SecurityPlugin(), LoggingPlugin()])
"""

from __future__ import annotations

import json
import logging
import time

logger = logging.getLogger(__name__)


class LoggingPlugin:
    """Structured logging for every agent invocation and model call."""

    async def before_run_callback(self, callback_context):
        callback_context.state["_run_start"] = time.monotonic()
        logger.info(json.dumps({
            "event": "run_start",
            "session_id": callback_context.session_id,
            "user_id": getattr(callback_context, "user_id", "unknown"),
        }))

    async def after_run_callback(self, callback_context):
        start = callback_context.state.pop("_run_start", None)
        elapsed = round(time.monotonic() - start, 3) if start else None
        logger.info(json.dumps({
            "event": "run_end",
            "session_id": callback_context.session_id,
            "elapsed_seconds": elapsed,
        }))

    async def after_model_callback(self, callback_context, llm_response):
        try:
            usage = getattr(llm_response, "usage_metadata", None)
            if usage:
                logger.info(json.dumps({
                    "event": "model_response",
                    "agent": callback_context.agent_name,
                    "input_tokens": getattr(usage, "prompt_token_count", None),
                    "output_tokens": getattr(usage, "candidates_token_count", None),
                }))
        except Exception:
            pass
        return None


"""
Cloud Logging integration — uncomment to send structured logs to GCP:

import google.cloud.logging as gcp_logging

_gcp_client = gcp_logging.Client()
_gcp_client.setup_logging()

# After setup, Python's standard logging goes to Cloud Logging automatically.
# No further changes needed in this plugin.
"""
