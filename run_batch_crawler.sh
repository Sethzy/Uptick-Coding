#!/bin/bash

# Purpose: Manual batch processing script for Modal crawler
# Description: Runs one batch at a time with persistent progress tracking
# Usage: ./run_batches.sh [batch_number] or ./run_batches.sh --status
#        ./run_batches.sh --next (runs next uncompleted batch)

set -e  # Exit on any error

# Configuration
TOTAL_DOMAINS=10097  # Actual number of domains in enriched-hubspot-TAM-08-25.csv
BATCH_SIZE=1000
TOTAL_BATCHES=$((TOTAL_DOMAINS / BATCH_SIZE))
PROGRESS_FILE="crawler/.batch_progress"  # Save in crawler directory
LOG_FILE="crawler/batch_log.txt"         # Log file for tracking
CSV_FILE="uptick-csvs/enriched-hubspot-TAM-08-25.csv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
show_help() {
    echo "Usage:"
    echo "  ./run_batches.sh                    # Show status and help"
    echo "  ./run_batches.sh --status          # Show current progress"
    echo "  ./run_batches.sh --next            # Run next uncompleted batch"
    echo "  ./run_batches.sh <batch_number>    # Run specific batch (1-5)"
    echo "  ./run_batches.sh --deploy          # Deploy Modal app only"
    echo "  ./run_batches.sh --reset           # Reset progress (start over)"
    echo "  ./run_batches.sh --log             # Show recent batch logs"
    echo ""
    echo "Batch breakdown:"
    echo "  Batch 1: domains 0-999"
    echo "  Batch 2: domains 1000-1999"
    echo "  Batch 3: domains 2000-2999"
    echo "  Batch 4: domains 3000-3999"
    echo "  Batch 5: domains 4000-4999"
    echo "  Batch 6: domains 5000-5999"
    echo "  Batch 7: domains 6000-6999"
    echo "  Batch 8: domains 7000-7999"
    echo "  Batch 9: domains 8000-8999"
    echo "  Batch 10: domains 9000-9999"
    echo "  Batch 11: domains 10000-10096"
    echo ""
    echo "Progress is saved to: $PROGRESS_FILE"
    echo "Logs are saved to: $LOG_FILE"
    echo "Input CSV: $CSV_FILE"
}

load_progress() {
    if [ -f "$PROGRESS_FILE" ]; then
        source "$PROGRESS_FILE"
    else
        # Initialize progress file
        mkdir -p "$(dirname "$PROGRESS_FILE")"
        cat > "$PROGRESS_FILE" << EOF
# Batch progress tracking - DO NOT EDIT MANUALLY
COMPLETED_BATCHES=()
CURRENT_BATCH=1
LAST_RUN_DATE=""
TOTAL_COMPLETED=0
TOTAL_ROWS_SCRAPED=0
BATCH_ROWS=()
EOF
        source "$PROGRESS_FILE"
    fi
}

save_progress() {
    mkdir -p "$(dirname "$PROGRESS_FILE")"
    cat > "$PROGRESS_FILE" << EOF
# Batch progress tracking - DO NOT EDIT MANUALLY
COMPLETED_BATCHES=(${COMPLETED_BATCHES[@]})
CURRENT_BATCH=$CURRENT_BATCH
LAST_RUN_DATE="$(date)"
TOTAL_COMPLETED=${#COMPLETED_BATCHES[@]}
TOTAL_ROWS_SCRAPED=$TOTAL_ROWS_SCRAPED
BATCH_ROWS=(${BATCH_ROWS[@]})
EOF
}

log_batch_event() {
    local event=$1
    local batch_num=$2
    local details=$3
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$timestamp] $event: Batch $batch_num - $details" >> "$LOG_FILE"
}

mark_batch_complete() {
    local batch_num=$1
    local session_id=$2
    local rows_scraped=$3
    
    if [[ ! " ${COMPLETED_BATCHES[@]} " =~ " ${batch_num} " ]]; then
        COMPLETED_BATCHES+=($batch_num)
        BATCH_ROWS+=($rows_scraped)
        TOTAL_ROWS_SCRAPED=$((TOTAL_ROWS_SCRAPED + rows_scraped))
        log_batch_event "COMPLETED" $batch_num "Session: $session_id, Rows: $rows_scraped"
    fi
    CURRENT_BATCH=$((batch_num + 1))
    save_progress
}

