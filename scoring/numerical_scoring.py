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


def calculate_numerical_score(classification_result: ClassificationResult) -> Dict[str, Any]:
    """
    Calculate numerical score and breakdown from classification result.
    
    Args:
        classification_result: The LLM classification result containing categorical values
        
    Returns:
        Dictionary containing:
        - final_score: Integer final score (-20 to 100)
        - score_breakdown: Dict with detailed scoring breakdown
    """
    config = get_scoring_config()
    
    scoring_rules = config["scoring_rules"]
    penalties = config["penalties"]
    field_weights = config["field_weights"]
    
    # Initialize score breakdown
    breakdown = {
        "field_scores": {},
        "penalties_applied": {},
        "base_score": 0,
        "final_score": 0
    }
    
    base_score = 0
    
    # 1. Classification Category (30 points max)
    category_value = classification_result.classification_category
    category_score = scoring_rules["classification_category"].get(category_value, 0)
    breakdown["field_scores"]["classification_category"] = {
        "value": category_value,
        "points": category_score,
        "max_points": field_weights["classification_category"]
    }
    base_score += category_score
    
    # 2. Website Quality (20 points max)
    quality_value = classification_result.website_quality
    quality_score = scoring_rules["website_quality"].get(quality_value, 0)
    breakdown["field_scores"]["website_quality"] = {
        "value": quality_value,
        "points": quality_score,
        "max_points": field_weights["website_quality"]
    }
    base_score += quality_score
    
    # 3. Maintenance & Service Focus (10 points max)
    maintenance_value = classification_result.mostly_does_maintenance_and_service
    maintenance_score = scoring_rules["mostly_does_maintenance_and_service"].get(maintenance_value, 0)
    breakdown["field_scores"]["mostly_does_maintenance_and_service"] = {
        "value": maintenance_value,
        "points": maintenance_score,
        "max_points": field_weights["mostly_does_maintenance_and_service"]
    }
    base_score += maintenance_score
    
    # 4-8. Text fields with binary scoring (10 points each if not N/A)
    text_fields = [
        "has_certifications_and_compliance_standards",
        "has_multiple_service_territories",
        "using_competitor_software",
        "part_of_known_fire_protection_association"
    ]
    
    for field_name in text_fields:
        # Get value from classification result, with fallback for missing fields
        field_value = getattr(classification_result, field_name, "N/A")
        
        # Check if value is N/A (case insensitive)
        is_na = field_value.upper() == "N/A"
        
        if field_name in scoring_rules["text_field_scoring"]:
            field_config = scoring_rules["text_field_scoring"][field_name]
            field_score = field_config["na_value"] if is_na else field_config["not_na_value"]
        else:
            # Fallback scoring for missing config
            field_score = 0 if is_na else 10
        
        breakdown["field_scores"][field_name] = {
            "value": field_value,
            "points": field_score,
            "max_points": field_weights.get(field_name, 10)
        }
        base_score += field_score
    
    breakdown["base_score"] = base_score
    
    # Apply parent company penalty
    parent_company_value = classification_result.has_parent_company
    parent_config = penalties["parent_company"]
    
    penalty_applied = 0
    if parent_company_value.upper() != parent_config["independent_value"]:
        # Company has parent company - apply penalty
        penalty_applied = parent_config["penalty_amount"]
        breakdown["penalties_applied"]["parent_company"] = {
            "reason": "Has parent company",
            "value": parent_company_value,
            "penalty": penalty_applied
        }
    else:
        breakdown["penalties_applied"]["parent_company"] = {
            "reason": "Independent company",
            "value": parent_company_value,
            "penalty": 0
        }
    
    final_score = base_score + penalty_applied
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
        return f"'{field_value}' scores {score} points out of 30 possible"
    
    elif field_name == "website_quality":
        score = scoring_rules["website_quality"].get(field_value, 0)
        return f"'{field_value}' website scores {score} points out of 20 possible"
    
    elif field_name == "mostly_does_maintenance_and_service":
        score = scoring_rules["mostly_does_maintenance_and_service"].get(field_value, 0)
        return f"Maintenance focus '{field_value}' scores {score} points out of 10 possible"
    
    elif field_name in scoring_rules.get("text_field_scoring", {}):
        is_na = field_value.upper() == "N/A"
        score = 0 if is_na else 10
        status = "no information found" if is_na else "information found"
        return f"{field_name.replace('_', ' ').title()}: {status} - {score} points out of 10 possible"
    
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
        required_sections = ["field_weights", "scoring_rules", "penalties", "validation"]
        for section in required_sections:
            if section not in config:
                return False
        
        # Check that field weights sum to expected total (100 before penalties)
        weights = config["field_weights"]
        total_weight = sum(weights.values())
        
        # Note: Parent company has 0 weight since it's penalty-only
        if total_weight != 100:
            return False
        
        return True
        
    except Exception:
        return False