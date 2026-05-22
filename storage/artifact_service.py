"""
Artifact service factory.

Artifacts are binary blobs (PDFs, images, CSVs…) produced by tools and agents.
Two backends are available:

  memory  → InMemoryArtifactService  (default, no GCP required, lost on restart)
  gcs     → GcsArtifactService       (persisted in Google Cloud Storage bucket)

Switch via ARTIFACT_BACKEND env var. For GCS you must also set GCS_BUCKET_NAME.

GCS setup (one-time):
  1. Create a bucket in europe-west1 (fewer model issues):
       gcloud storage buckets create gs://YOUR_BUCKET \\
         --project=YOUR_PROJECT \\
         --location=europe-west1 \\
         --uniform-bucket-level-access
  2. Grant the service account roles/storage.objectAdmin on the bucket.
  3. Set GCS_BUCKET_NAME=YOUR_BUCKET in .env.

Artifact namespacing (managed automatically by ADK):
  Session-scoped: {app_name}/{user_id}/{session_id}/{filename}
  User-scoped:    use "user:" prefix in filename → {app_name}/{user_id}/user/{filename}
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def build_artifact_service():
    """Return artifact service based on ARTIFACT_BACKEND env var."""
    backend = os.getenv("ARTIFACT_BACKEND", "memory").lower()

    if backend == "gcs":
        bucket = os.getenv("GCS_BUCKET_NAME")
        if not bucket:
            raise ValueError("GCS_BUCKET_NAME must be set when ARTIFACT_BACKEND=gcs")
        from google.adk.artifacts import GcsArtifactService
        logger.info("Using GcsArtifactService (bucket=%s)", bucket)
        return GcsArtifactService(bucket_name=bucket)

    from google.adk.artifacts import InMemoryArtifactService
    logger.info("Using InMemoryArtifactService")
    return InMemoryArtifactService()
