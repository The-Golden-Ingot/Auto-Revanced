import yaml
import json
from pathlib import Path
import subprocess
import argparse
import sys

def load_config(app_name: str) -> dict:
    config_path = Path("configs/apps") / f"{app_name}.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

def generate_apkmd_config(app_config: dict) -> dict:
    return {
        "options": {
            "arch": app_config['build']['arch'],
            "outDir": "downloads",
            "type": app_config['source'].get('type', 'apk')
        },
        "apps": [{
            "org": app_config['source']['org'],
            "repo": app_config['source']['repo'],
            "version": app_config['version'],
            "outFile": app_config['package']
        }]
    }

def download_apk(app_name: str, debug: bool = False):
    config = load_config(app_name)
    apkmd_config = generate_apkmd_config(config)
    
    config_file = Path("downloads") / f"{app_name}.json"
    with open(config_file, 'w') as f:
        json.dump(apkmd_config, f, indent=2)
    
    cmd = [
        "apkmd", "download", "--config", str(config_file),
        "--debug" if debug else ""
    ]
    cmd = [c for c in cmd if c]  # Remove empty arguments
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        print(f"APKMD Error ({result.returncode}):")
        print(result.stderr)
        sys.exit(1)
        
    print("Download completed successfully")
    print(result.stdout)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    
    try:
        download_apk(args.app, args.debug)
    except Exception as e:
        print(f"Download failed: {str(e)}")
        sys.exit(1) 