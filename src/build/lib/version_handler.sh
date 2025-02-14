#!/bin/bash

source "src/build/lib/utils.sh"
source "src/build/lib/config.sh"

# Version management utilities
get_compatible_version() {
    local package_name=$1
    local cli_version=$(get_cli_version)
    
    if [ "$cli_version" -ge 5 ]; then
        java -jar *cli*.jar list-patches --with-packages --with-versions *.rvp | \
            awk -v pkg="$package_name" '
                BEGIN { found = 0 }
                /^Index:/ { found = 0 }
                /Package name: / { if ($3 == pkg) { found = 1 } }
                /Compatible versions:/ {
                    if (found) {
                        getline
                        latest_version = $1
                        while (getline && $1 ~ /^[0-9]+\./) {
                            latest_version = $1
                        }
                        print latest_version
                        exit
                    }
                }'
    else
        jq -r "[.. | objects | select(.name == \"$package_name\" and .versions != null) | .versions[]] | reverse | .[0] // \"\"" *.json | uniq
    fi
}

format_version() {
    local version=$1
    echo "$version" | tr -d ' ' | sed 's/\./-/g'
}

validate_version() {
    local version=$1
    local package_name=$2
    
    if [ -z "$version" ]; then
        red_log "[-] Could not determine compatible version for $package_name"
        return 1
    fi
    
    return 0
} 