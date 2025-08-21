#!/bin/bash

# Quick Score - Easy scoring commands for the Uptick scoring module
# Usage: ./quick_score.sh [command] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🚀 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "quick_start.py" ]; then
    print_error "Please run this script from the scoring/ directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "No virtual environment detected"
    print_warning "Consider activating your virtual environment first"
fi

# Main command logic
case "${1:-help}" in
    "score")
        if [ -z "$2" ]; then
            print_error "Please provide an input file"
            echo "Usage: ./quick_score.sh score <input_file> [output_file] [model] [hubspot_csv]"
            exit 1
        fi
        
        print_status "Starting quick score..."
        python3 -m scoring.quick_start score "$2" ${3:+--output "$3"} ${4:+--model "$4"} ${5:+--hubspot-csv "$5"}
        ;;
        
    "enrich")
        if [ -z "$2" ] || [ -z "$3" ]; then
            print_error "Please provide both input file and HubSpot CSV"
            echo "Usage: ./quick_score.sh enrich <input_file> <hubspot_csv> [output_file]"
            exit 1
        fi
        
        print_status "Starting data enrichment..."
        python3 -m scoring.quick_start enrich "$2" "$3" ${4:+--output "$4"}
        ;;
        
    "check")
        print_status "Checking setup..."
        python3 -m scoring.quick_start check-setup
        ;;
        
    "sample")
        print_status "Running sample scoring..."
        python3 -m scoring.quick_start score-sample ${2:+--sample-size "$2"}
        ;;
        
    "help"|*)
        echo "🚀 Quick Score - Uptick Scoring Module"
        echo ""
        echo "Commands:"
        echo "  enrich <input_file> <hubspot_csv> [output] - Enrich crawler data with HubSpot CSV"
        echo "  score <input_file> [output] [model] [csv]  - Score a JSONL file (with optional enrichment)"
        echo "  check                                      - Check module setup"
        echo "  sample [size]                             - Run sample scoring"
        echo "  help                                       - Show this help"
        echo ""
        echo "Examples:"
        echo "  ./quick_score.sh enrich crawl_data.jsonl uptick-csvs/enriched-hutbpot-tam-v2.csv"
        echo "  ./quick_score.sh score crawl_data.jsonl"
        echo "  ./quick_score.sh score crawl_data.jsonl results.jsonl qwen/qwen3-30b-a3b uptick-csvs/enriched-hutbpot-tam-v2.csv"
        echo "  ./quick_score.sh check"
        echo "  ./quick_score.sh sample 10"
        echo ""
        echo "Environment:"
        echo "  Set OPENROUTER_API_KEY for authentication"
        echo "  Create .env file for local development"
        ;;
esac
