# Modal Deployment Documentation

## Feature Overview

The Modal deployment feature enables cloud-based execution of the Uptick crawler system through Modal's serverless infrastructure. This feature solves the problem of resource-intensive web crawling by providing scalable, on-demand computing resources in the cloud.

**Business Value:**

- Eliminates local resource constraints for large-scale crawling operations
- Provides enterprise-grade scalability and reliability
- Enables concurrent processing of multiple domains
- Reduces infrastructure management overhead

**Target Users:**

- Data analysts requiring large-scale web crawling
- Development teams needing scalable crawling infrastructure
- Business users requiring reliable, cloud-based crawling services

## Application Structure

### Core Files

- `crawler/modal_deploy_real.py` - Main deployment configuration and Modal app definition
- `crawler/run_crawl.py` - Core crawling logic executed in Modal containers
- `crawler/config.json` - Configuration parameters for crawling behavior

### Component Hierarchy

```
Modal App (uptick-crawler-real)
├── Container Image
│   ├── Python 3.11 Environment
│   ├── Dependencies (crawl4ai, playwright, fastapi, etc.)
│   └── Browser Automation (Chromium)
├── Functions
│   ├── crawl_domains_real (Simple API)
│   └── crawl_http_api (HTTP Web Endpoint)
└── Mounted Resources
    ├── Crawler Code (/root/crawler)
    └── Input CSV (/root/test.csv)
```

### Dependencies

- **Modal**: Cloud infrastructure and container management
- **FastAPI**: HTTP API framework for web endpoints
- **Playwright**: Browser automation for JavaScript-heavy sites
- **crawl4ai**: Core crawling and extraction logic

## Functionalities Overview

### 1. Simple API Function (`crawl_domains_real`)

**Purpose**: Direct function execution for local development and testing
**Files Involved**: `modal_deploy_real.py`, `run_crawl.py`
**Data Flow**:

```
Local Call → Modal Container → CSV Processing → Crawler Execution → Results Return
```

**Functionalities**:

- CSV file processing with configurable column mapping
- Domain crawling with configurable limits and concurrency
- Result aggregation and JSON output generation
- Error handling and status reporting

### 2. HTTP API Function (`crawl_http_api`)

**Purpose**: Web-accessible endpoint for external integrations
**Files Involved**: `modal_deploy_real.py`, `run_crawl.py`
**Data Flow**:

```
HTTP Request → Request Validation → Temporary CSV Creation → Crawler Execution → HTTP Response
```

**Functionalities**:

- RESTful POST endpoint with JSON request validation
- Dynamic CSV generation from request payload
- Same crawling logic as simple API
- Web-accessible from any HTTP client

### 3. Container Management

**Purpose**: Automated environment setup and dependency management
**Files Involved**: `modal_deploy_real.py`
**Functionalities**:

- Automated Python environment setup
- Browser installation and configuration
- Code mounting and file synchronization
- Resource allocation and scaling

## Technical Implementation

### Technology Stack

- **Container Runtime**: Modal's custom container infrastructure
- **Python Version**: 3.11 (Debian slim base)
- **Web Framework**: FastAPI with automatic OpenAPI documentation
- **Browser Automation**: Playwright with Chromium
- **Data Processing**: Pandas for CSV handling

### Dependencies Installation

```python
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "python-dotenv>=1.0.1",
        "crawl4ai",
        "playwright",
        "pandas",
        "fastapi[standard]",
        # ... additional dependencies
    )
    .run_commands(
        "playwright install chromium",
        "playwright install-deps chromium"
    )
)
```

### Resource Configuration

```python
@app.function(
    image=image,
    timeout=1800,      # 30 minutes maximum runtime
    memory=4096,       # 4GB RAM allocation
    cpu=2.0,          # 2 CPU cores for concurrent processing
)
```

### Build and Deployment Process

1. **Image Building**: Modal automatically builds container image with dependencies
2. **Code Mounting**: Local crawler code is mounted to `/root/crawler`
3. **Function Registration**: Functions are registered with Modal's infrastructure
4. **Deployment**: App is deployed to Modal's cloud infrastructure

## Integration Points

