"""
Purpose: Shared Pydantic models for the scoring package.
Description: Centralizes the core data models that are used across API and CLI.
Key Functions/Classes: `Evidence`, `ClassificationResult`, `LlmInput`.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    url: str
    snippet: str


class ClassificationResult(BaseModel):
    domain: str
    classification_category: str
    rationale: str


class LlmInput(BaseModel):
    domain: str
    aggregated_context: str


