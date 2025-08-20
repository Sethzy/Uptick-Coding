Old Detailed Scoring Breakdown

1. Classification Category (30 points)

"Maintenance & Service Only" → 30 points (Most valuable - stable recurring revenue)

"50/50 Split" → 15 points (Diversified revenue streams)

"Install Only" → 10 points (Project-based, cyclical business)

"Other" → 5 points (Specialized expertise, niche market)

"Not Classifiable" → 0 points (Unknown business model, high risk)

Prompt:

"Detailed Classification Criteria:\n"

"\n"

"1. MAINTENANCE & SERVICE ONLY:\n"

"   - Companies focused exclusively on ongoing upkeep and repair of existing fire protection systems\n"

"   - Work is primarily scheduled and recurring, based on mandated inspection cycles\n"

"   - Job tickets: service calls, inspections, testing, preventative maintenance\n"

"   - High volume of recurring, small-to-medium-sized tickets and maintenance agreements\n"

"   - RULE: If website mentions ANY installations, automatically classify as Install Only or 50/50 Split\n"

"\n"

"2. INSTALL ONLY:\n"

"   - Companies engaged in design and installation of new fire protection systems\n"

"   - Project-based work in new construction or major renovation projects\n"

"   - Job tickets: large, complex projects with multiple phases and significant financial value\n"

"   - Focus on blueprints, design, and initial capital expenditure projects\n"

"   - RULE: If website mentions ANY maintenance or service, automatically classify as Maintenance & Service Only or 50/50 Split\n"

"\n"

"3. 50/50 SPLIT:\n"

"   - Balanced business model between new installations and ongoing service/maintenance\n"

"   - Capacity for large new construction projects AND steady stream of recurring service work\n"

"   - Job tickets: mix of large multi-phase install jobs and smaller frequent service calls\n"

"   - RULE: If website mentions BOTH installations AND maintenance/service, classify here\n"

"\n"

"4. OTHER:\n"

"   - Specialized fire protection services not fitting other categories\n"

"   - Includes: Firestopping, Fireproofing, Kitchen Suppression Systems, Fire Alarms, Portable Extinguishers\n"

"   - Highly diverse jobs from small single-item services to complex specialized equipment\n"

"   - Not directly related to large-scale water-based suppression systems or general recurring maintenance\n"

"\n"

"5. NOT CLASSIFIABLE:\n"

"   - Use when website data is insufficient or contains no useful business information\n"

"   - Cases include: blank/empty aggregated context, website scrape failures\n"

"   - Websites showing 'Coming Soon', 'Under Construction', or placeholder content\n"

"   - Content that doesn't mention fire protection services, business activities, or company focus\n"

"   - RULE: Classify here if aggregated_context is empty, very short (<50 chars), or contains no business-relevant information\n"

"\n"

2. Website Quality (20 points)

"High Quality" → 20 points (Professional operations, strong market presence)

"Average" → 10 points (Moderate investment, basic digital maturity)

"Poor" → 0 points (Low investment, potential resource constraints)

3. Maintenance & Service Focus (Bonus 10 points)

"yes" → 10 points (Recurring revenue model, stable cash flow)

"no" → 0 points (Project-based, potentially higher volatility)

Note: helps to make companies that are 50/50 elevated if they focus on maintenance.

4. Certifications & Compliance Standards (10 points)

Anything that is not N/A - 10 points

"N/A" → 0 points (No credentials, quality concerns)

Prompt:

"3. has_certifications_and_compliance_standards:\n"

"   Question: Does the company mention any professional certifications, licenses, or compliance with specific regulatory standards?\n"

"   Look for: State licenses, manufacturer certifications, technician credentials, NFPA standards (25, 72, 13), UL standards, specific code references, compliance certifications\n"

"   Output: Provide a short answer detailing what was found. If nothing was found, output N/A.\n"

"\n"

5. Service Territory Coverage (10 points)

Anything that is not N/A - 10 points

"N/A" → 0 points (Local market focus, limited growth)

Prompt:

"4. has_multiple_service_territories:\n"

"   Question: Does the company operate in more than one distinct city/area, or does it have multiple branches or offices?\n"

"   Output: If they operate in 2 or more distinct cities/areas OR have multiple branches/offices, list all locations. If they only operate in a single city/area with no mention of multiple branches, output N/A.\n"

"   Examples:\n"

"   - Multiple cities: 'Alhambra, CA; Artesia, CA; Burbank, CA' → List all\n"

"   - Single city: 'Los Angeles, CA' → N/A\n"

"   - Multiple branches in same city: 'Downtown LA office, West LA office' → List all\n"

"   - Broad regions: 'Southern California' or 'Texas' → N/A (too vague)\n"

"   - Multiple specific cities: 'Los Angeles, CA; San Diego, CA; Phoenix, AZ' → List all\n"

"\n"

6. Parent Company Status (0 points)

"N/A" → 0 points (Independent company, full autonomy - preferred)

Any parent company → 0 points (Corporate backing - will be penalized later)

Prompt:

"5. has_parent_company:\n"

"   Question: Do they have a parent company?\n"

"   Look for: any variations of. it does not need to be case sensitive or exact phrasing. use common sense.\n"

"   Examples: Pye Barker, API Group, Summit Companies, Sciens Building Solutions, Cintas, Guardian Fire Protection, Hiller Fire, Impact Fire, Fortis Fire & Safety, Zeus Fire & Security\n"

"   Output: Provide a short answer detailing what was found. If nothing was found, output N/A.\n"

"\n"

7. Competitor Software Usage (10 points)

Anything that is not N/A - 10 points

"N/A" → 0 points (No market awareness, potential isolation)

Using HTML extraction so we can read images / logos. Looking for:

"building report",

"BuildingReports.com",

"inspect point",

"inspectpoint.com",

"inspectpoint",

"buildops",

"buildops.com",

"Service Trade",

"servicetrade.com",



8. Fire Protection Associations (10 points)

Anything that is not N/A - 10 points

"N/A" → 0 points (No industry engagement, isolation)

Using HTML extraction so we can read images / logos. Looking for:

"NFPA",

"National Fire Protection Association",

"NAFED",

"National Association of Fire Equipment Distributors",

"AFSA",

"American Fire Sprinkler Association",

"NFSA",

"National Fire Sprinkler Association",

"CFSA",

"CASA",

"Canadian Automatic Sprinkler Association",

"Canadian Fire Safety Association"

Supplementary Penalty System

Parent Company Status Penalty:

Independent companies (N/A): No penalty - 0 points deducted

Corporate-backed companies (any parent company): -20 points deducted from final score

How it works:

Calculate main score out of 100 points using the 8 fields above

If company has a parent company, deduct 20 points from final score

Final score can range from -20 to 100 points

Example:

Company scores 95/100 on main criteria

Has parent company → Final score: 95 - 20 = 75 points

Independent company → Final score: 95 - 0 = 95 points

Score Tiers (Base Score - Before Parent Company Penalty)

90-100 points: Elite Tier - Ideal companies with stable recurring revenue, strong credentials, multi-territory presence, and industry leadership

75-89 points: High Tier - Strong companies with good business models, professional operations, and market presence

60-74 points: Mid Tier - Solid companies with established operations and moderate growth potential

45-59 points: Basic Tier - Functional companies with limited scope or resources

0-44 points: Risk Tier - Companies with unknown business models, limited credentials, or operational constraints

Note: After applying parent company penalty (-20 points), final scores can range from -20 to 100 points.
