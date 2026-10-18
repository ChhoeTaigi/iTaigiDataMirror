
import datetime
import hashlib
import json
import shutil
import sys
import unicodedata
import urllib.parse
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
# iTaigi's dictionary page for one Mandarin headword (華語). It lists every
# Taigi answer for that headword; iTaigi has no page per answer.
URL_ITAIGI_LOOKUP = "https://itaigi.tw/k/"

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
MANIFEST_FILE = PUBLIC_DIR / "manifest.json"

# Entries whose 來源 is one of these are copies of other dictionaries that
# iTaigi imported, not crowdsourced iTaigi content. They are dropped from the
# bunji output. Matched as exact strings.
SKIPPED_SOURCES = (
    "台文華文線頂辭典",
    "臺灣閩南語常用詞辭典",
)

# The four fields of a source row, in the order they are hashed for `id`.
SOURCE_FIELDS = ("華語", "漢字", "羅馬字", "來源")
ID_SEPARATOR = "\x1f"  # U+001F unit separator; never appears in the data
ID_LENGTH = 16  # hex digits of SHA-256 kept

FIELDS = ["id", "華語", "漢字", "羅馬字", "來源", "link"]


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


def entry_text(entry):
    """The four fields of a source row, NFC-normalized and joined with ID_SEPARATOR."""
    return ID_SEPARATOR.join(
        unicodedata.normalize("NFC", entry.get(field) or "") for field in SOURCE_FIELDS
    )


def entry_hash(entry):
    """Content hash of a source row: the first ID_LENGTH hex digits of the
    SHA-256 of `entry_text`. The same row hashes to the same value in every
    version; any change to its text or contributor gives a new value.
    """
    return hashlib.sha256(entry_text(entry).encode("utf-8")).hexdigest()[:ID_LENGTH]


def itaigi_link(huagi):
    """URL of the iTaigi page listing every Taigi answer for `huagi` (華語).

    Entries that share a 華語 share a link. The headword is percent-encoded so
    the URL stays valid whatever characters it contains. The trailing slash is
    iTaigi's canonical form; without it the server answers with a redirect.
    Empty 華語 gives an empty link rather than a link to the bare search page.
    """
    if not huagi:
        return ""
    return URL_ITAIGI_LOOKUP + urllib.parse.quote(huagi, safe="") + "/"


def convert_export(source_json_path, bunji_json_path, bunji_csv_path):
    """Convert the raw iTaigi export into the bunji JSON and CSV.

    - `id` is a content hash of the row's four fields, see `entry_hash`. The
      export carries no identifier of its own.
    - Rows identical to an earlier row in all four fields are dropped, so
      every id is unique. The export does contain such repeats.
    - `link` is the iTaigi dictionary page for the entry's 華語, see
      `itaigi_link`.
    - Entries from SKIPPED_SOURCES are dropped.

    Returns a dict with `total`, `kept` and `skipped` (per source) counts.
    """
    import csv

    with open(source_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_entries = data["資料"]
    skipped = {name: 0 for name in SKIPPED_SOURCES}
    seen = set()  # entry_text of every kept row
    duplicates = 0
    entries = []
    for entry in source_entries:
        source = entry.get("來源", "")
        if source in skipped:
            skipped[source] += 1
            continue
        text = entry_text(entry)
        if text in seen:
            duplicates += 1
            continue
        seen.add(text)
        entries.append({
            "id": entry_hash(entry),
            "華語": entry.get("華語", ""),
            "漢字": entry.get("漢字", ""),
            "羅馬字": entry.get("羅馬字", ""),
            "來源": source,
            "link": itaigi_link(entry.get("華語", "")),
        })

    ids = [e["id"] for e in entries]
    if len(set(ids)) != len(ids):
        raise ValueError("id collision between different entries; raise ID_LENGTH")

    with open(bunji_json_path, "w", encoding="utf-8") as f:
        json.dump({"資料": entries}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with open(bunji_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for entry in entries:
            writer.writerow([entry[field] for field in FIELDS])

    return {
        "total": len(source_entries),
        "kept": len(entries),
        "skipped": skipped,
        "duplicates": duplicates,
    }


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

        print(f"Converting export to bunji JSON and CSV in {bunji_dir}...")
        counts = convert_export(str(tangloo_json), str(json_path), str(csv_path))
        for source, n in counts["skipped"].items():
            print(f"Skipped {n} entries from {source}.")
        print(f"Kept {counts['kept']} of {counts['total']} entries.")
        print(f"Skipped {counts['duplicates']} entries identical to an earlier entry.")

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
