# Fire Protection Company Scoring Rubric v2

## Overview

This document describes the updated scoring system for fire protection companies, combining web scraping, LLM classification, and automated keyword detection to assess company "fit" through a comprehensive scoring model.

## Major Changes from v1

### Updated Weights

- **Classification Category**: Increased from 30 points to **50 points** (highest weight)
- **Website Quality**: Decreased from 20 points to **10 points**
- **Maintenance & Service Focus**: Same at **10 points**
- **Certifications & Compliance**: Decreased from 10 points to **5 points**
- **Service Territory Coverage**: Decreased from 10 points to **5 points**
- **Competitor Software**: Decreased from 10 points to **5 points**
- **Fire Protection Associations**: Decreased from 10 points to **5 points**

### New Scoring Field

- **Full List of Services Offered**: New **10 points** field with categorical scoring

### Updated Classification Definitions

- **"Other" Category**: Now specifically for companies providing services "not directly related to fire protection" (previously for specialized fire protection services)
- **Classification Penalty**: "Other" category now receives **-10 points** (penalty)

### Automated Keyword Detection

- Competitor software and fire protection association fields are now automatically scored from HTML keyword extraction
- No longer relies on LLM analysis for these fields

## Detailed Scoring Breakdown (100 Point Base Scale)

### 1. Classification Category (50 points)

**"Maintenance & Service Only"** → **50 points** (Most valuable - stable recurring revenue)

- Companies focused exclusively on ongoing upkeep and repair of existing fire protection systems
- Work is primarily scheduled and recurring, based on mandated inspection cycles
- RULE: If website mentions ANY installations, automatically classify as Install Only or 50/50 Split

**"50/50 Split"** → **30 points** (Diversified revenue streams)

- Balanced business model between new fire protection installations and ongoing fire protection service/maintenance
- RULE: If website mentions BOTH installations AND maintenance/service, classify here

**"Install Only"** → **20 points** (Project-based, cyclical business)

- Companies engaged in design and installation of new fire protection systems
- RULE: If website mentions ANY maintenance or service, automatically classify as Maintenance & Service Only or 50/50 Split

**"Other"** → **-10 points** (Not fire protection focused - penalty applied)

- All services provided are not directly related to fire protection (e.g., marketing company)

**"Not Classifiable"** → **0 points** (Unknown business model, high risk)

- Use when website data is insufficient or contains no useful business information

### 2. Website Quality (10 points)

**"High Quality"** → **10 points** (Professional operations, strong market presence)

- Pages: 3+ pages
- Indicators: Comprehensive website with multiple sections, detailed content, strong online presence

**"Average"** → **5 points** (Moderate investment, basic digital maturity)

- Pages: 1-2 pages
- Indicators: Basic company info, some service descriptions, functional but minimal

**"Poor"** → **0 points** (Low investment, potential resource constraints)

- Pages: 1 page
- Indicators: Basic placeholder, minimal content, "Coming Soon" sites

### 3. Maintenance & Service Focus (10 points)

**"yes"** → **10 points** (Recurring revenue model, stable cash flow)

- Company primarily focuses on ongoing upkeep and repair of existing fire protection systems
- Target: Helps with scoring 50/50 split companies

**"no"** → **0 points** (Project-based, potentially higher volatility)

### 4. Full List of Services Offered (10 points) - NEW FIELD

**"Fire Protection Only"** → **10 points** (Focused expertise, specialized market)

- Example: "Fire Protection Only - Fire alarm system installation, Fire sprinkler maintenance, Emergency lighting"

**"Fire Protection and Other Services"** → **5 points** (Diversified but fire-focused)

- Example: "Fire Protection and Other Services - Fire alarm installation, HVAC services, Plumbing, Electrical work"

**"Other Services Only"** → **-10 points** (Not primarily fire protection - penalty applied)

- Example: "Other Services Only - HVAC services, Plumbing, Electrical work, General contracting"

### 5. Certifications & Compliance Standards (5 points)

**Any certification mentioned** → **5 points**

- State licenses, manufacturer certifications, technician credentials
- NFPA standards (25, 72, 13), UL standards, specific code references

**"N/A"** → **0 points** (No credentials, quality concerns)

### 6. Service Territory Coverage (5 points)

**Multiple territories listed** → **5 points** (Multi-territory operations)

- Operating in 2+ distinct cities/areas OR multiple branches/offices
- Examples: "Alhambra, CA; Artesia, CA; Burbank, CA"

**"N/A"** → **0 points** (Local market focus, limited growth)

- Single city operation with no multiple branches

### 7. Competitor Software Usage (5 points) - AUTOMATED

**Any software detected** → **5 points** (Market awareness, tech adoption)

Automatically detected keywords:

- "building report", "BuildingReports.com"
- "inspect point", "inspectpoint.com", "inspectpoint"
- "buildops", "buildops.com"
- "Service Trade", "servicetrade.com"

**"N/A"** → **0 points** (No market awareness, potential isolation)

### 8. Fire Protection Associations (5 points) - AUTOMATED

**Any association detected** → **5 points** (Industry engagement)

Automatically detected keywords:

- "NFPA", "National Fire Protection Association"
- "NAFED", "National Association of Fire Equipment Distributors"
- "AFSA", "American Fire Sprinkler Association"
- "NFSA", "National Fire Sprinkler Association"
- "CFSA", "Canadian Fire Safety Association"
- "CASA", "Canadian Automatic Sprinkler Association"

**"N/A"** → **0 points** (No industry engagement, isolation)

## Penalty System

### Parent Company Status Penalty

- **Independent companies** ("N/A"): No penalty - **0 points deducted**
- **Corporate-backed companies** (any parent company): **-20 points deducted** from final score

**How it works:**

1. Calculate main score out of 100 points using the 8 fields above
2. If company has a parent company, deduct 20 points from final score
3. Final score can range from **-40 to 100 points**

**Example:**

- Company scores 95/100 on main criteria
- Has parent company → Final score: 95 - 20 = **75 points**
- Independent company → Final score: **95 points**

## Score Tiers (After Parent Company Penalty)

**86-100 points: Elite Tier**

- Ideal companies with stable recurring revenue, strong credentials, multi-territory presence, and industry leadership

**75-85 points: High Tier**

- Strong companies with good business models, professional operations, and market presence

**60-74 points: Mid Tier**

- Solid companies with established operations and moderate growth potential

**45-59 points: Basic Tier**

- Functional companies with limited scope or resources

**0-44 points: Risk Tier**

- Companies with unknown business models, limited credentials, or operational constraints

**Below 0 points: Penalty Tier**

- Companies with significant negative factors (non-fire protection focus, corporate backing, etc.)
