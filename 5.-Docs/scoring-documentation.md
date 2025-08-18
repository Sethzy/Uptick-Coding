# Scoring Module Documentation

## Feature Overview

The **Scoring Module** is a lightweight LLM scoring pipeline designed to classify business domains based on aggregated website content. This feature solves the problem of manually categorizing companies by analyzing their web presence and automatically determining their business mix classification.

**Business Value:**

- Automates the tedious process of business classification
- Provides consistent, AI-powered categorization using LLM reasoning
- Scales to handle large volumes of domain analysis
- Generates structured outputs for further business intelligence processing

**Target Users:**

- Business analysts and researchers
- Sales and marketing teams
- Data scientists working with company classification
- Operations teams needing automated business categorization

**Use Cases:**

- Lead scoring and qualification
- Market research and competitive analysis
- Business intelligence and reporting
- Customer segmentation and targeting

## Application Structure

The scoring module consists of the following core components:

### Core Files

- **`__init__.py`** - Public API surface exposing `score_domain` and `score_labeled_file`
- **`api.py`** - Main scoring logic and LLM integration
- **`models.py`** - Pydantic data models for structured data handling
- **`cli.py`** - Command-line interface for batch processing
- **`config.py`** - Configuration management and environment variables
- **`io_jsonl.py`** - JSONL input/output operations
- **`io_csv.py`** - CSV output generation
- **`logging.py`** - Logging utilities
- **`run.py`** - Console script entry point

### Component Hierarchy

```
scoring/
├── __init__.py (Public API)
├── api.py (Core Logic)
│   ├── score_domain() - Single domain scoring
│   └── score_labeled_file() - Batch labeled dataset processing
├── models.py (Data Models)
│   ├── ClassificationResult
│   ├── LabeledDatasetRecord
│   └── Evidence
├── cli.py (CLI Interface)
├── config.py (Configuration)
├── io_jsonl.py (JSONL I/O)
├── io_csv.py (CSV Output)
├── logging.py (Logging)
└── run.py (Entry Point)
```

## Functionalities Overview

### 1. Single Domain Scoring (`score_domain`)

**Purpose:** Classify a single business domain using aggregated website content
**Files Involved:** `api.py`, `models.py`, `config.py`, `logging.py`
**Data Flow:**

- Input: domain string + aggregated context
- Process: LLM API call with structured prompt
- Output: ClassificationResult with category and rationale

**Key Features:**

- Automatic retry logic for transient errors
- Configurable model selection and timeout
- Structured JSON output parsing
- Comprehensive error handling and logging

### 2. Batch Labeled Dataset Processing (`score_labeled_file`)

**Purpose:** Process multiple domains from JSONL input files
**Files Involved:** `api.py`, `io_jsonl.py`, `io_csv.py`, `cli.py`
**Data Flow:**

- Input: JSONL file with multiple domain contexts
- Process: Iterative domain scoring with progress tracking
- Output: JSONL and/or CSV results files

**Key Features:**

- Progress tracking and logging
- Graceful error handling (continues on individual failures)
- Multiple output format support
- Batch processing optimization

### 3. Command-Line Interface

**Purpose:** Provide user-friendly CLI for batch processing
**Files Involved:** `cli.py`, `api.py`, `config.py`
**Functionality:**

- `scorer classify` command with options
- Input/output file specification
- Model and timeout configuration
- Environment validation

### 4. Data I/O Operations

**Purpose:** Handle various input/output formats and data validation
**Files Involved:** `io_jsonl.py`, `io_csv.py`, `models.py`

**JSONL Operations:**

- Stream processing for large files
- Pydantic model validation
- Efficient memory usage

**CSV Operations:**

- Structured output with evidence columns
- Consistent field mapping
- UTF-8 encoding support

## Technical Implementation

### Technology Stack

- **Python 3.10+** - Core runtime
- **Pydantic 2.8.2+** - Data validation and serialization
- **httpx 0.27.0+** - HTTP client for LLM API calls
- **Click 8.1.7+** - CLI framework
- **python-dotenv 1.0.1+** - Environment variable management

### Dependencies

```toml
dependencies = [
    "httpx>=0.27.0",      # HTTP client
    "click>=8.1.7",        # CLI framework
    "pydantic>=2.8.2",     # Data validation
    "python-dotenv>=1.0.1" # Environment management
]
```

### LLM Integration

- **Provider:** OpenRouter API
- **Default Model:** `qwen/qwen3-30b-a3b`
- **Response Format:** JSON with structured schema
- **Authentication:** API key via environment variables

### Configuration Management

