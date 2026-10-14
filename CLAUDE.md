# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data mirror for the iTaigi crowdsourced Taigi dictionary (https://itaigi.tw/). Part of the ChhoeTaigi project. The repo downloads dictionary data (JSON export), converts it to CSV, and hosts everything via GitHub Pages.

程式授權 MIT，辭典內容 CC0「不保留權利」授權。Data is exported from https://itaigi.tw/匯出資料.

## Commands

```bash
# Run the full update pipeline (downloads from itaigi.tw, checks for changes via SHA256 hash, converts JSON → CSV)
cd script && python update_data.py
```

Dependencies: `requests`. Install with `pip install requests`.

## Architecture

### Data Pipeline (`script/`)

1. **`update_data.py`** — Main entry point. Downloads the JSON export from itaigi.tw/匯出資料, compares SHA256 hash against `public/manifest.json` to detect changes, creates a timestamped version directory under `public/`, then runs `convert_export()` to produce the bunji JSON and CSV. The conversion:
   - adds `id` = the entry's 1-based position in the source export (the export has no id of its own; ids have gaps and shift between versions);
   - drops entries whose `來源` is in `SKIPPED_SOURCES` (`台文華文線頂辭典`, `臺灣閩南語常用詞辭典`), exact string match. These are imported dictionaries, not crowdsourced content. About 91k of 111k entries are skipped.
   - The conversion always runs, even when the hash is unchanged, so re-running the script regenerates the latest version's `bunji/`.

2. **`diff_versions.py`** — Compares two bunji JSON files. Entries are keyed by `(華語, 漢字, 羅馬字)` tuple; `id` is ignored when comparing fields because it is positional. Generates a `VERSION_DIFF.md` with added/removed/modified entries.

### Data Layout (`public/`)

```
public/
  manifest.json              # Tracks latest version and file hashes
  {YYYYMMDD-HHMM}/           # Timestamped version directory
    bunji/                    # Converted text data (CSV + JSON): id added, imported sources skipped
    tangloo/                  # Original downloads (JSON source, unfiltered) — gitignored
```

### Hosting

- `index.md` is the GitHub Pages landing page
- `.nojekyll` disables Jekyll processing

## Important Rules

- **`README.md` and `index.md` must stay in sync.** They have identical content. When updating version references or any other content in one, always update the other to match. Fix with `cp README.md index.md`.
- After a new version, update the version ID, date and the entry counts in the Skipped Sources table in both `README.md` and `index.md`. The counts are printed by `update_data.py`.

## Data Format

The source JSON has a single key `"資料"` containing an array. Each source entry has four fields; the bunji output prepends `id` (1-based position in the source export):

| Field | Description |
|-------|-------------|
| `id` | Position in the source export, 1-based (bunji output only) |
| `華語` | Mandarin Chinese gloss |
| `漢字` | Taigi Han characters (includes extended CJK codepoints beyond BMP) |
| `羅馬字` | Taigi Roman Orthography (Tâi-lô, the MOE standard) |
| `來源` | Contributor name, or `匿名` for anonymous |

## Unicode Considerations

- The `羅馬字` field uses Tâi-lô tone diacritics as Unicode combining marks or precomposed characters — normalize to NFC when comparing strings.
- The `漢字` field contains rare CJK Extension B/C characters (e.g. 𤺪, 𤆬, 𨑨) — tools and fonts must support supplementary Unicode planes.

## Terminology (Taigi)

- **bunji** (文字) — text data
- **tangloo** (檔路) — file storage / archives
