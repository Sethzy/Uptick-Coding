# 🎯 Uptick Fire Protection Company Scoring System

## Overview

The Uptick scoring system evaluates fire protection companies using a combination of web crawling data and HubSpot business intelligence. It produces numerical scores (0-100) to assess company "fit" for business partnerships.

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Crawler Data  │    │   HubSpot CSV    │    │  Enriched Data  │
│    (JSONL)      │───▶│   (Business)     │───▶│     (JSONL)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Final Results  │◄───│  LLM Analysis    │◄───│  Scoring Engine │
│    (JSONL)      │    │ (Classification) │    │  (Numerical)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔄 Data Flow Process

### Phase 1: Data Enrichment
```bash
crawler_data.jsonl + hubspot_data.csv → enriched_data.jsonl
```

### Phase 2: LLM Classification
```bash
enriched_data.jsonl → classification_results.jsonl
```

### Phase 3: Numerical Scoring
```bash
classification_results.jsonl → final_scored_results.jsonl
```

## 📋 Input Data Sources

### 1. Crawler Data Fields
**Source**: Web crawling of company websites
```json
{
  "domain": "example.com",
  "aggregated_context": "Website content summary...",
  "included_urls": ["https://example.com/about", "..."],
  "html_keywords_found": ["fire", "protection", "sprinkler"],
  "length": {"total_chars": 15000},
  "record_id": "12345",
  "crawl_status": "completed",
  "failure_reason": null,
  "pages_visited": 8
}
```

### 2. HubSpot CSV Fields (43 fields)
**Source**: Business intelligence and contact enrichment
```csv
Record ID, Company name, NA State, State/County, Country, Company Domain Name, 
Phone Number, Company owner, Lead Status, Clay score, Associated Note, 
Current Software, Current Software Contract End Date, Core service, 
Accounting software (US), Industry_, Client Use Case, Associated Note IDs, 
Perform Search, Link To Google Search, Results Returned Count, Serper Link, 
Enrich Company, Official Linkedin Url, Founded, Employee Count, Website, 
Find Contacts at Company, PIC 1 Name, PIC 1 TItle, PIC 1 URL, 
PIC 1 Contact Info, PIC 2 Name, PIC 2 Title, PIC 2 URL, PIC 2 Contact Info, 
Find Contacts at Company (2), PIC 3 Name, PIC 3 Title, PIC 3 URL, 
PIC 3 Contact Info, CEO LinkedIn URL (2), Linkedin Url
```

## 🤖 LLM Classification Fields

The LLM analyzes enriched data and produces categorical assessments:

| Field | Purpose | Values |
|-------|---------|--------|
| `classification_category` | Primary business model | "Maintenance & Service Only", "50/50 Split", "Install Only", "Other", "Not Classifiable" |
| `rationale` | Explanation of classification | Free text reasoning |
| `website_quality` | Website professionalism | "High Quality", "Average", "Poor" |
| `mostly_does_maintenance_and_service` | Service focus | "yes", "no" |
| `full_list_of_services_offered` | Service scope | "Fire Protection Only", "Fire Protection and Other Services", "Other Services Only" |

### Non-Scored Classification Fields
*These fields are analyzed but NOT included in numerical scoring:*
- `has_certifications_and_compliance_standards`
- `has_multiple_service_territories`
- `has_parent_company`
- `using_competitor_software`
- `part_of_known_fire_protection_association`

## 🧮 Numerical Scoring System

### Scoring Formula (100 Points Maximum)

```
Total Score = Classification (50) + Website Quality (10) + Maintenance Focus (10) + 
              Services Offered (10) + Employee Count (10) + Find Contacts (10)
```

### Detailed Scoring Breakdown

#### 1. Classification Category (50 points) 🏆
**Most Important Factor** - Determines business model and revenue stability

| Category | Points | Rationale |
|----------|--------|-----------|
| Maintenance & Service Only | **50** | Stable recurring revenue, ideal partner |
| 50/50 Split | **30** | Diversified revenue streams |
| Install Only | **20** | Project-based, cyclical business |
| Other | **-10** | Specialized niche, penalty applied |
| Not Classifiable | **0** | Unknown business model, high risk |

#### 2. Website Quality (10 points) 💻
**Indicates** - Professional operations and market presence

| Quality Level | Points | Indicators |
|---------------|--------|------------|
| High Quality | **10** | Professional design, comprehensive content, modern tech |
| Average | **5** | Decent design, basic information, functional |
| Poor | **0** | Outdated design, limited content, poor UX |

#### 3. Maintenance & Service Focus (10 points) 🔧
**Indicates** - Recurring revenue model vs. project-based

| Focus | Points | Business Impact |
|-------|--------|----------------|
| Yes | **10** | Recurring revenue, stable cash flow |
| No | **0** | Project-based, potentially volatile |

#### 4. Full List of Services Offered (10 points) 🛠️
**Indicates** - Fire protection specialization vs. diversification

| Service Focus | Points | Strategic Value |
|---------------|--------|----------------|
| Fire Protection Only | **10** | Focused expertise, specialized market |
| Fire Protection + Other | **5** | Diversified but fire-focused |
| Other Services Only | **-10** | Not fire protection focused (penalty) |

#### 5. Employee Count (10 points) 👥
**Indicates** - Company size and operational capacity

| Employee Range | Points | Business Scale |
|----------------|--------|----------------|
| 30+ employees | **10** | Large operation, significant capacity |
| 10-29 employees | **5** | Medium operation, moderate capacity |
| <10 or blank | **0** | Small/unknown operation |

#### 6. Find Contacts at Company (10 points) 📞
**Indicates** - Contact accessibility and sales potential