- Environment variable support (`.env` file)
- Configurable model parameters (temperature, top_p, max_tokens)
- Timeout and retry configuration
- API endpoint customization

### Build and Deployment

- **Package Name:** `uptick-scoring`
- **Entry Point:** `scorer` command-line tool
- **Installation:** Standard Python package installation
- **Scripts:** Console script entry point via `scoring.cli:scorer`

## Integration Points

### External Integrations

- **OpenRouter API** - LLM service provider
- **Environment Variables** - Configuration and authentication
- **File System** - Input/output file handling

### Internal Application Integration

- **Crawler Module** - Receives aggregated context data
- **Data Processing Pipeline** - Provides structured classification results
- **Business Intelligence Tools** - CSV/JSONL output consumption

### API Contracts

- **Input Schema:** `LabeledDatasetRecord` with domain, aggregated_context, and business intelligence fields
- **Output Schema:** `ClassificationResult` with classification and rationale
- **File Formats:** JSONL for input, JSONL/CSV for output

### Configuration Requirements

- `OPENROUTER_API_KEY` or `OPENROUTER_KEY` environment variable
- Optional `OPENROUTER_ENDPOINT` for custom endpoints
- `.env` file support for local development

## Development Status

### Current Status

- ✅ Core scoring functionality implemented
- ✅ CLI interface complete
- ✅ Multiple output format support
- ✅ Error handling and retry logic
- ✅ Comprehensive logging
- ✅ Data validation with Pydantic

### Known Limitations

- Single LLM provider (OpenRouter)
- Fixed classification schema (4 categories)
- Limited evidence tracking in current CSV output
- No async processing for large batches

### Planned Improvements

- Support for multiple LLM providers
- Configurable classification schemas
- Enhanced evidence tracking and storage
- Async processing for improved performance
- Model performance metrics and analytics
- Custom prompt templates

### Future Enhancements

- Web interface for interactive scoring
- Real-time scoring API endpoints
- Integration with business intelligence platforms
- Advanced analytics and reporting
- Machine learning model fine-tuning

## Usage Examples

### Python API Usage

```python
from scoring import score_domain, score_labeled_file

# Score a single domain
result = score_domain(
    domain="example.com",
    aggregated_context="Company provides maintenance services...",
    model="qwen/qwen3-30b-a3b"
)

# Process a file of domains
results = score_labeled_file(
    input_jsonl="domains.jsonl",
    output_jsonl="results.jsonl",
    output_csv="results.csv"
)
```

### Command Line Usage

```bash
# Basic classification
scorer classify --input-jsonl domains.jsonl --output-csv results.csv

# With custom model and timeout
scorer classify \
  --input-jsonl domains.jsonl \
  --output-jsonl results.jsonl \
  --output-csv results.csv \
  --model "qwen/qwen3-30b-a3b" \
  --timeout-seconds 120
```

### Input File Format (JSONL)

```jsonl
{"domain": "company1.com", "aggregated_context": "Company provides..."}
{"domain": "company2.com", "aggregated_context": "Installation services..."}
```

### Output Format

**JSONL Output:**

```jsonl
{
  "domain": "company1.com",
  "classification_category": "Maintenance & Service Only",
  "rationale": "Website content focuses on..."
}
```

**CSV Output:**

```csv
domain,classification_category,rationale,evidence_url_1,evidence_snippet_1,...
company1.com,Maintenance & Service Only,Website content focuses on...,,,...
```

## Troubleshooting Guide

### Common Issues

**1. API Key Not Found**

```
Error: OpenRouter key not found (set OPENROUTER_API_KEY or OPENROUTER_KEY, or .env)
```

**Solution:** Set environment variable `OPENROUTER_API_KEY` or create `.env` file

**2. LLM API Timeout**

```
Error: Timeout after 90 seconds
```

**Solution:** Increase `--timeout-seconds` parameter or check network connectivity

**3. JSON Parsing Errors**

```
Error: Invalid JSON response from LLM
```

**Solution:** Check LLM model compatibility, verify prompt format

**4. File Permission Errors**

```
Error: Permission denied when writing output files
```

**Solution:** Check write permissions for output directory

### Debug Mode

Enable verbose logging by setting environment variable:

```bash
export SCORING_DEBUG=1
```

### Performance Optimization

- Use appropriate timeout values for your network
- Process large files in smaller batches
- Monitor API rate limits and adjust accordingly
- Consider using faster LLM models for high-volume processing

### Error Recovery

The system automatically:

- Retries transient HTTP errors (up to 3 attempts)
- Continues processing on individual domain failures
- Logs detailed error information for debugging
- Provides graceful degradation for partial failures
