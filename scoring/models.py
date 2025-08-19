"""
Purpose: Shared Pydantic models for the scoring package.
Description: Centralizes the core data models that are used across API and CLI.
Key Functions/Classes: `Evidence`, `ClassificationResult`, `LabeledDatasetRecord`, `LabeledDatasetResult`.
Note: Now supports enriched HubSpot data with 40+ business fields including contact enrichment, geographic data, and company details.
Crawler fields: domain, aggregated_context, included_urls, html_keywords_found, length.
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
    html_keywords_found: List[str]
    length: Dict[str, Any]
    record_id: str
    
    # All enriched HubSpot CSV fields
    company_name: str = Field(alias="Company name")
    na_state: str = Field(alias="NA State")
    state_county: str = Field(alias="State/County")
    country: str = Field(alias="Country")
    company_domain_name: str = Field(alias="Company Domain Name")
    phone_number: str = Field(alias="Phone Number")
    company_owner: str = Field(alias="Company owner")
    lead_status: str = Field(alias="Lead Status")
    clay_score: str = Field(alias="Clay score")
    associated_note: str = Field(alias="Associated Note")
    current_software: str = Field(alias="Current Software")
    current_software_contract_end_date: str = Field(alias="Current Software Contract End Date")
    core_service: str = Field(alias="Core service")
    accounting_software_us: str = Field(alias="Accounting software (US)")
    industry: str = Field(alias="Industry_")
    client_use_case: str = Field(alias="Client Use Case")
    associated_note_ids: str = Field(alias="Associated Note IDs")
    perform_search: str = Field(alias="Perform Search")
    link_to_google_search: str = Field(alias="Link To Google Search")
    results_returned_count: str = Field(alias="Results Returned Count")
    serper_link: str = Field(alias="Serper Link")
    enrich_company: str = Field(alias="Enrich Company")
    founded: str = Field(alias="Founded")
    employee_count: str = Field(alias="Employee Count")
    website: str = Field(alias="Website")
    find_contacts_at_company: str = Field(alias="Find Contacts at Company")
    pic_1_name: str = Field(alias="PIC 1 Name")
    pic_1_title: str = Field(alias="PIC 1 TItle")
    pic_1_url: str = Field(alias="PIC 1 URL")
    pic_1_contact_info: str = Field(alias="PIC 1 Contact Info")
    pic_2_name: str = Field(alias="PIC 2 Name")
    pic_2_title: str = Field(alias="PIC 2 Title")
    pic_2_url: str = Field(alias="PIC 2 URL")
    pic_2_contact_info: str = Field(alias="PIC 2 Contact Info")
    find_contacts_at_company_2: str = Field(alias="Find Contacts at Company (2)")
    pic_3_name: str = Field(alias="PIC 3 Name")
    pic_3_title: str = Field(alias="PIC 3 Title")
    pic_3_url: str = Field(alias="PIC 3 URL")
    pic_3_contact_info: str = Field(alias="PIC 3 Contact Info")
    ceo_linkedin_url_2: str = Field(alias="CEO LinkedIn URL (2)")
    linkedin_url: str = Field(alias="Linkedin Url")
    
    class Config:
        populate_by_name = True


class LabeledDatasetResult(BaseModel):
    """Model for labeled dataset records with classification results appended."""
    # All original fields
    domain: str
    aggregated_context: str
    included_urls: List[str]
    html_keywords_found: List[str]
    length: Dict[str, Any]
    record_id: str
    
    # All enriched HubSpot CSV fields
    company_name: str = Field(alias="Company name")
    na_state: str = Field(alias="NA State")
    state_county: str = Field(alias="State/County")
    country: str = Field(alias="Country")
    company_domain_name: str = Field(alias="Company Domain Name")
    phone_number: str = Field(alias="Phone Number")
    company_owner: str = Field(alias="Company owner")
    lead_status: str = Field(alias="Lead Status")
    clay_score: str = Field(alias="Clay score")
    associated_note: str = Field(alias="Associated Note")
    current_software: str = Field(alias="Current Software")
    current_software_contract_end_date: str = Field(alias="Current Software Contract End Date")
    core_service: str = Field(alias="Core service")
    accounting_software_us: str = Field(alias="Accounting software (US)")
    industry: str = Field(alias="Industry_")
    client_use_case: str = Field(alias="Client Use Case")
    associated_note_ids: str = Field(alias="Associated Note IDs")
    perform_search: str = Field(alias="Perform Search")
    link_to_google_search: str = Field(alias="Link To Google Search")
    results_returned_count: str = Field(alias="Results Returned Count")
    serper_link: str = Field(alias="Serper Link")
    enrich_company: str = Field(alias="Enrich Company")
    founded: str = Field(alias="Founded")
    employee_count: str = Field(alias="Employee Count")
    website: str = Field(alias="Website")
    find_contacts_at_company: str = Field(alias="Find Contacts at Company")
    pic_1_name: str = Field(alias="PIC 1 Name")
    pic_1_title: str = Field(alias="PIC 1 TItle")
    pic_1_url: str = Field(alias="PIC 1 URL")
    pic_1_contact_info: str = Field(alias="PIC 1 Contact Info")
    pic_2_name: str = Field(alias="PIC 2 Name")
    pic_2_title: str = Field(alias="PIC 2 Title")
    pic_2_url: str = Field(alias="PIC 2 URL")
    pic_2_contact_info: str = Field(alias="PIC 2 Contact Info")
    find_contacts_at_company_2: str = Field(alias="Find Contacts at Company (2)")
    pic_3_name: str = Field(alias="PIC 3 Name")
    pic_3_title: str = Field(alias="PIC 3 Title")
    pic_3_url: str = Field(alias="PIC 3 URL")
    pic_3_contact_info: str = Field(alias="PIC 3 Contact Info")
    ceo_linkedin_url_2: str = Field(alias="CEO LinkedIn URL (2)")
    linkedin_url: str = Field(alias="Linkedin Url")
    
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


