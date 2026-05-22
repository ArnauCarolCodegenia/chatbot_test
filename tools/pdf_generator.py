"""
PDF generator tool.

Generates a PDF from a title + body text and saves it as an ADK artifact.
The artifact can then be downloaded via the ADK web UI or served by your API.

Requires: reportlab (already in requirements.txt)

Usage by agent:
    generate_pdf(title="My Report", content="Full text here...", filename="report.pdf")
"""

from __future__ import annotations

import io
import logging

from google.adk import types
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


async def generate_pdf_tool(
    title: str,
    content: str,
    filename: str,
    tool_context: ToolContext,
) -> dict:
    """Generate a PDF document from a title and text content, save as artifact.

    Args:
        title: Document title shown at the top of the PDF.
        content: Body text for the PDF (plain text, newlines respected).
        filename: Artifact filename, must end with .pdf (e.g. "report.pdf").

    Returns:
        dict with keys: status, filename, version, size_bytes
    """
    if not filename.lower().endswith(".pdf"):
        filename = filename + ".pdf"

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        return {
            "status": "error",
            "message": "reportlab is not installed. Run: pip install reportlab",
        }

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 0.5 * cm),
    ]

    for paragraph in content.split("\n\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip().replace("\n", "<br/>"), styles["Normal"]))
            story.append(Spacer(1, 0.3 * cm))

    doc.build(story)
    pdf_bytes = buffer.getvalue()

    part = types.Part(
        inline_data=types.Blob(data=pdf_bytes, mime_type="application/pdf")
    )
    version = tool_context.save_artifact(filename, part)

    logger.info("Generated PDF artifact: %s (version=%s, %d bytes)", filename, version, len(pdf_bytes))

    return {
        "status": "success",
        "filename": filename,
        "version": version,
        "size_bytes": len(pdf_bytes),
        "message": f"PDF saved as artifact '{filename}'. The user can download it from the artifacts panel.",
    }
