#!/bin/bash
# ReVanced Experiments build script

source "src/build/lib/utils.sh"
source "src/build/lib/config.sh"
source "src/build/lib/error_handler.sh"
source "src/build/lib/download_handler.sh"
source "src/build/lib/patch_handler.sh"
source "src/build/lib/cli_handler.sh"
source "src/build/lib/init.sh"

# Initialize environment
init_build_env

# Download requirements
setup_requirements() {
    green_log "[+] Downloading build requirements..."
    
    # Download patches and CLI
    dl_gh "${REPOS[experiments]%%|*}" "latest"
    dl_gh "${REPOS[revanced_cli]%%|*}" "latest"
    
    # Setup patch configuration
    get_patches_key "instagram-experiments"
}

# Build Instagram
build_instagram() {
    green_log "[+] Building Instagram..."
    
    # Get base APK if not already downloaded
    if [ ! -f "${DOWNLOAD_DIR}/instagram.apk" ]; then
        get_apk "com.instagram.android" "instagram" "instagram" "instagram/instagram"
    fi
    
    # Apply patches
    apply_patch_set "instagram" "instagram-experiments" "" "standard"
}

main() {
    # Initial setup
    setup_requirements
    
    # Build Instagram
    build_instagram
}

# Execute main function
main