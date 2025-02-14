#!/bin/bash

source "src/build/lib/utils.sh"
source "src/build/lib/config.sh"
source "src/build/lib/error_handler.sh"

# Initialize build environment
init_build_env() {
    # Create necessary directories
    mkdir -p "${DOWNLOAD_DIR}" "${RELEASE_DIR}"
    
    # Setup required tools
    setup_pup
    setup_apk_editor
    
    # Validate requirements
    validate_requirements
}

# Setup pup tool for downloading APK files
setup_pup() {
    wget -q -O ./pup.zip "https://github.com/ericchiang/pup/releases/download/v0.4.0/pup_v0.4.0_linux_amd64.zip"
    unzip "./pup.zip" -d "./" > /dev/null 2>&1
    chmod +x ./pup
    export pup="./pup"
}

# Setup APKEditor for combining split APKs
setup_apk_editor() {
    wget -q -O ./APKEditor.jar "https://github.com/REAndroid/APKEditor/releases/download/V1.4.1/APKEditor-1.4.1.jar"
    export APK_EDITOR="./APKEditor.jar"
} 