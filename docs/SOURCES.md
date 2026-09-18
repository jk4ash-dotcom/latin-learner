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
- **Alignment:** verse-level by `(chapter, verse)` against Vulgate USFX ids.
- **Versification:** known eng-dra drifts are remapped in-pack (`meta.gaps`, resolution `remap`). Where eng-dra is dummy/corrupt (e.g. Gen.39.19, Gen.49.29), curated Challoner PD is used — **never** show “dummy verses” as Challoner. Remaining true misses stay flagged missing.

### Remap table (Vulgate → eng-dra)
| Vulgate | eng-dra |
|---------|---------|
| 18.2 | 18.3 |
| 20.17 | 20.18 |
| 38.17 | 38.18 |
| 38.28 | 38.30 |
| 39.9 | curated Challoner (eng-dra 39.11 OCR-corrupt) |
| 39.19 | curated Challoner |
| 40.17 | 40.19 |
| 41.7 | 41.9 |
| 49.17 | 49.19 |
| 49.29 | curated Challoner |

## Phonetics
- **Scheme id:** `ecclesiastical-italianate-v1`
- **Documented rules (POC):**
  - `ae`/`æ`, `oe`/`œ` → `e` **unless** the second vowel carries diaeresis (*Noë*, *Israël* → split vowels `noe` / `israel`, `phoneticPending=true`)
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
- **POC matching:** naive stem + ending strip against DICTLINE stems (no full WORDS morphology engine).
- **Homograph / POS policy (v0.1.2):** Biblical **noun/verb** preference applies **only** to true homographs *deus* / *dominus* (masc. N over *domina* / rare *deut*). It does **not** apply to closed-class **PREP / CONJ / PRON / ADV** — when those POS exist among DICTLINE candidates, prefer them over stray N/V. Frequency and area flags break remaining ties.
- **Curated overrides (ship-block):** high-frequency Genesis forms and known false friends force curated primaries (`curated:<key>`), including:
  - Prior PASS: `deus`, `dominus`, `sum`/`est`/`sunt`, `ejus`, *dixit*, *ait*, …
  - **v0.1.2 closed-class:** `et`→and (not go/walk); `in`→in/into (not fiber); `ad`→to/toward (not Adam); `de`→of/from (not God); `super`→above/over (not gods on high); `qui`→who/which (not be able); `mei`/`mi`→my/me (**NOT** urinate — unshippable if wrong); `ubi`→where (not Ubii); `num`→whether/interrogative (not Numerius); `vita`/`vitae`→life (not rim); `lux` (Gen.1.3)→light (not luxury).
  - **v0.1.3 meus-family / quis:** declined `meus`/`mea`/`meum`/`meae`/`meo`/`meam`/`meos`/`meas`/`meorum`/`mearum`/`meis` → my/mine (**NEVER** `w:mei` urinate; Gen.2.23 *ossibus meis* + all 11× Genesis *meis*); `quis`/`Quis` → who? (**NOT** qui ADV how? — Gen.3.11). Guard blocks meiō/mingō and qui-how false stems.
  - **v0.1.4 illud / manus:** `illud` (+ ille-family) → that/it (**NEVER** illūdō mock/sexual — Gen.3.3 *ne tangeremus illud*); `manum`/`manus` (+ manu/manui/manibus/manuum) → hand (**NEVER** maneō remain/sexual overnight — Gen.3.22 *mittat manum*). Guards block false stems.
  - **v0.1.5 Adam:** all Genesis `Adam` → proper name Adam (**NEVER** `w:adam` / adamō “fall in love/lust with” — Gen.2–3 had 14 unshippable lust primaries). Guard blocks lust false stem.
  - **v0.1.6 Adam genitive:** `Adæ`/`Adae` → Adam (gen.) (**NEVER** `w:adar` “plow carefully” — Gen.2.20, 3.17, 3.21). Nominative-only `adam` key insufficient. Later (non-block): Gen.4.23 Adæ=Ada (Lamech’s wife); Gen.10/14 Adama/Admah place-names.
  - **v0.1.7 terra family:** `terra`/`terram`/`terrae`/`terras`/`terris`/`terrarum` (+ *-que* enclitics) → earth/land (**NEVER** `w:terr` / terreō frighten/terrify — Gen.1.1 *terram* + all Genesis noun surfaces). Do **not** fold `terror`/`terroris`, terreō verb forms (*terret*…), or `terrestris`.
  - Optional *-que*: `vocavitque`, `benedixitque`.
- UI copy remains **“Possible sense(s)”** / **“Gloss ≠ verse translation”**.
- Misses become `stub:*` glosses clearly labeled for **Scriba**.

## Rebuild pack
```bash
python3 tools/pipeline/build_genesis_pack.py
```
