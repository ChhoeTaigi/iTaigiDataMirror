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

1. **`update_data.py`** — Main entry point. Downloads the JSON export from itaigi.tw/匯出資料, compares SHA256 hash against `public/manifest.json` to detect changes, creates a timestamped version directory under `public/`, then converts the JSON to CSV.

2. **`diff_versions.py`** — Compares two iTaigi JSON export files. Entries are keyed by `(華語, 漢字, 羅馬字)` tuple. Generates a `VERSION_DIFF.md` with added/removed/modified entries.

### Data Layout (`public/`)

```
public/
  manifest.json              # Tracks latest version and file hashes
  {YYYYMMDD-HHMM}/           # Timestamped version directory
    bunji/                    # Converted text data (CSV + JSON)
    tangloo/                  # Original downloads (JSON source) — gitignored
```

### Hosting

- `index.md` is the GitHub Pages landing page
- `.nojekyll` disables Jekyll processing

## Important Rules

- **`README.md` and `index.md` must stay in sync.** They have identical content. When updating version references or any other content in one, always update the other to match.

## Data Format

The source JSON has a single key `"資料"` containing an array. Each entry has four fields:

| Field | Description |
|-------|-------------|
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
