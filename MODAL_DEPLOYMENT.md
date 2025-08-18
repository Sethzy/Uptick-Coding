# Modal Deployment for Uptick Crawler

## Overview

This document explains how to deploy the Uptick crawler on Modal for cloud-based web crawling.

## Quick Deploy

### Option 1: Using the deployment script

```bash
./deploy_crawler.sh
```

### Option 2: Manual deployment

```bash
# Install Modal
pip install modal

# Deploy
modal deploy crawler/modal_deploy.py
```

## What Gets Deployed

The Modal deployment creates a cloud function that:

- Wraps your existing crawler logic
- Runs in a container with all necessary dependencies
- Can be triggered remotely or scheduled
- Handles CSV input and JSONL output
- Has configurable limits and parameters

## Configuration

The Modal function accepts these parameters:

- `input_csv_path`: Path to your CSV file
- `output_jsonl_path`: Where to save results
- `limit`: Maximum domains to process (default: 10)
- `domain_column`: CSV column with domains (default: "tam_site")
- `id_column`: CSV column with record IDs (default: "Record ID")

## Usage After Deployment

### Remote execution

```python
import modal

# Get the deployed function
crawl_fn = modal.Function.from_name("uptick-crawler", "crawl_domains")

# Execute with custom parameters
result = crawl_fn.remote(
    limit=20,
    input_csv_path="your-data.csv"
)
```

### Web interface

Visit: https://modal.com/apps/seth-1/uptick-crawler

## Dependencies

The Modal container includes:

- Python 3.11
- crawl4ai (core crawling)
- playwright (browser automation)
- pandas (CSV handling)
- aiohttp (async HTTP)

## Resource Limits

- **Timeout**: 1 hour
- **Memory**: 2GB RAM
- **CPU**: 1 core
- **Concurrency**: 2 (reduced from 4 for stability)

## Troubleshooting

1. **Installation issues**: Make sure you have Modal CLI installed
2. **Permission errors**: Run `chmod +x deploy_crawler.sh`
3. **Dependency issues**: Check that all requirements are in requirements.txt

## Next Steps

After deployment, you can:

1. Test with small datasets first
2. Monitor logs in the Modal dashboard
3. Scale resources if needed
4. Add scheduling for automated runs
