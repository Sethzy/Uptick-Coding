"""
Purpose: Numerical scoring module for fire protection company classification results.
Description: Converts categorical LLM classification results into numerical scores (0-100 scale).
Key Functions: calculate_numerical_score, get_scoring_config, apply_scoring_rules.
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional
from pathlib import Path

import yaml

from .models import ClassificationResult


# Global config cache
_scoring_config: Optional[Dict[str, Any]] = None


def get_scoring_config() -> Dict[str, Any]:
    """Load and cache the numerical scoring configuration from YAML file."""
    global _scoring_config
    
    if _scoring_config is None:
        config_path = Path(__file__).parent / "numerical_scoring_config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Scoring configuration not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            _scoring_config = yaml.safe_load(f)
    
    return _scoring_config


def calculate_employee_count_score(employee_count_value: str, scoring_rules: Dict[str, Any]) -> int:
    """
    Calculate score for employee count field.
    
    Args:
        employee_count_value: String value from Employee Count field
        scoring_rules: Scoring configuration rules
        
    Returns:
        Score points (0, 10, or 20)
    """
    import re
    
    if not employee_count_value or employee_count_value.strip() == "":
        return scoring_rules["employee_count_scoring"]["blank_value"]
    
    # Extract numeric value from string
    try:
        # Look for numeric patterns in the string
        numbers = re.findall(r'\d+', str(employee_count_value))
        if numbers:
            count = int(numbers[0])  # Take first number found
            if 0 <= count <= 20:
                return scoring_rules["employee_count_scoring"]["range_0_19"]
            elif count >= 21:
                return scoring_rules["employee_count_scoring"]["range_21_plus"]
    except (ValueError, IndexError):
        pass
    
    # If we can't parse a valid number, treat as blank
    return scoring_rules["employee_count_scoring"]["blank_value"]


def calculate_find_contacts_score(find_contacts_value: str, scoring_rules: Dict[str, Any]) -> int:
    """
    Calculate score for find contacts field.
    
    Args:
        find_contacts_value: String value from Find Contacts at Company field
        scoring_rules: Scoring configuration rules
        
    Returns:
        Score points (0 or 10)
    """
    import re
    
    if not find_contacts_value or find_contacts_value.strip() == "":
        return scoring_rules["find_contacts_scoring"]["no_contacts"]
    
    # Check for "no profile found" or "company not found" patterns
    if "no profile found" in find_contacts_value.lower() or "company not found" in find_contacts_value.lower():
        return scoring_rules["find_contacts_scoring"]["no_contacts"]
    
    # Look for "Found X People" pattern
    found_pattern = re.search(r'found\s+(\d+)\s+people', find_contacts_value.lower())
    if found_pattern:
        count = int(found_pattern.group(1))
        if count >= 1:  # Changed from > 1 to >= 1 (1+ people = 10 points)
            return scoring_rules["find_contacts_scoring"]["found_contacts"]
    
    # Default to no contacts if pattern doesn't match
    return scoring_rules["find_contacts_scoring"]["no_contacts"]


def calculate_numerical_score(classification_result: ClassificationResult) -> Dict[str, Any]:
    """
    Calculate numerical score and breakdown from classification result.
    
    Args:
        classification_result: The LLM classification result containing categorical values
        
    Returns:
        Dictionary containing:
        - final_score: Integer final score (-40 to 100)
        - score_breakdown: Dict with detailed scoring breakdown
    """
    config = get_scoring_config()
    
    scoring_rules = config["scoring_rules"]
    field_weights = config["field_weights"]
    
    # Initialize score breakdown
    breakdown = {
        "field_scores": {},
        "penalties_applied": {},
        "base_score": 0,
        "final_score": 0
    }
    
    base_score = 0
    
    # 1. Classification Category (50 points max)
    category_value = classification_result.classification_category
    category_score = scoring_rules["classification_category"].get(category_value, 0)
    breakdown["field_scores"]["classification_category"] = {
        "value": category_value,
        "points": category_score,
        "max_points": field_weights["classification_category"]
    }
    base_score += category_score
    
    # 2. Website Quality (10 points max)
    quality_value = classification_result.website_quality
    quality_score = scoring_rules["website_quality"].get(quality_value, 0)
    breakdown["field_scores"]["website_quality"] = {
        "value": quality_value,
        "points": quality_score,
        "max_points": field_weights["website_quality"]
    }
    base_score += quality_score
    
    # 3. Full List of Services Offered (10 points max) - Special categorical scoring
    services_value = getattr(classification_result, "full_list_of_services_offered", "Not Assessed")
    # The field name in the test data doesn't exactly match the config keys
    # Let's try to find a match by checking if the value contains the key phrases
    services_score = 0
    if "Fire Protection Only" in services_value:
        services_score = 10
    elif "Fire Protection and Other Services" in services_value:
        services_score = 5
    elif "Other Services Only" in services_value:
        services_score = -10
    
    breakdown["field_scores"]["full_list_of_services_offered"] = {
        "value": services_value,
        "points": services_score,
        "max_points": field_weights["full_list_of_services_offered"]
    }
    base_score += services_score
    
    # Text fields scoring has been removed for simplified scoring
    # The following fields are no longer scored but remain in output data:
    # - has_certifications_and_compliance_standards
    # - has_multiple_service_territories
    # - using_competitor_software
    # - part_of_known_fire_protection_association
    # - mostly_does_maintenance_and_service
    
    # 4. Employee Count Scoring (20 points max)
    employee_count_value = getattr(classification_result, "employee_count", "")
    employee_count_score = calculate_employee_count_score(employee_count_value, scoring_rules)
    breakdown["field_scores"]["employee_count"] = {
        "value": employee_count_value,
        "points": employee_count_score,
        "max_points": field_weights.get("employee_count", 20)
    }
    base_score += employee_count_score
    
    # 5. Find Contacts Scoring (10 points max)
    find_contacts_value = getattr(classification_result, "find_contacts_at_company", "")
    find_contacts_score = calculate_find_contacts_score(find_contacts_value, scoring_rules)
    breakdown["field_scores"]["find_contacts_at_company"] = {
        "value": find_contacts_value,
        "points": find_contacts_score,
        "max_points": field_weights.get("find_contacts_at_company", 10)
    }
    base_score += find_contacts_score
    
    breakdown["base_score"] = base_score
    
    # No penalties applied in simplified scoring system
    breakdown["penalties_applied"] = {}
    
    final_score = base_score
    breakdown["final_score"] = final_score
    
    return {
        "final_score": final_score,
        "score_breakdown": breakdown
    }


def apply_scoring_to_result(classification_result: ClassificationResult) -> Dict[str, Any]:
    """
    Apply numerical scoring to a classification result and return enhanced result.
    
    Args:
        classification_result: The classification result to score
        
    Returns:
        Dictionary with all original fields plus final_score and score_breakdown
    """
    # Calculate numerical score
    scoring_result = calculate_numerical_score(classification_result)
    
    # Convert classification result to dict and add scoring fields
    result_dict = classification_result.dict()
    result_dict.update(scoring_result)
    
    return result_dict


def get_field_score_explanation(field_name: str, field_value: str) -> str:
    """
    Get human-readable explanation for why a field received its score.
    
    Args:
        field_name: Name of the classification field
        field_value: Value of the field
        
    Returns:
        Human-readable explanation string
    """
    config = get_scoring_config()
    scoring_rules = config["scoring_rules"]
    
    if field_name == "classification_category":
        score = scoring_rules["classification_category"].get(field_value, 0)
        max_points = config["field_weights"]["classification_category"]
        return f"'{field_value}' scores {score} points out of {max_points} possible"
    
    elif field_name == "website_quality":
        score = scoring_rules["website_quality"].get(field_value, 0)
        max_points = config["field_weights"]["website_quality"]
        return f"'{field_value}' website scores {score} points out of {max_points} possible"
    
    
    elif field_name == "full_list_of_services_offered":
        # Use the same logic as the scoring function
        score = 0
        if "Fire Protection Only" in field_value:
            score = 10
        elif "Fire Protection and Other Services" in field_value:
            score = 5
        elif "Other Services Only" in field_value:
            score = -10
        
        max_points = config["field_weights"]["full_list_of_services_offered"]
        return f"Services '{field_value}' scores {score} points out of {max_points} possible"
    
    elif field_name in ["has_certifications_and_compliance_standards", "has_multiple_service_territories", 
                        "using_competitor_software", "part_of_known_fire_protection_association", "has_parent_company",
                        "mostly_does_maintenance_and_service"]:
        return f"{field_name.replace('_', ' ').title()}: Field removed from scoring but remains in output data"
    
    elif field_name == "employee_count":
        score = calculate_employee_count_score(field_value, scoring_rules)
        max_points = config["field_weights"].get("employee_count", 20)
        if not field_value or field_value.strip() == "":
            reason = "no employee count provided"
        else:
            import re
            numbers = re.findall(r'\d+', str(field_value))
            if numbers:
                count = int(numbers[0])
                if 0 <= count <= 20:
                    reason = f"{count} employees (0-20 range)"
                elif count >= 21:
                    reason = f"{count} employees (21+ range)"
            else:
                reason = "invalid employee count format"
        return f"Employee Count: {reason} - {score} points out of {max_points} possible"
    
    elif field_name == "find_contacts_at_company":
        score = calculate_find_contacts_score(field_value, scoring_rules)
        max_points = config["field_weights"].get("find_contacts_at_company", 10)
        if not field_value or field_value.strip() == "":
            reason = "no contact information"
        elif "no profile found" in field_value.lower() or "company not found" in field_value.lower():
            reason = "no profiles found"
        else:
            import re
            found_pattern = re.search(r'found\s+(\d+)\s+people', field_value.lower())
            if found_pattern:
                count = int(found_pattern.group(1))
                reason = f"found {count} contact{'s' if count != 1 else ''} (1+ contacts = 10 points)"
            else:
                reason = "contact search performed but unclear results"
        return f"Find Contacts: {reason} - {score} points out of {max_points} possible"
    
    else:
        return f"Unknown field: {field_name}"


def validate_scoring_config() -> bool:
    """
    Validate that the scoring configuration is properly formatted.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        config = get_scoring_config()
        
        # Check required sections exist
        required_sections = ["field_weights", "scoring_rules", "validation"]
        for section in required_sections:
            if section not in config:
                return False
        
        # Check that field weights sum to expected total (100 points)
        weights = config["field_weights"]
        total_weight = sum(weights.values())
        
        if total_weight != 100:
            return False
        
        return True
        
    except Exception:
        return False