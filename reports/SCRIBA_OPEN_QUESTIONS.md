# Open questions for Scriba (Biblical Latin) — post v0.1.1 blockers

## Phonetics
1. Confirm ecclesiastical-italianate-v1 rules (soft c/g, ti+vowel, ae/oe→e) for Genesis proper names.
2. Diaeresis handling (*Noë*, *Israël*, *Ismaël*, …): pack now skips ae/oe merge and sets `phoneticPending` — confirm or refine.
3. Should macron-aware or stress-marked output be required before promote?
4. Classical toggle: defer, but document any verses where ecclesiastical vs classical differs pedagogically.

## Glosses (blockers addressed in v0.1.1)
1. ~~False Whitaker: deus/domin/sum/ejur~~ → curated Biblical primaries.
2. ~~Must-list stubs (est, ait, dixit, …)~~ → curated filled; UI policy unchanged.
3. Remaining `stub:*` (~6.5k token occurrences) — priority next wave after Scriba re-review.
4. Homograph policy documented in `docs/SOURCES.md` (Biblical N/V preference). Prefer full WORDS morphology later?

## Versification
Original 10 Douay gaps remapped or curated Challoner PD (`meta.gaps`). Additional eng-dra “dummy” slots are left as honest missing (no fake Challoner). Confirm remaps + curated 39.19 / 49.29.

## Copy
About string locked: “Latin text: Clementine Vulgate (PD; Clementine Vulgate Project / Michael Tweedale).”
