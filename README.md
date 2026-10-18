# iTaigiDataMirror

Data mirror for iTaigi. This site provides direct access to the exported iTaigi crowdsourced dictionary data. The files are hosted on GitHub Pages for easy access.

## Chu-liāu Pán-koân

版權聲明

- 程式授權：[MIT License](https://github.com/i3thuan5/itaigi)
- 辭典內容：[CC0「不保留權利」授權](https://creativecommons.org/public-domain/cc0/)
- [iTaigi隱私權保護條款](https://itaigi.tw/privacy)

![版權聲明](./LICENSE.png)

## Latest Version

- **Version ID:** `20261019-0110`
- **Last Updated:** 2026-10-19

You can check [**manifest.json**](./public/manifest.json) for the latest version information programmatically.

## Accessing Files

The files are organized by version. The latest files are in `public/20261019-0110/`.

### Text Data (Dictionary)

- [**iTaigiSuTian.csv** (Dictionary Data CSV)](./public/20261019-0110/bunji/iTaigiSuTian.csv)
- [**iTaigiSuTian.json** (Dictionary Data JSON)](./public/20261019-0110/bunji/iTaigiSuTian.json)

### Data Fields

| Field  | Description                                      |
|--------|--------------------------------------------------|
| `id` | Unique id: content hash of the four source fields, see below |
| `華語` | Mandarin Chinese gloss |
| `漢字` | Taigi Han characters |
| `羅馬字` | Taigi Roman Orthography in KPL (Kàu-io̍k Pō͘ Lô-má-jī, the MOE standard) |
| `來源` | Contributor name or `匿名` (anonymous) |
| `link` | iTaigi dictionary page for the entry's `華語` |

The JSON file has a single key `資料` holding an array of entries with the fields above. The CSV has the same columns in the same order.

### Entry id

The iTaigi export carries no identifier of its own, so `id` is derived from the entry's content: the first 16 hex digits of the SHA-256 of its four source fields `華語`, `漢字`, `羅馬字` and `來源`, each normalized to Unicode NFC and joined with U+001F (unit separator). An unchanged entry therefore keeps its id across versions, and any change to its text or contributor gives it a new id.

The export sometimes contains several rows that are identical in all four fields. Only the first is kept, so every id is unique; see Skipped Sources below.

### Entry link

`link` is the iTaigi dictionary page for the entry's `華語`, for example <https://itaigi.tw/k/%E8%A8%8E%E5%8E%AD/> for 討厭. iTaigi has a page per Mandarin headword, not per answer, so the page lists every Taigi answer for that headword and entries that share a `華語` share a link. The headword is percent-encoded in the URL.

### Skipped Sources

iTaigi bundles entries imported from two other dictionaries. They are not crowdsourced iTaigi content and are available from their own sources, so this mirror drops every entry whose `來源` is one of:

| `來源` | Entries in version `20261019-0110` |
|--------|------------------------------------|
| `台文華文線頂辭典` | 64,372 |
| `臺灣閩南語常用詞辭典` | 26,911 |

Rows identical to an earlier row in all four fields are skipped as well; version `20261019-0110` has 65 of them. Of the 111,592 entries in the source export, 20,244 remain after skipping. The raw export in `tangloo/` is kept unchanged but is not committed to this repository.

## Chu-liāu bāng-chí

辭典資料下載

1. [iTaigi 匯出資料](https://itaigi.tw/%E5%8C%AF%E5%87%BA%E8%B3%87%E6%96%99)

## Source

Original data source: <https://itaigi.tw/>
