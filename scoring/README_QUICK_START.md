# 🚀 Quick Start Guide - Uptick Scoring Module

This guide shows you how to quickly get started with the scoring module using simplified commands.

## Prerequisites

1. **Python 3.10+** installed
2. **OpenRouter API Key** set as environment variable
3. **Dependencies** installed (`pip install -r requirements.txt`)

## 🎯 Recommended Workflow

**Always enrich your crawler data with HubSpot CSV data first, then score.** This ensures you have complete business context for better classification results.

```
Crawler Data (JSONL) → Enrich with HubSpot CSV → Score → Results
```

## Quick Commands

### 1. Enrich Data (Required First Step!)

**Always start here!** Enrich your crawler data with HubSpot CSV data:

```bash
# From the scoring/ directory
./quick_score.sh enrich ../crawl_data.jsonl ../uptick-csvs/enriched-hubspot-TAM-08-25.csv

# Or using Python directly
python3 -m scoring.quick_start enrich ../crawl_data.jsonl ../uptick-csvs/enriched-hubspot-TAM-08-25.csv
```

### 2. Check Setup

```bash
# From the scoring/ directory
./quick_score.sh check

# Or using Python directly
python3 -m scoring.quick_start check-setup
```

### 3. Score Your Data

The `score` command now automatically detects whether you're using raw crawler data or enriched data, and handles both seamlessly:

```bash
# Score enriched data (recommended - better results)
./quick_score.sh score crawl_data_enriched.jsonl

# Score raw crawler data (will work but HubSpot fields will be empty)
./quick_score.sh score crawl_data.jsonl

# Score with automatic enrichment in one step
./quick_score.sh score crawl_data.jsonl results.jsonl qwen/qwen3-30b-a3b ../uptick-csvs/enriched-hubspot-TAM-08-25.csv

# Specify output file
./quick_score.sh score data.jsonl output_scored.jsonl

# Specify custom model (overrides .env default)
./quick_score.sh score data.jsonl results.jsonl qwen/qwen3-30b-a3b
```

### 4. Run Sample Scoring

Test with a small sample:

```bash
# Sample with default size (5 records)
./quick_score.sh sample

# Sample with custom size
./quick_score.sh sample 10
```

## Environment Setup

### Option 1: Environment Variable

```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

### Option 2: .env File

Create a `.env` file in your project root:

```bash
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_ENDPOINT=https://openrouter.ai/api/v1
CUSTOM_MODEL=qwen/qwen3-30b-a3b-instruct-2507
DEFAULT_LLM_MODEL=qwen/qwen3-30b-a3b
CONTEXT_SIZE=128000
```

**Note**: The `CUSTOM_MODEL` variable is used as the primary default model for all scoring operations. If not set, it falls back to `DEFAULT_LLM_MODEL`.

## Examples

### Complete Workflow from Project Root (Recommended)

```bash
cd /path/to/Uptick-Coding

# Step 1: Enrich crawler data with HubSpot CSV (ALWAYS DO THIS FIRST!)
cd scoring
./quick_score.sh enrich ../crawl_data.jsonl ../uptick-csvs/enriched-hubspot-TAM-08-25.csv

# Step 2: Score the enriched data (uses CUSTOM_MODEL from .env)
./quick_score.sh score ../crawl_data_enriched.jsonl

# Or do both in one step (enrich + score)
./quick_score.sh score ../crawl_data.jsonl ../results.jsonl ../uptick-csvs/enriched-hubspot-TAM-08-25.csv
```

### Quick Test Run

```bash
cd scoring
./quick_score.sh check
./quick_score.sh sample 5  # Test with 5 records
```

## What Each Command Does

- **`enrich`**: **REQUIRED FIRST STEP** - Merges crawler JSONL data with HubSpot CSV data to create enriched dataset
- **`score`**: **SMART SCORING** - Automatically detects data type and runs scoring (works with both raw and enriched data)
- **`check`**: Verifies API keys, dependencies, and module availability
- **`sample`**: Runs scoring on a small subset for testing
- **`help`**: Shows available commands and examples

## Data Flow

```
Crawler Data (JSONL) + HubSpot CSV → Enrich → Enriched JSONL → Score → Scored Results
     ↓                    ↓              ↓           ↓           ↓
domain, context...   Company info...  Merged    LLM Scoring  Final Output
                     State, Industry   Data      + Results    + All Fields
```

## Why Enrichment is Important

**Enrichment provides crucial business context that significantly improves classification accuracy:**

- **Company Information**: Size, industry, location, employee count
- **Contact Data**: Decision makers, titles, LinkedIn profiles  
- **Business Context**: Current software, lead status, company age
- **Geographic Data**: State, county, country for territory analysis

**Without enrichment, the scoring system only sees website content and may miss important business context.**

## Troubleshooting

### Missing API Key

```
❌ Error: OpenRouter API key not found!
   Set OPENROUTER_API_KEY environment variable or create a .env file
```

**Solution**: Set your OpenRouter API key as described in Environment Setup above.

### Module Import Errors

```
❌ Scoring modules: Error - [error details]
```

**Solution**: Make sure you're running from the correct directory and have all dependencies installed.

### No JSONL Files Found

```
❌ No JSONL files found in current directory
```

**Solution**: Run the command from a directory containing JSONL files, or specify the full path to your input file.

### Validation Errors

```
❌ Error during scoring: [validation errors]
```

**Solution**: Use the `enrich` command first to add HubSpot data, then score. The `score` command now automatically handles both data types.

## Advanced Usage

For more control, you can still use the original CLI:

```bash
python3 -m scoring.cli classify --input-jsonl input.jsonl --output-jsonl output.jsonl --model qwen/qwen3-30b-a3b
```

## File Structure

```
scoring/
├── quick_start.py      # Quick start Python module
├── quick_score.sh      # Shell script wrapper
├── README_QUICK_START.md  # This file
├── cli.py             # Original CLI
├── api.py             # Core scoring logic
└── ...
```