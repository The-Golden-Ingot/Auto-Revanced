import subprocess
from pathlib import Path

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

if __name__ == "__main__":
    for apk in Path("downloads").iterdir():
        if needs_merging(apk):
            print(f"Merging {apk.name}...")
            merged = merge_splits(apk)
            print(f"Created merged APK: {merged.name}") 