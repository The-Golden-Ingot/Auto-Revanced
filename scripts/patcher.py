import yaml
import subprocess
from pathlib import Path

def apply_patches(apk_path, app_config):
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
    for arch in app_config['build']['optimize'].get('arch', []):
        if arch != "universal":
            base_cmd.extend(["--rip-lib", arch])
            
    # Additional DPI optimization can be added here if needed
    
    output_apk = Path("dist") / f"{apk_path.stem}_patched.apk"
    
    result = subprocess.run(base_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Patching failed: {result.stderr}")
    
    return output_apk

if __name__ == "__main__":
    # Update to use new config structure
    app_name = apk_path.stem.split("_")[0]
    config_file = Path("configs/apps") / f"{app_name}.yaml"
    
    with open(config_file) as f:
        app_config = yaml.safe_load(f)
    
    for apk in Path("downloads").glob("*_merged.apk"):
        app_name = apk.stem.split("_")[0]
        print(f"Patching {app_name}...")
        patched = apply_patches(apk, app_config)
        print(f"Patched APK: {patched.name}") 