# PRD: Numerical Scoring Layer for Fire Protection Company Classification

## Introduction/Overview

This document outlines the requirements for implementing a numerical scoring layer on top of the existing fire protection company classification system. The current system successfully classifies companies using LLM-based categorization (e.g., "Maintenance & Service Only", "High Quality", etc.) but needs an additional layer that converts these categorical results into numerical scores for business prioritization and automated decision-making.

The feature will transform classification outputs into a 100-point scoring system with detailed breakdowns, enabling stakeholders to quickly identify and prioritize the most valuable prospect companies based on quantifiable business criteria.

## Goals

1. **Convert categorical classifications to numerical scores**: Transform existing LLM classification results into standardized 0-100 point scores
2. **Provide transparent scoring breakdown**: Offer detailed visibility into how each classification field contributes to the final score
3. **Enable automated business prioritization**: Allow stakeholders to sort, filter, and prioritize companies based on numerical scores
4. **Maintain system flexibility**: Implement configurable scoring rules that can be easily adjusted without code changes
5. **Preserve existing functionality**: Ensure backward compatibility with current classification pipeline and JSONL outputs

## User Stories

1. **As a sales manager**, I want to see numerical scores for each prospect company so that I can quickly identify the highest-value targets for outreach
2. **As a data analyst**, I want detailed score breakdowns so that I can understand which business characteristics drive company valuations
3. **As a business stakeholder**, I want configurable scoring weights so that I can adjust criteria importance based on changing business priorities
4. **As a system administrator**, I want the scoring to happen automatically after classification so that all outputs include both categorical and numerical results
5. **As a developer**, I want the scoring logic in a separate module so that I can easily modify business rules without affecting the core classification system

## Functional Requirements

### Core Scoring Requirements

1. **The system MUST calculate numerical scores** based on the 8 classification fields from existing LLM output:
   - `classification_category` (30 points max)
   - `website_quality` (20 points max) 
   - `mostly_does_maintenance_and_service` (10 points max)
   - `has_certifications_and_compliance_standards` (10 points max)
   - `has_multiple_service_territories` (10 points max)
   - `has_parent_company` (0 points base, -20 penalty)
   - `using_competitor_software` (10 points max)
   - `part_of_known_fire_protection_association` (10 points max)

2. **The system MUST implement the parent company penalty system**:
   - Independent companies (has_parent_company = "N/A"): No penalty
   - Companies with parent companies: -20 points from final score
   - Final scores can range from -20 to 100 points

3. **The system MUST output two new fields** in the JSONL:
   - `final_score`: Integer representing the final numerical score
   - `score_breakdown`: Object containing detailed scoring breakdown

4. **The system MUST load scoring configuration** from a YAML file containing:
   - Point values for each classification field value
   - Penalty rules
   - Field weights

5. **The system MUST integrate seamlessly** with existing classification pipeline:
   - Run immediately after each domain is classified
   - Preserve all existing JSONL fields
   - Maintain backward compatibility

### Scoring Logic Requirements

6. **Classification Category Scoring** (30 points maximum):
   - "Maintenance & Service Only": 30 points
   - "50/50 Split": 15 points
   - "Install Only": 10 points
   - "Other": 5 points
   - "Not Classifiable": 0 points

7. **Website Quality Scoring** (20 points maximum):
   - "High Quality": 20 points
   - "Average": 10 points
   - "Poor": 0 points

8. **Binary Field Scoring** (10 points each):
   - "yes" values: 10 points
   - "no" values: 0 points

9. **Text Field Scoring** (10 points each):
   - Any value other than "N/A": 10 points
   - "N/A" values: 0 points

### Technical Architecture Requirements

10. **The system MUST create a separate scoring module** (`scoring/numerical_scoring.py`) containing:
    - Core scoring calculation function
    - Configuration loading function
    - Score validation logic

11. **The system MUST create a configuration file** (`scoring/numerical_scoring_config.yaml`) containing:
    - All scoring rules and point values
    - Field mappings and weights
    - Penalty configurations

12. **The system MUST modify the API layer** to:
    - Call numerical scoring after LLM classification
    - Add new score fields to result objects
    - Maintain existing function signatures

13. **The system MUST update data models** to include:
    - `final_score` field as integer
    - `score_breakdown` field as dictionary
    - Proper field definitions in Pydantic models

## Non-Goals (Out of Scope)

1. **Historical score recalculation**: This feature will not automatically rescore existing records
2. **Score validation or logging**: No additional error handling or debug logging beyond basic functionality
3. **Machine learning optimization**: Scoring weights will be manually configured, not ML-optimized
4. **Real-time score updates**: Scores are calculated once during classification, not updated dynamically
5. **Score comparison analytics**: No built-in functionality for comparing scores across datasets
6. **User interface changes**: This is a backend-only feature with no frontend modifications

## Design Considerations

### Configuration Design
- Use YAML format for easy human editing
- Separate configuration from code for business flexibility
- Include clear comments explaining each scoring rule
- Validate configuration on startup

### Data Structure Design
- `score_breakdown` should include:
  - Individual field scores
  - Field contributions to total
  - Penalty applications
  - Final calculation summary

### Integration Design
- Minimize changes to existing code
- Use dependency injection for scoring function
- Ensure scoring failure doesn't break classification
- Maintain consistent error handling patterns

## Technical Considerations

### Performance
- Scoring calculation should be lightweight (sub-millisecond)
- Configuration should be loaded once and cached
- No database calls required for scoring logic

### Maintainability
- Scoring logic isolated in separate module
- Configuration-driven rules for easy business changes
- Clear separation between scoring and classification concerns
- Comprehensive documentation for future modifications

### Data Consistency
- All existing JSONL fields must be preserved exactly
- New fields must not conflict with existing field names
- Scoring must handle edge cases gracefully (missing fields, unexpected values)

## Success Metrics

1. **Functional Success**:
   - All classified records include accurate numerical scores
   - Score breakdowns correctly reflect individual field contributions
   - Configuration changes update scoring without code deployment

2. **Performance Success**:
   - No measurable impact on classification processing time
   - Scoring calculation completes in <1ms per record
   - Memory usage remains consistent with current levels

3. **Integration Success**:
   - Zero breaking changes to existing API endpoints
   - All existing JSONL fields preserved exactly
   - Backward compatibility maintained with existing consumers

## Open Questions

1. **Configuration validation**: Should the system validate configuration file format and values on startup, or fail gracefully during scoring?

2. **Score precision**: Should final scores be integers only, or allow decimal places for more precise ranking?

3. **Edge case handling**: How should the system handle unexpected classification values not defined in configuration?

4. **Migration strategy**: Should there be a separate script to add scores to existing JSONL files, or is forward-only scoring sufficient?

5. **Testing approach**: What level of unit testing is required for the scoring logic and configuration loading?