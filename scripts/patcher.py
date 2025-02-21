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
    
    # Add root installation flags if configured
    if app_config.get('root_install', {}).get('enabled', False):
        base_cmd.extend([
            "-d", app_config['root_install']['device'],
            "--mount",
            *app_config['root_install']['flags']
        ])
    
    # Add patch inclusion/exclusion
    base_cmd.extend([
        "-e", ",".join(app_config['patches']['include']),
        "-d", ",".join(app_config['patches']['exclude'])
    ])
    
    # Add architecture stripping from build rules
    with open("configs/build_rules.yaml") as f:
        build_rules = yaml.safe_load(f)
        for arch in build_rules['global']['architectures']['strip']:
            base_cmd.extend(["--rip-lib", arch])
    
    output_apk = Path("dist") / f"{apk_path.stem}_patched.apk"
    
    result = subprocess.run(base_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Patching failed: {result.stderr}")
    
    return output_apk

if __name__ == "__main__":
    with open("configs/applications.yaml") as f:
        config = yaml.safe_load(f)
    
    for apk in Path("downloads").glob("*_merged.apk"):
        app_name = apk.stem.split("_")[0]
        print(f"Patching {app_name}...")
        patched = apply_patches(apk, config[app_name])
        print(f"Patched APK: {patched.name}") 