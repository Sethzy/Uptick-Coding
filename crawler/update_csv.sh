#!/bin/bash

# CSV Configuration Update Script for Uptick Crawler
# Usage: ./update_csv.sh [options]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "config.json" ]; then
    echo "❌ Please run this script from the crawler/ directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "No virtual environment detected"
    print_warning "Consider activating your virtual environment first"
fi

# Function to show current config
show_config() {
    print_info "Current CSV configuration:"
    python3 update_csv_config.py --show
}

# Function to update CSV file
update_csv_file() {
    if [ -z "$1" ]; then
        echo "❌ Please specify a CSV file path"
        echo "Usage: ./update_csv.sh --file path/to/your/file.csv"
        exit 1
    fi
    
    print_info "Updating CSV file to: $1"
    python3 update_csv_config.py --csv-file "$1"
}

# Function to update domain column
update_domain_column() {
    if [ -z "$1" ]; then
        echo "❌ Please specify a domain column name"
        echo "Usage: ./update_csv.sh --domain-column column_name"
        exit 1
    fi
    
    print_info "Updating domain column to: $1"
    python3 update_csv_config.py --domain-column "$1"
}

# Function to update ID column
update_id_column() {
    if [ -z "$1" ]; then
        echo "❌ Please specify an ID column name"
        echo "Usage: ./update_csv.sh --id-column column_name"
        exit 1
    fi
    
    print_info "Updating ID column to: $1"
    python3 update_csv_config.py --id-column "$1"
}

# Function to show help
show_help() {
    echo "🚀 CSV Configuration Update Script"
    echo ""
    echo "Usage: ./update_csv.sh [options]"
    echo ""
    echo "Options:"
    echo "  --file, -f <path>           Update default CSV file path"
    echo "  --domain-column, -d <name>  Update domain column name"
    echo "  --id-column, -i <name>      Update ID column name"
    echo "  --show, -s                  Show current configuration"
    echo "  --help, -h                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./update_csv.sh --file ../new_domains.csv"
    echo "  ./update_csv.sh --domain-column website"
    echo "  ./update_csv.sh --id-column id"
    echo "  ./update_csv.sh --show"
    echo ""
    echo "After updating config, run crawler normally:"
    echo "  python3 run_crawl.py"
}

# Main logic
case "${1:-help}" in
    "--file"|"-f")
        update_csv_file "$2"
        ;;
    "--domain-column"|"-d")
        update_domain_column "$2"
        ;;
    "--id-column"|"-i")
        update_id_column "$2"
        ;;
    "--show"|"-s")
        show_config
        ;;
    "--help"|"-h"|"help"|*)
        show_help
        ;;
esac
