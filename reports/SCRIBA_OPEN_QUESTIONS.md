# Open questions for Scriba (Biblical Latin) — post v0.1.10 Wave 4 sum leftovers

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
6. ~~v0.1.5 Adam~~ → all Genesis *Adam* → proper name Adam (block `w:adam`/adamō lust; Gen.2–3 14×).
7. ~~v0.1.6 Adam genitive~~ → *Adæ*/*Adae* → Adam (gen.) (block `w:adar` plow carefully; Gen.2.20, 3.17, 3.21). Nominative-only key insufficient.
8. ~~v0.1.7 terra~~ → *terra*/*terram*/*terrae*/*terras* (+ *terrisque*/*terramque*) → earth/land (block `w:terr`/terreō frighten; Gen.1.1 *terram*). Do not fold terror/terrestris/terret.
9. ~~v0.1.8 Wave 2 prefer-N~~ → *caeli* heaven(s) not beer; *dies*/*die*/*diem*/*diei* day not diesis; *lucem* light; *aqua** water(s) not fetch-V (not *aquilonem*); *tenebr** darkness N; *faciem*/*facie*/*facies* face N (*faciam* stays make); *anim** soul/living being not mind-only; *imaginem* image; *species*/*speciem* kind; *stellas* stars.
10. Later (non-block): Gen.6.14–16 / 18.29 etc. *facies* = faciō 2sg fut. “you will make” — surface prefer-N currently forces face; needs verse-context disambiguation.
11. Later (non-block): Gen.4.23 *Adæ* = Ada (Lamech’s wife); Gen.10/14 Adama/Admah place-names — need verse-context disambiguation.
12. ~~v0.1.9 Wave 3 pronouns~~ → *tibi* to/for you (not flute); *ei* to/for him/her (not Ah!/Woe!); *eos*/*eis*/*ea*/*eas*; *suas* own (not urge); *suum*/*eam*/*hoc*/*vobis* filled. **Scriba Wave 3 CLEAR**.
13. ~~v0.1.10 Wave 4 sum leftovers~~ → *sit* let it be/may be (not allow/permit); *erunt* they will be (not pluck/dig); *essem*/*esses* I/you were (not eat); *esset* were (stub filled); *sint* they may be (not but if); cheap *sim*/*sis*/*simus*/*sitis*/*essent*/*ero*/*eris*/*erit*/*erimus*/*eritis*/*fuerit*/*fuerint*/*fuisset*. **Scriba Wave 3 CLEAR**; Hold Critic→Argus.
14. Remaining `stub:*` — priority next wave; Hold Critic→Argus.
15. Homograph policy (v0.1.2): Biblical N/V **only** for deus/dominus — **not** prep/conj/pron/adv. Documented in `docs/SOURCES.md` + pack builder. Prefer full WORDS morphology later?

## Versification
Original 10 Douay gaps remapped or curated Challoner PD (`meta.gaps`). Additional eng-dra “dummy” slots are left as honest missing (no fake Challoner). Confirm remaps + curated 39.19 / 49.29.

## Copy
About string locked: “Latin text: Clementine Vulgate (PD; Clementine Vulgate Project / Michael Tweedale).”
