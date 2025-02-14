#!/bin/bash
# Revanced Extended forked by Anddea build
source src/build/utils.sh

# Download requirements
revanced_dl() {
    dl_gh "revanced-patches" "anddea" "prerelease"
    dl_gh "revanced-cli" "inotia00" "latest"
}

# Patch YouTube with architecture splits
patch_youtube() {
    revanced_dl
    # Get patches and base APK
    get_patches_key "youtube-rve-anddea"
    get_apk "com.google.android.youtube" "youtube-beta" "youtube" "google-inc/youtube/youtube"
    
    # Patch base version
    patch "youtube-beta" "anddea" "inotia"
    
    # Split and patch for different architectures
    get_patches_key "youtube-rve-anddea"
    for i in {0..3}; do
        split_arch "youtube-beta" "anddea" "$(gen_rip_libs ${libs[i]})"
    done
}

# Main execution
patch_youtube
