# Open questions for Scriba (Biblical Latin) — post v0.1.4 illud/manus

## Phonetics
1. Confirm ecclesiastical-italianate-v1 rules (soft c/g, ti+vowel, ae/oe→e) for Genesis proper names.
2. Diaeresis handling (*Noë*, *Israël*, *Ismaël*, …): pack now skips ae/oe merge and sets `phoneticPending` — confirm or refine.
3. Should macron-aware or stress-marked output be required before promote?
4. Classical toggle: defer, but document any verses where ecclesiastical vs classical differs pedagogically.

## Glosses
1. ~~False Whitaker: deus/domin/sum/ejur~~ → curated Biblical primaries (v0.1.1 PASS).
2. ~~Must-list stubs (est, ait, dixit, …)~~ → curated filled; UI policy unchanged.
3. ~~v0.1.2 ship-block closed-class~~ → curated: et/in/ad/de/super/qui/mei/mi/ubi/num/vita(e)/lux (+ vocavitque/benedixitque). **mei/mi must never gloss “urinate”.**
4. ~~v0.1.3 meis/quis~~ → declined meus-family (incl. all 11× Genesis *meis*, Gen.2.23) curated my/mine with w:mei urinate guard; *Quis/quis* → who? (not how?).
5. ~~v0.1.4 illud/manus~~ → *illud* (+ ille-family) that/it (block illūdō sexual; Gen.3.3); *manum*/*manus* hand (block maneō sexual overnight; Gen.3.22).
6. Remaining `stub:*` — priority next wave after Scriba re-review.
7. Homograph policy (v0.1.2): Biblical N/V **only** for deus/dominus — **not** prep/conj/pron/adv. Documented in `docs/SOURCES.md` + `tools/pipeline/build_genesis_pack.py`. Prefer full WORDS morphology later?

## Versification
Original 10 Douay gaps remapped or curated Challoner PD (`meta.gaps`). Additional eng-dra “dummy” slots are left as honest missing (no fake Challoner). Confirm remaps + curated 39.19 / 49.29.

## Copy
About string locked: “Latin text: Clementine Vulgate (PD; Clementine Vulgate Project / Michael Tweedale).”
