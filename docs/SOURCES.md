# Sources — Latin Learner POC

## Latin text
- **Edition:** Clementine Vulgate
- **Pin:** `https://raw.githubusercontent.com/seven1m/open-bibles/master/lat-clementine.usfx.xml`
- **Local extract:** `vendor/open-bibles/lat-clementine-genesis.usfx.xml`
- **Attribution (About copy):** Latin text: Clementine Vulgate (PD; Clementine Vulgate Project / Michael Tweedale).
- **License:** Public Domain

## English underlay
- **Edition:** Douay–Rheims Challoner (eng-dra / DOUR) — **not KJV**
- **Pin:** `https://raw.githubusercontent.com/seven1m/open-bibles/master/eng-dra.zefania.xml`
- **Local extract:** `vendor/open-bibles/eng-dra-genesis.zefania.xml`
- **License:** Public Domain
- **Alignment:** verse-level by `(chapter, verse)` against Vulgate USFX ids. A few versification mismatches are flagged in-pack as missing underlay (see `reports/pack_genesis_0.1.0.json`).

## Phonetics
- **Scheme id:** `ecclesiastical-italianate-v1`
- **Documented rules (POC):**
  - `ae`/`æ`, `oe`/`œ` → `e`
  - `c` before e/i/y → `ch`; else `k`
  - `g` before e/i/y → soft `j`; else `g`
  - `ti` + vowel → `tsi` (not after `s`)
  - `ph`→`f`, `th`→`t`, `qu`→`kw`, `x`→`ks`, `j`→`y`, `v`→`v`
- **Not invented classical macron vocalization.** Classical toggle is future work.
- **Scriba** must accuracy-gate before promote. Tokens may set `phoneticPending`.

## Glosses
- **Lexicon:** Whitaker’s WORDS — https://github.com/mk270/whitakers-words
- **File:** `vendor/whitaker/DICTLINE.GEN`
- **Attribution:** William A. Whitaker (1936–2010)
- **License:** permissive (see `vendor/whitaker/LICENCE.txt`) — free use of program and data
- **POC matching:** naive stem + ending strip against DICTLINE stems (no full WORDS morphology engine). Misses become `stub:*` glosses clearly labeled for **Scriba**.

## Rebuild pack
```bash
python3 tools/pipeline/build_genesis_pack.py
```
