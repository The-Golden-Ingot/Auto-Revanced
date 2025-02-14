#!/bin/bash
# Revanced Extended forked by Anddea build

source src/build/lib/utils.sh

# Configuration
PATCHES_REPO="anddea/revanced-patches"
CLI_REPO="inotia00/revanced-cli"

# Download requirements
setup_requirements() {
    green_log "[+] Downloading build requirements..."
    
    # Download patches and CLI
    dl_gh "$PATCHES_REPO" "prerelease"
    dl_gh "$CLI_REPO" "latest"
    
    # Setup patch configuration
    get_patches_key "youtube-rve-anddea"
}

# Build YouTube with architecture splits
build_youtube() {
    local arch=$1
    local libs=$2
    
    green_log "[+] Building YouTube for ${arch}..."
    
    # Get base APK if not already downloaded
    if [ ! -f "./download/youtube-beta.apk" ]; then
        get_apk "com.google.android.youtube" "youtube-beta" "youtube" "google-inc/youtube/youtube"
    fi
    
    # Apply patches with architecture-specific options
    local patch_opts="$(gen_rip_libs ${libs})"
    apply_patches "youtube-beta" "youtube-${arch}-anddea" "${patch_opts}"
}

main() {
    # Initial setup
    setup_requirements
    
    # Build base version
    patch "youtube-beta" "anddea" "inotia"
    
    # Build architecture-specific versions
    declare -A arch_configs=(
        ["arm64-v8a"]="armeabi-v7a x86_64 x86"
        ["armeabi-v7a"]="arm64-v8a x86_64 x86"
        ["x86_64"]="armeabi-v7a arm64-v8a x86"
        ["x86"]="armeabi-v7a arm64-v8a x86_64"
    )
    
    for arch in "${!arch_configs[@]}"; do
        build_youtube "$arch" "${arch_configs[$arch]}"
    done
}

# Execute main function
main
