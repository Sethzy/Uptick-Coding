"""
Purpose: Typed schemas for LLM scoring inputs/outputs.
Description: Defines strict Pydantic models for model responses and helpers to access JSON schema text for prompts.
Key Functions/Classes: ModelClassification, get_model_classification_json_schema.
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
import re


# AIDEV-NOTE: Keep schema minimal and aligned with PRD; evidence removed per PRD fix-json-evidence.


class ModelClassification(BaseModel):
    classification_category: Literal[
        "Maintenance & Service Only",
        "Install Focus",
        "50/50 Split",
        "Other",
    ]
    confidence: int = Field(..., ge=0, le=100)
    rationale: str = Field(..., min_length=1)
    # Only required when classification_category == "Other"
    other_sublabel: Optional[str] = Field(default=None, description="Optional short sublabel for 'Other'.")
    other_sublabel_definition: Optional[str] = Field(default=None, description="Optional brief definition for 'Other'.")

    # AIDEV-NOTE: Ignore unknown fields (e.g., legacy 'evidence') to avoid invalid_json on extra keys.
    model_config = ConfigDict(extra="ignore")


def get_model_classification_json_schema() -> str:
    """Return a compact JSON schema snippet for inclusion in the prompt text."""
    # Using a hand-authored snippet for clarity in prompts.
    return (
        '{\n'
        '  "classification_category": "Maintenance & Service Only|Install Focus|50/50 Split|Other",\n'
        '  "confidence": 0-100,\n'
        '  "rationale": "string",\n'
        '  "other_sublabel": "string (optional)",\n'
        '  "other_sublabel_definition": "string (optional)"\n'
        '}'
    )