| Contact Discovery | Points | Sales Opportunity |
|-------------------|--------|-------------------|
| Found 2+ People | **10** | Multiple contact points, higher success rate |
| Found 1 Person or blank | **0** | Limited contact o
ptions |

### Score Range Examples

#### Perfect Score (100 points)
```json
{
  "classification_category": "Maintenance & Service Only",  // 50 pts
  "website_quality": "High Quality",                       // 10 pts
  "mostly_does_maintenance_and_service": "yes",            // 10 pts
  "full_list_of_services_offered": "Fire Protection Only", // 10 pts
  "employee_count": "45",                                   // 10 pts
  "find_contacts_at_company": "Found 3 People",           // 10 pts
  "final_score": 100
}
```

#### Low Score (-10 points)
```json
{
  "classification_category": "Other",                      // -10 pts
  "website_quality": "Poor",                              // 0 pts
  "mostly_does_maintenance_and_service": "no",            // 0 pts
  "full_list_of_services_offered": "Other Services Only", // -10 pts
  "employee_count": "",                                    // 0 pts
  "find_contacts_at_company": "",                         // 0 pts
  "final_score": -10
}
```

## 📤 Final Output Structure

### Complete Output Record (LabeledDatasetResult)
The final JSONL output contains **70+ fields** combining all data sources:

```json
{
  // === CRAWLER DATA ===
  "domain": "example.com",
  "aggregated_context": "Website content...",
  "included_urls": ["https://example.com/about"],
  "html_keywords_found": ["fire", "protection"],
  "length": {"total_chars": 15000},
  "record_id": "12345",
  "crawl_status": "completed",
  "failure_reason": null,
  "pages_visited": 8,
  
  // === HUBSPOT BUSINESS DATA (43 fields) ===
  "Company name": "Example Fire Protection",
  "NA State": "CA",
  "State/County": "Los Angeles",
  "Country": "United States",
  "Company Domain Name": "example.com",
  "Phone Number": "555-123-4567",
  "Company owner": "John Smith",
  "Lead Status": "New",
  "Clay score": "8",
  "Employee Count": "45",
  "Find Contacts at Company": "Found 3 People",
  "Official Linkedin Url": "https://linkedin.com/company/example",
  "Founded": "2010",
  "Website": "https://example.com",
  // ... (remaining 30+ HubSpot fields)
  
  // === LLM CLASSIFICATION RESULTS ===
  "classification_category": "Maintenance & Service Only",
  "rationale": "Company focuses primarily on maintenance contracts...",
  "website_quality": "High Quality",
  "mostly_does_maintenance_and_service": "yes",
  "has_certifications_and_compliance_standards": "NFPA certified",
  "has_multiple_service_territories": "yes",
  "has_parent_company": "N/A",
  "full_list_of_services_offered": "Fire Protection Only",
  "using_competitor_software": "N/A",
  "part_of_known_fire_protection_association": "NAFED member",
  
  // === NUMERICAL SCORING ===
  "final_score": 100,
  "score_breakdown": {
    "field_scores": {
      "classification_category": {
        "value": "Maintenance & Service Only",
        "points": 50,
        "max_points": 50
      },
      "website_quality": {
        "value": "High Quality", 
        "points": 10,
        "max_points": 10
      },
      // ... (breakdown for all 6 scored fields)
    },
    "base_score": 100,
    "penalties_applied": {},
    "final_score": 100
  }
}
```

## 🚀 Usage Commands

### Quick Scoring Workflow
```bash
# 1. Enrich crawler data with HubSpot CSV
./quick_score.sh enrich crawl_data.jsonl uptick-csvs/enriched-hutbpot-tam-v2.csv

# 2. Score the enriched data
./quick_score.sh score crawl_data_enriched.jsonl

# 3. Results saved to crawl_data_enriched_scored.jsonl
```

### Advanced Usage
```bash
# Score with custom model and output file
./quick_score.sh score input.jsonl output.jsonl qwen/qwen3-30b-a3b

# Combined enrichment and scoring
./quick_score.sh score crawl_data.jsonl results.jsonl qwen/qwen3-30b-a3b uptick-csvs/enriched-hutbpot-tam-v2.csv
```

## 📊 Scoring Statistics

### Score Distribution Expectations
- **90-100**: Ideal fire protection partners (maintenance-focused, professional)
- **70-89**: Good candidates (mixed models, solid operations)
- **50-69**: Average prospects (install-focused or quality concerns)
- **30-49**: Below average (limited fire protection focus)
- **0-29**: Poor fit (minimal fire protection business)
- **Negative**: Actively excluded (non-fire protection companies)

### Key Success Indicators
1. **High Classification Score (50 pts)**: Maintenance & service focus
2. **Professional Web Presence (10 pts)**: Quality website indicates investment
3. **Service-Oriented Business (10 pts)**: Recurring revenue model
4. **Fire Protection Specialization (10 pts)**: Industry expertise
5. **Adequate Scale (10 pts)**: Sufficient employee base
6. **Contact Accessibility (10 pts)**: Sales opportunity viability

## 🔧 Configuration Files

### Key Files
- `numerical_scoring_config.yaml`: Scoring rules and weights
- `models.py`: Data structure definitions
- `numerical_scoring.py`: Scoring calculation logic
- `enrich_crawler_with_hubspot.py`: Data enrichment process

### Customization
The scoring system is fully configurable through `numerical_scoring_config.yaml`. Field weights, scoring thresholds, and validation rules can be adjusted without code changes.

---

*This scoring system enables data-driven evaluation of fire protection companies, combining web intelligence with business data to identify optimal partnership opportunities.*