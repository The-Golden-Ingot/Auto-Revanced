#!/bin/bash
# Revanced build script
source ./src/build/utils.sh

# Download requirements
revanced_dl() {
	dl_gh "revanced-patches" "revanced" "prerelease"
	dl_gh "revanced-cli" "revanced" "latest"
}

# Patch Google Photos
patch_google_photos() {
	revanced_dl
	# Patch Google photos:
	# Arm64-v8a
	get_patches_key "gg-photos"
	get_apk "com.google.android.apps.photos" "gg-photos-arm64-v8a-beta" "photos" "google-inc/photos/google-photos" "arm64-v8a" "nodpi"
	patch "gg-photos-arm64-v8a-beta" "revanced"
}

# Patch SoundCloud
patch_soundcloud() {
	revanced_dl
	# Patch SoundCloud Arm64-v8a:
	get_patches_key "soundcloud"
	get_apk "com.soundcloud.android" "soundcloud-beta" "soundcloud" "soundcloud/soundcloud/soundcloud" "Bundle_extract"
	split_editor "soundcloud-beta" "soundcloud-arm64-v8a-beta" "exclude" "split_config.armeabi_v7a split_config.x86 split_config.x86_64"
	patch "soundcloud-arm64-v8a-beta" "revanced"
}

# Patch Lightroom
patch_adobe_lightroom() {
	revanced_dl
	# Patch Lightroom:
	get_patches_key "lightroom"
	url="https://adobe-lightroom-mobile.en.uptodown.com/android/download"
	url="https://dw.uptodown.com/dwn/$(req "$url" - | $pup -p --charset utf-8 'button#detail-download-button attr{data-url}')"
	req "$url" "lightroom-beta.apk"
	patch "lightroom-beta" "revanced"
}

# Main execution
case "$1" in
	1)
		patch_google_photos
		;; 
	2)
		patch_soundcloud
		;;
	3)
		patch_adobe_lightroom
		;;
	*)
		echo "Usage: $0 {1|2|3}"
		echo "1: Google Photos"
		echo "2: SoundCloud"
		echo "3: Lightroom"
		exit 1
		;;
esac
