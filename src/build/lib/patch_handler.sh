#!/bin/bash

source "src/build/lib/utils.sh"
source "src/build/lib/config.sh"
source "src/build/lib/error_handler.sh"

# Patch application utilities
apply_patch_set() {
    local input_name=$1
    local patch_set=$2
    local options=$3
    local cli_version=$4
    
    green_log "[+] Applying patch set ${patch_set} to ${input_name}..."
    
    # Validate input
    if [ ! -f "${DOWNLOAD_DIR}/${input_name}.apk" ]; then
        red_log "[-] Input APK not found: ${input_name}.apk"
        return 1
    fi
    
    # Load patch configuration
    load_patch_config "$patch_set"
    
    # Apply patches based on CLI version
    if [ "$cli_version" = "inotia" ]; then
        apply_inotia_patches "$input_name" "$patch_set" "$options"
    else
        apply_standard_patches "$input_name" "$patch_set" "$options"
    fi
}

load_patch_config() {
    local patch_set=$1
    local exclude_file="${PATCHES_DIR}/${patch_set}/exclude-patches"
    local include_file="${PATCHES_DIR}/${patch_set}/include-patches"
    
    # Reset patch configurations
    excludePatches=""
    includePatches=""
    
    # Load CLI version specific configurations
    if cli_version_ge 5; then
        load_v5_config "$exclude_file" "$include_file"
    else
        load_legacy_config "$exclude_file" "$include_file"
    fi
} 