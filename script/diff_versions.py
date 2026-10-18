
import json
import unicodedata
from pathlib import Path


def _entry_label(entry):
    huayu = entry.get("華語", "")
    hanji = entry.get("漢字", "")
    lomaji = entry.get("羅馬字", "")
    if hanji and lomaji:
        return f"{huayu} → {hanji} ({lomaji})"
    return huayu or hanji or lomaji or "?"


KEY_FIELDS = ("華語", "漢字", "羅馬字", "來源")


def _nfc(value):
    """NFC-normalize a field value; tone marks may be precomposed or combining."""
    return unicodedata.normalize("NFC", value) if isinstance(value, str) else value


def _make_key(entry):
    """Key for matching entries across versions: the four source fields, NFC
    normalized. This is the same content `id` is hashed from. Keying on fewer
    fields collapses rows that differ only in 來源 and reports phantom
    modifications when the export order changes.
    """
    return tuple(_nfc(entry.get(f) or "") for f in KEY_FIELDS)


def diff_versions(old_json_path, new_json_path):
    """Compare two iTaigi JSON export files and return a diff dict."""
    with open(old_json_path, encoding="utf-8") as f:
        old_data = json.load(f)
    with open(new_json_path, encoding="utf-8") as f:
        new_data = json.load(f)

    old_entries = old_data.get("資料", old_data) if isinstance(old_data, dict) else old_data
    new_entries = new_data.get("資料", new_data) if isinstance(new_data, dict) else new_data

    old_map = {}
    for e in old_entries:
        key = _make_key(e)
        old_map[key] = e

    new_map = {}
    for e in new_entries:
        key = _make_key(e)
        new_map[key] = e

    old_keys = set(old_map)
    new_keys = set(new_map)

    added = [{"key": k, "label": _entry_label(new_map[k])} for k in sorted(new_keys - old_keys)]
    removed = [{"key": k, "label": _entry_label(old_map[k])} for k in sorted(old_keys - new_keys)]

    modified = []
    for k in sorted(old_keys & new_keys):
        old_e, new_e = old_map[k], new_map[k]
        if old_e == new_e:
            continue
        field_changes = []
        # `id` is a hash of the key fields, so it is identical for a matched
        # key unless one side predates the hash ids. `link` is derived from
        # 華語, which is part of the key, so it can only differ when one side
        # predates the column.
        all_fields = sorted((set(old_e) | set(new_e)) - {"id", "link"})
        for f in all_fields:
            ov, nv = _nfc(old_e.get(f)), _nfc(new_e.get(f))
            if ov != nv:
                field_changes.append(f"  - `{f}`: {_fmt(ov)} → {_fmt(nv)}")
        if not field_changes:
            continue
        modified.append({
            "label": _entry_label(new_e),
            "field_changes": field_changes,
        })

    return {
        "old_count": len(old_entries),
        "new_count": len(new_entries),
        "added": added,
        "removed": removed,
        "modified": modified,
    }


def _fmt(val):
    if val is None:
        return "(empty)"
    s = str(val)
    if len(s) > 80:
        return s[:77] + "..."
    return s


def write_diff_md(diff, old_version, new_version, out_path):
    lines = [
        f"# Version Diff: {old_version} → {new_version}",
        "",
        f"- Previous: **{old_version}** ({diff['old_count']} entries)",
        f"- Current: **{new_version}** ({diff['new_count']} entries)",
        f"- Added: **{len(diff['added'])}** | Removed: **{len(diff['removed'])}** | Modified: **{len(diff['modified'])}**",
        "",
    ]

    if diff["added"]:
        lines.append("## Added Entries")
        lines.append("")
        for e in diff["added"]:
            lines.append(f"- {e['label']}")
        lines.append("")

    if diff["removed"]:
        lines.append("## Removed Entries")
        lines.append("")
        for e in diff["removed"]:
            lines.append(f"- {e['label']}")
        lines.append("")

    if diff["modified"]:
        lines.append("## Modified Entries")
        lines.append("")
        for e in diff["modified"]:
            lines.append(f"### {e['label']}")
            lines.append("")
            for c in e["field_changes"]:
                lines.append(c)
            lines.append("")

    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
