import sys
import os

# SentinelRisk AI Engine v2.0 — Vercel Serverless Entry Point
# Adds project root to sys.path so Vercel Python runtime can resolve backend packages.
# Deploy build: 2026-09-04
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
