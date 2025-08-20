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

## Numerical Scoring System (100 Point Scale)

### Field Weighting & Scoring

| Field                               | Max Points | Weight   | Scoring Logic                        |
| ----------------------------------- | ---------- | -------- | ------------------------------------ |
| **1. Classification Category**      | **30**     | 30%      | Business model value                 |
| **2. Website Quality**              | **20**     | 20%      | Digital investment & professionalism |
| **3. Maintenance & Service Focus**  | **10**     | 10%      | Revenue stability                    |
| **4. Certifications & Compliance**  | **10**     | 10%      | Professional credibility             |
| **5. Service Territory Coverage**   | **10**     | 10%      | Market reach & growth potential      |
| **6. Parent Company Status**        | **0**      | 0%       | Independent companies preferred      |
| **7. Competitor Software Usage**    | **10**     | 10%      | Market awareness & tech adoption     |
| **8. Fire Protection Associations** | **10**     | 10%      | Industry engagement                  |
| **TOTAL**                           | **100**    | **100%** | **Perfect Company Score**            |

---

### Detailed Scoring Breakdown

#### 1. Classification Category (30 points)

- `"Maintenance & Service Only"` → **30 points** (Most valuable - stable recurring revenue)
- `"50/50 Split"` → **15 points** (Diversified revenue streams)
- `"Install Only"` → **10 points** (Project-based, cyclical business)
- `"Other"` → **5 points** (Specialized expertise, niche market)
- `"Not Classifiable"` → **0 points** (Unknown business model, high risk)

#### 2. Website Quality (20 points)

- `"High Quality"` → **20 points** (Professional operations, strong market presence)
- `"Average"` → **10 points** (Moderate investment, basic digital maturity)
- `"Poor"` → **0 points** (Low investment, potential resource constraints)

#### 3. Maintenance & Service Focus (10 points)

- `"yes"` → **10 points** (Recurring revenue model, stable cash flow)
- `"no"` → **0 points** (Project-based, potentially higher volatility)

#### 4. Certifications & Compliance Standards (10 points)

- Anything that is not N/A - 10 points
- `"N/A"` → **0 points** (No credentials, quality concerns)

#### 5. Service Territory Coverage (10 points)

- Anything that is not N/A - 10 points
- `"N/A"` → **0 points** (Local market focus, limited growth)

#### 6. Parent Company Status (0 points)

- `"N/A"` → **0 points** (Independent company, full autonomy - preferred)
- Any parent company → **0 points** (Corporate backing - will be penalized later)

#### 7. Competitor Software Usage (10 points)

Anything that is not N/A - 10 points

- `"N/A"` → **0 points** (No market awareness, potential isolation)

#### 8. Fire Protection Associations (10 points)

Anything that is not N/A - 10 points

- `"N/A"` → **0 points** (No industry engagement, isolation)

---

### Supplementary Penalty System

**Parent Company Status Penalty:**

- **Independent companies** (N/A): **No penalty** - 0 points deducted
- **Corporate-backed companies** (any parent company): **-20 points deducted** from final score

**How it works:**

1. Calculate main score out of 100 points using the 8 fields above
2. If company has a parent company, deduct 20 points from final score
3. Final score can range from **-20 to 100 points**

**Example:**

- Company scores 95/100 on main criteria
- Has parent company → Final score: 95 - 20 = **75 points**
- Independent company → Final score: 95 - 0 = **95 points**

---

### Score Tiers (Base Score - Before Parent Company Penalty)

- **90-100 points**: **Elite Tier** - Ideal companies with stable recurring revenue, strong credentials, multi-territory presence, and industry leadership
- **75-89 points**: **High Tier** - Strong companies with good business models, professional operations, and market presence
- **60-74 points**: **Mid Tier** - Solid companies with established operations and moderate growth potential
- **45-59 points**: **Basic Tier** - Functional companies with limited scope or resources
- **0-44 points**: **Risk Tier** - Companies with unknown business models, limited credentials, or operational constraints

**Note:** After applying parent company penalty (-20 points), final scores can range from -20 to 100 points.

---

### Example Scoring

**Perfect Company (100 points):**

- Maintenance & Service Only (30) + High Quality website (20) + Maintenance focus (10) + Certifications (10) + Multi-territory (10) + Independent (0) + Competitor software (10) + Associations (10) = **100 points**

**Average Company (75 points):**

- 50/50 Split (15) + Average website (10) + Maintenance focus (10) + Certifications (10) + Multi-territory (10) + Independent (0) + Competitor software (10) + Associations (10) = **75 points**

**Risk Company (0 points):**

- Not Classifiable (0) + Poor website (0) + No maintenance focus (0) + No certifications (0) + Single territory (0) + Independent (0) + No software (0) + No associations (0) = **0 points**

---

**With Parent Company Penalty Applied:**

**Perfect Independent Company:** 100 - 0 = **100 points** ✅
**Perfect Corporate Company:** 100 - 20 = **80 points** ⚠️
**Average Independent Company:** 75 - 0 = **75 points** ✅
**Average Corporate Company:** 75 - 20 = **55 points** ⚠️
