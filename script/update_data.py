
import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path

try:
    from diff_versions import diff_versions, write_diff_md
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent))
    from diff_versions import diff_versions, write_diff_md

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    sys.exit(1)

# Constants
URL_ITAIGI = "https://itaigi.tw/%E5%8C%AF%E5%87%BA%E8%B3%87%E6%96%99"

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
MANIFEST_FILE = PUBLIC_DIR / "manifest.json"


def get_timestamp_dir():
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    return PUBLIC_DIR / timestamp


def download_file(url, target_path):
    print(f"Downloading {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_length = r.headers.get('content-length')

            with open(target_path, 'wb') as f:
                if total_length is None:
                    f.write(r.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in r.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(50 * dl / total_length)
                        sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {dl/1024/1024:.2f} MB")
                        sys.stdout.flush()
            print()
    except Exception as e:
        print(f"\nError downloading: {e}")
        return False
    return True


def calculate_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_manifest():
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_manifest(data):
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def json_to_csv(json_path, csv_path):
    """Convert iTaigi JSON export to CSV."""
    import csv

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data["資料"]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["華語", "漢字", "羅馬字", "來源"])
        for entry in entries:
            writer.writerow([
                entry.get("華語", ""),
                entry.get("漢字", ""),
                entry.get("羅馬字", ""),
                entry.get("來源", ""),
            ])

    return len(entries)


def main():
    print("Starting iTaigi update check...")

    temp_dir = PUBLIC_DIR / "temp_update"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_json = temp_dir / "iTaigiSuTian.json"

    try:
        if not download_file(URL_ITAIGI, temp_json):
            print("Failed to download. Aborting.")
            shutil.rmtree(temp_dir)
            return

        new_hash = calculate_file_hash(temp_json)

        current_manifest = load_manifest()
        current_hashes = current_manifest.get("files", {})

        changes_detected = False
        if not current_hashes:
            print("No existing manifest found. Proceeding with initial update...")
            changes_detected = True
        else:
            old_hash = current_hashes.get("iTaigiSuTian.json")
            if new_hash != old_hash:
                print("Change detected in iTaigi data.")
                changes_detected = True

        target_dir = None

        if not changes_detected:
            print("No changes detected.")
            latest_version_dir_name = current_manifest.get("latest_version_dir")
            if latest_version_dir_name:
                target_dir = PUBLIC_DIR / latest_version_dir_name
                if target_dir.exists():
                    print(f"Using existing latest directory: {target_dir}")
                else:
                    print(f"Existing directory {latest_version_dir_name} not found. Forcing creation.")
                    changes_detected = True
            else:
                print("Latest version directory not defined. Forcing creation.")
                changes_detected = True

        if changes_detected:
            print("Proceeding with update...")

            target_dir = get_timestamp_dir()
            bunji_dir = target_dir / "bunji"
            tangloo_dir = target_dir / "tangloo"

            bunji_dir.mkdir(parents=True, exist_ok=True)
            tangloo_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created version directory: {target_dir}")

            tangloo_json = tangloo_dir / "iTaigiSuTian.json"
            shutil.move(temp_json, tangloo_json)

            new_manifest = {
                "last_updated": datetime.datetime.now().isoformat(),
                "latest_version_dir": str(target_dir.name),
                "files": {
                    "iTaigiSuTian.json": new_hash
                }
            }
            save_manifest(new_manifest)
            print("Updated manifest.json.")

        # Always run conversion
        tangloo_json = target_dir / "tangloo" / "iTaigiSuTian.json"
        if not tangloo_json.exists():
            print(f"Error: JSON file not found at {tangloo_json}")
            return

        bunji_dir = target_dir / "bunji"
        bunji_dir.mkdir(parents=True, exist_ok=True)

        csv_path = bunji_dir / "iTaigiSuTian.csv"
        json_path = bunji_dir / "iTaigiSuTian.json"

        print(f"Converting JSON to CSV in {bunji_dir}...")
        # Copy the source JSON as the "clean" bunji JSON
        shutil.copy2(tangloo_json, json_path)
        entry_count = json_to_csv(str(tangloo_json), str(csv_path))
        print(f"Converted {entry_count} entries.")

        # Compare against previous version
        prev_version = current_manifest.get("latest_version_dir")
        if prev_version and prev_version != target_dir.name:
            prev_json = PUBLIC_DIR / prev_version / "bunji" / "iTaigiSuTian.json"
            if prev_json.exists() and json_path.exists():
                print(f"Comparing {prev_version} → {target_dir.name}...")
                diff = diff_versions(str(prev_json), str(json_path))
                diff_md_path = BASE_DIR / "VERSION_DIFF.md"
                write_diff_md(diff, prev_version, target_dir.name, str(diff_md_path))

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    print(f"\nUpdate complete!")
    print(f"Data stored in: {target_dir}")


if __name__ == "__main__":
    main()
