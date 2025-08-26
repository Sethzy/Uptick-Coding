#!/usr/bin/env python3
"""
Re-score sample data with the updated scoring system that includes mostly_does_maintenance_and_service
"""

import json
from scoring.models import ClassificationResult  
from scoring.numerical_scoring import calculate_numerical_score

def rescore_file(input_file, output_file):
    """Re-score existing classification results with updated scoring system"""
    rescored_records = []
    
    with open(input_file, 'r') as f:
        for line in f:
            record = json.loads(line)
            
            # Create ClassificationResult object from the existing record
            classification_result = ClassificationResult(
                domain=record['domain'],
                classification_category=record['classification_category'],
                rationale=record['rationale'],
                website_quality=record['website_quality'],
                mostly_does_maintenance_and_service=record['mostly_does_maintenance_and_service'],
                has_certifications_and_compliance_standards=record['has_certifications_and_compliance_standards'],
                has_multiple_service_territories=record['has_multiple_service_territories'],
                has_parent_company=record['has_parent_company'],
                full_list_of_services_offered=record['full_list_of_services_offered'],
                services_detailed_list=record.get('services_detailed_list', 'N/A'),
                using_competitor_software=record.get('using_competitor_software', 'N/A'),
                part_of_known_fire_protection_association=record.get('part_of_known_fire_protection_association', 'N/A'),
                record_id=record.get('record_id'),
                employee_count=record.get('employee_count', record.get('Employee Count', '')),
                find_contacts_at_company=record.get('find_contacts_at_company', record.get('Find Contacts at Company', ''))
            )
            
            # Calculate new numerical score
            scoring_result = calculate_numerical_score(classification_result)
            
            # Update the record with new scoring
            record['final_score'] = scoring_result['final_score']
            record['score_breakdown'] = scoring_result['score_breakdown']
            
            rescored_records.append(record)
    
    # Write rescored data to output file
    with open(output_file, 'w') as f:
        for record in rescored_records:
            f.write(json.dumps(record) + '\n')
    
    print(f"Rescored {len(rescored_records)} records")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    # Show scoring summary
    scores = [r['final_score'] for r in rescored_records]
    print(f"\nNew Scoring Summary:")
    print(f"Average: {sum(scores)/len(scores):.1f}")
    print(f"Range: {min(scores)} - {max(scores)}")
    
    # Show maintenance scoring breakdown
    maintenance_yes = [r for r in rescored_records if r['mostly_does_maintenance_and_service'] == 'yes']
    maintenance_no = [r for r in rescored_records if r['mostly_does_maintenance_and_service'] == 'no']
    
    print(f"\nMaintenance Field Analysis:")
    print(f"  'yes': {len(maintenance_yes)} companies (+10 points each)")
    print(f"  'no': {len(maintenance_no)} companies (+0 points each)")

if __name__ == "__main__":
    rescore_file(
        'crawl-runs/sample_2_domains_enriched_scored.jsonl',
        'crawl-runs/sample_2_domains_enriched_scored_updated.jsonl'
    )