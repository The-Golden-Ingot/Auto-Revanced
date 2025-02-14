#!/bin/bash

# Error handling utilities
set -o errexit  # Exit on error
set -o nounset  # Exit on undefined variable
set -o pipefail # Exit on pipe failure

# Error handler
error_handler() {
    local line_no=$1
    local command=$2
    local error_code=$3
    red_log "[-] Error occurred in command '$command' on line $line_no (exit code: $error_code)"
}

trap 'error_handler ${LINENO} "$BASH_COMMAND" $?' ERR

# Validation utilities
validate_requirements() {
    local missing_deps=()
    
    # Check required commands
    for cmd in java wget unzip jq; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        red_log "[-] Missing required dependencies: ${missing_deps[*]}"
        exit 1
    fi
} 