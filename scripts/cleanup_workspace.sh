#!/bin/bash
#
# Workspace Cleanup Script - FAANG Quality
#
# Cleans temporary files, caches, and build artifacts to optimize Codespace performance
# and prevent VS Code/Claude restart issues.
#
# Usage:
#   ./scripts/cleanup_workspace.sh [--dry-run]
#
# Author: StarHouse CRM
# Date: 2025-11-15

set -euo pipefail

# Configuration
WORKSPACE_ROOT="/workspaces/starhouse-database-v2"
LOG_FILE="logs/cleanup_$(date +%Y%m%d_%H%M%S).log"
DRY_RUN=false

# Parse arguments
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No files will be deleted"
    echo ""
fi

# Create logs directory
mkdir -p logs

# Logging function
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Metrics tracking
declare -A METRICS_BEFORE
declare -A METRICS_AFTER

# Measure before cleanup
measure_before() {
    log "=" "Measuring workspace before cleanup..."
    log ""

    METRICS_BEFORE[pycache]=$(find "$WORKSPACE_ROOT" -type d -name "__pycache__" 2>/dev/null | wc -l)
    METRICS_BEFORE[nextjs]=$(du -sb "$WORKSPACE_ROOT/starhouse-ui/.next" 2>/dev/null | cut -f1 || echo "0")
    METRICS_BEFORE[logs_count]=$(find "$WORKSPACE_ROOT/logs" -name "*.log" 2>/dev/null | wc -l)
    METRICS_BEFORE[logs_size]=$(du -sb "$WORKSPACE_ROOT/logs" 2>/dev/null | cut -f1 || echo "0")
    METRICS_BEFORE[temp_csv]=$(ls "$WORKSPACE_ROOT"/*.csv 2>/dev/null | wc -l)
    METRICS_BEFORE[git_changed]=$(git -C "$WORKSPACE_ROOT" status --porcelain 2>/dev/null | wc -l)
    METRICS_BEFORE[total_size]=$(du -sb "$WORKSPACE_ROOT" 2>/dev/null | cut -f1)

    log "Before Cleanup:"
    log "  Python cache dirs:    ${METRICS_BEFORE[pycache]}"
    log "  Next.js build:        $(numfmt --to=iec ${METRICS_BEFORE[nextjs]})"
    log "  Log files:            ${METRICS_BEFORE[logs_count]} files ($(numfmt --to=iec ${METRICS_BEFORE[logs_size]}))"
    log "  Temp CSV files:       ${METRICS_BEFORE[temp_csv]}"
    log "  Git changed files:    ${METRICS_BEFORE[git_changed]}"
    log "  Total workspace:      $(numfmt --to=iec ${METRICS_BEFORE[total_size]})"
    log ""
}

# Cleanup function
cleanup_item() {
    local description="$1"
    local pattern="$2"
    local find_type="${3:-f}"  # f=file, d=directory

    log "Cleaning: $description"

    if [[ "$DRY_RUN" == true ]]; then
        local count=$(find $pattern -type $find_type 2>/dev/null | wc -l)
        log "  [DRY RUN] Would remove $count items"
    else
        local count=$(find $pattern -type $find_type 2>/dev/null | wc -l)
        find $pattern -type $find_type -print0 2>/dev/null | xargs -0 rm -rf
        log "  ✅ Removed $count items"
    fi
}

# Main cleanup operations
run_cleanup() {
    log "=" "Starting Workspace Cleanup..."
    log ""

    # 1. Python cache
    cleanup_item "Python __pycache__ directories" \
        "$WORKSPACE_ROOT -name __pycache__" \
        "d"

    # 2. Python .pyc files
    cleanup_item "Python .pyc files" \
        "$WORKSPACE_ROOT -name *.pyc" \
        "f"

    # 3. Pytest cache
    cleanup_item "Pytest cache directories" \
        "$WORKSPACE_ROOT -name .pytest_cache" \
        "d"

    # 4. Next.js build artifacts
    if [[ -d "$WORKSPACE_ROOT/starhouse-ui/.next" ]]; then
        log "Cleaning: Next.js build directory"
        if [[ "$DRY_RUN" == true ]]; then
            local size=$(du -sh "$WORKSPACE_ROOT/starhouse-ui/.next" 2>/dev/null | cut -f1)
            log "  [DRY RUN] Would remove .next/ ($size)"
        else
            local size=$(du -sh "$WORKSPACE_ROOT/starhouse-ui/.next" 2>/dev/null | cut -f1)
            rm -rf "$WORKSPACE_ROOT/starhouse-ui/.next"
            log "  ✅ Removed .next/ ($size)"
        fi
    fi

    # 5. TypeScript build info
    cleanup_item "TypeScript build info files" \
        "$WORKSPACE_ROOT -name *.tsbuildinfo" \
        "f"

    # 6. Temporary CSV files in root
    cleanup_item "Temporary CSV files (root)" \
        "$WORKSPACE_ROOT -maxdepth 1 -name *.csv -not -name README.md" \
        "f"

    # 7. Old log files (>7 days)
    log "Cleaning: Log files older than 7 days"
    if [[ "$DRY_RUN" == true ]]; then
        local count=$(find "$WORKSPACE_ROOT/logs" -name "*.log" -mtime +7 -type f 2>/dev/null | wc -l)
        log "  [DRY RUN] Would remove $count old log files"
    else
        local count=$(find "$WORKSPACE_ROOT/logs" -name "*.log" -mtime +7 -type f 2>/dev/null | wc -l)
        find "$WORKSPACE_ROOT/logs" -name "*.log" -mtime +7 -type f -delete 2>/dev/null
        log "  ✅ Removed $count old log files"
    fi

    # 8. Temp files in /tmp
    log "Cleaning: Temp NCOA files in /tmp"
    if [[ "$DRY_RUN" == true ]]; then
        local count=$(ls /tmp/ncoa_*.log 2>/dev/null | wc -l)
        log "  [DRY RUN] Would remove $count temp files"
    else
        local count=$(ls /tmp/ncoa_*.log 2>/dev/null | wc -l)
        rm -f /tmp/ncoa_*.log 2>/dev/null || true
        log "  ✅ Removed $count temp files"
    fi

    log ""
}

# Measure after cleanup
measure_after() {
    if [[ "$DRY_RUN" == true ]]; then
        log "Skipping metrics (dry-run mode)"
        return
    fi

    log "=" "Measuring workspace after cleanup..."
    log ""

    METRICS_AFTER[pycache]=$(find "$WORKSPACE_ROOT" -type d -name "__pycache__" 2>/dev/null | wc -l)
    METRICS_AFTER[nextjs]=$(du -sb "$WORKSPACE_ROOT/starhouse-ui/.next" 2>/dev/null | cut -f1 || echo "0")
    METRICS_AFTER[logs_count]=$(find "$WORKSPACE_ROOT/logs" -name "*.log" 2>/dev/null | wc -l)
    METRICS_AFTER[logs_size]=$(du -sb "$WORKSPACE_ROOT/logs" 2>/dev/null | cut -f1 || echo "0")
    METRICS_AFTER[temp_csv]=$(ls "$WORKSPACE_ROOT"/*.csv 2>/dev/null | wc -l)
    METRICS_AFTER[git_changed]=$(git -C "$WORKSPACE_ROOT" status --porcelain 2>/dev/null | wc -l)
    METRICS_AFTER[total_size]=$(du -sb "$WORKSPACE_ROOT" 2>/dev/null | cut -f1)

    log "After Cleanup:"
    log "  Python cache dirs:    ${METRICS_AFTER[pycache]} (was ${METRICS_BEFORE[pycache]})"
    log "  Next.js build:        $(numfmt --to=iec ${METRICS_AFTER[nextjs]}) (was $(numfmt --to=iec ${METRICS_BEFORE[nextjs]}))"
    log "  Log files:            ${METRICS_AFTER[logs_count]} files (was ${METRICS_BEFORE[logs_count]})"
    log "  Temp CSV files:       ${METRICS_AFTER[temp_csv]} (was ${METRICS_BEFORE[temp_csv]})"
    log "  Git changed files:    ${METRICS_AFTER[git_changed]} (was ${METRICS_BEFORE[git_changed]})"
    log "  Total workspace:      $(numfmt --to=iec ${METRICS_AFTER[total_size]}) (was $(numfmt --to=iec ${METRICS_BEFORE[total_size]}))"
    log ""

    # Calculate savings
    local saved=$((METRICS_BEFORE[total_size] - METRICS_AFTER[total_size]))
    log "💾 Space Saved: $(numfmt --to=iec $saved)"
    log ""
}

# Print summary
print_summary() {
    log "=" "Cleanup Summary"
    log ""
    if [[ "$DRY_RUN" == true ]]; then
        log "✅ Dry-run complete - no files were deleted"
        log "   Run without --dry-run to perform actual cleanup"
    else
        log "✅ Workspace cleanup complete"
        log "   Log file: $LOG_FILE"
    fi
    log ""
    log "Recommended: Restart VS Code for best performance"
    log ""
}

# Main execution
main() {
    cd "$WORKSPACE_ROOT"

    measure_before
    run_cleanup
    measure_after
    print_summary
}

main
