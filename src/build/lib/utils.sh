#!/bin/bash

# Common utility functions for build scripts

# Logging utilities
log() {
    local color=$1
    local message=$2
    echo -e "\e[${color}m${message}\e[0m"
}

green_log() { log "32" "$1"; }
red_log() { log "31" "$1"; }
yellow_log() { log "33" "$1"; }

# Download utilities
download_file() {
    local url=$1
    local output=$2
    local headers=(
        "User-Agent: Mozilla/5.0 (Android 14; Mobile; rv:134.0) Gecko/134.0 Firefox/134.0"
        "Content-Type: application/octet-stream"
        "Accept-Language: en-US,en;q=0.9"
        "Connection: keep-alive"
        "Upgrade-Insecure-Requests: 1"
        "Cache-Control: max-age=0"
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
    )
    
    local header_args=""
    for header in "${headers[@]}"; do
        header_args+=" --header='${header}'"
    done

    if [ "$output" = "-" ]; then
        eval wget -nv -O "$output" $header_args --keep-session-cookies --timeout=30 "$url" || rm -f "$output"
    else
        eval wget -nv -O "./download/$output" $header_args --keep-session-cookies --timeout=30 "$url" || rm -f "./download/$output"
    fi
}

# GitHub API utilities
fetch_github_release() {
    local owner=$1
    local repo=$2
    local tag=$3
    
    local api_url="https://api.github.com/repos/${owner}/${repo}/releases"
    if [ "$tag" = "latest" ]; then
        api_url+="/latest"
    elif [ "$tag" = "tags" ]; then
        api_url+="/tags/${tag}"
    fi
    
    wget -qO- "$api_url"
}

# Patch utilities
apply_patches() {
    local input_apk=$1
    local output_name=$2
    local patch_options=$3
    
    green_log "[+] Patching ${input_apk}..."
    
    if [ ! -f "./download/${input_apk}.apk" ]; then
        red_log "[-] Input APK not found: ${input_apk}.apk"
        return 1
    fi
    
    java -jar *cli*.jar patch \
        -p *.rvp \
        ${patch_options} \
        --out="./release/${output_name}.apk" \
        "./download/${input_apk}.apk"
}

split_editor() {
    local input_name=$1
    local output_name=$2
    local mode=${3:-""}  # Set empty default
    local config_files=${4:-""}  # Set empty default
    
    if [[ -z "$mode" || -z "$config_files" ]]; then
        green_log "[+] Merge splits apk to standalone apk"
        java -jar "$APK_EDITOR" m -i "./download/$input_name" -o "./download/$input_name.apk" > /dev/null 2>&1
        return 0
    fi
    
    IFS=' ' read -r -a include_files <<< "$config_files"
    mkdir -p "./download/$output_name"
    
    for file in "./download/$input_name"/*.apk; do
        filename=$(basename "$file")
        basename_no_ext="${filename%.apk}"
        if [[ "$filename" == "base.apk" ]]; then
            cp -f "$file" "./download/$output_name/" > /dev/null 2>&1
            continue
        fi
        if [[ "$mode" == "include" ]]; then
            if [[ " ${include_files[*]} " =~ " ${basename_no_ext} " ]]; then
                cp -f "$file" "./download/$output_name/" > /dev/null 2>&1
            fi
        elif [[ "$mode" == "exclude" ]]; then
            if [[ ! " ${include_files[*]} " =~ " ${basename_no_ext} " ]]; then
                cp -f "$file" "./download/$output_name/" > /dev/null 2>&1
            fi
        fi
    done

    green_log "[+] Merge splits apk to standalone apk"
    java -jar "$APK_EDITOR" m -i "./download/$output_name" -o "./download/$output_name.apk" > /dev/null 2>&1
}

# Export the function for subshell usage
export -f split_editor 