# Crawler Feature Documentation

## Feature Overview

The **Targeted Domain Crawler** is a sophisticated web crawling system designed to discover and extract structured content from company websites with a focus on service-related pages. It prioritizes high-value internal links using deterministic rules and scoring signals, generates normalized page records, and emits machine-readable JSONL output along with human-friendly Markdown summaries.

**Business Value:**

- Enables rapid enrichment of target accounts with verified website content and key signals (headings, keywords, evidence)
- Supports batch processing, resumability, politeness controls, and robots.txt respect
- Provides deterministic, reproducible results for consistent data analysis

**Problems Solved:**

- Canonical domain resolution and robots.txt gating
- Deterministic, service-oriented link selection with intelligent scoring
- Lightweight, consistent page normalization and comprehensive reporting
- Efficient handling of large domain sets with checkpointing and resume capabilities

**Target Users:**

- Data and research operations teams
- Growth and sales teams
- Engineering teams orchestrating content discovery across large domain sets
- Business intelligence and competitive analysis teams

## Application Structure

### Core Architecture

The crawler follows a modular, orchestration-centric architecture with clear separation of concerns:

```
crawler/
├── __init__.py                 # Package initializer
├── run_crawl.py               # Main CLI entrypoint and orchestration
├── config.json                # Runtime configuration
├── canonical.py               # Canonical URL resolution and robots preflight
├── checkpoint.py              # File-based progress tracking
├── extraction.py              # Content extraction and normalization
├── link_selection.py          # Link discovery, scoring, and selection
├── logging.py                 # Structured logging utilities
├── output_writer.py           # Atomic JSONL output handling
├── politeness.py              # Delay and backoff controls
├── reachability.py            # Domain loading and normalization
├── report_md.py               # Markdown report generation
├── session.py                 # Session management and headers
├── modal_deploy_real.py       # Modal cloud deployment
└── tests/                     # Test suite
    ├── conftest.py
    ├── test_extraction.py
    ├── test_link_selection.py
    ├── test_output_writer.py
    └── test_reachability.py
```

### Component Hierarchy

```
CLI Entrypoint (run_crawl.py)
├── Configuration Loading (config.json)
├── Domain Intake (reachability.py)
├── For Each Domain:
│   ├── Canonical URL Resolution (canonical.py)
│   ├── Robots Preflight Check (canonical.py)
│   ├── Homepage Crawl (Crawl4AI + Playwright)
│   ├── Link Discovery & Selection (link_selection.py)
│   ├── Subpage Crawls (Crawl4AI)
│   ├── Content Extraction (extraction.py)
│   └── Record Generation
├── Output Writing (output_writer.py)
└── Report Generation (report_md.py)
```

## Functionalities Overview

### 1. Domain Intake and Normalization

**File:** `reachability.py`

- **Function:** `load_domains_from_csv()` - Reads domains from CSV files
- **Function:** `normalize_domain()` - Converts raw URLs to apex domains
- **Features:** Preserves input order, removes duplicates, validates domain format
- **Input:** CSV with configurable column names (default: `tam_site`)
- **Output:** Cleaned, normalized domain list

### 2. Canonical URL Resolution

**File:** `canonical.py`

- **Function:** `canonicalize_domain()` - Probes multiple URL schemes
- **Fallback Sequence:** `https://{root}` → `https://www.{root}` → `http://{root}` → `http://www.{root}`
- **Features:** Retry logic with exponential backoff, timeout controls
- **Robots Check:** `is_robot_disallowed()` - Conservative preflight validation

### 3. Web Crawling Engine

**File:** `run_crawl.py`

- **Technology:** Crawl4AI with Playwright backend
- **Features:** Headless browser automation, content filtering, link preview scoring
- **Configuration:** Browser settings, timeout controls, concurrency limits
- **Content Processing:** HTML to Markdown conversion, DOM-scoped extraction

### 4. Intelligent Link Selection

**File:** `link_selection.py`

- **Function:** `extract_anchors_from_html()` - Pure HTML anchor extraction
- **Function:** `select_links_with_scoring()` - Scoring-based selection
- **Function:** `select_links_simple()` - Bucket-based fallback selection
- **Features:**
  - Internal link filtering only
  - Disallowed path exclusion (privacy, terms, legal)
  - Deterministic ranking with tie-breakers
  - Service-intent detection and boosting

### 5. Content Extraction and Normalization

**File:** `extraction.py`

- **Function:** `make_page_record()` - Standardized page record creation
- **Function:** `extract_headings_simple()` - Markdown heading extraction
- **Function:** `detect_html_keywords()` - HTML keyword detection
- **Features:**
  - Text normalization and cleaning
  - Heading hierarchy preservation
  - Keyword evidence detection
  - Content deduplication

### 6. Output Generation

**File:** `output_writer.py`

- **Function:** `write_record()` - Atomic JSONL record writing
- **Function:** `open_jsonl()` - Safe file handling with atomic writes
- **Features:** Transactional writes, error handling, UTF-8 encoding

**File:** `report_md.py`

