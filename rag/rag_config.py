"""
Vertex AI RAG Engine integration.

Retrieval-Augmented Generation lets agents query your document corpus stored
in Vertex AI before answering, grounding responses in your private data.

SETUP (one-time per project):
  1. Enable the Vertex AI API:
       gcloud services enable aiplatform.googleapis.com

  2. Create a RAG corpus (use european region to avoid quota issues):
       gcloud ai rag-corpora create \\
         --display-name="my-knowledge-base" \\
         --project=YOUR_PROJECT \\
         --location=europe-west1

     Note the output resource name:
       projects/YOUR_PROJECT/locations/europe-west1/ragCorpora/CORPUS_ID

  3. Upload documents to the corpus (PDF, TXT, HTML, Google Drive…):
       gcloud ai rag-files import \\
         --rag-corpus=CORPUS_ID \\
         --project=YOUR_PROJECT \\
         --location=europe-west1 \\
         --gcs-uris=gs://YOUR_BUCKET/docs/

  4. Set in .env:
       VERTEX_RAG_CORPUS_1=projects/YOUR_PROJECT/locations/europe-west1/ragCorpora/CORPUS_ID
       GOOGLE_CLOUD_PROJECT=YOUR_PROJECT
       GOOGLE_CLOUD_LOCATION=europe-west1
       GOOGLE_GENAI_USE_VERTEXAI=1

  5. Add build_rag_tool() to any agent's tools list.

Multiple corpora: set VERTEX_RAG_CORPUS_2, VERTEX_RAG_CORPUS_3… and use
build_multi_rag_toolset() to search all of them.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def build_rag_tool():
    """
    Build a single Vertex AI RAG retrieval tool from VERTEX_RAG_CORPUS_1.

    Returns None if the env var is not set (safe to ignore in dev).
    """
    corpus = os.getenv("VERTEX_RAG_CORPUS_1")
    if not corpus:
        logger.warning("VERTEX_RAG_CORPUS_1 not set — RAG tool disabled.")
        return None

    from google.adk.tools.retrieval import VertexAiRagRetrieval
    import vertexai.preview.rag as rag

    rag_resource = rag.RagResource(rag_corpus=corpus)

    tool = VertexAiRagRetrieval(
        name="search_knowledge_base",
        description=(
            "Search the internal knowledge base for relevant information. "
            "Use this before answering questions about company data, products, or policies."
        ),
        rag_resources=[rag_resource],
        similarity_top_k=5,
        vector_distance_threshold=0.6,
    )
    logger.info("RAG tool configured with corpus: %s", corpus)
    return tool


def build_multi_rag_toolset() -> list:
    """
    Build RAG tools for all configured corpora (VERTEX_RAG_CORPUS_1, _2, _3…).

    Returns a list of VertexAiRagRetrieval tools (one per corpus).
    Empty list if none configured.
    """
    tools = []
    idx = 1
    while True:
        corpus = os.getenv(f"VERTEX_RAG_CORPUS_{idx}")
        if not corpus:
            break

        from google.adk.tools.retrieval import VertexAiRagRetrieval
        import vertexai.preview.rag as rag

        tool = VertexAiRagRetrieval(
            name=f"search_knowledge_base_{idx}",
            description=f"Search knowledge base {idx} for relevant information.",
            rag_resources=[rag.RagResource(rag_corpus=corpus)],
            similarity_top_k=5,
            vector_distance_threshold=0.6,
        )
        tools.append(tool)
        logger.info("RAG tool %d configured: %s", idx, corpus)
        idx += 1

    if not tools:
        logger.warning("No VERTEX_RAG_CORPUS_* env vars found — RAG disabled.")
    return tools
