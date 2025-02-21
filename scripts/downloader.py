import yaml
import json
from pathlib import Path
import subprocess
import argparse
import sys
import logging
from natsort import natsorted

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
                "type": app_config['source'].get('type', 'apk')
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
    """Get all compatible versions from patches.json for a package"""
    try:
        with open("patches.json") as f:
            patches = json.load(f)
            
        # Collect all versions from all patches targeting this package
        all_versions = set()
        for patch in patches:
            pkg_versions = patch.get("compatiblePackages", {}).get(app_package, [])
            all_versions.update(pkg_versions)
            
        if not all_versions:
            return []
            
        # Sort versions naturally (18.40.34 > 18.33.40 etc)
        return natsorted(all_versions)
        
    except Exception as e:
        raise RuntimeError(f"Failed to process patches.json: {e}")

def download_apk(app_name: str, debug: bool = False):
    logger.info(f"Starting download for {app_name}")
    config = load_config(app_name)
    
    compatible_versions = get_compatible_versions(config['package'])
    if not compatible_versions:
        raise RuntimeError(f"No patch-compatible versions found for {config['package']}")
    
    # Get latest version from sorted list
    latest_compatible = compatible_versions[-1]
    logger.info(f"Latest patch-compatible version: {latest_compatible}")
    
    # Existing download logic
    org = config['source']['org']
    repo = config['source']['repo']
    
    # Update command to use this specific version
    cmd = [
        "apkmd",
        "download",
        org,
        repo,
        "--version", latest_compatible,
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