# Data contract (v0.1.0-poc)

## Catalog `assets/data/catalog.json`
Lists books, asset paths (`asset` / `assetGz`), gloss paths, totals.

## Pack `assets/data/books/Gen.json(.gz)`
```
Pack { meta, chapters[], verses[], glosses? }
Verse { id, book, chapter, verse, latin, english{text,source,license}, words[] }
Token { la, lemmaId?, phonetic, phoneticScheme, phoneticPending, glossId? }
```

## Glosses `assets/data/glosses.json(.gz)`
Map `glossId → Gloss { id, primary, senses[], source, definition?, note? }`

Ids: `w:<stem>` Whitaker hit; `stub:<key>` pending Scriba.
