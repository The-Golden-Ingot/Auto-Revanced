#!/bin/bash
# Official ReVanced build script

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
	dl_gh "${REPOS[revanced]%%|*}" "prerelease"
	dl_gh "${REPOS[revanced_cli]%%|*}" "latest"
}

# Build Google Photos
build_photos() {
	green_log "[+] Building Google Photos..."
	
	if [ ! -f "${DOWNLOAD_DIR}/photos.apk" ]; then
		get_apk "com.google.android.apps.photos" "photos" "google-photos" "google-inc/google-photos/google-photos"
	fi
	
	apply_patch_set "photos" "photos-revanced" "" "standard"
}

# Build Adobe Lightroom
build_lightroom() {
	green_log "[+] Building Adobe Lightroom..."
	
	if [ ! -f "${DOWNLOAD_DIR}/lightroom.apk" ]; then
		get_apk "com.adobe.lrmobile" "lightroom" "adobe-lightroom" "adobe/lightroom/adobe-lightroom"
	fi
	
	apply_patch_set "lightroom" "lightroom-revanced" "" "standard"
}

# Build SoundCloud
build_soundcloud() {
	green_log "[+] Building SoundCloud..."
	
	if [ ! -f "${DOWNLOAD_DIR}/soundcloud.apk" ]; then
		get_apk "com.soundcloud.android" "soundcloud" "soundcloud" "soundcloud/soundcloud"
	fi
	
	apply_patch_set "soundcloud" "soundcloud-revanced" "" "standard"
}

main() {
	# Initial setup
	setup_requirements
	
	# Build all apps
	build_photos
	build_lightroom
	build_soundcloud
}

# Execute main function
main
