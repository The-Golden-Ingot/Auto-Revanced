#!/bin/bash

source "src/build/lib/utils.sh"
source "src/build/lib/config.sh"

# APK download and processing utilities
download_apk() {
    local package_name=$1
    local output_name=$2
    local app_type=$3
    local app_path=$4
    local arch=${5:-""}
    local dpi=${6:-""}
    
    green_log "[+] Downloading ${app_type} APK..."
    
    local version
    if [ -z "$version" ] && [ "$lock_version" != "1" ]; then
        version=$(get_compatible_version "$package_name")
    fi
    
    if [ -n "$version" ]; then
        download_specific_version "$output_name" "$app_type" "$app_path" "$version" "$arch" "$dpi"
    else
        download_latest_version "$output_name" "$app_type" "$app_path" "$arch" "$dpi"
    fi
}

split_apk() {
    local input_name=$1
    local output_name=$2
    local mode=${3:-"exclude"}
    local config_files=$4
    
    green_log "[+] Splitting APK ${input_name}..."
    
    if [ ! -d "${DOWNLOAD_DIR}/${input_name}" ]; then
        red_log "[-] Input directory not found: ${input_name}"
        return 1
    fi
    
    mkdir -p "${DOWNLOAD_DIR}/${output_name}"
    
    # Copy base APK
    cp -f "${DOWNLOAD_DIR}/${input_name}/base.apk" "${DOWNLOAD_DIR}/${output_name}/"
    
    # Process split APKs
    for file in "${DOWNLOAD_DIR}/${input_name}"/*.apk; do
        local filename=$(basename "$file")
        if [ "$filename" = "base.apk" ]; then continue; fi
        
        local basename_no_ext="${filename%.apk}"
        if should_process_file "$mode" "$basename_no_ext" "$config_files"; then
            cp -f "$file" "${DOWNLOAD_DIR}/${output_name}/"
        fi
    done
    
    merge_splits "$output_name"
}

merge_splits() {
    local name=$1
    green_log "[+] Merging split APKs for ${name}..."
    java -jar "$APK_EDITOR" m \
        -i "${DOWNLOAD_DIR}/${name}" \
        -o "${DOWNLOAD_DIR}/${name}.apk" > /dev/null 2>&1
} 