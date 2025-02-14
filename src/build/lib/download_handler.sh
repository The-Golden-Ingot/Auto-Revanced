#!/bin/bash

source "src/build/lib/utils.sh"
source "src/build/lib/config.sh"

# Download APK from APKMirror
get_apk() {
    local pkg_name=$1
    local output_name=$2
    local app_type=$3
    local apkmirror_dlurl=$4
    local bundle_type=${5:-""}  # Default to empty string if not provided
    local version=${6:-""}      # Default to empty string if not provided
    
    green_log "[+] Building ${output_name}..."
    
    # Check if APK already exists
    if [ -f "./download/${output_name}.apk" ]; then
        return 0
    fi
    
    # Construct APKMirror URL
    local base_url="https://www.apkmirror.com"
    local version_url
    
    # Get version-specific URL if version is provided
    if [ -n "$version" ]; then
        version_url="${base_url}/apk/${apkmirror_dlurl}/${app_type}-${version}-release/"
        green_log "[+] Attempting download of ${pkg_name} version: ${version}"
    else
        # Get latest version URL
        version_url="${base_url}/uploads/?appcategory=${pkg_name}"
    fi
    
    # Get download page URL using our robust get_download_url function
    local download_url=$(get_download_url "$version_url")
    if [ -z "$download_url" ]; then
        red_log "[-] Failed to find download URL for ${pkg_name}"
        return 1
    fi
    
    # Get APK download link
    local apk_url="${base_url}${download_url}"
    local final_url=$(wget -qO- "$apk_url" | $pup 'a[href*="/download/"].downloadButton attr{href}' | head -n 1)
    if [ -z "$final_url" ]; then
        red_log "[-] Failed to get final download URL"
        return 1
    fi
    
    # Download APK
    green_log "[+] Downloading APK..."
    download_file "${base_url}${final_url}" "${output_name}.apk"
    
    # Handle bundle if needed
    if [ "$bundle_type" = "Bundle_extract" ] && [ -f "./download/${output_name}.apk" ]; then
        green_log "[+] Extracting bundle..."
        mkdir -p "./download/${output_name}-bundle"
        unzip -q "./download/${output_name}.apk" -d "./download/${output_name}-bundle"
        local base_apk=$(find "./download/${output_name}-bundle" -name "base.apk")
        [ -f "$base_apk" ] && mv "$base_apk" "./download/${output_name}.apk"
    fi
    
    # Verify download
    if [ ! -f "./download/${output_name}.apk" ]; then
        red_log "[-] Failed to download APK"
        return 1
    fi
    
    green_log "[+] Successfully downloaded ${output_name}"
    return 0
}

# GitHub download utilities
dl_gh() {
    local repo=$1
    local release_type=$2
    
    green_log "[+] Downloading from GitHub: ${repo} (${release_type})"
    
    local owner="${repo%/*}"
    local repo_name="${repo#*/}"
    local api_response
    
    if [ "$release_type" = "latest" ]; then
        api_response=$(fetch_github_release "$owner" "$repo_name" "latest")
    else
        api_response=$(fetch_github_release "$owner" "$repo_name" "")
    fi
    
    echo "$api_response" | jq -r 'if type=="array" then .[] else . end | .assets[] | select(.name | test("\\.(jar|apk|rvp)$")) | .browser_download_url' | \
    while read -r url; do
        local filename=$(basename "$url")
        download_file "$url" "$filename"
    done
}

# Format version string to be compatible with APKMirror URLs
format_version() {
    local version=$1
    
    if [ -z "$version" ]; then
        return 1
    fi
    
    # Remove any whitespace and replace dots with hyphens
    echo "$version" | tr -d ' ' | sed 's/\./-/g'
}

# Helper function to get download URL from APKMirror
get_download_url() {
    local page_url=$1
    local download_page=$(download_file "$page_url" -)
    
    # Check if the download page is empty
    if [ -z "$download_page" ]; then
        red_log "[-] Download page is empty for URL: $page_url"
        echo ""
        return
    fi
    
    # Try different selectors in sequence using pup
    local apk_url
    apk_url=$(echo "$download_page" | $pup 'a[data-google-vignette="false"]:contains("Download APK") attr{href}' | head -1)
    if [ -z "$apk_url" ]; then
        apk_url=$(echo "$download_page" | $pup 'a.accent_color[href*="/download/"] attr{href}' | head -1)
    fi
    
    # Fallback using grep with a more robust regex pattern (matches both double and single quotes)
    if [ -z "$apk_url" ]; then
        apk_url=$(echo "$download_page" | grep -oE "https://www\\.apkmirror\\.com/apk/[^\"'\\s<>]+" | head -1)
    fi

    # Validate URL format
    if [[ -n "$apk_url" ]]; then
        [[ "$apk_url" != http* ]] && apk_url="https://www.apkmirror.com$apk_url"
        echo "$apk_url"
    else
        red_log "[-] No download link found on page: $page_url"
        echo ""
    fi
}

# Patch key utilities
get_patches_key() {
    echo "--keystore=./src/_ks.keystore"
} 