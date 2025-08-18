# Numerical Scoring System - Output Mapping

## Overview

This document maps all possible outputs from the LLM scoring system to enable numerical score assignment. Each field has specific possible values that can be assigned numerical scores based on business criteria.

## Field-by-Field Output Mapping

### 1. Classification Category

**Field:** `classification_category`  
**Type:** Categorical (5 possible values)

| Output Value                   | Description                                                                                    | Business Significance                                     |
| ------------------------------ | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| `"Maintenance & Service Only"` | Companies focused exclusively on ongoing upkeep and repair of existing fire protection systems | High recurring revenue, stable business model             |
| `"Install Only"`               | Companies engaged in design and installation of new fire protection systems                    | Project-based, high-value contracts, cyclical business    |
| `"50/50 Split"`                | Balanced business model between new installations and ongoing service/maintenance              | Diversified revenue streams, most valuable business model |
| `"Other"`                      | Specialized fire protection services not fitting other categories                              | Niche market, specialized expertise                       |
| `"Not Classifiable"`           | Website data insufficient or contains no useful business information                           | Unknown business model, high risk                         |

---

### 2. Website Quality

**Field:** `website_quality`  
**Type:** Categorical (3 possible values)

| Output Value     | Description                                                                                      | Business Significance                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| `"Poor"`         | 1 page, basic placeholder, minimal content, "Coming Soon" sites                                  | Low investment in online presence, potential resource constraints        |
| `"Average"`      | 1-2 pages, basic company info, some service descriptions, functional but minimal                 | Moderate online investment, basic digital maturity                       |
| `"High Quality"` | 3+ pages, comprehensive website with multiple sections, detailed content, strong online presence | High digital investment, professional operations, strong market presence |

---

### 3. Maintenance & Service Focus

**Field:** `mostly_does_maintenance_and_service`  
**Type:** Binary (2 possible values)

| Output Value | Description                                                                                | Business Significance                                                |
| ------------ | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| `"yes"`      | Company primarily focuses on ongoing upkeep and repair of existing fire protection systems | Recurring revenue model, stable customer base, predictable cash flow |
| `"no"`       | Company does NOT primarily focus on maintenance and service                                | Project-based or specialized services, potentially higher volatility |

---

### 4. Certifications and Compliance Standards

**Field:** `has_certifications_and_compliance_standards`  
**Type:** Text with common patterns

| Output Pattern                  | Description                                         | Business Significance                                   |
| ------------------------------- | --------------------------------------------------- | ------------------------------------------------------- |
| `"N/A"`                         | No certifications or compliance standards mentioned | No professional credentials, potential quality concerns |
| `"State licenses"`              | State-issued business or technician licenses        | Regulatory compliance, professional standards           |
| `"Manufacturer certifications"` | Equipment manufacturer certifications               | Technical expertise, vendor relationships               |
| `"Technician credentials"`      | Individual technician certifications                | Skilled workforce, professional development             |
| `"NFPA standards"`              | NFPA standards compliance (25, 72, 13)              | Industry best practices, safety compliance              |
| `"UL standards"`                | Underwriters Laboratories standards compliance      | Safety certification, quality assurance                 |
| `"Multiple certifications"`     | Multiple types of certifications mentioned          | High professional standards, comprehensive compliance   |
| `"Code compliance"`             | Building code or fire code compliance               | Regulatory adherence, safety standards                  |

---

### 5. Service Territory Coverage

**Field:** `has_multiple_service_territories`  
**Type:** Text with common patterns

| Output Pattern        | Description                                    | Business Significance                               |
| --------------------- | ---------------------------------------------- | --------------------------------------------------- |
| `"N/A"`               | Single location, no multi-territory operations | Local market focus, limited growth potential        |
| `"2-3 states"`        | Multi-state but regional coverage              | Regional expansion, moderate growth                 |
| `"5+ states"`         | Significant multi-state coverage               | Strong regional presence, good growth trajectory    |
| `"National coverage"` | Operations across multiple regions nationally  | Large-scale operations, significant market presence |
| `"Multiple offices"`  | Multiple physical locations mentioned          | Operational scale, market penetration               |
| `"Regional branches"` | Branch office network                          | Structured growth, operational efficiency           |

---

### 6. Parent Company Status

**Field:** `has_parent_company`  
**Type:** Text with common patterns

