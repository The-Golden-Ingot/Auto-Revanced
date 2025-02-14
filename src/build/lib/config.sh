#!/bin/bash

# Global configuration values
if [ -z "${DOWNLOAD_DIR+x}" ]; then
    declare -r DOWNLOAD_DIR="./download"
    declare -r RELEASE_DIR="./release"
    declare -r PATCHES_DIR="./src/patches"
    declare -r OPTIONS_DIR="./src/options"
fi

# Repository configurations
declare -A REPOS=(
    ["revanced"]="revanced/revanced-patches|prerelease"
    ["revanced_cli"]="revanced/revanced-cli|latest"
    ["anddea"]="anddea/revanced-patches|prerelease"
    ["anddea_cli"]="inotia00/revanced-cli|latest"
    ["piko"]="crimera/piko|prerelease"
    ["experiments"]="Aunali321/ReVancedExperiments|latest"
)

# Architecture configurations
declare -A ARCH_CONFIGS=(
    ["arm64-v8a"]="armeabi-v7a x86_64 x86"
    ["armeabi-v7a"]="arm64-v8a x86_64 x86"
    ["x86_64"]="armeabi-v7a arm64-v8a x86"
    ["x86"]="armeabi-v7a arm64-v8a x86_64"
)

# HTTP request headers
declare -a HTTP_HEADERS=(
    "User-Agent: Mozilla/5.0 (Android 14; Mobile; rv:134.0) Gecko/134.0 Firefox/134.0"
    "Content-Type: application/octet-stream"
    "Accept-Language: en-US,en;q=0.9"
    "Connection: keep-alive"
    "Upgrade-Insecure-Requests: 1"
    "Cache-Control: max-age=0"
    "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
) 