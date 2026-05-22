"""
Common utility tools available to any agent.

Each tool is a plain async Python function with type-annotated parameters and
a docstring — ADK uses the docstring + type hints to build the tool schema
that is sent to the LLM.

Rules for writing ADK tools:
  1. Type-annotate all parameters (str, int, float, bool, list, dict).
  2. Return a dict with at least {"status": "success"} or {"status": "error"}.
  3. Keep tool names as verb_noun (get_user, create_report, fetch_url…).
  4. One clear responsibility per tool.
  5. Use ToolContext for state, artifacts, and auth — not global variables.
"""

from __future__ import annotations

import datetime
import logging

import httpx
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


async def get_current_datetime(tool_context: ToolContext) -> dict:
    """Return the current date and time in ISO-8601 format (UTC).

    Returns:
        dict with keys: status, datetime, date, time, timezone
    """
    now = datetime.datetime.utcnow()
    return {
        "status": "success",
        "datetime": now.isoformat() + "Z",
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": "UTC",
    }


async def fetch_url(url: str, tool_context: ToolContext) -> dict:
    """Fetch the text content of a public URL via HTTP GET.

    Args:
        url: The full URL to fetch (must start with http:// or https://).

    Returns:
        dict with keys: status, url, content (first 4000 chars), content_type
    """
    if not url.startswith(("http://", "https://")):
        return {"status": "error", "message": "URL must start with http:// or https://"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            return {
                "status": "success",
                "url": str(response.url),
                "content": response.text[:4000],
                "content_type": response.headers.get("content-type", "unknown"),
            }
    except httpx.HTTPStatusError as exc:
        logger.warning("fetch_url HTTP error: %s", exc)
        return {"status": "error", "message": f"HTTP {exc.response.status_code}"}
    except Exception as exc:
        logger.error("fetch_url error: %s", exc)
        return {"status": "error", "message": str(exc)}


"""
Additional tools — uncomment as needed:

async def send_email(
    to: str,
    subject: str,
    body: str,
    tool_context: ToolContext,
) -> dict:
    # Requires SMTP env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    import smtplib, os
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 587))) as s:
        s.starttls()
        s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
        s.send_message(msg)
    return {"status": "success", "to": to, "subject": subject}


async def get_weather(city: str, tool_context: ToolContext) -> dict:
    # Requires OPENWEATHER_API_KEY env var
    import os
    key = os.getenv("OPENWEATHER_API_KEY")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": key, "units": "metric"},
        )
        r.raise_for_status()
        data = r.json()
    return {
        "status": "success",
        "city": city,
        "temperature_c": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"],
    }


async def run_python_snippet(code: str, tool_context: ToolContext) -> dict:
    # WARNING: only safe for trusted inputs — runs arbitrary Python
    # Consider using Vertex AI Code Interpreter (sandboxed) instead
    import io, contextlib
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            exec(code, {})  # noqa: S102
        return {"status": "success", "output": stdout.getvalue()}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
"""