show_status() {
    echo -e "${BLUE}📊 Batch Processing Status${NC}"
    echo "================================"
    echo "Total domains: $TOTAL_DOMAINS"
    echo "Batch size: $BATCH_SIZE"
    echo "Total batches: $TOTAL_BATCHES"
    echo "Progress file: $PROGRESS_FILE"
    echo ""
    
    if [ -n "$LAST_RUN_DATE" ]; then
        echo "Last run: $LAST_RUN_DATE"
    fi
    echo "Completed: ${#COMPLETED_BATCHES[@]}/$TOTAL_BATCHES batches"
    echo "Total rows scraped: $TOTAL_ROWS_SCRAPED"
    echo ""
    
    echo "Progress:"
    for ((batch=1; batch<=TOTAL_BATCHES; batch++)); do
        if [[ " ${COMPLETED_BATCHES[@]} " =~ " ${batch} " ]]; then
            # Find the index of this batch in completed batches
            local batch_index=-1
            for i in "${!COMPLETED_BATCHES[@]}"; do
                if [[ "${COMPLETED_BATCHES[$i]}" == "$batch" ]]; then
                    batch_index=$i
                    break
                fi
            done
            
            if [ $batch_index -ge 0 ] && [ $batch_index -lt ${#BATCH_ROWS[@]} ]; then
                local rows=${BATCH_ROWS[$batch_index]}
                echo -e "  ${GREEN}✅ Batch $batch: COMPLETED (${rows} rows)${NC}"
            else
                echo -e "  ${GREEN}✅ Batch $batch: COMPLETED${NC}"
            fi
        elif [ $batch -eq $CURRENT_BATCH ]; then
            echo -e "  ${YELLOW}🔄 Batch $batch: NEXT TO RUN${NC}"
        else
            echo -e "  ${BLUE}⏳ Batch $batch: PENDING${NC}"
        fi
    done
    
    echo ""
    if [ ${#COMPLETED_BATCHES[@]} -eq $TOTAL_BATCHES ]; then
        echo -e "${GREEN}🎉 All batches completed!${NC}"
    else
        echo -e "${YELLOW}Next batch to run: Batch $CURRENT_BATCH${NC}"
        echo "Run: ./run_batches.sh --next"
    fi
    
    echo ""
    echo "💡 Progress persists across terminal sessions!"
    echo "📁 Check status anytime: ./run_batches.sh --status"
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}📋 Recent Batch Logs${NC}"
        echo "========================"
        tail -20 "$LOG_FILE"
        echo ""
        echo "Full log: $LOG_FILE"
    else
        echo "No logs found yet."
    fi
}

run_batch() {
    local batch_num=$1
    local start_index=$(((batch_num - 1) * BATCH_SIZE))
    local end_index=$((start_index + BATCH_SIZE - 1))
    
    echo -e "${BLUE}🔄 Processing Batch ${batch_num}/${TOTAL_BATCHES} (domains ${start_index}-${end_index})${NC}"
    echo "⏰ Started at: $(date)"
    
    # Check if Modal is available
    if ! command -v modal &> /dev/null; then
        echo -e "${RED}❌ Modal CLI not found. Please install Modal first:${NC}"
        echo "   pip install modal"
        exit 1
    fi
    
    log_batch_event "STARTED" $batch_num "Domains $start_index-$end_index"
    
    # Run the crawler for this batch and capture output
    if [ $start_index -eq 0 ]; then
        echo "🚀 Running: modal run crawler/modal_deploy_real.py --limit ${BATCH_SIZE}"
        modal_output=$(modal run crawler/modal_deploy_real.py --limit ${BATCH_SIZE} 2>&1)
    else
        echo "🚀 Running: modal run crawler/modal_deploy_real.py --from-index ${start_index} --limit ${BATCH_SIZE}"
        modal_output=$(modal run crawler/modal_deploy_real.py --from-index ${start_index} --limit ${BATCH_SIZE} 2>&1)
    fi
    
    # Show the output for debugging
    echo "$modal_output"
    
    # Extract session ID and rows count from Modal output
    local session_id="batch_${batch_num}_$(date +%Y%m%d_%H%M%S)"
    
    # Parse Modal output to get actual rows count
    # Look for lines like "📄 Output lines: 5" in the output
    local actual_rows=$(echo "$modal_output" | grep "📄 Output lines:" | sed 's/.*📄 Output lines: \([0-9]*\).*/\1/' | head -1)
    
    if [ -n "$actual_rows" ] && [ "$actual_rows" -gt 0 ]; then
        local rows_scraped=$actual_rows
        echo "📊 Actual rows scraped: $rows_scraped"
    else
        # Fallback to estimated rows based on domains processed
        local rows_scraped=$BATCH_SIZE
        echo "📊 Estimated rows scraped: $rows_scraped (actual count not found in output)"
    fi
    
    echo -e "${GREEN}✅ Batch ${batch_num} completed at: $(date)${NC}"
    echo "💾 Session ID: $session_id"
    mark_batch_complete $batch_num $session_id $rows_scraped
}

deploy_app() {
    echo -e "${BLUE}📦 Deploying Modal app...${NC}"
    modal deploy crawler/modal_deploy_real.py
    echo -e "${GREEN}✅ Modal app deployed!${NC}"
    log_batch_event "DEPLOYED" "N/A" "Modal app deployment"
}

reset_progress() {
    echo -e "${YELLOW}⚠️  Resetting batch progress...${NC}"
    rm -f "$PROGRESS_FILE"
    load_progress
    log_batch_event "RESET" "N/A" "Progress reset to start"
    echo -e "${GREEN}✅ Progress reset. Ready to start from Batch 1.${NC}"
}

# Main script logic
load_progress

case "${1:-}" in
    "--help"|"-h"|"")
        show_help
        show_status
        ;;
    "--status")
        show_status
        ;;
    "--log")
        show_logs
        ;;
    "--next")
        if [ $CURRENT_BATCH -le $TOTAL_BATCHES ]; then
            run_batch $CURRENT_BATCH
        else
            echo -e "${GREEN}🎉 All batches are already completed!${NC}"
        fi
        ;;
    "--deploy")
        deploy_app
        ;;
    "--reset")
        reset_progress
        ;;
    [1-9]|1[0-1])
        batch_num=$1
        if [ $batch_num -le $TOTAL_BATCHES ]; then
            run_batch $batch_num
        else
            echo -e "${RED}❌ Invalid batch number. Use 1-11.${NC}"
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}❌ Invalid option: $1${NC}"
        show_help
        exit 1
        ;;
esac
