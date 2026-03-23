"""
Example: Full Corpus Ingest & Query Flow

Demonstrates the complete lifecycle:
1. Create a corpus
2. Upload a document (presign -> S3 upload -> finalize)
3. Add artifact to corpus (triggers ingestion)
4. Poll ingestion status until PROCESSED
5. Query the corpus (LLM-synthesized + context-only)
6. Cleanup

Usage:
    export MAGICKMIND_EMAIL="user@example.com"
    export MAGICKMIND_PASSWORD="your_password"
    export MAGICKMIND_BASE_URL="https://dev-bifrost.magickmind.ai"
    export MAGICKMIND_API_KEY="sk-your-litellm-key"   # for query

    # Provide a file to ingest:
    python examples/corpus_ingest.py path/to/document.pdf

    # Or use a built-in sample:
    python examples/corpus_ingest.py --sample
"""

from __future__ import annotations

import asyncio
import mimetypes
import os
import sys
import tempfile
import time

import httpx
from dotenv import load_dotenv

from magick_mind import MagickMind

load_dotenv()

POLL_INTERVAL = 5
MAX_POLL_TIME = 600

SAMPLE_TEXT = """\
# MagickMind Platform Overview

MagickMind is an AI platform that provides intelligent conversation agents
with long-term memory, knowledge retrieval, and personality customisation.

## Core Features

- **Corpus & RAG**: Upload documents to build knowledge bases. The system
  extracts entities and relationships into a knowledge graph for semantic search.
- **Mindspaces**: Persistent conversation contexts where AI agents can
  reference corpus knowledge and maintain conversation history.
- **Personas**: Customisable AI personalities with traits, growth curves,
  and dyadic relationship modelling.
- **Real-time Streaming**: All AI responses stream via Centrifugo pub/sub
  for low-latency delivery.

## Architecture

Requests flow through Bifrost (REST gateway) to domain services via gRPC:
Xavier (chat orchestration), Corpus (knowledge management), Semantic Memory
(vector search & knowledge graph), Artifact (file storage), and Mindspace
(session management).

## Getting Started

Install the SDK: pip install magickmind
"""


def resolve_file(argv: list[str]) -> tuple[str, str, bool]:
    """Return (file_path, content_type, is_temp) from CLI args."""
    if len(argv) >= 2 and argv[1] != "--sample":
        path = argv[1]
        if not os.path.isfile(path):
            print(f"Error: file not found: {path}")
            sys.exit(1)
        ct, _ = mimetypes.guess_type(path)
        return path, ct or "application/octet-stream", False

    tmp = tempfile.NamedTemporaryFile(
        suffix=".md", prefix="magickmind_sample_", delete=False, mode="w"
    )
    tmp.write(SAMPLE_TEXT)
    tmp.close()
    return tmp.name, "text/markdown", True


async def main() -> None:
    base_url = os.getenv("MAGICKMIND_BASE_URL", "https://dev-bifrost.magickmind.ai")
    email = os.getenv("MAGICKMIND_EMAIL")
    password = os.getenv("MAGICKMIND_PASSWORD")
    api_key = os.getenv("MAGICKMIND_API_KEY", "")

    if not email or not password:
        print("Error: MAGICKMIND_EMAIL and MAGICKMIND_PASSWORD required")
        return

    file_path, content_type, is_temp = resolve_file(sys.argv)
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    print("=" * 60)
    print("Corpus Ingest & Query -- Full Flow")
    print("=" * 60)
    print(f"  File: {file_name} ({file_size:,} bytes, {content_type})")
    print(f"  API:  {base_url}\n")

    async with MagickMind(base_url=base_url, email=email, password=password) as client:
        # 1. Create corpus
        print("1. Creating corpus...")
        corpus = await client.v1.corpus.create(
            name=f"Ingest Example -- {file_name}",
            description="Created by corpus_ingest.py example",
        )
        corpus_id = corpus.id
        print(f"   Corpus: {corpus_id}\n")

        try:
            # 2. Upload file (presign + S3 PUT)
            print("2. Uploading file...")
            presign = await client.v1.artifact.presign_upload(
                file_name=file_name,
                content_type=content_type,
                size_bytes=file_size,
                corpus_id=corpus_id,
            )
            artifact_id = presign.id
            print(f"   Artifact: {artifact_id}")
            print(f"   S3 key:   {presign.key}")

            async with httpx.AsyncClient() as s3:
                with open(file_path, "rb") as f:
                    resp = await s3.put(
                        presign.upload_url,
                        content=f.read(),
                        headers=presign.required_headers or {},
                    )
                resp.raise_for_status()
            print(f"   S3 upload: {resp.status_code}\n")

            # 3. Finalize (client-driven, for dev environments without webhook)
            print("3. Finalizing upload...")
            await client.v1.artifact.finalize(
                artifact_id=artifact_id,
                bucket=presign.bucket,
                key=presign.key,
                corpus_id=corpus_id,
            )
            print("   Finalized\n")

            # 4. Add artifact to corpus (triggers ingestion pipeline)
            print("4. Adding artifact to corpus (triggers ingestion)...")
            add_result = await client.v1.corpus.add_artifact(
                corpus_id, artifact_id, api_key=api_key
            )
            print(f"   Added: {add_result.added_count} artifact(s)\n")

            # 5. Poll ingestion status until PROCESSED or FAILED
            print("5. Waiting for ingestion...")
            t0 = time.time()
            while True:
                status = await client.v1.corpus.get_artifact_status(
                    corpus_id, artifact_id
                )
                elapsed = time.time() - t0
                print(f"   [{elapsed:5.0f}s] {status.status}")

                if status.status.upper() == "PROCESSED":
                    print(f"   Ingestion complete ({elapsed:.0f}s)\n")
                    break
                if status.status.upper() == "FAILED":
                    print(f"   Ingestion FAILED: {status.content_summary}")
                    return
                if elapsed > MAX_POLL_TIME:
                    print(f"   Timed out after {MAX_POLL_TIME}s")
                    return

                await asyncio.sleep(POLL_INTERVAL)

            # 6. Query with LLM synthesis
            query_text = "What is this document about?"
            print(f"6. Query (LLM-synthesized): '{query_text}'")
            result = await client.v1.corpus.query(
                corpus_id, query=query_text, api_key=api_key
            )
            print(f"   Result ({len(result.result)} chars):")
            print(f"   {result.result[:300]}\n")

            # 7. Query context-only (no LLM, raw retrieved context)
            print(f"7. Query (context-only): '{query_text}'")
            ctx = await client.v1.corpus.query(
                corpus_id,
                query=query_text,
                only_need_context=True,
                api_key=api_key,
            )
            print(f"   Raw context ({len(ctx.result)} chars):")
            print(f"   {ctx.result[:300]}\n")

        finally:
            # 8. Cleanup
            print("8. Cleaning up...")
            try:
                await client.v1.corpus.delete(corpus_id)
                print(f"   Deleted corpus {corpus_id}")
            except Exception as e:
                print(f"   Cleanup failed: {e}")

            if is_temp:
                os.unlink(file_path)

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