- **Function:** `generate_markdown_report()` - Human-readable summary generation
- **Output:** Overview tables, per-domain details, content samples

### 7. Politeness and Rate Limiting

**File:** `politeness.py`

- **Function:** `jitter_delay_seconds()` - Randomized delays between requests
- **Function:** `human_like_pause()` - Human-like interaction simulation
- **Features:** Configurable delays, jitter controls, conservative defaults

### 8. Session Management

**File:** `session.py`

- **Function:** `stable_session_id()` - Deterministic session ID generation
- **Function:** `build_headers()` - Browser-like HTTP headers
- **Features:** User agent rotation, locale support, WAF-friendly headers

### 9. Progress Tracking and Resumability

**File:** `checkpoint.py`

- **Function:** `load_checkpoint()` - Load previous progress
- **Function:** `save_checkpoint()` - Save current state
- **Function:** `mark_attempt()` / `mark_success()` - Track domain status
- **Features:** JSON-based storage, atomic writes, idempotent operations

### 10. Structured Logging

**File:** `logging.py`

- **Function:** `log_progress()` - Domain-level progress tracking
- **Function:** `log_event()` - System event logging
- **Function:** `log_summary()` - Run completion summaries
- **Features:** JSON-structured output, consistent formatting, easy parsing

### 11. Cloud Deployment

**File:** `modal_deploy_real.py`

- **Function:** `crawl_domains_real()` - Modal cloud deployment
- **Features:** Containerized execution, dependency management, scalable resources

## Technical Implementation

### Technology Stack

- **Language:** Python 3.12+
- **Core Libraries:**
  - **Crawl4AI** - Main crawling engine with Playwright integration
  - **Playwright** - Browser automation and rendering
  - **httpx** - Async HTTP client for reachability checks
  - **BeautifulSoup4** - HTML parsing and anchor extraction
  - **python-dotenv** - Environment variable management

### Configuration System

**File:** `config.json`

```json
{
  "html_keywords": ["building report", "fire protection", "NFPA", ...],
  "disallowed_paths": ["/privacy", "/terms", "/legal", ...],
  "page_cap": 5,
  "per_domain_delay_seconds": {"min": 1.5, "max": 2.0, "jitter": 0.4},
  "global_concurrency": 4,
  "retries": 2,
  "page_timeout_ms": 60000,
  "content_selectors": ["main", "article", "#content", ...]
}
```

### Environment Variables

- `PROXY_URL` - Proxy endpoint for crawler runtime
- `LOCALE` - Default Accept-Language header
- `INPUT_CSV` - Input CSV file path
- `OUTPUT_JSONL` - Output JSONL file path
- `CHECKPOINT` - Checkpoint file path
- `FROM_INDEX` - Starting index for domain processing
- `LIMIT` - Maximum number of domains to process
- `CONCURRENCY` - Concurrent processing limit
- `DOMAIN_COLUMN` - CSV column containing domains
- `ID_COLUMN` - CSV column containing record IDs

### Build and Deployment

- **Local Execution:** Direct Python execution with Playwright browser installation
- **Cloud Deployment:** Modal containerized deployment with dependency management
- **Dependencies:** Automatic installation via requirements.txt and pyproject.toml

## Integration Points

### External Integrations

- **Crawl4AI:** Core crawling engine with Playwright backend
- **Playwright:** Browser automation and rendering
- **httpx:** HTTP client for reachability and robots.txt checks
- **BeautifulSoup4:** HTML parsing and manipulation

### Internal Contracts

- **JSONL Schema:** One record per domain with aggregated context
- **Page Records:** Standardized structure with metadata and content
- **Checkpoint Format:** JSON-based progress tracking
- **Log Format:** Structured JSON logging for easy parsing

### Data Flow

```
CSV Input → Domain Normalization → Canonical URL Resolution →
Robots Check → Homepage Crawl → Link Discovery → Link Selection →
Subpage Crawls → Content Extraction → Normalization →
Aggregation → JSONL Output → Markdown Report
```

## Development Status

### Current Implementation Status

- ✅ **Complete:** End-to-end orchestration with link preview scoring
- ✅ **Complete:** Deterministic link selection and ranking
- ✅ **Complete:** Markdown reporting and progress tracking
- ✅ **Complete:** Resumable checkpoints and error handling
- ✅ **Complete:** Cloud deployment via Modal
- ✅ **Complete:** Comprehensive test suite

### Known Limitations

- Conservative robots.txt preflight; final handling delegated to Crawl4AI
- Link scoring availability may vary by Crawl4AI build version
- Content filtering thresholds may need tuning for specific use cases

### Planned Improvements

- Enhanced robots.txt parsing and handling
- More sophisticated content deduplication algorithms
- Additional output formats and integrations
- Performance optimization for large-scale deployments

## Usage Examples

### Basic Local Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Install Playwright browser
python -m playwright install chromium

# Run crawler with default settings
python crawler/run_crawl.py

# Run with custom parameters
python crawler/run_crawl.py \
  --input-csv "uptick-csvs/companies.csv" \
  --output-jsonl "output.jsonl" \
  --limit 10 \
  --concurrency 2
