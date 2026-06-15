# Fire Protection Company Scoring Prompt Template

This document shows how to use the scoring system prompt for fire protection companies.

## Complete JSON Prompt

```json
{
  "model": "qwen/qwen3-30b-a3b-thinking-2507",
  "messages": [
    {
      "role": "system",
      "content": "You are a strict classifier. Output ONLY valid JSON per the schema."
    },
    {
      "role": "user",
      "content": "You are a scoring system for fire protection companies. Given a classification result in JSON format, you must calculate a numerical score from 0-100 based on specific scoring rules.\n\n**SCORING RULES:**\n\n1. **Classification Category (40 points max):**\n   - \"Maintenance & Service Only\": 40 points\n   - \"50/50 Split\": 30 points\n   - \"Install Only\": 0 points\n   - \"Other\": 0 points\n   - \"Not Classifiable\": 0 points\n\n2. **Website Quality (10 points max):**\n   - \"High Quality\": 10 points\n   - \"Average\": 5 points\n   - \"Poor\": 0 points\n\n3. **Services Category (20 points max):**\n   - If contains \"Fire Protection Only\": 20 points\n   - If contains \"Fire Protection and Other Services\": 10 points\n   - If contains \"Other Services Only\": 0 points\n\n4. **Employee Count (20 points max):**\n   - Extract the number from the employee_count field\n   - If blank/empty/\"N/A\": 0 points\n   - If 0-10 employees: 0 points\n   - If 11-50 employees: 10 points\n   - If 51+ employees: 20 points\n\n5. **Find Contacts (10 points max):**\n   - Extract the number from the find_contacts_at_company field\n   - If blank/empty/\"N/A\": 0 points\n   - If 0 contacts found: 0 points\n   - If 1 contact found: 5 points\n   - If 2+ contacts found: 10 points\n\n**INPUT TO SCORE:**\n\n
      
      
      
      {\n  \"classification_category\": \"Other\",\n  \"classification_category_rationale\": \"The company operates a retirement system for firefighters, providing benefits like retirement, disability, death, and survivor coverage. The website contains no mention of fire protection services, installations, or maintenance, and the services are unrelated to fire protection systems.\",\n  \"website_quality\": \"Average\",\n  \"mostly_does_maintenance_and_service\": \"no\",\n  \"has_certifications_and_compliance_standards\": \"N/A\",\n  \"has_multiple_service_territories\": \"N/A\",\n  \"has_parent_company\": \"N/A\",\n  \"services_category\": \"Other Services Only\",\n  \"services_detailed_list\": \"Retirement benefits, Disability benefits, Death benefits, Survivor benefits\",\n  \"employee_count\": \"1\",\n  \"find_contacts_at_company\": \"77\"\n}
      
      \n\n
      
      
      
      **EXAMPLE OUTPUT FORMAT:**\n\n{\n  \"final_score\": 90,\n  \"score_breakdown\": {\n    \"classification_category\": {\"value\": \"Maintenance & Service Only\", \"points\": 40, \"max_points\": 40},\n    \"website_quality\": {\"value\": \"High Quality\", \"points\": 10, \"max_points\": 10},\n    \"services_category\": {\"value\": \"Fire Protection Only\", \"points\": 20, \"max_points\": 20},\n    \"employee_count\": {\"value\": \"25\", \"points\": 10, \"max_points\": 20},\n    \"find_contacts_at_company\": {\"value\": \"8\", \"points\": 10, \"max_points\": 10}\n  }\n}"
    }
  ],
  "temperature": 0
}
```

## How to Use

1. **Copy the complete JSON above**
2. **Replace the INPUT TO SCORE section** with your company data
3. **Send to the API**

## What to Replace

Replace this entire JSON object in the "INPUT TO SCORE" section:

```json
{
  "classification_category": "Other",
  "classification_category_rationale": "...",
  "website_quality": "Average",
  "mostly_does_maintenance_and_service": "no",
  "has_certifications_and_compliance_standards": "N/A",
  "has_multiple_service_territories": "N/A",
  "has_parent_company": "N/A",
  "services_category": "Other Services Only",
  "services_detailed_list": "...",
  "employee_count": "1",
  "find_contacts_at_company": "77"
}
```

With your new company data, keeping the same field structure.

## Expected Score for Sample Input

For the sample input provided:
- Classification Category: "Other" → 0 points
- Website Quality: "Average" → 5 points  
- Services Category: "Other Services Only" → 0 points
- Employee Count: "1" → 0 points (0-10 range)
- Find Contacts: "77" → 10 points (2+ contacts)

**Expected Final Score: 15/100**