import yaml
import json
from pathlib import Path
import subprocess
import argparse
import sys
import logging

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

def download_apk(app_name: str, debug: bool = False):
    logger.info(f"Starting download for {app_name}")
    config = load_config(app_name)
    
    # Extract required parameters from config
    org = config['source']['org']
    repo = config['source']['repo']
    version = config.get('version', 'stable')
    apk_type = config['source'].get('type', 'apk')
    arch = config.get('arch', 'universal')
    if isinstance(arch, list):
        arch = arch[0]  # Take first architecture if multiple are specified
    
    # Build command with required positional args first
    cmd = [
        "apkmd",
        "download",
        org,
        repo,
        "--version", version,
        "--arch", arch,
        "--type", apk_type,
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