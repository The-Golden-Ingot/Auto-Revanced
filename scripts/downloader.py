import yaml
import subprocess
from pathlib import Path
import requests

CONFIG_DIR = Path("configs/apps")
OUTPUT_DIR = "downloads"

def load_configs():
    configs = {}
    for config_file in CONFIG_DIR.glob("*.yaml"):
        app_name = config_file.stem
        with open(config_file) as f:
            configs[app_name] = yaml.safe_load(f)
    return configs

def get_version_constraint(app_config):
    """Get version constraint based on app package"""
    # Only check patches.json for YouTube
    if app_config['package'] == "com.google.android.youtube":
        try:
            patches_url = app_config['patches']['source']
            # Get the latest release tag
            response = requests.get(patches_url, allow_redirects=False)
            if response.status_code == 302:  # GitHub redirects 'latest' to actual release
                actual_release = response.headers['Location'].split('/')[-1]
                base_url = patches_url.replace("latest", actual_release)
                patches_response = requests.get(f"{base_url}/patches.json")
                patches_response.raise_for_status()
                patches_json = patches_response.json()
                
                # Find latest compatible version for YouTube
                for patch in patches_json:
                    if "compatiblePackages" in patch:
                        for pkg, versions in patch["compatiblePackages"].items():
                            if pkg == app_config['package'] and versions:
                                return sorted(versions)[-1]
        except Exception as e:
            print(f"Error fetching patches.json: {e}")
            return app_config.get('version', 'latest')
    
    # All other apps use latest version
    return app_config.get('version', 'latest')

def download_app(app_config, app_name):
    version = get_version_constraint(app_config)
    
    cmd = [
        "apkmd", "download",
        app_config['source']['org'],
        app_config['source']['repo'],
        "--version", version,
        "--out-dir", OUTPUT_DIR
    ]
    
    # Add type flag if specified
    if 'type' in app_config['source']:
        cmd.extend(["--type", app_config['source']['type']])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Download failed for {app_name}: {result.stderr}")
    
    return list(Path(OUTPUT_DIR).glob(f"{app_name}*.*"))

if __name__ == "__main__":
    configs = load_configs()
    for app_name, app_config in configs.items():
        print(f"Downloading {app_name}...")
        downloaded_files = download_app(app_config, app_name)
        print(f"Downloaded: {[f.name for f in downloaded_files]}") 