### Existing System Integration

- **Crawler Logic**: Integrates with existing `run_crawl.py` implementation
- **Configuration**: Uses existing `config.json` for crawling parameters
- **Output Format**: Maintains compatibility with existing result structures

### New Interfaces Introduced

- **HTTP API Endpoint**: New web-accessible interface for external systems
- **Modal Function Interface**: New cloud execution interface
- **Concurrent Processing**: Enhanced concurrency support for multiple domains

### External Integrations

- **Modal Cloud Platform**: Container orchestration and scaling
- **Web Clients**: HTTP API accessible from any web application
- **Browser Automation**: Playwright integration for JavaScript rendering

## Development Status

### Current Status: ✅ PRODUCTION READY

- **Simple API**: Fully functional and tested
- **HTTP API**: Deployed and accessible
- **Container Infrastructure**: Stable and optimized
- **Error Handling**: Comprehensive error handling implemented

### Known Issues

- **None currently identified**

### Planned Improvements

- **Custom Domain Support**: Add support for custom domain names
- **Authentication**: Implement API key authentication for HTTP endpoints
- **Monitoring**: Add comprehensive logging and monitoring
- **Auto-scaling**: Implement automatic scaling based on demand

## Quick Start Guide

### Local Version (Simple API) - Quick Start

#### Prerequisites

- Python 3.11+ installed
- Modal CLI configured (`modal setup`)
- Virtual environment activated

#### Step 1: Deploy the App

```bash
# Navigate to project directory
cd /path/to/uptick-coding

# Activate virtual environment
source venv/bin/activate

# Deploy to Modal (first time only)
modal deploy crawler/modal_deploy_real.py
```

#### Step 2: Run Local Test

```bash
# Test the deployed crawler
modal run crawler/modal_deploy_real.py
```

#### Step 3: Use in Your Python Code

```python
import modal

# Get your deployed app
app = modal.App('uptick-crawler-real')

# Call the crawler function
result = app.crawl_domains_real.remote(
    limit=5,                           # Number of domains to process
    domain_column="Company Domain Name", # CSV column name for domains
    id_column="Record ID"              # CSV column name for IDs
)

print(f"Status: {result['status']}")
print(f"Domains processed: {result['domains_processed']}")
```

### HTTP Version (Web API) - Quick Start

#### Prerequisites

- Modal app deployed (follow Local Version steps 1-2)
- HTTP client (browser, Postman, curl, etc.)

#### Step 1: Get Your API URL

```bash
# Run this to get your web URL
modal run crawler/modal_deploy_real.py
```

Look for this output:

```
🌐 HTTP API URL: https://your-workspace--uptick-crawler-real-crawl-http-api.modal.run
📖 API Documentation: https://your-workspace--uptick-crawler-real-crawl-http-api.modal.run/docs
```

#### Step 2: Test with cURL

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"domains": [{"domain": "example.com", "id": "12345"}]}' \
  https://your-workspace--uptick-crawler-real-crawl-http-api.modal.run
```

#### Step 3: Use in JavaScript/Web

```javascript
// Replace with your actual API URL
const API_URL =
  "https://your-workspace--uptick-crawler-real-crawl-http-api.modal.run";

fetch(API_URL, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    domains: [
      { domain: "example.com", id: "12345" },
      { domain: "another.com", id: "67890" },
    ],
  }),
})
  .then((response) => response.json())
  .then((data) => {
    console.log("Crawler results:", data);
    // Process results in your application
  });
```

#### Step 4: View API Documentation

Open your browser and navigate to:

```
https://your-workspace--uptick-crawler-real-crawl-http-api.modal.run/docs
```

This provides interactive API documentation and testing interface.

### Quick Start Troubleshooting

#### Common Quick Start Issues

**Issue**: `modal: command not found`
**Solution**: Install Modal CLI

```bash
pip install modal
modal setup
```

**Issue**: Deployment fails with authentication error
**Solution**: Configure Modal authentication

```bash
modal token new
# Follow the prompts to authenticate
```

**Issue**: HTTP API returns 404
**Solution**: Verify deployment and get correct URL

```bash
# Check if app is deployed
modal app list

