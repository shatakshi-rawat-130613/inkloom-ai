"""Inkloom AI FastAPI application entry point.

Phase 0 foundation: exposes only the health endpoint. Routers, database
setup and the analysis pipeline are added in later phases.
"""

from fastapi import FastAPI

app = FastAPI(title="Inkloom AI API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by Render and the frontend warm-up call."""
    return {"status": "ok"}
