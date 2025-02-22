import yaml
import requests
from datetime import datetime, UTC
from pathlib import Path
import json
import logging
import argparse
import sys
from natsort import natsorted

logger = logging.getLogger(__name__)

def get_latest_version(org, repo):
    url = f"https://api.apkmirror.com/v2/apps/{org}/{repo}/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        json_data = response.json()
        version = json_data.get('data', {}).get('version')
        if not version:
            logger.warning(f"Latest version not found in response from {url}")
            return None
        return version
    except requests.RequestException as e:
        logger.error(f"Failed to fetch latest version from {url}: {e}")
        return None

def get_patch_version(patch_url):
    response = requests.get(patch_url)
    return response.url.split('/')[-2]  # Extract version from release URL

def get_compatible_versions(package_name):
    """Get compatible versions for a package from patches.json"""
    try:
        # First try patches.json in current directory
        patches_file = Path("patches.json")
        if not patches_file.exists():
            patches_file = Path("patches.json.2")
        
        logger.debug(f"Trying to read from: {patches_file.absolute()}")
        if not patches_file.exists():
            available_files = list(Path(".").glob("patches.json*"))
            logger.error(f"No patches file found. Available files: {[f.name for f in available_files]}")
            return None
            
        with open(patches_file) as f:
            content = f.read().strip()
            if not content:
                logger.error("patches.json is empty")
                return None
            try:
                patches = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {patches_file.name}: {e}")
                return None
        
        logger.debug(f"Total patches found: {len(patches)}")
        
        if not isinstance(patches, list):
            logger.error(f"Expected list of patches, got {type(patches)}")
            return None
            
        versions = set()
        for i, patch in enumerate(patches, 1):
            if not isinstance(patch, dict):
                logger.debug(f"Skipping non-dict patch at index {i}")
                continue
                
            compatible_packages = patch.get("compatiblePackages")
            logger.debug(f"Patch {i} compatiblePackages type: {type(compatible_packages)}")
            
            if isinstance(compatible_packages, dict):
                logger.debug(f"Dict structure keys: {list(compatible_packages.keys())[:3]}...")
                pkg_versions = compatible_packages.get(package_name, [])
                if pkg_versions:
                    versions.update(pkg_versions)
            elif isinstance(compatible_packages, list):
                logger.debug(f"List structure first item: {compatible_packages[0] if compatible_packages else 'empty'}")
                for pkg in compatible_packages:
                    if isinstance(pkg, dict) and pkg.get("name") == package_name:
                        versions.update(pkg.get("versions", []))
            else:
                logger.debug(f"Unexpected compatiblePackages type in patch {i}")
                
        if versions:
            sorted_versions = natsorted(versions)
            logger.debug(f"Final compatible versions for {package_name}: {sorted_versions}")
            return sorted_versions
            
        logger.warning(f"No versions found for {package_name} in any patch")
        return None
        
    except Exception as e:
        logger.error(f"Critical error in get_compatible_versions: {e}")
        logger.debug("Stack trace:", exc_info=True)
        return None

def get_patches_json(source_url: str) -> dict:
    """Get patches.json from the source URL"""
    try:
        # Use local patches.json if it exists (downloaded by workflow)
        if Path("patches.json").exists():
            with open("patches.json") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        
        # Fallback to downloading from URL
        response = requests.get(source_url)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        logger.error(f"Failed to get patches.json: {e}")
        return {}

def check_updates():
    updates = {}
    
    for config_file in Path("configs/apps").glob("*.yaml"):
        app_name = config_file.stem
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        # Check if app should use compatible version from patches.json
        if config.get('patches', {}).get('fetchLatestCompatibleVersion', False):
            # Get patches.json for version compatibility
            patches_json = get_patches_json(config['patches']['source'])
            latest_compatible = get_compatible_versions(config['package'])
            
            if latest_compatible:
                current_apk = config.get('version', 'latest')
                if current_apk != latest_compatible[-1]:
                    updates[app_name] = {
                        'apk': {'current': current_apk, 'latest': latest_compatible[-1]},
                        'patch': {'current': 'latest', 'latest': 'latest'},
                        'updated': datetime.now(UTC).isoformat()
                    }
            continue  # Skip APKMirror check for apps using patches.json
        
        # For apps using APKMirror, check if they have source config
        if 'source' in config and 'org' in config['source'] and 'repo' in config['source']:
            current_apk = config.get('version', 'latest')
            latest_apk = get_latest_version(config['source']['org'], config['source']['repo'])
            
            if current_apk != latest_apk:
                updates[app_name] = {
                    'apk': {'current': current_apk, 'latest': latest_apk},
                    'patch': {'current': 'latest', 'latest': 'latest'},
                    'updated': datetime.now(UTC).isoformat()
                }
    
    # Write updates to versions.json for the workflow
    with open("versions.json", "w") as f:
        json.dump(updates or {}, f)
    
    return updates

def update_lockfile(updates):
    if not updates:
        logger.warning("No updates to write to versions.lock")
        return
        
    lock = {}
    try:
        with open("versions.lock") as f:
            lock = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.info("Creating new versions.lock file")
    
    for app, data in updates.items():
        lock[app] = {
            'apk_version': f"{data['apk']['latest']} {data['patch']['latest']}", # Format: "apk_version patch_version"
            'last_checked': data['updated']
        }
        
    with open("versions.lock", "w") as f:
        yaml.safe_dump(lock, f, default_flow_style=False)
    logger.info(f"Updated versions.lock with: {lock}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True, help="App identifier (e.g., youtube)")
    parser.add_argument("--get-latest", action="store_true", help="Output the latest APK version for the app")
    args = parser.parse_args()

    if args.get_latest:
        # Read config from configs/apps/<app>.yaml
        config_path = Path("configs", "apps", f"{args.app.lower()}.yaml")
        if not config_path.exists():
            logger.error(f"Config file for app '{args.app}' not found at {config_path}")
            sys.exit(1)
            
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        # Check if we should use patch-compatible version
        if config.get("patches", {}).get("fetchLatestCompatibleVersion", False):
            package = config.get("package")
            if not package:
                logger.error("App config must include 'package' when fetchLatestCompatibleVersion is true")
                sys.exit(1)
                
            compatible_versions = get_compatible_versions(package)
            if not compatible_versions:
                logger.error(f"No patch-compatible versions found for {package}")
                sys.exit(1)
                
            version = compatible_versions[-1]  # Get latest compatible version
            print(version)
            sys.exit(0)
        else:
            # Use latest version from APKMirror
            source = config.get("source", {})
            org = source.get("org")
            repo = source.get("repo")
            if not org or not repo:
                logger.error("App config must include 'org' and 'repo' in the source field")
                sys.exit(1)
                
            version = get_latest_version(org, repo)
            if version:
                print(version)
                sys.exit(0)
            else:
                sys.exit(1)
    else:
        updates = check_updates()
        if updates:
            print("Updates available:")
            for app, data in updates.items():
                print(f"{app}: APK {data['apk']['current']} → {data['apk']['latest']}, Patch {data['patch']['current']} → {data['patch']['latest']}")
            update_lockfile(updates)
        else:
            print("All apps up to date") 