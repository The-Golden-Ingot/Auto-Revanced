import yaml
import json
from pathlib import Path
import subprocess
import argparse
import sys
import logging
from natsort import natsorted
import requests

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_config(app_name: str) -> dict:
    config_path = Path("configs/apps") / f"{app_name}.yaml"
    logger.debug(f"Loading config from {config_path}")
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            logger.debug(f"Loaded config: {json.dumps(config, indent=2)}")
            return config
    except FileNotFoundError:
        raise RuntimeError(f"Config file not found: {config_path}")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Invalid YAML in config: {e}")

def generate_apkmd_config(app_config: dict) -> dict:
    logger.debug("Generating apkmd config")
    try:
        # Get architecture, defaulting to 'universal' if not specified
        arch = app_config.get('arch', 'universal')
        if isinstance(arch, list):
            arch = arch[0]  # Take first architecture if multiple are specified
        
        config = {
            "options": {
                "arch": arch,
                "outDir": "downloads",
                "type": app_config['source'].get('type', 'apk'),
                "minandroidversion": app_config.get('min_android_version', 21)
            },
            "apps": [{
                "org": app_config['source']['org'],
                "repo": app_config['source']['repo'],
                "version": app_config.get('version', 'stable'),
                "outFile": app_config.get('package', app_config['source']['repo'])
            }]
        }
        logger.debug(f"Generated apkmd config: {json.dumps(config, indent=2)}")
        return config
    except KeyError as e:
        raise RuntimeError(f"Missing required config key: {e}")

def get_compatible_versions(app_package: str) -> list:
    """Get all compatible versions from any patch for a package"""
    try:
        # Try all possible patches.json filenames
        for fn in ["patches.json", "patches.json.1", "patches.json.2"]:
            patches_file = Path(fn)
            if patches_file.exists():
                with open(patches_file) as f:
                    content = f.read().strip()
                    if content:
                        return process_patches_content(content, app_package)
        
        logger.error("No valid patches.json found locally, trying remote...")
        return get_remote_compatible_versions(app_package)
        
    except Exception as e:
        logger.error(f"Version check failed: {str(e)}")
        return []

def process_patches_content(content: str, app_package: str) -> list:
    """Process patches.json content"""
    try:
        patches = json.loads(content)
        all_versions = set()
        
        for patch in patches:
            # Handle different patch format versions
            compatible_packages = patch.get("compatiblePackages")
            if not compatible_packages:
                continue
                
            for pkg in compatible_packages:
                if pkg.get("name") == app_package:
                    versions = pkg.get("versions")
                    if isinstance(versions, list):
                        all_versions.update(versions)
                    elif isinstance(versions, str):
                        all_versions.add(versions)
        
        return natsorted(all_versions) if all_versions else []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in patches file: {str(e)}")
        return []

def get_remote_compatible_versions(app_package: str) -> list:
    """Fallback to downloading patches.json directly"""
    try:
        patches_url = "https://github.com/anddea/revanced-patches/releases/latest/download/patches.json"
        response = requests.get(patches_url)
        response.raise_for_status()
        return process_patches_content(response.text, app_package)
    except Exception as e:
        logger.error(f"Remote fetch failed: {str(e)}")
        return []

def download_apk(app_name: str, debug: bool = False):
    logger.info(f"Starting download for {app_name}")
    config = load_config(app_name)
    
    # Check if we should use patch-compatible version
    if 'patches' in config and config['patches'].get('fetchLatestCompatibleVersion', False):
        compatible_versions = get_compatible_versions(config['package'])
        if not compatible_versions:
            raise RuntimeError(f"No patch-compatible versions found for {config['package']}")
        version = compatible_versions[-1]  # Get latest compatible version
        logger.info(f"Using patch-compatible version: {version}")
    else:
        # Use version from config, defaulting to 'stable'
        version = config.get('version', 'stable')
        logger.info(f"Using configured version: {version}")
    
    # Existing download logic
    org = config['source']['org']
    repo = config['source']['repo']
    
    # Update command to use determined version
    cmd = [
        "apkmd",
        "download",
        org,
        repo,
        "--version", version,
        "--arch", config.get('arch', 'universal'),
        "--type", config['source'].get('type', 'apk'),
        "--outdir", "downloads",
        "--outfile", config.get('package', repo)
    ]
    
    if debug:
        cmd.append("--debug")
    
    logger.debug(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )
    
    logger.debug(f"Command output:\n{result.stdout}")
    if result.stderr:
        logger.error(f"Command stderr:\n{result.stderr}")
    
    if result.returncode != 0:
        raise RuntimeError(f"APKMD failed with exit code {result.returncode}\nOutput: {result.stdout}\nError: {result.stderr}")
    
    # Verify download
    apks = list(Path("downloads").glob("*.apk"))
    if not apks:
        raise RuntimeError("No APKs were downloaded")
    
    logger.info(f"Successfully downloaded: {[apk.name for apk in apks]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    
    try:
        download_apk(args.app, args.debug)
    except Exception as e:
        logger.error(f"Download failed: {str(e)}", exc_info=True)
        sys.exit(1) 