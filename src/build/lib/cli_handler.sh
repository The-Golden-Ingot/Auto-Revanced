#!/bin/bash

source "src/build/lib/utils.sh"
source "src/build/lib/config.sh"

# CLI version handling utilities
get_cli_version() {
    if [[ $(ls revanced-cli-*.jar) =~ revanced-cli-([0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo "0"
    fi
}

cli_version_ge() {
    local required_version=$1
    local current_version=$(get_cli_version)
    
    if [ "$current_version" -ge "$required_version" ]; then
        return 0
    else
        return 1
    fi
}

setup_cli_env() {
    local cli_version=$1
    
    if [ "$cli_version" = "inotia" ]; then
        unset CI GITHUB_ACTION GITHUB_ACTIONS GITHUB_ACTOR GITHUB_ENV \
              GITHUB_EVENT_NAME GITHUB_EVENT_PATH GITHUB_HEAD_REF \
              GITHUB_JOB GITHUB_REF GITHUB_REPOSITORY GITHUB_RUN_ID \
              GITHUB_RUN_NUMBER GITHUB_SHA GITHUB_WORKFLOW GITHUB_WORKSPACE \
              RUN_ID RUN_NUMBER
    fi
} 