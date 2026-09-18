# Data contract (v0.1.1-poc)

## Catalog `assets/data/catalog.json`
Lists books, asset paths (`asset` / `assetGz`), gloss paths, totals.

## Pack `assets/data/books/Gen.json(.gz)`
```
Pack { meta, chapters[], verses[], glosses? }
Verse { id, book, chapter, verse, latin, english{text,source,license}, words[] }
Token { la, lemmaId?, phonetic, phoneticScheme, phoneticPending, glossId? }
meta.gaps[] { vulgate, douay?, reason, resolution: remap|curated_challoner|missing }
```

## Glosses `assets/data/glosses.json(.gz)`
Map `glossId → Gloss { id, primary, senses[], source, definition?, note? }`

Ids:
- `w:<stem>` Whitaker hit (POS-preferred)
- `curated:<key>` Biblical curated override (homograph / high-freq)
- `stub:<key>` pending Scriba

UI policy: Possible sense(s); Gloss ≠ verse translation.
