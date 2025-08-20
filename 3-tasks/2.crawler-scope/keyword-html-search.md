# Product Requirements Document (PRD) — Keyword HTML Search Feature

## Introduction/Overview

The Keyword HTML Search feature is a lightweight, real-time pattern detection system that adds keyword detection capabilities to the existing `output.jsonl` file without modifying the `raw-output.jsonl` storage approach. This feature searches HTML content during the crawl process to detect specific keywords (such as building report references) and adds the results as a new field in the processed output.

**Problem Solved:** The current crawler stores massive amounts of raw HTML in `raw-output.jsonl` (2MB+ per crawl run), making raw output files unwieldy, slow to process, and expensive to store. This feature provides a clean, efficient alternative that maintains 100% keyword detection capability by adding structured keyword data to the existing `output.jsonl` file.

**Goal:** Implement real-time HTML keyword detection that adds keyword evidence to the existing `output.jsonl` while keeping the raw HTML storage in `raw-output.jsonl` intact, providing both comprehensive data storage and clean, searchable keyword information.

## Goals

1. **Add Keyword Detection**: Add a new field to the existing `output.jsonl` containing detected keywords from HTML content
2. **Maintain Detection Accuracy**: Preserve 100% of current keyword detection capability for building reports and other target patterns
3. **Improve Analysis Efficiency**: Provide quick access to keyword evidence without needing to search through raw HTML files
4. **Enhance Output Format**: Add structured keyword data to the existing output while maintaining current functionality
5. **Real-time Performance**: Ensure keyword detection adds zero additional delay to the crawl process

## User Stories

- **As a data analyst**, I want to quickly identify which domains contain building report references so I can prioritize outreach efforts without dealing with massive HTML files.

- **As a developer**, I want a clean, lightweight output format that's easy to parse and analyze programmatically.

- **As a system administrator**, I want to reduce storage costs and improve processing performance while maintaining all the detection functionality.

- **As a researcher**, I want to search through crawl results efficiently to find specific patterns without loading gigabytes of HTML content.

## Functional Requirements

1. **Real-time HTML Keyword Detection**: The system must search HTML content during the crawl process using configurable keyword patterns and add results to the existing `output.jsonl`.

2. **Configurable Keyword List**: Keywords must be definable via `config.json` file, allowing easy modification without code changes.

3. **Enhanced Output Format**: Each page record in `output.jsonl` must include a new field containing a simple list of keywords found (e.g., `["building report", "BuildingReports.com"]`).

4. **HTML Content Search**: The system must search the actual HTML content (not markdown) to ensure accurate pattern detection.

5. **Zero Performance Impact**: Keyword detection must complete in real-time during the crawl with no additional delay.

6. **Preserve Existing Output**: This feature must add to the existing `output.jsonl` structure without replacing or removing current fields.

7. **Pattern Flexibility**: The system must support both exact text matches and regex patterns for complex keyword detection.

8. **Case-insensitive Search**: Keyword detection must work regardless of text case to ensure comprehensive coverage.

## Non-Goals (Out of Scope)

- **Raw HTML Storage**: This feature will NOT modify the existing `raw-output.jsonl` storage approach - raw HTML will continue to be stored as before.
- **Detailed Evidence Snippets**: The feature will NOT provide context around keyword matches or detailed evidence snippets.
- **HTML Structure Analysis**: The feature will NOT analyze or preserve HTML element relationships or DOM structure.
- **Markdown Content Search**: The feature will NOT search markdown content, only HTML source.
- **Performance Degradation**: The feature will NOT add any processing delay to the crawl process.
- **Output File Replacement**: The feature will NOT replace the existing `output.jsonl` structure - it will enhance it with new fields.
- **Advanced Pattern Matching**: The feature will NOT include complex NLP or semantic analysis beyond basic keyword matching.

## Design Considerations

- **Clean Output Schema**: The output JSON should be minimal and focused, containing only essential information.
- **Configurable Keywords**: Keywords should be easily modifiable through configuration files for different use cases.
- **Consistent Format**: All page records should follow the same structure for easy parsing and analysis.
- **Error Handling**: The system should gracefully handle cases where HTML content is missing or malformed.

## Technical Considerations

- **Integration with Crawl4ai**: Must work seamlessly with the existing `AsyncWebCrawler` and `CrawlerRunConfig` setup.
- **Modification of `extraction.py`**: The `make_page_record()` function must be updated to remove HTML storage and add keyword detection.
- **Configuration Updates**: The `config.json` file must be updated to include the keyword list.
- **Backward Compatibility**: The output format change may affect downstream analysis tools that expect raw HTML.

## Success Metrics

1. **Storage Reduction**: Achieve 90%+ reduction in output file size (from 2MB+ to under 200KB per crawl run)
2. **Performance Maintenance**: Maintain crawl speed with zero additional delay for keyword detection
3. **Detection Accuracy**: Maintain 100% of current keyword detection capability
4. **Processing Speed**: Reduce analysis time by eliminating the need to search through massive HTML files
5. **Output Clarity**: Provide clean, structured data that's immediately actionable for analysts

## Open Questions

1. **Keyword Pattern Complexity**: Should the system support regex patterns, or stick to simple text matching for performance?
2. **Output Format Standardization**: Should the output format be standardized across all crawler modes for consistency?
3. **Error Handling Strategy**: How should the system handle cases where HTML content is unavailable or corrupted?
4. **Configuration Validation**: What validation should be in place for the keyword configuration to prevent errors?
5. **Migration Strategy**: How should existing systems that depend on raw HTML output be updated to work with the new format?

## Implementation Priority

**High Priority**: Core keyword detection functionality and HTML storage replacement
**Medium Priority**: Configuration system and error handling
**Low Priority**: Advanced pattern matching and output format optimization
