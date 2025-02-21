import yaml
import requests
from datetime import datetime, UTC
from pathlib import Path
import json
import logging

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

def get_compatible_version(package_name, patches_json):
    """Get the latest compatible version for a package from patches.json"""
    for patch in patches_json:
        if "compatiblePackages" in patch:
            for pkg, versions in patch["compatiblePackages"].items():
                if pkg == package_name and versions:
                    # Return the latest compatible version
                    return sorted(versions)[-1]
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
            latest_compatible = get_compatible_version(config['package'], patches_json)
            
            if latest_compatible:
                current_apk = config.get('version', 'latest')
                if current_apk != latest_compatible:
                    updates[app_name] = {
                        'apk': {'current': current_apk, 'latest': latest_compatible},
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
    updates = check_updates()
    if updates:
        print("Updates available:")
        for app, data in updates.items():
            print(f"{app}: APK {data['apk']['current']} → {data['apk']['latest']}, Patch {data['patch']['current']} → {data['patch']['latest']}")
        update_lockfile(updates)
    else:
        print("All apps up to date") 