| Output Pattern                | Description                        | Business Significance                                  |
| ----------------------------- | ---------------------------------- | ------------------------------------------------------ |
| `"N/A"`                       | No parent company mentioned        | Independent company, full decision-making autonomy     |
| `"Pye Barker"`                | Part of Pye Barker family          | Large established network, potential resources         |
| `"API Group"`                 | Part of API Group                  | Industry consolidation, potential scale advantages     |
| `"Summit Companies"`          | Part of Summit Companies           | Regional consolidation, market presence                |
| `"Sciens Building Solutions"` | Part of Sciens                     | Building services integration, cross-selling potential |
| `"Cintas"`                    | Part of Cintas                     | Major corporate backing, significant resources         |
| `"Guardian Fire Protection"`  | Part of Guardian network           | Fire protection specialization, industry focus         |
| `"Hiller Fire"`               | Part of Hiller Fire                | Regional fire protection network                       |
| `"Impact Fire"`               | Part of Impact Fire                | Fire protection consolidation                          |
| `"Fortis Fire & Safety"`      | Part of Fortis                     | Safety services integration                            |
| `"Zeus Fire & Security"`      | Part of Zeus                       | Fire and security integration                          |
| `"Other parent company"`      | Different parent company mentioned | Corporate backing, but unknown scale/benefits          |

---

### 7. Using Competitor Software

**Field:** `using_competitor_software`  
**Type:** Text with common patterns

| Output Pattern                | Description                             | Business Significance                                |
| ----------------------------- | --------------------------------------- | ---------------------------------------------------- |
| `"N/A"`                       | No competitor software mentioned        | No known competitive software usage                  |
| `"BuildingReports.com"`       | Using BuildingReports.com platform      | Competitor software adoption, market awareness       |
| `"InspectPoint"`              | Using InspectPoint.com platform         | Competitor software adoption, market awareness       |
| `"BuildOps"`                  | Using BuildOps.com platform             | Competitor software adoption, market awareness       |
| `"ServiceTrade"`              | Using ServiceTrade.com platform         | Competitor software adoption, market awareness       |
| `"Multiple platforms"`        | Using multiple competitor platforms     | High market awareness, multiple software investments |
| `"Other competitor software"` | Different competitor software mentioned | Competitor software adoption, market awareness       |

---

### 8. Part of Known Fire Protection Association

**Field:** `part_of_known_fire_protection_association`  
**Type:** Text with common patterns

| Output Pattern            | Description                                         | Business Significance                                 |
| ------------------------- | --------------------------------------------------- | ----------------------------------------------------- |
| `"N/A"`                   | No fire protection associations mentioned           | No industry association membership                    |
| `"NFPA"`                  | National Fire Protection Association membership     | Industry standards, professional development          |
| `"NAFED"`                 | National Association of Fire Equipment Distributors | Industry networking, distribution expertise           |
| `"AFSA"`                  | American Fire Sprinkler Association membership      | Sprinkler industry focus, professional standards      |
| `"NFSA"`                  | National Fire Sprinkler Association membership      | Sprinkler industry focus, professional standards      |
| `"CFSA"`                  | Canadian Fire Safety Association membership         | Canadian market presence, regional standards          |
| `"CASA"`                  | Canadian Automatic Sprinkler Association membership | Canadian sprinkler industry, regional expertise       |
| `"Multiple associations"` | Membership in multiple fire protection groups       | High industry engagement, strong professional network |
| `"Other association"`     | Different fire protection association mentioned     | Industry membership, but unknown specific benefits    |

---

## Scoring Framework Considerations

### High-Value Indicators

- **50/50 Split** business model (diversified revenue)
- **High Quality** website (professional operations)
- **Multiple certifications and compliance standards** (professional credibility)
- **Multi-territory coverage** (growth potential)
- **Established parent company** (resources/backing)
- **Multiple competitor software platforms** (market awareness)
- **Multiple fire protection associations** (industry engagement)

### Risk Indicators

- **Not Classifiable** (unknown business model)
- **Poor website quality** (resource constraints)
- **No certifications or compliance standards** (quality concerns)
- **Single territory** (limited growth)
- **Independent company** (potential resource limitations)
- **No competitor software usage** (market isolation)
- **No fire protection associations** (industry isolation)

### Neutral Indicators

- **Maintenance Only** vs **Install Only** (business model preference)
- **Average website quality** (moderate investment)
- **Basic certifications** (minimum compliance)
- **Single competitor software** (basic market awareness)
- **Single fire protection association** (basic industry engagement)

## Next Steps for Numerical Scoring

1. Assign base scores to each categorical field
2. Create weighted scoring for text-based fields
3. Develop composite scoring algorithms
4. Establish score thresholds for different business tiers
5. Validate scoring against known business outcomes
