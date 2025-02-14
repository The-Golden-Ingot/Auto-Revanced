#!/bin/bash

source "src/build/lib/utils.sh"
source "src/build/lib/config.sh"

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
    
    # Download assets with improved jq filter to handle both object and array responses
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

# APK Mirror download utilities
get_apk() {
    local package_name=$1
    local app_name=$2
    local apk_name=$3
    local apk_path=$4
    local app_type=$5
    local version=$6
    local output_name="$2"
    
    local attempt=0
    local base_apk
    
    # Set default app_type if not provided
    [[ -z "$app_type" ]] && app_type="apk"
    
    while [ $attempt -lt 10 ]; do
        if [[ -z $version ]] || [ $attempt -ne 0 ]; then
            local upload_tail="?$( [[ "$apk_name" == "duolingo" ]] && echo "devcategory=" || echo "appcategory=" )"
            version=$(download_file "https://www.apkmirror.com/uploads/$upload_tail$apk_name" - | \
                $pup 'div.listWidget a.accent_color[title*="APK"] text{}' | \
                grep -oP '[\d\.]+(?:-[\w\d]+)?' | \
                sort -Vr | \
                sed -n "$((attempt + 1))p")
        fi
        
        # Don't format version if it's explicitly provided
        if [[ -z "$6" ]]; then
            version=$(echo "$version" | tr -d ' ' | sed 's/\./-/g')
        fi
        
        green_log "[+] Attempting download of $apk_name version: $version"
        
        # Fix URL construction to match APKMirror's format
        local dl_url
        if [[ "$app_type" == "Bundle" ]] || [[ "$app_type" == "Bundle_extract" ]]; then
            dl_url=$(get_download_url "https://www.apkmirror.com/apk/$apk_path/$apk_name-$version-release/")
        else
            dl_url=$(get_download_url "https://www.apkmirror.com/apk/$apk_path/$apk_name-$version-release/")
        fi
        
        green_log "[+] Trying URL: $dl_url"
        
        if [ -n "$dl_url" ]; then
            if download_file "$dl_url" "$output_name.$([[ "$app_type" =~ Bundle ]] && echo "apkm" || echo "apk")"; then
                green_log "[+] Successfully downloaded $output_name"
                
                # Handle bundle extraction if needed
                if [[ "$app_type" == "Bundle_extract" ]]; then
                    local bundle_dir="./download/$(basename "$output_name.apkm" .apkm)"
                    mkdir -p "$bundle_dir"
                    unzip -q "./download/$output_name.apkm" -d "$bundle_dir"
                    if [ $? -eq 0 ]; then
                        green_log "[+] Successfully extracted bundle to $bundle_dir"
                        return 0
                    else
                        red_log "[-] Failed to extract bundle"
                        return 1
                    fi
                fi
                return 0
            fi
        fi
        
        ((attempt++))
        red_log "[-] Failed to download $output_name, trying another version"
        unset version
    done
    
    red_log "[-] No more versions to try. Failed download"
    return 1
}

# Helper function to get download URL from APKMirror
get_download_url() {
    local page_url=$1
    local download_page=$(download_file "$page_url" -)
    
    # Try different selectors in sequence
    local apk_url=$(echo "$download_page" | $pup 'a[data-google-vignette="false"]:contains("Download APK") attr{href}' | head -1)
    [[ -z "$apk_url" ]] && apk_url=$(echo "$download_page" | $pup 'a.accent_color[href*="/download/"] attr{href}' | head -1)
    [[ -z "$apk_url" ]] && apk_url=$(echo "$download_page" | grep -oP 'https://www\.apkmirror\.com/apk/[^"]+' | head -1)
    
    # Validate URL format
    if [[ -n "$apk_url" ]]; then
        [[ "$apk_url" != http* ]] && apk_url="https://www.apkmirror.com$apk_url"
        echo "$apk_url"
    else
        red_log "[-] No download link found on page"
        echo ""
    fi
}

# Patch key utilities
get_patches_key() {
    echo "--keystore=./src/_ks.keystore"
} 