```

### Environment Configuration

```bash
# Create .env file
cat > .env << EOF
INPUT_CSV=uptick-csvs/final_merged_hubspot_tam_data_resolved.csv
OUTPUT_JSONL=llm-input.jsonl
CHECKPOINT=.crawl-checkpoint.json
FROM_INDEX=0
LIMIT=100
CONCURRENCY=4
DOMAIN_COLUMN=tam_site
ID_COLUMN=Record ID
ROBOTS_MODE=auto
EOF

# Run with environment variables
python crawler/run_crawl.py
```

### Cloud Deployment via Modal

```python
# Deploy to Modal
modal deploy crawler/modal_deploy_real.py

# Run cloud crawler
modal run crawler/modal_deploy_real.py::crawl_domains_real \
  --limit 50 \
  --domain-column "Company Domain Name" \
  --id-column "Record ID"
```

### Programmatic Usage

```python
from crawler.run_crawl import main
from crawler.reachability import load_domains_from_csv
from crawler.extraction import make_page_record

# Load domains
domains = load_domains_from_csv("companies.csv")

# Process domains
for domain in domains:
    # ... crawling logic ...
    record = make_page_record(domain, content)
    # ... output handling ...
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Playwright Installation Issues

**Problem:** `playwright install chromium` fails
**Solution:**

```bash
# Install system dependencies first
python -m playwright install-deps chromium
python -m playwright install chromium
```

#### 2. CSV Loading Errors

**Problem:** "CSV missing required column" error
**Solution:**

- Verify CSV file exists and is readable
- Check column names match `--column` and `--id-column` arguments
- Ensure CSV encoding is UTF-8

#### 3. Network Timeout Issues

**Problem:** Domains fail with timeout errors
**Solution:**

- Increase `page_timeout_ms` in config.json
- Check network connectivity and proxy settings
- Verify domain reachability manually

#### 4. Memory Issues

**Problem:** Out of memory during large crawls
**Solution:**

- Reduce `global_concurrency` setting
- Process domains in smaller batches using `--limit`
- Monitor system resources during execution

#### 5. Robots.txt Blocking

**Problem:** Many domains return robots.txt disallow errors
**Solution:**

- Set `--robots ignore` for testing
- Review `robots_overrides` in config.json
- Check robots.txt content manually for false positives

#### 6. Checkpoint Corruption

**Problem:** Checkpoint file becomes corrupted
**Solution:**

- Delete checkpoint file and restart
- Use `--from-index` to resume from specific position
- Verify file permissions and disk space

### Debug Mode

```bash
# Enable verbose logging
python crawler/run_crawl.py --dry-run

# Check specific domain
python crawler/run_crawl.py --limit 1 --from-index 0

# Resume from checkpoint
python crawler/run_crawl.py --resume --checkpoint .crawl-checkpoint.json
```

### Performance Tuning

- **Concurrency:** Start with low values (1-2) and increase gradually
- **Delays:** Adjust `per_domain_delay_seconds` based on target site tolerance
- **Timeouts:** Balance between reliability and speed
- **Memory:** Monitor resource usage and adjust batch sizes accordingly

### Log Analysis

```bash
# Filter progress logs
python crawler/run_crawl.py 2>&1 | grep '"type":"progress"'

# Extract error reasons
python crawler/run_crawl.py 2>&1 | grep '"status":"fail"' | jq '.reason'
```

## Configuration Reference

### Complete Configuration Options

```json
{
  "html_keywords": ["keyword1", "keyword2"],
  "disallowed_paths": ["/path1", "/path2"],
  "page_cap": 5,
  "per_domain_delay_seconds": {
    "min": 1.5,
    "max": 2.0,
    "jitter": 0.4
  },
  "global_concurrency": 4,
  "retries": 2,
  "page_timeout_ms": 60000,
  "canonicalization_timeout_sec": 12.0,
  "canonicalization_retries": 2,
  "allow_blog_if_signals": true,
  "exclude_external_links": true,
  "excluded_tags": ["nav", "footer", "script", "style"],
  "respect_robots": false,
  "robots_overrides": ["example.com"],
  "content_filter_threshold": 0.2,
  "sampling_ignore_robots": true,
  "emit_links": false,
  "content_selectors": ["main", "article", "#content"]
}
```

### Command Line Arguments

```bash
python crawler/run_crawl.py [OPTIONS]

Options:
  --input-csv PATH          Input CSV file path
  --output-jsonl PATH       Output JSONL file path
  --checkpoint PATH         Checkpoint file path
  --from-index INT          Starting index for processing
  --limit INT               Maximum domains to process
  --concurrency INT         Concurrent processing limit
  --dry-run                 Validate configuration without crawling
  --resume                  Resume from checkpoint
  --column TEXT             CSV column containing domains
  --id-column TEXT          CSV column containing record IDs
  --robots [respect|ignore|auto]  Robots.txt handling mode
  --help                    Show help message
```

This documentation serves as the definitive reference for the Targeted Domain Crawler feature, providing comprehensive coverage of its purpose, implementation, and usage patterns.
