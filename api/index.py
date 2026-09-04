import sys
import os

# SentinelRisk AI Engine v2.0 — Vercel Serverless Entry Point
# Adds project root to sys.path so Vercel Python runtime can resolve backend packages.
# Deploy build: 2026-09-04
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from backend.app.main import app
except Exception as _e:
    # Surface import errors as a FastAPI app for diagnostics
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/api/v1/health")
    async def _error_health():
        return {"status": "BOOT_ERROR", "error": str(_e), "python": sys.version}
