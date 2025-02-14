#!/bin/bash
# Piko build script

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
	dl_gh "${REPOS[piko]%%|*}" "prerelease"
	dl_gh "${REPOS[revanced_cli]%%|*}" "latest"
	
	# Setup patch configuration
	get_patches_key "twitter-piko"
}

# Build Twitter
build_twitter() {
	green_log "[+] Building Twitter..."
	
	# Get base APK if not already downloaded
	if [ ! -f "${DOWNLOAD_DIR}/twitter.apk" ]; then
		get_apk "com.twitter.android" "twitter" "twitter" "twitter/twitter" "Bundle_extract"
	fi
	
	# Add split handling before patching
	split_editor "twitter" "twitter"
	apply_patch_set "twitter" "twitter-piko" "" "standard"
}

main() {
	# Initial setup
	setup_requirements
	
	# Build Twitter
	build_twitter
}

# Execute main function
main
