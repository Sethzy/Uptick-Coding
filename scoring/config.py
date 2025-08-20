"""
Purpose: Centralized configuration helpers for the scoring package.
Description: Loads environment variables and provides small helpers for defaults.
Key Functions/Classes: `get_openrouter_api_key`, `get_openrouter_endpoint`, `get_default_model`.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv


# AIDEV-NOTE: Load env from .env if present to ease local dev.
load_dotenv()


def get_openrouter_api_key() -> Optional[str]:
    # Support both common env var names
    return os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")


def get_openrouter_endpoint() -> str:
    return os.getenv("OPENROUTER_ENDPOINT", "https://openrouter.ai/api/v1")


def get_default_model() -> str:
    """Get the default LLM model from environment variables."""
    # AIDEV-NOTE: Use CUSTOM_MODEL from .env as the primary default, fallback to DEFAULT_LLM_MODEL
    return os.getenv("CUSTOM_MODEL") or os.getenv("DEFAULT_LLM_MODEL", "qwen/qwen3-30b-a3b")


