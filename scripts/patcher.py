import yaml
import subprocess
from pathlib import Path
import argparse
import sys

def apply_patches(apk_path, app_config):
    """Apply ReVanced patches to an APK"""
    # Skip if this is an optimized APK
    if "_optimized" in apk_path.stem:
        return apk_path
        
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
    
    if include_patches:
        base_cmd.extend(["-e", ",".join(include_patches)])
    
    if exclude_patches:
        base_cmd.extend(["-d", ",".join(exclude_patches)])
    
    print(f"Running command: {' '.join(base_cmd)}")
    result = subprocess.run(base_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Patching failed with code {result.returncode}")
    
    return output_apk

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--app', required=True)
    parser.add_argument('--version')
    parser.add_argument('--patch-version')
    args = parser.parse_args()
    
    try:
        config_file = Path("configs/apps") / f"{args.app}.yaml"
        with open(config_file) as f:
            app_config = yaml.safe_load(f)
        
        # Look for merged APKs in all subdirectories
        apks = list(Path("downloads").rglob(f"{app_config['package']}*_merged.apk"))
        if not apks:
            # Try non-merged APKs in all subdirectories
            apks = list(Path("downloads").rglob(f"{app_config['package']}*.apk"))
        
        if not apks:
            raise RuntimeError(f"No APK found for {args.app}")
            
        for apk in apks:
            print(f"Patching {apk.name}...")
            patched = apply_patches(apk, app_config)
            print(f"Patched APK: {patched.name}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 