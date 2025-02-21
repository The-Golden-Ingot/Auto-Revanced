import yaml
import subprocess
from pathlib import Path
import argparse

def apply_patches(apk_path, app_config):
    # Define output_apk before using it in base_cmd
    output_apk = Path("dist") / f"{apk_path.stem}_patched.apk"
    
    base_cmd = [
        "java", "-jar", "revanced-cli-all.jar", "patch",
        "-p", "patches.rvp",
        "--legacy-options=options.json",
        "--purge",
        "-o", str(output_apk),
        str(apk_path)
    ]
    
    # Handle patch inclusion/exclusion
    include_patches = app_config['patches'].get('include', [])
    exclude_patches = app_config['patches'].get('exclude', [])
    
    # Only add include flag if patches are specifically listed
    if include_patches:
        base_cmd.extend(["-e", ",".join(include_patches)])
    
    # Always add exclude flag if there are exclusions
    if exclude_patches:
        base_cmd.extend(["-d", ",".join(exclude_patches)])
    
    # Add architecture optimization
    if 'build' in app_config and 'optimize' in app_config['build']:
        for arch in app_config['build']['optimize'].get('arch', []):
            if arch != "universal":
                base_cmd.extend(["--rip-lib", arch])
    
    result = subprocess.run(base_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Patching failed: {result.stderr}")
    
    return output_apk

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--app', required=True)
    parser.add_argument('--version')
    parser.add_argument('--patch-version')
    args = parser.parse_args()
    
    config_file = Path("configs/apps") / f"{args.app}.yaml"
    with open(config_file) as f:
        app_config = yaml.safe_load(f)
    
    # Look for merged APKs
    apks = list(Path("downloads").glob(f"{args.app}*_merged.apk"))
    if not apks:
        # Try non-merged APKs
        apks = list(Path("downloads").glob(f"{args.app}*.apk"))
    
    if not apks:
        raise RuntimeError(f"No APK found for {args.app}")
        
    for apk in apks:
        print(f"Patching {apk.name}...")
        patched = apply_patches(apk, app_config)
        print(f"Patched APK: {patched.name}") 