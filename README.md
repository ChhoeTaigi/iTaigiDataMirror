# iTaigiDataMirror

Data mirror for iTaigi. This site provides direct access to the exported iTaigi crowdsourced dictionary data. The files are hosted on GitHub Pages for easy access.

## Chu-liāu Pán-koân

版權聲明

- 程式授權：[MIT License](https://github.com/i3thuan5/itaigi)
- 辭典內容：[CC0「不保留權利」授權](https://creativecommons.org/public-domain/cc0/)
- [iTaigi隱私權保護條款](https://itaigi.tw/privacy)

![版權聲明](./LICENSE.png)

## Latest Version

- **Version ID:** `20261014-1838`
- **Last Updated:** 2026-10-14

You can check [**manifest.json**](./public/manifest.json) for the latest version information programmatically.

## Accessing Files

The files are organized by version. The latest files are in `public/20261014-1838/`.

### Text Data (Dictionary)

- [**iTaigiSuTian.csv** (Dictionary Data CSV)](./public/20261014-1838/bunji/iTaigiSuTian.csv)
- [**iTaigiSuTian.json** (Dictionary Data JSON)](./public/20261014-1838/bunji/iTaigiSuTian.json)

### Data Fields

| Field  | Description                                      |
|--------|--------------------------------------------------|
| `id` | Unique id: the entry's 1-based position in the source export |
| `華語` | Mandarin Chinese gloss |
| `漢字` | Taigi Han characters |
| `羅馬字` | Taigi Roman Orthography (Tâi-lô) |
| `來源` | Contributor name or `匿名` (anonymous) |

The JSON file has a single key `資料` holding an array of entries with the fields above. The CSV has the same columns in the same order.

### Entry id

The iTaigi export carries no identifier of its own, so `id` is derived from the source: it is the entry's position in the export, counting from 1. Entries skipped by this mirror (see below) keep their slot, so ids have gaps. An id is only meaningful within one version; when iTaigi adds or removes an entry, the ids of every later entry shift.

### Skipped Sources

iTaigi bundles entries imported from two other dictionaries. They are not crowdsourced iTaigi content and are available from their own sources, so this mirror drops every entry whose `來源` is one of:

| `來源` | Entries in version `20261014-1838` |
|--------|------------------------------------|
| `台文華文線頂辭典` | 64,372 |
| `臺灣閩南語常用詞辭典` | 26,911 |

Of the 111,592 entries in the source export, 20,309 remain after skipping. The raw export in `tangloo/` is kept unchanged but is not committed to this repository.

## Chu-liāu bāng-chí

辭典資料下載

1. [iTaigi 匯出資料](https://itaigi.tw/%E5%8C%AF%E5%87%BA%E8%B3%87%E6%96%99)

## Source

Original data source: <https://itaigi.tw/>