# Get the correct web URL
modal run crawler/modal_deploy_real.py
```

**Issue**: CSV file not found
**Solution**: Ensure test.csv exists

```bash
# Create test CSV if missing
mkdir -p uptick-csvs
echo "Company Domain Name,Record ID" > uptick-csvs/test.csv
echo "example.com,12345" >> uptick-csvs/test.csv
```

## Usage Examples

```python
import modal

# Get deployed app
app = modal.App('uptick-crawler-real')

# Call crawler function
result = app.crawl_domains_real.remote(
    limit=5,
    domain_column="Company Domain Name",
    id_column="Record ID"
)

print(f"Status: {result['status']}")
print(f"Domains processed: {result['domains_processed']}")
```

### HTTP API Usage (Web Integration)

```javascript
// JavaScript example
fetch("https://seth-1--uptick-crawler-real-crawl-http-api.modal.run", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    domains: [{ domain: "example.com", id: "12345" }],
  }),
})
  .then((response) => response.json())
  .then((data) => console.log(data));
```

### cURL Usage

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"domains": [{"domain": "example.com", "id": "12345"}]}' \
  https://seth-1--uptick-crawler-real-crawl-http-api.modal.run
```

## Troubleshooting Guide

### Common Issues

#### 1. Deployment Failures

**Symptoms**: Modal deployment fails with dependency errors
**Solution**:

- Verify all dependencies are correctly specified in `modal_deploy_real.py`
- Check Python version compatibility
- Ensure Playwright dependencies are properly configured

#### 2. HTTP API Not Accessible

**Symptoms**: 404 errors when calling HTTP endpoint
**Solution**:

- Verify the app is deployed: `modal app list`
- Check the correct web URL: `crawl_http_api.get_web_url()`
- Ensure the function has `@modal.fastapi_endpoint` decorator

#### 3. Container Timeout

**Symptoms**: Functions fail with timeout errors
**Solution**:

- Increase `timeout` parameter in function decorator
- Optimize crawling logic for faster execution
- Check for infinite loops or blocking operations

#### 4. Memory Issues

**Symptoms**: Container crashes with memory errors
**Solution**:

- Increase `memory` parameter in function decorator
- Optimize data structures and processing
- Implement streaming for large datasets

### Debugging Commands

```bash
# Check app status
modal app list

# View app logs
modal app logs uptick-crawler-real

# Check function calls
modal function calls uptick-crawler-real::crawl_domains_real

# Redeploy app
modal deploy crawler/modal_deploy_real.py
```

### Performance Optimization

- **Concurrency**: Set `concurrency` parameter to match CPU cores
- **Memory**: Allocate sufficient memory for browser automation
- **Timeout**: Set appropriate timeout based on expected crawling duration
- **Resource Limits**: Configure `limit` parameter to control domain processing

## Configuration Reference

### Function Parameters

```python
@app.function(
    image=image,           # Container image with dependencies
    timeout=1800,          # Maximum runtime in seconds
    memory=4096,           # Memory allocation in MB
    cpu=2.0,              # CPU cores allocation
)
```

### HTTP API Configuration

```python
@modal.fastapi_endpoint(
    method="POST",         # HTTP method
    docs=True,            # Enable OpenAPI documentation
)
```

### Crawler Configuration

```json
{
  "page_cap": 8,
  "global_concurrency": 2,
  "per_domain_delay_seconds": {
    "min": 1.5,
    "max": 2.0,
    "jitter": 0.4
  }
}
```

## Version History

### v1.0.0 (Current)

- **Initial Release**: Basic Modal deployment with simple API
- **HTTP API**: Web-accessible endpoint for external integrations
- **Container Optimization**: Optimized resource allocation and concurrency
- **Error Handling**: Comprehensive error handling and status reporting

### Future Versions

- **v1.1.0**: Custom domain support and authentication
- **v1.2.0**: Advanced monitoring and logging
- **v1.3.0**: Auto-scaling and performance optimization
- **v2.0.0**: Multi-region deployment and load balancing

---

_Last Updated: January 2025_  
_Documentation Version: 1.0.0_  
_Maintainer: Development Team_
