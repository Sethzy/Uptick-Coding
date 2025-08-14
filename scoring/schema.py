"""
Purpose: Typed schemas for LLM scoring inputs/outputs.
Description: Defines strict Pydantic models for model responses and helpers to access JSON schema text for prompts.
Key Functions/Classes: EvidenceItem, ModelClassification, get_model_classification_json_schema.
"""

from __future__ import annotations

from typing import List, Literal
from pydantic import BaseModel, Field, HttpUrl, conint


# AIDEV-NOTE: Keep schema minimal and aligned with PRD; expand only with explicit scope changes.


class EvidenceItem(BaseModel):
    url: HttpUrl = Field(..., description="URL cited as evidence; must be present in aggregated headers")
    snippet: str = Field(..., min_length=1, description="Verbatim quote from aggregated_context")


class ModelClassification(BaseModel):
    classification_category: Literal[
        "Maintenance & Service Only",
        "Install Focus",
        "50/50 Split",
        "Other",
    ]
    confidence: conint(ge=0, le=100)
    rationale: str = Field(..., min_length=1)
    evidence: List[EvidenceItem] = Field(..., min_items=1, max_items=3)


def get_model_classification_json_schema() -> str:
    """Return a compact JSON schema snippet for inclusion in the prompt text."""
    # Using a hand-authored snippet for clarity in prompts.
    return (
        '{\n'
        '  "classification_category": "Maintenance & Service Only|Install Focus|50/50 Split|Other",\n'
        '  "confidence": 0-100,\n'
        '  "rationale": "string",\n'
        '  "evidence": [\n'
        '    { "url": "string", "snippet": "string" },\n'
        '    { "url": "string", "snippet": "string" },\n'
        '    { "url": "string", "snippet": "string" }\n'
        '  ]\n'
        '}'
    )


