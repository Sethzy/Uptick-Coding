# 🚀 Quick Start Guide - Uptick Scoring Module

This guide shows you how to quickly get started with the scoring module using simplified commands.

## Prerequisites

1. **Python 3.10+** installed
2. **OpenRouter API Key** set as environment variable
3. **Dependencies** installed (`pip install -r requirements.txt`)

## Quick Commands

### 1. Enrich Data (New!)

First, enrich your crawler data with HubSpot CSV data:

```bash
# From the scoring/ directory
./quick_score.sh enrich ../crawl_20250818_184945_5domains_with_keywords.jsonl ../uptick-csvs/enriched-hubspot-TAM-08-25.csv

# Or using Python directly
python3 -m scoring.quick_start enrich ../crawl_20250818_184945_5domains_with_keywords.jsonl ../uptick-csvs/enriched-hubspot-TAM-08-25.csv
```

### 2. Check Setup

```bash
# From the scoring/ directory
./quick_score.sh check

# Or using Python directly
python3 -m scoring.quick_start check-setup
```

### 2. Score a File

Score a JSONL file with sensible defaults. You can now score either:

- **Enriched data** (recommended): Use the output from the enrich step
- **Raw crawler data**: The system will work but HubSpot fields will be empty

```bash
# Basic scoring (auto-generates output filename)
./quick_score.sh score crawl_data.jsonl

# Specify output file
./quick_score.sh score input.jsonl output_scored.jsonl

# Specify custom model
./quick_score.sh score data.jsonl results.jsonl qwen/qwen3-30b-a3b
```

### 3. Run Sample Scoring

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
DEFAULT_LLM_MODEL=qwen/qwen3-30b-a3b
```

## Examples

### Complete Workflow from Project Root

```bash
cd /path/to/Uptick-Coding

# Step 1: Enrich crawler data with HubSpot CSV
cd scoring
./quick_score.sh enrich ../crawl_20250818_184945_5domains_with_keywords.jsonl ../uptick-csvs/enriched-hubspot-TAM-08-25.csv

# Step 2: Score the enriched data
./quick_score.sh score ../crawl_20250818_184945_5domains_with_keywords_enriched.jsonl

# Or do both in one step (enrich + score)
./quick_score.sh score ../crawl_20250818_184945_5domains_with_keywords.jsonl ../results.jsonl qwen/qwen3-30b-a3b ../uptick-csvs/enriched-hubspot-TAM-08-25.csv
```

### Check Setup Before Running

```bash
cd scoring
./quick_score.sh check
./quick_score.sh score your_data.jsonl
```

## What Each Command Does

- **`enrich`**: Merges crawler JSONL data with HubSpot CSV data to create enriched dataset
- **`score`**: Runs the full scoring pipeline on your JSONL file (enriched or raw)
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
