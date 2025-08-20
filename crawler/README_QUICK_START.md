# 🚀 Quick Start Guide - Uptick Targeted Domain Crawler

This guide shows you how to quickly get started with the targeted domain crawler for company website analysis.

## Prerequisites

1. **Python 3.11+** installed
2. **Modal account** for cloud deployment (optional for local runs)
3. **CSV file** with company domains
4. **Dependencies** installed

## 🎯 Deployment Options

Choose between local development or cloud deployment:

```
CSV Domains → Local Crawler → JSONL Output
CSV Domains → Modal Cloud (3 containers) → JSONL Output (Recommended for large batches)
```

## Quick Commands

### 1. Setup (One-time)

```bash
# Install dependencies
python -m venv venv && source venv/bin/activate
pip3 install -U crawl4ai httpx beautifulsoup4 python-dotenv click pydantic
python -m playwright install chromium

# For Modal deployment
pip install modal
modal token new  # Follow setup instructions
```

### 2. Local Development Run

**Small batches or testing:**

```bash
# From the crawler/ directory
cd crawler

# Basic crawl (10 domains)
python run_crawl.py \
  --input-csv ../uptick-csvs/enriched-hubspot-TAM-08-25.csv \
  --output-jsonl output.jsonl \
  --limit 10 \
  --concurrency 3

# With checkpointing (resumable)
python run_crawl.py \
  --input-csv ../uptick-csvs/enriched-hubspot-TAM-08-25.csv \
  --output-jsonl output.jsonl \
  --checkpoint .crawl-checkpoint.json \
  --from-index 0 --limit 50 --concurrency 4
```

### 3. Modal Cloud Deployment (Recommended)

**Large batches with 3-container parallel processing:**

```bash
# Deploy the app (one-time)
cd crawler
modal deploy modal_deploy_real.py

# Run with 3 containers, 50 concurrent crawlers each
modal run modal_deploy_real.py --total-domains 420 \
  --domain-column "Company Domain Name" \
  --id-column "Record ID"

# Download results
modal volume get uptick-crawler-outputs concurrent_batch_1_YYYYMMDD_HHMMSS.jsonl
```

### 4. Dry Run (Validate Setup)

```bash
# Test configuration without crawling
python run_crawl.py --dry-run
```

## 🏗️ Modal Architecture (3-Container Setup)

**Performance:**
- **3 separate containers** running in parallel
- **50 concurrent crawlers** per container
- **Total throughput:** 150 domains simultaneously
- **Cost optimized:** 1 CPU + 2GB RAM per container

**Expected Performance:**
- 420 domains: ~2-3 minutes (vs 14 minutes with single container)
- Cost: $0.14/hour for 3 containers vs $0.09/hour for 1 container

## Environment Setup

### Option 1: Environment Variables

```bash
export DOMAIN_COLUMN="Company Domain Name"
export ID_COLUMN="Record ID"
export CONCURRENCY=4
```

### Option 2: Config File

The crawler uses `crawler/config.json` for behavior settings:

```json
{
  "keywords": ["fire", "protection", "safety", "security"],
  "page_cap": 5,
  "global_concurrency": 4,
  "per_domain_delay_seconds": {"min": 1, "max": 3, "jitter": 0.5}
}
```

## Examples

### Complete Modal Workflow (Recommended for Production)

```bash
cd /path/to/Uptick-Coding/crawler

# 1. Deploy the Modal app (one-time)
modal deploy modal_deploy_real.py

# 2. Run large batch with 3-container parallelism
modal run modal_deploy_real.py --total-domains 1000 \
  --domain-column "Company Domain Name" \
  --id-column "Record ID"

# 3. Download all results
modal volume list uptick-crawler-outputs
modal volume get uptick-crawler-outputs concurrent_batch_1_20250820_123456.jsonl
modal volume get uptick-crawler-outputs concurrent_batch_2_20250820_123456.jsonl
modal volume get uptick-crawler-outputs concurrent_batch_3_20250820_123456.jsonl
```

### Local Development Workflow

```bash
cd crawler

# Small test run
python run_crawl.py \
  --input-csv ../uptick-csvs/enriched-hubspot-TAM-08-25.csv \
  --output-jsonl test_output.jsonl \
  --limit 5 --concurrency 2

# Check results
head -n 1 test_output.jsonl | jq .
```

## What Each Command Does

- **`run_crawl.py`**: Core crawler script for local execution
- **`modal_deploy_real.py`**: Cloud deployment with 3-container parallelism
- **`--dry-run`**: Validates configuration without crawling
- **`--checkpoint`**: Enables resumable crawling for large batches
- **`--concurrency`**: Controls simultaneous domain processing

## Data Flow

```
CSV Input → Domain Canonicalization → Robots Check → Homepage Crawl → 
Link Selection → Subpage Crawling → Content Extraction → JSONL Output
```

**Output Structure:**
```json
{
  "domain": "example.com",
  "canonical_url": "https://www.example.com",
  "status": "SUCCESS",
  "pages": [
    {
      "url": "https://www.example.com/services",
      "title": "Fire Protection Services",
      "headings": ["Emergency Response", "Installation"],
      "keywords": ["fire protection", "safety"],
      "evidence": ["24/7 emergency fire protection services..."]
    }
  ]
}
```

## Modal Container Monitoring

View your running containers and progress:

1. **Modal Dashboard:** https://modal.com/apps/[your-username]/main
2. **Container Status:** Check "Containers: X live, Calls: Y running"
3. **Logs:** Click on individual containers to view real-time logs
4. **Volume Management:** `modal volume list uptick-crawler-outputs`

## Troubleshooting

### Container Issues

```
❌ Only 1 container spawning instead of 3
```

**Solution**: Ensure you removed the `@modal.concurrent` decorator from `crawl_domains_worker`. The code should use `.starmap()` for true parallelism.

### DNS/Canonical Issues

```
❌ DNS_FAIL: Cannot reach domain
```

**Solution**: Check domain validity in CSV. The crawler tries https/www/http fallbacks automatically.

### Rate Limiting

```
❌ Too many requests / rate limited
```

**Solution**: Increase delays in `config.json` or reduce `--concurrency` parameter.

### Memory Issues (Local)

```
❌ Out of memory during large batch
```

**Solution**: Use Modal deployment for large batches, or reduce `--concurrency` and add `--checkpoint` for resumability.

### Modal Deployment Issues

```
❌ Modal app not found
```

**Solution**: 
```bash
modal deploy modal_deploy_real.py  # Deploy first
modal token new  # If authentication issues
```

## Performance Recommendations

### Local Development
- **Small batches:** < 100 domains
- **Concurrency:** 2-4 (depends on your machine)
- **Use checkpoints** for runs > 50 domains

### Modal Production
- **Large batches:** 100+ domains
- **3-container setup:** Automatic with `modal_deploy_real.py`
- **Monitoring:** Use Modal dashboard for progress tracking

## File Structure

```
crawler/
├── README_QUICK_START.md    # This file
├── run_crawl.py            # Local crawler script
├── modal_deploy_real.py    # Modal cloud deployment
├── config.json             # Crawler configuration
├── canonical.py            # Domain canonicalization
├── extraction.py           # Content extraction
├── link_selection.py       # Link prioritization
└── tests/                  # Test suite
```

## Advanced Usage

For detailed configuration and development, see:
- `targeted-domain-crawler-documentation.md` - Complete technical documentation
- `config.json` - Behavior and selection tuning
- `tests/` - Test suite for development