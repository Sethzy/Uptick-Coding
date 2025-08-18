"""
Purpose: Shared Pydantic models for the scoring package.
Description: Centralizes the core data models that are used across API and CLI.
Key Functions/Classes: `Evidence`, `ClassificationResult`, `LabeledDatasetRecord`, `LabeledDatasetResult`.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    url: str
    snippet: str


class ClassificationResult(BaseModel):
    domain: str
    classification_category: str
    rationale: str
    website_quality: str
    mostly_does_maintenance_and_service: str
    has_certifications_and_compliance_standards: str
    has_multiple_service_territories: str
    has_parent_company: str
    record_id: Optional[str] = None


class LabeledDatasetRecord(BaseModel):
    """Model for labeled dataset records with all original fields preserved."""
    domain: str
    aggregated_context: str
    included_urls: List[str]
    overflow: bool
    length: Dict[str, Any]
    record_id: str
    # Additional fields from the labeled dataset
    # Using Field with alias to handle spaces and special characters in field names
    lead_status: str = Field(alias="Lead Status")
    clay_score: str = Field(alias="Clay score")
    associated_note: str = Field(alias="Associated Note")
    current_software: str = Field(alias="Current Software")
    core_service: str = Field(alias="Core service")
    
    class Config:
        populate_by_name = True


class LabeledDatasetResult(BaseModel):
    """Model for labeled dataset records with classification results appended."""
    # All original fields
    domain: str
    aggregated_context: str
    included_urls: List[str]
    overflow: bool
    length: Dict[str, Any]
    record_id: str
    lead_status: str = Field(alias="Lead Status")
    clay_score: str = Field(alias="Clay score")
    associated_note: str = Field(alias="Associated Note")
    current_software: str = Field(alias="Current Software")
    core_service: str = Field(alias="Core service")
    
    # New classification fields
    classification_category: str
    rationale: str
    website_quality: str
    mostly_does_maintenance_and_service: str
    has_certifications_and_compliance_standards: str
    has_multiple_service_territories: str
    has_parent_company: str
    
    class Config:
        populate_by_name = True


