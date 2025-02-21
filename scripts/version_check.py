import yaml
import requests
from datetime import datetime

def get_latest_version(org, repo):
    url = f"https://api.apkmirror.com/v2/apps/{org}/{repo}/"
    response = requests.get(url)
    return response.json()['data']['version']

def get_patch_version(patch_url):
    response = requests.get(patch_url)
    return response.url.split('/')[-2]  # Extract version from release URL

def check_updates():
    with open("configs/applications.yaml") as f:
        apps = yaml.safe_load(f)
    
    updates = {}
    for app, config in apps.items():
        # APK Version check
        current_apk = config.get('version', 'latest')
        latest_apk = get_latest_version(config['org'], config['repo'])
        
        # Patch Version check
        patch_source = config['patches']['source']
        current_patch = config['patches'].get('version', 'unknown')
        latest_patch = get_patch_version(patch_source)
        
        apk_updated = current_apk != latest_apk
        patch_updated = current_patch != latest_patch
        
        if apk_updated or patch_updated:
            updates[app] = {
                'apk': {'current': current_apk, 'latest': latest_apk},
                'patch': {'current': current_patch, 'latest': latest_patch},
                'updated': datetime.utcnow().isoformat()
            }
    
    return updates

def update_lockfile(updates):
    try:
        with open("versions.lock") as f:
            lock = yaml.safe_load(f) or {}
    except FileNotFoundError:
        lock = {}
        
    for app, data in updates.items():
        lock[app] = {
            'apk_version': data['apk']['latest'],
            'patch_version': data['patch']['latest'],
            'last_checked': data['updated'],
            'patch_version': lock.get(app, {}).get('patch_version', 'unknown')
        }
        
    with open("versions.lock", "w") as f:
        yaml.safe_dump(lock, f)

if __name__ == "__main__":
    updates = check_updates()
    if updates:
        print("Updates available:")
        for app, data in updates.items():
            print(f"{app}: APK {data['apk']['current']} → {data['apk']['latest']}, Patch {data['patch']['current']} → {data['patch']['latest']}")
        update_lockfile(updates)
    else:
        print("All apps up to date") 