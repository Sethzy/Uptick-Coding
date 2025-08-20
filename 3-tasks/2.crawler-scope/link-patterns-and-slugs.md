/\_
Purpose: Summarize real-world link patterns and path slugs observed across 25 fire protection company websites.

<!-- AIDEV-NOTE: data source sample-25; 648 links; counts reflect first path segment -->
<!-- AIDEV-NOTE: use these slugs to refine link_priority_buckets in crawler/config.json -->

## Overview

- **Dataset**: 25 domains (sample-25), 648 internal navigational links (assets filtered)
- **Method**: Count first-level path segment from `pages[].links.internal[].href`
- **Goal**: Identify common link patterns that reveal "what they do" and inform bucket heuristic

### Notes on skewed segments

- **service-area (147)**: Dominated by `firesolutionsnw.com` (145 links), which publishes a large location/SEO tree:
  - Hub: `/service-area`
  - Locations: `/service-area/{state-or-city}`
  - Service-in-location: `/service-area/{service-slug}` and `/service-area/{service-slug}/{city}`
- **products (43)**: Concentrated on `apfecorp.com` (40 links) with a product catalog under `/products/...`.
- **index.cfm/contact_us.cfm/article.cfm**: CMS artifacts on a few legacy sites.

## Common link patterns and example

### Services hub with nested service pages

Action item:
##this is important. we must prioritise scoring for this.

- Pattern: `/services` + child slugs
- Examples:
  - `https://www.capitolfire.com/services/installation`
  - `https://www.capitolfire.com/services/inspections`
  - `https://www.capitolfire.com/services/violations`
- Variants:
  - `https://lafiresprinklers.com/all-our-services` ("all services" page)

###Top-level service pages without a parent hub:

Action item:

if it's top level service page without a parent hub, we must also prioritise this.

    - `https://www.bighorn-fire.com/fire-extinguisher-services`
    - `https://www.bighorn-fire.com/backflows`
    - `https://www.bighorn-fire.com/firesprinkler`

The slugs to prioritise are

    "Inspection",
    "maintenance",
    "protection",
    "Installation",
    "install",
    "commissioning",
    "commission",
    "fire",
    "alarm",
    "testing",
    "extinguishers",
    "repair",
    "system",

### About us page is a must do. Almost every company has one.

https://www.alpha-fsc.com/about-us

as long as there's aobut in the slug, it must be prioritised

### Service-area trees (coverage/SEO)

IGNORE THIS. If this comes up, it should be lowly ranked.

- Pattern: `/service-area` → geographic or service-in-geo pages
- Examples:
  - `https://www.firesolutionsnw.com/service-area`
  - `https://www.firesolutionsnw.com/service-area/idaho`
  - `https://www.firesolutionsnw.com/service-area/standpipe-hydrostatic-testing-5year`
  - `https://lafiresprinklers.com/service-area`

### Product catalogs

- Pattern: `/products` → equipment categories
- Examples:
  - `https://apfecorp.com/products/fire-sprinklers`
  - `https://apfecorp.com/products/fire-alarms`
  - `https://apfecorp.com/products/fire-pumps`
  - `https://apfecorp.com/products/extinguishers`
  - `https://cachevalleyfire.com/products`
