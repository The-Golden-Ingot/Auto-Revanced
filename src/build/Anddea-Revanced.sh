#!/bin/bash
# Revanced Extended forked by Anddea build

source "src/build/lib/utils.sh"
source "src/build/lib/config.sh"
source "src/build/lib/error_handler.sh"
source "src/build/lib/download_handler.sh"
source "src/build/lib/patch_handler.sh"
source "src/build/lib/cli_handler.sh"
source "src/build/lib/init.sh"

# Initialize environment
init_build_env

# Configuration
PATCHES_REPO="anddea/revanced-patches"
CLI_REPO="inotia00/revanced-cli"

# Download requirements
setup_requirements() {
    green_log "[+] Downloading build requirements..."
    
    # Download patches and CLI
    dl_gh "${REPOS[anddea]%%|*}" "prerelease"
    dl_gh "${REPOS[anddea_cli]%%|*}" "latest"
    
    # Setup patch configuration
    get_patches_key "youtube-rve-anddea"
}

# Build YouTube with architecture splits
build_youtube() {
    local arch=$1
    local libs=$2
    local version=${YOUTUBE_VERSION:-""}  # Default to empty if not set
    
    green_log "[+] Building YouTube for ${arch}..."
    
    # Get base APK if not already downloaded
    if [ ! -f "${DOWNLOAD_DIR}/youtube-beta.apk" ]; then
        get_apk "com.google.android.youtube" "youtube-beta" "youtube" \
                "google-inc/youtube/youtube" "Bundle_extract" "$version"
    fi
    
    # Apply patches with architecture-specific options
    local patch_opts="--rip-lib $(echo "$libs" | tr ' ' ' --rip-lib ')"
    apply_patch_set "youtube-beta" "youtube-${arch}-anddea" "${patch_opts}" "inotia"
}

main() {
    # Initial setup
    setup_requirements
    
    # Build architecture-specific versions
    for arch in "${!ARCH_CONFIGS[@]}"; do
        build_youtube "$arch" "${ARCH_CONFIGS[$arch]}"
    done

    # After main build loop
    split_editor "youtube" "youtube-arm64-v8a" "exclude" "split_config.armeabi_v7a split_config.x86 split_config.x86_64"
    apply_patch_set "youtube-arm64-v8a" "youtube-anddea" "" "inotia"
}

# Execute main function
main
