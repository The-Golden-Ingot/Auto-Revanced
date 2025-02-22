import subprocess
from pathlib import Path
import yaml

def load_build_rules():
    """Load global build rules"""
    with open("configs/build_rules.yaml") as f:
        return yaml.safe_load(f)['global']

def merge_splits(input_path):
    output_file = input_path.parent / f"{input_path.stem}_merged.apk"
    build_rules = load_build_rules()
    
    # Base merge command
    base_cmd = ["java", "-jar", "APKEditor.jar", "m", "-i", str(input_path), "-o", str(output_file)]
    
    # Add architecture optimization if configured
    if 'architectures' in build_rules:
        # Keep only specified architectures
        for arch in build_rules['architectures'].get('strip', []):
            base_cmd.extend(["--remove-lib", arch])
    
    # Add DPI optimization if configured
    if 'dpi' in build_rules:
        keep_dpi = build_rules['dpi'].get('keep', [])
        if keep_dpi:
            base_cmd.extend(["--keep-dpi", ",".join(keep_dpi)])
    
    # Add legacy flag for compatibility
    base_cmd.append("--legacy")
    
    result = subprocess.run(
        base_cmd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Merge failed: {result.stderr}")
    
    return output_file

def needs_merging(file_path):
    return file_path.suffix.lower() in ['.apks', '.xapk', '.apkm']

def should_check_app(app_name):
    """Check if app is configured to use bundles/splits"""
    config_file = Path("configs/apps") / f"{app_name}.yaml"
    if not config_file.exists():
        return False
        
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    # Only check apps configured to use bundles/splits
    return config['source'].get('type', 'apk') in ['bundle', 'split']

if __name__ == "__main__":
    for apk in Path("downloads").iterdir():
        app_name = apk.stem.split('_')[0]  # Get app name from filename
        
        # Only process files that need merging for apps configured to use splits
        if should_check_app(app_name) and needs_merging(apk):
            print(f"Merging {apk.name}...")
            merged = merge_splits(apk)
            print(f"Created merged APK: {merged.name}") 