import subprocess
from pathlib import Path
import yaml

def merge_splits(input_path):
    output_file = input_path.parent / f"{input_path.stem}_merged.apk"
    
    result = subprocess.run(
        ["java", "-jar", "APKEditor.jar", "m", "-i", str(input_path), "-o", str(output_file)],
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