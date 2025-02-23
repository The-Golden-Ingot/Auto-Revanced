import subprocess
from pathlib import Path
import yaml
import os
import tempfile
import shutil

def load_build_rules():
    """Load global build rules"""
    with open("configs/build_rules.yaml") as f:
        return yaml.safe_load(f)['global']

def filter_dpi_resources(decoded_dir, keep_dpis):
    """Filter DPI-specific resources, keeping only specified DPIs"""
    res_dir = Path(decoded_dir) / "res"
    if not res_dir.exists():
        return
        
    # Get all resource directories
    for res_type_dir in res_dir.iterdir():
        if not res_type_dir.is_dir():
            continue
            
        # Check if directory name contains DPI specification
        for dpi_dir in res_type_dir.iterdir():
            if not dpi_dir.is_dir():
                continue
                
            # Parse directory name (e.g., drawable-hdpi, layout-xxhdpi)
            dir_parts = dpi_dir.name.split('-')
            if len(dir_parts) > 1 and any(p.endswith('dpi') for p in dir_parts[1:]):
                # Check if directory matches any kept DPI
                if not any(keep_dpi in dpi_dir.name for keep_dpi in keep_dpis):
                    print(f"Removing {dpi_dir.relative_to(res_dir)}")
                    try:
                        import shutil
                        shutil.rmtree(dpi_dir)
                    except Exception as e:
                        print(f"Warning: Failed to remove {dpi_dir}: {e}")

def optimize_apk(input_path, is_merged=False):
    """Optimize APK using APKEditor's capabilities"""
    input_path = Path(input_path).resolve()
    output_file = input_path.parent / f"{input_path.stem}_optimized.apk"
    
    # Create unique temp directory using system temp
    temp_dir = Path(tempfile.mkdtemp(prefix="apkeditor_"))
    
    # Remove existing temp dir if needed
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    try:
        # Decode APK first
        decode_cmd = ["java", "-jar", str(Path("APKEditor.jar").resolve()), "d", 
                     "-i", str(input_path), "-o", str(temp_dir)]
        result = subprocess.run(decode_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"APK decode failed: {result.stderr}")
        
        # Filter DPI resources if configured
        if 'dpi' in build_rules:
            keep_dpi = build_rules['dpi'].get('keep', [])
            if keep_dpi:
                filter_dpi_resources(temp_dir, keep_dpi)
        
        # Build optimized APK
        base_cmd = ["java", "-jar", str(Path("APKEditor.jar").resolve()), "b",
                    "-i", str(temp_dir), "-o", str(output_file)]
        
        # Add architecture optimization if configured
        if 'architectures' in build_rules:
            for arch in build_rules['architectures'].get('strip', []):
                base_cmd.extend(["--remove-lib", arch])
        
        print(f"Running build command: {' '.join(base_cmd)}")
        result = subprocess.run(base_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise RuntimeError(f"APK optimization failed: {result.stderr}")
        
        return output_file
    finally:
        # Always clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)

def merge_splits(input_path):
    """Merge split APKs and optimize the result"""
    merged_file = input_path.parent / f"{input_path.stem}_merged.apk"
    
    # Merge command
    merge_cmd = [
        "java", "-jar", "APKEditor.jar", "m",
        "-i", str(input_path),
        "-o", str(merged_file),
        "--legacy"
    ]
    
    result = subprocess.run(merge_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Merge failed: {result.stderr}")
    
    # Optimize the merged APK
    return optimize_apk(merged_file, is_merged=True)

def process_apk(input_path):
    """Process APK - either merge+optimize or just optimize"""
    try:
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        if needs_merging(input_path):
            merged = merge_splits(input_path)
            return optimize_apk(merged)  # Optimize after merging
        else:
            return optimize_apk(input_path)  # Direct optimization
    except Exception as e:
        print(f"Error processing {input_path.name}: {str(e)}")
        raise

def needs_merging(file_path):
    return file_path.suffix.lower() in ['.apks', '.xapk', '.apkm']

def should_check_app(app_name):
    """Check if app is configured to use bundles/splits"""
    config_file = Path("configs/apps") / f"{app_name}.yaml"
    if not config_file.exists():
        return False
        
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    return config['source'].get('type', 'apk') in ['bundle', 'split']

if __name__ == "__main__":
    for apk in Path("downloads").rglob("*.*"):  # Use rglob to find all files recursively
        if apk.suffix.lower() not in ['.apk', '.apks', '.xapk', '.apkm']:
            continue  # Skip non-APK files
            
        app_name = apk.stem.split('_')[0]
        try:
            print(f"Processing {apk.name}...")
            optimized = process_apk(apk)
            print(f"Created optimized APK: {optimized.name}")
        except Exception as e:
            print(f"Error processing {apk.name}: {str(e)}") 