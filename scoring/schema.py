"""
Purpose: Typed schemas for LLM scoring inputs/outputs.
Description: Defines strict Pydantic models for model responses and helpers to access JSON schema text for prompts.
Key Functions/Classes: ModelClassification, get_model_classification_json_schema.
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
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
    other_sublabel: Optional[str] = Field(
        default=None,
        description="Short noun phrase (3-6 words) naming the 'Other' subcategory (e.g., 'Security company').",
    )
    other_sublabel_definition: Optional[str] = Field(
        default=None,
        description="Concise definition (2-3 sentences) explaining the sublabel for 'Other'.",
    )

    @field_validator("other_sublabel")
    @classmethod
    def _validate_other_sublabel(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        text = value.strip()
        word_count = len([w for w in re.split(r"\s+", text) if w])
        if word_count < 3 or word_count > 6:
            raise ValueError("other_sublabel must be 3-6 words")
        return text

    @field_validator("other_sublabel_definition")
    @classmethod
    def _validate_other_sublabel_definition(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        text = value.strip()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if len(sentences) < 2 or len(sentences) > 3:
            raise ValueError("other_sublabel_definition must be 2-3 sentences")
        return text

    @model_validator(mode="after")
    def _enforce_other_fields(self) -> "ModelClassification":
        if self.classification_category == "Other":
            if not self.other_sublabel or not self.other_sublabel_definition:
                raise ValueError("For 'Other', other_sublabel and other_sublabel_definition are required")
        else:
            # Normalize away these fields when not Other
            try:
                self.other_sublabel = None  # type: ignore[assignment]
                self.other_sublabel_definition = None  # type: ignore[assignment]
            except Exception:
                pass
        return self

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
        '  "other_sublabel": "string (3-6 words, required when classification_category=\"Other\")",\n'
        '  "other_sublabel_definition": "string (2-3 sentences, required when classification_category=\"Other\")"\n'
        '}'
    )


