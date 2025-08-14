"""
Purpose: Orchestration helpers for scoring runs.
Description: Provides a simple async runner wiring config, http client with OPENROUTER_KEY, and model call.
Key Functions/Classes: build_http_client.
"""

from __future__ import annotations

import os
import httpx

from .config import ScoringConfig, load_config


def build_http_client(cfg: ScoringConfig) -> httpx.AsyncClient:
    headers = {
        "Content-Type": "application/json",
    }
    key = os.getenv("OPENROUTER_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
        headers["HTTP-Referer"] = "uptick-scoring"
        headers["X-Title"] = "uptick-scoring"
    return httpx.AsyncClient(headers=headers)


