"""
ADK Project — Entry point.

Usage:
  adk web          # Launch the ADK dev UI (recommended during development)
  python main.py   # Run a single turn via CLI for quick testing
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from agents.orchestrator import build_orchestrator
from storage.artifact_service import build_artifact_service
from database.connection import build_session_service


async def run_cli(user_message: str) -> None:
    """Run a single conversation turn and print the response."""
    session_service = build_session_service()
    artifact_service = build_artifact_service()

    runner = Runner(
        agent=build_orchestrator(),
        app_name=os.getenv("APP_NAME", "adk-project"),
        session_service=session_service,
        artifact_service=artifact_service,
    )

    session = await session_service.create_session(
        app_name=os.getenv("APP_NAME", "adk-project"),
        user_id="local-user",
    )

    from google.adk import types
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_message)],
    )

    print(f"\nUser: {user_message}\n")
    async for event in runner.run_async(
        user_id="local-user",
        session_id=session.id,
        new_message=content,
    ):
        if event.is_final_response():
            response_text = event.content.parts[0].text if event.content.parts else ""
            print(f"Agent: {response_text}\n")


if __name__ == "__main__":
    import sys
    message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello, what can you help me with?"
    asyncio.run(run_cli(message))
