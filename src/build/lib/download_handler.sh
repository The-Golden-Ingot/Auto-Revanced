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
    
    # Download assets
    echo "$api_response" | jq -r '.assets[] | select(.name | test(".(jar|apk|rvp)$")) | .browser_download_url' | \
    while read -r url; do
        local filename=$(basename "$url")
        download_file "$url" "$filename"
    done
}

# APK Mirror download utilities
get_apk() {
    local package_name=$1
    local output_name=$2
    local app_type=$3
    local app_path=$4
    
    local attempt=0
    local version=""
    
    while [ $attempt -lt 10 ]; do
        if [[ -z $version ]] || [ $attempt -ne 0 ]; then
            local upload_tail="?$([[ $app_type = duolingo ]] && echo devcategory= || echo appcategory=)"
            version=$(download_file "https://www.apkmirror.com/uploads/$upload_tail$app_type" - | \
                $pup 'div.widget_appmanager_recentpostswidget h5 a.fontBlack text{}' | \
                grep -Evi 'alpha|beta' | \
                grep -oPi '\b\d+(\.\d+)+(?:\-\w+)?(?:\.\d+)?(?:\.\w+)?\b' | \
                sed -n "$((attempt + 1))p")
        fi
        
        version=$(format_version "$version")
        green_log "[+] Attempting download of $app_type version: $version"
        
        local dl_url=$(get_download_url "https://www.apkmirror.com/apk/$app_path-$version-release/")
        if [ -n "$dl_url" ]; then
            download_file "$dl_url" "$output_name.apk" && {
                green_log "[+] Successfully downloaded $output_name"
                return 0
            }
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
    echo "$download_page" | grep -o 'https://.*downloadapk.*' | head -n1
}

# Patch key utilities
get_patches_key() {
    local app_name=$1
    
    green_log "[+] Getting patches key for ${app_name}..."
    
    local key_file="${PATCHES_DIR}/${app_name}/patches.key"
    if [ -f "$key_file" ]; then
        cat "$key_file"
    else
        red_log "[-] Patches key file not found: ${key_file}"
        return 1
    fi
} 