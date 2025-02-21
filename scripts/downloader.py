import yaml
import subprocess
from pathlib import Path

CONFIG_PATH = "configs/applications.yaml"
OUTPUT_DIR = "downloads"

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def download_app(app_config, app_name):
    cmd = [
        "apkmd", "download",
        app_config["org"],
        app_config["repo"],
        "--arch", app_config.get("arch", "universal"),
        "--dpi", app_config.get("dpi", "nodpi"),
        "--out-dir", OUTPUT_DIR,
        *app_config.get("apkmd_args", [])
    ]
    
    if "version" in app_config:
        cmd.extend(["--version", app_config["version"]])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Download failed for {app_name}: {result.stderr}")
    
    return list(Path(OUTPUT_DIR).glob(f"{app_name}*.*"))

if __name__ == "__main__":
    config = load_config()
    for app_name, app_config in config.items():
        print(f"Downloading {app_name}...")
        downloaded_files = download_app(app_config, app_name)
        print(f"Downloaded: {[f.name for f in downloaded_files]}") 