#!/usr/bin/env python3
"""Build Genesis offline pack for Latin Learner POC.

Sources (see docs/SOURCES.md):
  - Clementine Vulgate USFX (seven1m/open-bibles)
  - Douay–Rheims Challoner (eng-dra zefania, open-bibles)
  - Whitaker's WORDS DICTLINE.GEN (permissive)
  - Curated Biblical Latin overrides (homograph / false-stem fixes)

Phonetics: documented ecclesiastical (Italianate) scheme — not classical.
  Scriba must accuracy-gate before promote.
"""
from __future__ import annotations

import gzip
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
ASSETS = ROOT / "app" / "src" / "main" / "assets" / "data"
TEST_RES = ROOT / "app" / "src" / "test" / "resources" / "data"

VULGATE = VENDOR / "open-bibles" / "lat-clementine-genesis.usfx.xml"
DOUAY = VENDOR / "open-bibles" / "eng-dra-genesis.zefania.xml"
DICTLINE = VENDOR / "whitaker" / "DICTLINE.GEN"

PACK_VERSION = "0.1.15-poc"
GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# --- Ecclesiastical (Italianate) phonetics ---------------------------------
FRONT = set("eiy")

# Vulgate (c,v) → eng-dra (c,v) when versification drifts (amos dummies / offsets).
# Do NOT invent Challoner; remap to real eng-dra verses or curated PD text below.
DOUAY_REMAP: dict[tuple[int, int], tuple[int, int]] = {
    (18, 2): (18, 3),
    (20, 17): (20, 18),
    (38, 17): (38, 18),
    (38, 28): (38, 30),
    (39, 9): (39, 11),
    (40, 17): (40, 19),
    (41, 7): (41, 9),
    (49, 17): (49, 19),
}

# Clean Challoner (PD) for Vulgate ids where eng-dra is dummy/corrupt after remap.
# Source: traditional Douay–Rheims Challoner public-domain text.
CURATED_CHALLONER: dict[tuple[int, int], str] = {
    (39, 9): (
        "Neither is there any thing which is not in my power, or that he hath not "
        "delivered to me, but thee, who art his wife: how then can I do this wicked "
        "thing, and sin against my God?"
    ),
    (39, 19): (
        "His master hearing these things, and giving too much credit to his wife's "
        "words, was very angry."
    ),
    (49, 29): (
        "And he charged them, saying: I am now going to be gathered to my people: "
        "bury me with my fathers in the double cave, which is in the field of Ephron "
        "the Hethite,"
    ),
}

# Biblical Latin curated glosses — force correct primary for high-freq / false Whitaker.
# UI policy: Possible sense(s); Gloss ≠ verse translation.
def _cur(primary: str, senses: list[str], note: str | None = None) -> dict:
    return {
        "primary": primary,
        "senses": senses,
        "source": "curated Biblical Latin (Genesis POC)",
        "definition": "; ".join(senses),
        "note": note
        or "Curated for Biblical Latin; Gloss ≠ verse translation. Prefer over naive DICTLINE stem.",
    }


CURATED_GLOSS_DEFS: dict[str, dict] = {
    # Blocker false Whitaker hits
    "deus": _cur("God / deity", ["God", "deity", "divine being"], "Biblical noun Deus (not Whitaker deut/misuse)."),
    "dei": _cur("of God / God's", ["of God", "God's", "divine (gen.)"], "Genitive of Deus."),
    "deo": _cur("to/for God", ["to God", "for God", "by God (abl.)"]),
    "deum": _cur("God (acc.)", ["God (accusative)", "deity"]),
    "dominus": _cur("Lord / master", ["Lord", "master", "owner (m.)"], "Biblical Dominus — not domina/mistress."),
    "domine": _cur("O Lord / master (voc.)", ["O Lord", "master (vocative)"]),
    "domini": _cur("of the Lord / master's", ["of the Lord", "of the master", "lords (nom. pl.)"]),
    "domino": _cur("to/for the Lord", ["to the Lord", "for/by the master"]),
    "dominum": _cur("the Lord / master (acc.)", ["the Lord (acc.)", "master (acc.)"]),
    "sum": _cur("to be (I am)", ["I am", "to be (1sg present)"], "Irregular esse — not summus/highest or sumo."),
    "es": _cur("you are", ["you are (2sg)", "to be"]),
    "est": _cur("is / there is", ["is", "there is", "he/she/it is"], "esse 3sg — not Whitaker miss."),
    "sumus": _cur("we are", ["we are"]),
    "estis": _cur("you (pl.) are", ["you are (pl.)"]),
    "sunt": _cur("are / there are", ["are", "there are", "they are"]),
    "eram": _cur("I was", ["I was", "I used to be"]),
    "eras": _cur("you were", ["you were"]),
    "erat": _cur("was / there was", ["was", "there was", "he/she/it was"]),
    "erant": _cur("were / there were", ["were", "there were"]),
    "fui": _cur("I have been / I was", ["I was", "I have been"]),
    "fuit": _cur("was / has been", ["was", "has been", "he/she/it was"]),
    "fuerunt": _cur("were / have been", ["were", "have been"]),
    "esse": _cur("to be", ["to be", "exist"]),
    "ejus": _cur("his / her / its", ["his", "her", "its", "of him/her/it"], "is/ea/id gen. — not ejuro/abjure."),
    "eius": _cur("his / her / its", ["his", "her", "its", "of him/her/it"]),
    # Must-list stubs (surface forms)
    "ait": _cur("says / said (defective)", ["says", "said", "he/she says"]),
    "dixit": _cur("he/she said", ["said", "spoke", "declared"]),
    "dixitque": _cur("and he/she said", ["and said", "and spoke"]),
    "genuit": _cur("he begot / fathered", ["begot", "fathered", "brought forth"]),
    "eum": _cur("him / it (acc.)", ["him", "it (m./n. acc.)", "that one"]),
    "te": _cur("you (acc./abl. sg.)", ["you (sg.)", "thee"]),
    "mihi": _cur("to/for me", ["to me", "for me", "me (dat.)"]),
    "vocavit": _cur("he/she called", ["called", "named", "summoned"]),
    "vidit": _cur("he/she saw", ["saw", "beheld"]),
    "fecit": _cur("he/she made / did", ["made", "did", "performed"]),
    "creavit": _cur("he/she created", ["created", "brought into being"]),
    "fiat": _cur("let it be / may it happen", ["let it be done", "may it be", "let there be"]),
    "benedixit": _cur("he/she blessed", ["blessed", "spoke well of"]),
    "posuit": _cur("he/she placed / put", ["placed", "put", "set"]),
    "vocavitque": _cur("and he/she called", ["and called", "and named", "and summoned"]),
    "benedixitque": _cur("and he/she blessed", ["and blessed", "and spoke well of"]),
    # v0.1.2 ship-block closed-class / false Whitaker (Mahomes/Scriba)
    "et": _cur("and", ["and", "also", "even"], "Conjunction et — not eo/go/walk."),
    "in": _cur("in / into", ["in", "into", "on", "among"], "Preposition in — not fiber/sinew."),
    "ad": _cur("to / toward", ["to", "toward", "near", "at"], "Preposition ad — not Adam."),
    "de": _cur("of / from", ["of", "from", "about", "concerning"], "Preposition de — not Deus/God."),
    "super": _cur("above / over", ["above", "over", "upon", "concerning"], "Prep/adv super — not 'gods on high'."),
    "qui": _cur("who / which", ["who", "which", "that (rel.)"], "Relative qui — not queo/be able."),
    "mei": _cur(
        "my / of me",
        ["my", "of me", "mine (gen.)"],
        "Genitive of meus/ego — NOT meiō/urinate. Unshippable if wrong.",
    ),
    "mi": _cur(
        "my / me (voc./dat.)",
        ["my (voc.)", "to me", "me"],
        "Vocative meus (domine mi) / dat. ego — NOT mingō/urinate. Unshippable if wrong.",
    ),
    "ubi": _cur("where", ["where", "when", "whenever"], "Adverb/conj ubi — not Ubii tribe."),
    "num": _cur(
        "whether / interrogative",
        ["whether", "surely not?", "really?"],
        "Interrogative particle — not Numerius.",
    ),
    "vita": _cur("life", ["life", "livelihood", "manner of life"], "Noun vita — not vit rim."),
    "vitae": _cur(
        "of life / lives",
        ["of life", "lives", "life (gen./dat./nom.pl.)"],
        "vita declined — not vit rim.",
    ),
    "lux": _cur(
        "light",
        ["light", "daylight", "day"],
        "Gen.1.3 Fiat lux — noun lux/lucis, not luxury/sprain.",
    ),
    # v0.1.3: declined meus-family (block w:mei urinate) + interrogative quis
    "meus": _cur(
        "my / mine",
        ["my", "mine", "my own"],
        "Possessive adjective meus — NOT meiō/mingō urinate. Unshippable if wrong.",
    ),
    "mea": _cur(
        "my / mine (f.)",
        ["my", "mine", "my (f.)"],
        "meus-family (f.) — NOT urinate.",
    ),
    "meum": _cur(
        "my / mine (n./acc.)",
        ["my", "mine", "my (n./acc.)"],
        "meus-family — NOT urinate.",
    ),
    "meae": _cur(
        "my / of my (f.)",
        ["my", "of my", "mine (f. gen./dat./nom.pl.)"],
        "meus-family — NOT urinate.",
    ),
    "meo": _cur(
        "to/for/by my",
        ["to my", "for my", "by/with my (m./n.)"],
        "meus-family — NOT urinate.",
    ),
    "meam": _cur(
        "my (f. acc.)",
        ["my (f. acc.)", "mine"],
        "meus-family — NOT urinate.",
    ),
    "meos": _cur(
        "my (m. pl. acc.)",
        ["my (m. pl.)", "mine"],
        "meus-family — NOT urinate.",
    ),
    "meas": _cur(
        "my (f. pl. acc.)",
        ["my (f. pl.)", "mine"],
        "meus-family — NOT urinate.",
    ),
    "meorum": _cur(
        "of my (m./n. pl.)",
        ["of my", "of mine", "my (gen. pl.)"],
        "meus-family — NOT urinate.",
    ),
    "mearum": _cur(
        "of my (f. pl.)",
        ["of my", "of mine", "my (f. gen. pl.)"],
        "meus-family — NOT urinate.",
    ),
    "meis": _cur(
        "my / mine",
        ["my", "mine", "with/from/to my (dat./abl. pl.)"],
        "Gen.2.23 ossibus meis + all Genesis meis — meus-family dat./abl. pl. NEVER meiō/urinate.",
    ),
    "quis": _cur(
        "who?",
        ["who?", "who", "anyone/someone (indef.)"],
        "Gen.3.11 Quis enim — interrogative quis, NOT qui ADV how?.",
    ),
    # v0.1.4: illud/ille-family (block illūdō sexual) + manus-family (block maneō sexual overnight)
    "illud": _cur(
        "that / it",
        ["that", "it", "that thing (n. nom./acc.)"],
        "Gen.3.3 ne tangeremus illud — demonstrative ille/illud, NEVER illūdō mock/sexual. Unshippable if wrong.",
    ),
    "ille": _cur(
        "that (m.)",
        ["that", "he", "that one (m.)"],
        "Demonstrative ille — NOT illūdō mock/sexual.",
    ),
    "illa": _cur(
        "that (f./n.pl.)",
        ["that", "she", "those (n. pl.)"],
        "Demonstrative ille-family — NOT illūdō.",
    ),
    "illum": _cur(
        "that / him (m. acc.)",
        ["that", "him", "that one (m. acc.)"],
        "Demonstrative ille-family — NOT illūdō.",
    ),
    "illam": _cur(
        "that / her (f. acc.)",
        ["that", "her", "that one (f. acc.)"],
        "Demonstrative ille-family — NOT illūdō.",
    ),
    "illius": _cur(
        "of that / his / her / its",
        ["of that", "his", "her", "its (gen.)"],
        "Demonstrative ille gen. — NOT illūdō.",
    ),
    "illi": _cur(
        "to that / those (m.)",
        ["to that", "to him", "those (m. nom. pl.)"],
        "Demonstrative ille-family — NOT illūdō.",
    ),
    "illo": _cur(
        "by/with that (abl.)",
        ["by that", "with that", "from that (m./n. abl.)"],
        "Demonstrative ille abl. — NOT ADV illo/thither alone; NOT illūdō.",
    ),
    "illis": _cur(
        "to/for/by those",
        ["to those", "for those", "by/with those (dat./abl. pl.)"],
        "Demonstrative ille-family — NOT illidō strike; NOT illūdō.",
    ),
    "illos": _cur(
        "those (m. acc. pl.)",
        ["those", "them (m. acc.)"],
        "Demonstrative ille-family — NOT illūdō.",
    ),
    "illas": _cur(
        "those (f. acc. pl.)",
        ["those", "them (f. acc.)"],
        "Demonstrative ille-family — NOT illūdō.",
    ),
    "illae": _cur(
        "those (f. nom. pl.)",
        ["those", "they (f.)"],
        "Demonstrative ille-family — NOT illūdō.",
    ),
    "illorum": _cur(
        "of those (m./n.)",
        ["of those", "their (m./n. gen. pl.)"],
        "Demonstrative ille-family — NOT illūdō.",
    ),
    "illarum": _cur(
        "of those (f.)",
        ["of those", "their (f. gen. pl.)"],
        "Demonstrative ille-family — NOT illūdō.",
    ),
    "manus": _cur(
        "hand",
        ["hand", "fist", "band/troop"],
        "Noun manus — NEVER maneō remain/spend the night (sexual). Unshippable if wrong.",
    ),
    "manum": _cur(
        "hand (acc.)",
        ["hand (acc.)", "hand"],
        "Gen.3.22 mittat manum — manus acc. NEVER maneō remain/sexual overnight. Unshippable if wrong.",
    ),
    "manu": _cur(
        "by/with the hand (abl.)",
        ["by hand", "with the hand", "hand (abl.)"],
        "manus abl. — NEVER maneō.",
    ),
    "manui": _cur(
        "to/for the hand (dat.)",
        ["to the hand", "for the hand", "hand (dat.)"],
        "manus dat. — NEVER maneō.",
    ),
    "manibus": _cur(
        "hands (dat./abl. pl.)",
        ["hands", "by/with hands", "to hands"],
        "manus dat./abl. pl. — NEVER maneō.",
    ),
    "manuum": _cur(
        "of hands (gen. pl.)",
        ["of hands", "hands (gen. pl.)"],
        "manus gen. pl. — NEVER maneō.",
    ),
    # v0.1.5: Adam proper name (block w:adam / adamō lust)
    "adam": _cur(
        "Adam",
        ["Adam", "Adam (first man)", "proper name"],
        "All Genesis Adam — proper name Adam. NEVER adamō/w:adam fall in love/lust with. Unshippable if wrong.",
    ),
    # v0.1.6: Adam genitive Adæ/Adae (block w:adar plow carefully)
    "adae": _cur(
        "Adam (gen.)",
        ["Adam (gen.)", "of Adam", "Adam"],
        "Genesis Adæ/Adae genitive of Adam (e.g. Gen.2.20, 3.17, 3.21). NEVER w:adar plow carefully. "
        "Gen.4.23 Adæ→Ada (Lamech wife) via verse-context override (Wave 7). "
        "Gen.10/14 Adamam/Adamæ→Admah place (v0.1.11). Unshippable if plow.",
    ),
    # v0.1.7: terra NOUN family → earth/land (block w:terr / terreō frighten)
    # Do NOT fold: terror/terroris; terreō verb forms (terret…); terrestris.
    "terra": _cur(
        "earth / land",
        ["earth", "land", "ground", "country"],
        "Noun terra — NEVER terreō/w:terr frighten/terrify/terror. Unshippable if wrong.",
    ),
    "terram": _cur(
        "earth / land (acc.)",
        ["earth (acc.)", "land (acc.)", "ground"],
        "Gen.1.1 cælum et terram — terra acc. NEVER terreō/w:terr frighten. Unshippable if wrong.",
    ),
    "terrae": _cur(
        "of/to the earth / lands",
        ["of the earth", "to the earth", "lands (nom. pl.)", "earth (gen./dat.)"],
        "terra gen./dat./nom.pl. (incl. terræ) — NEVER terreō. Unshippable if frighten.",
    ),
    "terras": _cur(
        "lands (acc. pl.)",
        ["lands", "earths (acc. pl.)"],
        "terra acc. pl. — NEVER terreō/w:terr.",
    ),
    "terris": _cur(
        "lands (dat./abl. pl.)",
        ["lands", "by/with/from lands", "to lands"],
        "terra dat./abl. pl. — NEVER terreō. Covers terrisque (Gen.10.20).",
    ),
    "terrarum": _cur(
        "of lands (gen. pl.)",
        ["of lands", "of the earth (gen. pl.)"],
        "terra gen. pl. — NEVER terreō. Family completeness (no bare form in Genesis).",
    ),

    # v0.1.8 Wave 2 SHIP_BLOCK — surface families prefer N sense (Mahomes/Scriba)
    # 1) caelum family → heaven(s) (block w:caeli beer)
    "caelum": _cur(
        "heaven / sky",
        ["heaven", "sky", "heavens"],
        "Noun caelum — NEVER caeli beer. Unshippable if beer.",
    ),
    "caeli": _cur(
        "of heaven / heavens",
        ["of heaven", "heavens", "heaven (gen./nom.pl.)"],
        "Gen.1.14+ cæli/caeli — caelum gen./nom.pl. NEVER w:caeli beer. Unshippable if beer.",
    ),
    "caelo": _cur(
        "in/from heaven (abl./dat.)",
        ["in heaven", "from heaven", "to heaven", "heaven (abl./dat.)"],
        "caelum abl./dat. — NEVER beer.",
    ),
    "caelos": _cur(
        "heavens (acc. pl.)",
        ["heavens", "skies (acc. pl.)"],
        "caelum acc. pl. — NEVER beer.",
    ),
    "caelis": _cur(
        "heavens (dat./abl. pl.)",
        ["heavens", "in/from heavens"],
        "caelum dat./abl. pl. — NEVER beer.",
    ),
    "caelorum": _cur(
        "of the heavens (gen. pl.)",
        ["of the heavens", "of heaven (gen. pl.)"],
        "caelum gen. pl. — NEVER beer.",
    ),
    # 2) dies family → day (block w:dies diesis/quarter tone)
    "dies": _cur(
        "day",
        ["day", "daylight", "daytime"],
        "Noun dies — NEVER diesis/quarter tone (w:dies). Unshippable if quarter/diesis.",
    ),
    "die": _cur(
        "on/in the day (abl.)",
        ["on the day", "in the day", "day (abl.)"],
        "dies abl. — NEVER diesis. Unshippable if quarter/diesis.",
    ),
    "diem": _cur(
        "day (acc.)",
        ["day (acc.)", "day"],
        "dies acc. — NEVER diesis.",
    ),
    "diei": _cur(
        "of the day (gen.)",
        ["of the day", "day (gen./dat.)"],
        "dies gen./dat. — NEVER diesis.",
    ),
    "diebus": _cur(
        "days (dat./abl. pl.)",
        ["days", "in/on the days", "to the days"],
        "dies dat./abl. pl. — NEVER diesis.",
    ),
    "dierum": _cur(
        "of days (gen. pl.)",
        ["of days", "days (gen. pl.)"],
        "dies gen. pl. — NEVER diesis. Covers dierumque.",
    ),
    # 3) lux declined → light (lux already curated v0.1.2; block grove/luxury)
    "lucem": _cur(
        "light (acc.)",
        ["light (acc.)", "light", "daylight"],
        "lux acc. Gen.1.4–5 — NEVER w:luc grove; NOT luxury. Unshippable if grove.",
    ),
    "lucis": _cur(
        "of light (gen.)",
        ["of light", "light (gen.)"],
        "lux gen. — NEVER grove/luxury.",
    ),
    "luce": _cur(
        "by/with light (abl.)",
        ["by light", "with light", "light (abl.)"],
        "lux abl. — NEVER grove/luxury. Do NOT fold luceant/lucerent (shine V).",
    ),
    "luci": _cur(
        "to/for light (dat.)",
        ["to light", "for light", "light (dat.)"],
        "lux dat. — NEVER grove/luxury.",
    ),
    # 4) aqua family → water(s) (block w:aqu fetch-water V); NOT aquilo north
    "aqua": _cur(
        "water",
        ["water", "waters", "a water"],
        "Noun aqua — NEVER aquor fetch/bring water. Unshippable if fetch.",
    ),
    "aquae": _cur(
        "of water / waters",
        ["of water", "waters", "water (gen./dat./nom.pl.)"],
        "aqua declined — NEVER fetch-water V.",
    ),
    "aquam": _cur(
        "water (acc.)",
        ["water (acc.)", "water"],
        "aqua acc. — NEVER fetch-water V.",
    ),
    "aquas": _cur(
        "waters (acc. pl.)",
        ["waters", "water (acc. pl.)"],
        "aqua acc. pl. Gen.1.2+ — NEVER fetch-water V.",
    ),
    "aquarum": _cur(
        "of waters (gen. pl.)",
        ["of waters", "of water (gen. pl.)"],
        "aqua gen. pl. — NEVER fetch-water V.",
    ),
    "aquis": _cur(
        "waters (dat./abl. pl.)",
        ["waters", "in/by/from waters", "to waters"],
        "aqua dat./abl. pl. — NEVER fetch-water V.",
    ),
    # 5) tenebrae family → darkness N (block darken V; not teneō hold)
    "tenebrae": _cur(
        "darkness",
        ["darkness", "gloom", "shadows"],
        "Noun tenebrae — NEVER tenebrō darken V; NOT teneō hold. Unshippable if darken/hold.",
    ),
    "tenebras": _cur(
        "darkness (acc. pl.)",
        ["darkness", "darkness (acc.)", "gloom"],
        "tenebrae acc. — NEVER darken V; NOT teneō.",
    ),
    "tenebris": _cur(
        "in/from darkness (dat./abl. pl.)",
        ["in darkness", "from darkness", "darkness (dat./abl.)"],
        "tenebrae dat./abl. — NEVER darken V; NOT teneō.",
    ),
    "tenebrarum": _cur(
        "of darkness (gen. pl.)",
        ["of darkness", "darkness (gen. pl.)"],
        "tenebrae gen. pl. — NEVER darken V.",
    ),
    # 6) facies N → face (faciam/faciat/faciens stay make V). Prefer N on these surfaces.
    "faciem": _cur(
        "face",
        ["face", "countenance", "surface/face (of)"],
        "Noun facies acc. Gen.1.2+ — NEVER faciō make/build. faciam etc. stay make. Unshippable if make.",
    ),
    "facie": _cur(
        "face (abl.)",
        ["face (abl.)", "from the face", "countenance"],
        "facies abl. — NEVER faciō make. Prefer N.",
    ),
    "facies": _cur(
        "face",
        ["face", "countenance", "appearance"],
        "Noun facies — prefer N face (Gen.4.6, 40.7). Faciō 2sg fut. (Gen.6.14–16, 18.29, etc.) via verse-context override curated:facies_make. Unshippable if make as sole primary here.",
    ),
    "facies_make": _cur(
        "you will make",
        ["you will make", "you will do", "faciō 2sg future"],
        "Verse-context: Gen.6.14–16 / 18.25 / 18.29 / 20.13 / 21.23 / 47.29 facies = faciō 2sg fut. "
        "Default surface curated:facies stays face N. Mirror Ada Gen.4.23 pattern. Unshippable if face on these verses.",
    ),
    # 7) anima family → soul/living being (NOT animus mind); do not fold animant/animal/animadvert*
    "anima": _cur(
        "soul / living being",
        ["soul", "living being", "life", "breath"],
        "Noun anima — NEVER animus mind as primary. Biblical living soul. Unshippable if mind-only.",
    ),
    "animam": _cur(
        "soul / living being (acc.)",
        ["soul (acc.)", "living being", "life"],
        "anima acc. Gen.1.21+ — NEVER mind-only animus.",
    ),
    "animae": _cur(
        "of the soul / living beings",
        ["of the soul", "living beings", "soul (gen./dat./nom.pl.)"],
        "anima declined — NEVER mind-only.",
    ),
    "animas": _cur(
        "souls / living beings (acc. pl.)",
        ["souls", "living beings", "lives (acc. pl.)"],
        "anima acc. pl. — NEVER mind-only.",
    ),
    "animarum": _cur(
        "of souls / living beings (gen. pl.)",
        ["of souls", "of living beings", "souls (gen. pl.)"],
        "anima gen. pl. — NEVER mind-only.",
    ),
    "animo": _cur(
        "soul / spirit (dat./abl.)",
        ["soul", "spirit", "living being (dat./abl.)"],
        "Prefer anima/spirit sense — NOT mind-only animus. Do not fold animadvert*.",
    ),
    "animis": _cur(
        "souls / spirits (dat./abl. pl.)",
        ["souls", "spirits", "living beings (dat./abl. pl.)"],
        "Prefer soul/living being — NOT mind-only.",
    ),
    "animum": _cur(
        "soul / spirit (acc.)",
        ["soul", "spirit", "heart (acc.)"],
        "Prefer soul/spirit over Whitaker animus mind-only (Gen.26.35). Unshippable if mind-only.",
    ),
    # 8) imago / species / stella
    "imaginem": _cur(
        "image",
        ["image", "likeness", "copy"],
        "Noun imago acc. Gen.1.26–27 — NEVER imaginor imagine V. Unshippable if imagine.",
    ),
    "imago": _cur(
        "image",
        ["image", "likeness", "copy"],
        "Noun imago — NEVER imagine V.",
    ),
    "imagine": _cur(
        "image (abl.)",
        ["image (abl.)", "likeness"],
        "imago abl. — NEVER imagine V.",
    ),
    "species": _cur(
        "kind / species",
        ["kind", "species", "sort", "appearance"],
        "Noun species Gen.1.21+ — NEVER speciō look-at V. Unshippable if look.",
    ),
    "speciem": _cur(
        "kind / appearance (acc.)",
        ["kind (acc.)", "species", "appearance"],
        "species acc. Gen.1.12 — NEVER look-at V.",
    ),
    "stella": _cur(
        "star",
        ["star", "planet", "constellation"],
        "Noun stella — NEVER stellō set-with-stars V.",
    ),
    "stellas": _cur(
        "stars (acc. pl.)",
        ["stars", "stars (acc. pl.)"],
        "stella acc. pl. Gen.1.16+ — NEVER stellō set/furnish with stars. Unshippable if set/furnish.",
    ),
    "stellae": _cur(
        "of the star / stars",
        ["of the star", "stars", "star (gen./dat./nom.pl.)"],
        "stella declined — NEVER stellō V.",
    ),
    "stellis": _cur(
        "stars (dat./abl. pl.)",
        ["stars", "with/from stars"],
        "stella dat./abl. pl. — NEVER stellō V.",
    ),
    "stellarum": _cur(
        "of stars (gen. pl.)",
        ["of stars", "stars (gen. pl.)"],
        "stella gen. pl. — NEVER stellō V.",
    ),

    # v0.1.9 Wave 3 SHIP_BLOCK — pronouns (Mahomes/Scriba; Wave 2 CLEAR)
    # Core blockers
    "tibi": _cur(
        "to/for you",
        ["to you", "for you", "you (dat. sg.)"],
        "Dative of tu — NEVER tibi flute/pipe. Unshippable if flute/pipe.",
    ),
    "ei": _cur(
        "to/for him/her",
        ["to him", "to her", "for him/her", "him/her (dat.)"],
        "Dative of is/ea/id — NEVER interjection Ah!/Woe!. Unshippable if Ah/Woe/alas.",
    ),
    # is/ea/id pronoun mess (cheap add-ons)
    "eos": _cur(
        "them (m. acc. pl.)",
        ["them", "those (m. acc. pl.)", "them (m.)"],
        "Acc. pl. of is — NEVER Eos dawn. Unshippable if dawn.",
    ),
    "eis": _cur(
        "to/for them",
        ["to them", "for them", "by/with them (dat./abl. pl.)"],
        "Dat./abl. pl. of is/ea/id — pronoun, not Whitaker miss.",
    ),
    "ea": _cur(
        "she / that (f.) / them (n.)",
        ["she", "that (f.)", "them (n. nom./acc. pl.)", "by that (abl.)"],
        "is/ea/id feminine / n.pl. — Biblical pronoun.",
    ),
    "eas": _cur(
        "them (f. acc. pl.)",
        ["them", "those (f. acc. pl.)", "them (f.)"],
        "Acc. pl. f. of is/ea/id — Biblical pronoun.",
    ),
    # Mahomes extras / cheap stubs filled
    "suas": _cur(
        "his/her/their own (f. pl.)",
        ["his own", "her own", "their own", "own (f. pl. acc.)"],
        "Possessive suus f.pl. (Gen.1.21 species suas) — NEVER suadeō urge/recommend or suāsus advice. Unshippable if urge/advice.",
    ),
    "suum": _cur(
        "his/her/its/their own",
        ["his own", "her own", "its own", "their own", "own (n./m. acc.)"],
        "Possessive suus — Biblical pronoun/adj.",
    ),
    "eam": _cur(
        "her / it (f. acc.)",
        ["her", "it (f. acc.)", "that one (f. acc.)"],
        "Acc. f. of is/ea/id — Biblical pronoun.",
    ),
    "hoc": _cur(
        "this",
        ["this", "this thing (n. nom./acc.)", "by this (abl.)"],
        "Demonstrative hic/hoc — Biblical pronoun. NOT hockey.",
    ),
    "vobis": _cur(
        "to/for you (pl.)",
        ["to you (pl.)", "for you (pl.)", "you (dat./abl. pl.)"],
        "Dative/abl. of vos — Biblical pronoun.",
    ),

    # v0.1.10 Wave 4 SHIP_BLOCK — sum leftovers (Mahomes/Scriba; Wave 3 CLEAR)
    # Core blockers
    "sit": _cur(
        "let it be / may be",
        ["let it be", "may be", "may it be", "let there be (subj.)"],
        "esse 3sg present subjunctive — NEVER sinō allow/permit. Unshippable if allow/permit.",
    ),
    "erunt": _cur(
        "they will be",
        ["they will be", "will be (3pl)", "there will be"],
        "esse 3pl future — NEVER eruō pluck/dig/root up. Unshippable if pluck/dig.",
    ),
    "essem": _cur(
        "I were / I might be",
        ["I were", "I might be", "I would be (1sg impf. subj.)"],
        "esse 1sg imperfect subjunctive — NEVER edō/ess- eat/consume. Unshippable if eat.",
    ),
    "esses": _cur(
        "you were / you might be",
        ["you were", "you might be", "you would be (2sg impf. subj.)"],
        "esse 2sg imperfect subjunctive — NEVER edō/ess- eat/consume. Unshippable if eat.",
    ),
    "esset": _cur(
        "were / might be",
        ["were", "might be", "would be", "he/she/it were (3sg impf. subj.)"],
        "esse 3sg imperfect subjunctive — fill stub; NEVER edō eat.",
    ),
    "sint": _cur(
        "they may be",
        ["they may be", "may be (3pl)", "let them be"],
        "esse 3pl present subjunctive — NEVER sin CONJ but if. Unshippable if but if.",
    ),
    # Cheap add-ons — other broken sum/esse forms in Genesis
    "sim": _cur(
        "I may be",
        ["I may be", "I might be", "let me be (1sg subj.)"],
        "esse 1sg present subjunctive — NEVER sim- flatnosed/snub-nosed. Unshippable if flatnosed.",
    ),
    "sis": _cur(
        "you may be",
        ["you may be", "you might be", "be (2sg subj.)"],
        "esse 2sg present subjunctive — fill stub.",
    ),
    "simus": _cur(
        "we may be",
        ["we may be", "we might be", "let us be"],
        "esse 1pl present subjunctive — NEVER sim- flatnosed.",
    ),
    "sitis": _cur(
        "you (pl.) may be",
        ["you may be (pl.)", "you might be (pl.)", "be (2pl subj.)"],
        "esse 2pl present subjunctive — NEVER sitis thirst. Unshippable if thirst.",
    ),
    "essent": _cur(
        "they were / might be",
        ["they were", "they might be", "they would be (3pl impf. subj.)"],
        "esse 3pl imperfect subjunctive — NEVER essentō make real. Unshippable if make real.",
    ),
    "ero": _cur(
        "I will be",
        ["I will be", "I shall be"],
        "esse 1sg future — NEVER ero basket of reeds. Unshippable if basket.",
    ),
    "eris": _cur(
        "you will be",
        ["you will be", "you shall be (2sg fut.)"],
        "esse 2sg future — NEVER eris hedgehog. Unshippable if hedgehog.",
    ),
    "erit": _cur(
        "he/she/it will be",
        ["will be", "he/she/it will be", "there will be"],
        "esse 3sg future — fill stub.",
    ),
    "erimus": _cur(
        "we will be",
        ["we will be", "we shall be"],
        "esse 1pl future — fill stub.",
    ),
    "eritis": _cur(
        "you (pl.) will be",
        ["you will be (pl.)", "you shall be (pl.)"],
        "esse 2pl future — fill stub.",
    ),
    "fuerit": _cur(
        "will have been / may have been",
        ["will have been", "may have been", "has been (fut. perf./perf. subj.)"],
        "esse future perfect / perfect subjunctive 3sg — fill stub.",
    ),
    "fuerint": _cur(
        "will have been / may have been (pl.)",
        ["will have been (pl.)", "may have been (pl.)", "have been (3pl)"],
        "esse future perfect / perfect subjunctive 3pl — fill stub.",
    ),
    "fuisset": _cur(
        "had been / would have been",
        ["had been", "would have been", "might have been"],
        "esse pluperfect subjunctive 3sg — fill stub.",
    ),

    # v0.1.11 Wave 5 SHIP_BLOCK — proper names / false friends (Mahomes/Scriba; Wave 4 CLEAR)
    "sara": _cur(
        "Sarah",
        ["Sarah", "Sara (proper name)"],
        "Genesis Sara/Saram/Saræ — proper name Sarah. NEVER sar-/hoe. Unshippable if hoe.",
    ),
    "saram": _cur(
        "Sarah (acc.)",
        ["Sarah (acc.)", "Sara (acc.)", "Sarah"],
        "Acc. of Sara — NEVER sar-/hoe. Unshippable if hoe.",
    ),
    "sarae": _cur(
        "Sarah (gen./dat.)",
        ["Sarah (gen./dat.)", "of Sarah", "to/for Sarah", "Sarah"],
        "Gen./dat. of Sara (Saræ) — NEVER sar-/hoe. Unshippable if hoe.",
    ),
    "sarai": _cur(
        "Sarai",
        ["Sarai", "Sarai (proper name)", "Sarah (earlier name)"],
        "Genesis Sarai — proper name (later Sara/Sarah). Fill stub; never hoe.",
    ),
    "lot": _cur(
        "Lot",
        ["Lot", "Lot (proper name)"],
        "Genesis Lot — proper name. NEVER lot-/wash/bathe. Unshippable if wash.",
    ),
    "edom": _cur(
        "Edom",
        ["Edom", "Edom (proper name / place)"],
        "Genesis Edom — proper name/place (Esau). NEVER edom-/subdue. Unshippable if subdue.",
    ),
    "sex": _cur(
        "six",
        ["six", "6"],
        "Cardinal numeral sex — NEVER English 'sex'. Unshippable if sex.",
    ),
    "venit": _cur(
        "come / comes",
        ["come", "comes", "he/she/it comes", "came (hist. present)"],
        "veniō 3sg — NEVER vēnum īre / go for sale. Unshippable if go for sale / sold.",
    ),
    "venite": _cur(
        "come! (pl.)",
        ["come! (pl.)", "come ye", "come (2pl imp.)"],
        "veniō 2pl imperative — NEVER go for sale. Unshippable if go for sale.",
    ),
    "adamam": _cur(
        "Admah (place)",
        ["Admah (place)", "Adama", "Admah"],
        "Genesis Adamam — place-name Admah (Gen.10.19). NEVER adamō/lust. Kill lust primary. Unshippable if lust.",
    ),
    "adamae": _cur(
        "Admah (place, gen./dat.)",
        ["Admah (place)", "of Admah", "Adama (gen.)", "Admah"],
        "Genesis Adamæ — place-name Admah (Gen.14.2/14.8). NEVER adamō/lust. Kill lust primary. Unshippable if lust.",
    ),
    "bala": _cur(
        "Bala (proper name)",
        ["Bala", "Bala (proper name)", "Bilhah", "Bela"],
        "Genesis Bala/Balam/Balæ — proper name (Bilhah maid / place Bela). NEVER bal-/bleat. Unshippable if bleat.",
    ),
    "balam": _cur(
        "Bala (acc.)",
        ["Bala (acc.)", "Bilhah (acc.)", "Bala"],
        "Acc. of Bala/Bilhah — NEVER bal-/bleat. Unshippable if bleat.",
    ),
    "balae": _cur(
        "Bala (gen./dat.)",
        ["Bala (gen./dat.)", "of Bala", "Bilhah (gen.)", "Bela (gen.)"],
        "Gen./dat. Balæ — proper name (Bilhah / place Bela). NEVER bal-/bleat. Unshippable if bleat.",
    ),
    "her": _cur(
        "Her (proper name)",
        ["Her", "Her (proper name)", "Er"],
        "Genesis Her — proper name (Judah's son Er). NEVER haereō stick/adhere. Unshippable if stick/adhere.",
    ),
    "sale": _cur(
        "Sale (proper name)",
        ["Sale", "Sale (proper name)", "Salah"],
        "Genesis Sale — proper name (genealogy). NEVER sal-/leap/jump. Unshippable if leap.",
    ),
    "salem": _cur(
        "Salem (place)",
        ["Salem", "Salem (place)", "city of Salem"],
        "Genesis Salem — place-name (Melchizedek / Sichem). NEVER sal-/leap. Unshippable if leap.",
    ),

    # v0.1.12 Wave 6 SHIP_BLOCK — V-over-N mid pack prefer N (Mahomes/Scriba; Wave 5 CLEAR)
    # 1) domus → house (block w:dom / domō subdue). Do NOT fold Dominus/Domine.
    "domus": _cur(
        "house / household",
        ["house", "home", "household", "family"],
        "Noun domus — NEVER domō subdue/tame/master. Unshippable if subdue. Dominus/Domine stay Lord.",
    ),
    "domum": _cur(
        "house (acc.)",
        ["house (acc.)", "home", "household"],
        "domus acc. — NEVER domō subdue. Unshippable if subdue.",
    ),
    "domo": _cur(
        "from/in the house (abl.)",
        ["from the house", "in the house", "house (abl.)", "home"],
        "domus abl. — NEVER domō subdue V. Unshippable if subdue.",
    ),
    "domui": _cur(
        "to/for the house (dat.)",
        ["to the house", "for the household", "house (dat.)"],
        "domus dat. — NEVER domō subdue.",
    ),
    "domi": _cur(
        "at home (loc.)",
        ["at home", "in the house", "home (loc.)"],
        "domus locative — NEVER domō subdue. Not Domine (voc. Dominus).",
    ),
    "domos": _cur(
        "houses (acc. pl.)",
        ["houses", "homes (acc. pl.)"],
        "domus acc. pl. — NEVER domō subdue.",
    ),
    "domibus": _cur(
        "houses (dat./abl. pl.)",
        ["houses", "households", "in/from houses"],
        "domus dat./abl. pl. — NEVER domō subdue.",
    ),
    # 2) locus → place N (block locō place-as-verb)
    "locus": _cur(
        "place",
        ["place", "spot", "location", "site"],
        "Noun locus — NEVER locō place/put/station V. Unshippable if put/station as sole primary.",
    ),
    "locum": _cur(
        "place (acc.)",
        ["place (acc.)", "place", "spot"],
        "locus acc. Gen.1.9+ — NEVER locō place-V. Unshippable if put/station.",
    ),
    "loco": _cur(
        "in/from the place (abl./dat.)",
        ["in the place", "from the place", "place (abl./dat.)", "instead of (adv. sense)"],
        "locus abl./dat. — prefer place N; NEVER locō place-V as primary.",
    ),
    "loci": _cur(
        "of the place / places",
        ["of the place", "places", "place (gen./nom.pl.)"],
        "locus gen./nom.pl. — NEVER locō place-V.",
    ),
    "locis": _cur(
        "places (dat./abl. pl.)",
        ["places", "in/from places"],
        "locus dat./abl. pl. — NEVER locō place-V.",
    ),
    # 3) servus → servant N (block serviō serve-V). Includes servam maidservant.
    "servus": _cur(
        "servant / slave",
        ["servant", "slave", "bondman"],
        "Noun servus — NEVER serviō serve V. Unshippable if serve as sole primary.",
    ),
    "servum": _cur(
        "servant (acc.)",
        ["servant (acc.)", "slave", "servant"],
        "servus acc. — NEVER serviō serve V. Covers servumque.",
    ),
    "servi": _cur(
        "of the servant / servants",
        ["of the servant", "servants", "slaves"],
        "servus gen./nom.pl. — NEVER serviō serve V.",
    ),
    "servo": _cur(
        "to/for the servant (dat./abl.)",
        ["to the servant", "for the servant", "servant (dat./abl.)"],
        "servus dat./abl. — NEVER serviō/servō keep V as primary.",
    ),
    "servos": _cur(
        "servants (acc. pl.)",
        ["servants", "slaves (acc. pl.)"],
        "servus acc. pl. — NEVER serve V.",
    ),
    "servorum": _cur(
        "of servants (gen. pl.)",
        ["of servants", "of slaves", "servants (gen. pl.)"],
        "servus gen. pl. — NEVER serve V.",
    ),
    "servis": _cur(
        "servants (dat./abl. pl.)",
        ["servants", "to/for servants", "slaves (dat./abl. pl.)"],
        "servus dat./abl. pl. — NEVER serve V.",
    ),
    "servam": _cur(
        "maidservant (acc.)",
        ["maidservant", "female servant", "handmaid (acc.)"],
        "serva acc. — maidservant N; NEVER serviō serve V.",
    ),
    # 4) pactum → covenant (block compose)
    "pactum": _cur(
        "covenant / pact",
        ["covenant", "pact", "agreement", "treaty"],
        "Noun pactum — Biblical covenant. NEVER pangō/compōnō compose. Unshippable if compose.",
    ),
    # 5) peccatum → sin N (not sin-V peccō)
    "peccatum": _cur(
        "sin (noun)",
        ["sin", "offense", "transgression", "fault"],
        "Noun peccatum — sin N. NEVER peccō sin/err V as primary. Unshippable if verb-only.",
    ),
    "peccati": _cur(
        "of sin (gen.)",
        ["of sin", "sin (gen.)", "guilt"],
        "peccatum gen. — sin N; NEVER peccō V.",
    ),
    # 6) vox → voice N (block vocō call on declined forms)
    "vox": _cur(
        "voice",
        ["voice", "sound", "cry", "tone"],
        "Noun vox — NEVER vocō call/summon V. Unshippable if call/summon as sole primary.",
    ),
    "vocem": _cur(
        "voice (acc.)",
        ["voice (acc.)", "voice", "sound"],
        "vox acc. Gen.3.8+ — NEVER vocō call V. Unshippable if call/summon.",
    ),
    "voce": _cur(
        "with/by voice (abl.)",
        ["with voice", "by voice", "voice (abl.)"],
        "vox abl. — NEVER vocō call V.",
    ),
    "voci": _cur(
        "to/for the voice (dat.)",
        ["to the voice", "voice (dat.)"],
        "vox dat. — NEVER vocō call V.",
    ),
    # 7) opus → work/deed N (block operiō cover; not mere 'need' sole)
    "opus": _cur(
        "work / deed",
        ["work", "deed", "task", "labor"],
        "Noun opus — work/deed. NEVER operiō cover; prefer work over bare need. Unshippable if cover.",
    ),
    "opere": _cur(
        "by/in work (abl.)",
        ["by work", "in work", "work (abl.)", "deed"],
        "opus abl. — NEVER operiō cover. Unshippable if cover.",
    ),
    "opera": _cur(
        "works / deeds",
        ["works", "deeds", "tasks", "labors"],
        "opus nom/acc.pl. (or opera help) — prefer works/deeds N; NEVER cover V.",
    ),
    "operis": _cur(
        "of work (gen.)",
        ["of work", "of the deed", "work (gen.)"],
        "opus gen. — NEVER cover V.",
    ),
    "operi": _cur(
        "to/for work (dat.)",
        ["to work", "for the task", "work (dat.)"],
        "opus dat. — NEVER cover V.",
    ),
    "operibus": _cur(
        "works (dat./abl. pl.)",
        ["works", "deeds", "in/by works"],
        "opus dat./abl. pl. — NEVER cover V.",
    ),
    # 8) genus → kind/race N (block gener son-in-law on declined)
    "genus": _cur(
        "kind / race",
        ["kind", "race", "species", "stock", "offspring"],
        "Noun genus — kind/race/stock. Biblical Gen.1+ each after its kind. Prefer over gener son-in-law.",
    ),
    "genere": _cur(
        "of/in kind (abl.)",
        ["in kind", "of its kind", "kind (abl.)", "race"],
        "genus abl. — NEVER gener son-in-law as primary. Unshippable if son-in-law.",
    ),
    "generis": _cur(
        "of kind / race (gen.)",
        ["of kind", "of race", "of its kind", "kind (gen.)"],
        "genus gen. — NEVER gener son-in-law. Unshippable if son-in-law.",
    ),
    "generum": _cur(
        "of kinds (gen. pl.)",
        ["of kinds", "of races", "kinds (gen. pl.)"],
        "genus gen. pl. — NEVER gener son-in-law as primary.",
    ),
    # 9) boves → oxen/cattle (block bovō bellow)
    "boves": _cur(
        "oxen / cattle",
        ["oxen", "cattle", "cows", "herd"],
        "Noun bōs pl. — oxen/cattle. NEVER bovō cry/roar/bellow. Unshippable if bellow/roar.",
    ),
    # 10) ancilla → maidservant N (block ancillor V)
    "ancilla": _cur(
        "maidservant / handmaid",
        ["maidservant", "handmaid", "female slave", "maid"],
        "Noun ancilla — NEVER ancillor act-as-handmaid V. Unshippable if wait on / serve hand and foot.",
    ),
    "ancillam": _cur(
        "maidservant (acc.)",
        ["maidservant (acc.)", "handmaid", "maid"],
        "ancilla acc. Gen.16+ — NEVER ancillor V.",
    ),
    "ancillae": _cur(
        "of the maidservant / maidservants",
        ["of the maidservant", "maidservants", "handmaid (gen./dat./nom.pl.)"],
        "ancilla declined — NEVER ancillor V / adjectival-only.",
    ),
    "ancillas": _cur(
        "maidservants (acc. pl.)",
        ["maidservants", "handmaids (acc. pl.)"],
        "ancilla acc. pl. — NEVER ancillor V. Covers ancillasque.",
    ),
    # 11) vestis → garment N (block vestiō clothe)
    "vestem": _cur(
        "garment (acc.)",
        ["garment", "clothing", "robe (acc.)", "clothes"],
        "vestis acc. — NEVER vestiō clothe V. Unshippable if clothe.",
    ),
    "veste": _cur(
        "with/in a garment (abl.)",
        ["with a garment", "in clothing", "garment (abl.)"],
        "vestis abl. — NEVER vestiō clothe V.",
    ),
    "vestibus": _cur(
        "garments (dat./abl. pl.)",
        ["garments", "clothes", "in/with clothing"],
        "vestis dat./abl. pl. — NEVER vestiō clothe V.",
    ),
    "vestium": _cur(
        "of garments (gen. pl.)",
        ["of garments", "of clothes", "garments (gen. pl.)"],
        "vestis gen. pl. — NEVER vestiō clothe V.",
    ),
    # 12) pars → part N (block forbear/bear false stems)
    "pars": _cur(
        "part / portion",
        ["part", "portion", "share", "piece"],
        "Noun pars — NEVER parco forbear; NEVER pariō bear. Unshippable if forbear/bear.",
    ),
    "partem": _cur(
        "part (acc.)",
        ["part (acc.)", "portion", "share"],
        "pars acc. — NEVER pariō bear. Unshippable if bear.",
    ),
    "parte": _cur(
        "in/from a part (abl.)",
        ["in part", "from a part", "part (abl.)", "portion"],
        "pars abl. — NEVER bear/forbear.",
    ),
    "partes": _cur(
        "parts (nom./acc. pl.)",
        ["parts", "portions", "shares"],
        "pars pl. — NEVER bear/forbear.",
    ),
    "partibus": _cur(
        "parts (dat./abl. pl.)",
        ["parts", "portions", "in/from parts"],
        "pars dat./abl. pl. — NEVER bear/forbear.",
    ),
    # 13) nomen → name N (block nominō name-V on nomina)
    "nomen": _cur(
        "name",
        ["name", "title", "reputation"],
        "Noun nomen — name N. Prefer over nominō call/name V on declined. Covers nomenque.",
    ),
    "nomina": _cur(
        "names (nom./acc. pl.)",
        ["names", "name (pl.)"],
        "nomen pl. — NEVER nominō name/call V. Unshippable if call/name-V as sole primary.",
    ),
    "nominibus": _cur(
        "names (dat./abl. pl.)",
        ["names", "by names", "with names"],
        "nomen dat./abl. pl. Gen.2.20 — NEVER nominō call V.",
    ),
    # 14) porta → gate N (block portō carry)
    "porta": _cur(
        "gate",
        ["gate", "door", "entrance"],
        "Noun porta — gate. NEVER portō carry/bring. Unshippable if carry/bring.",
    ),
    "portam": _cur(
        "gate (acc.)",
        ["gate (acc.)", "gate", "door"],
        "porta acc. — NEVER portō carry. Unshippable if carry/bring.",
    ),
    "portas": _cur(
        "gates (acc. pl.)",
        ["gates", "doors (acc. pl.)"],
        "porta acc. pl. — NEVER portō carry.",
    ),
    # 15) potus → drink N (block possum be-able on potum)
    "potum": _cur(
        "drink (acc.)",
        ["drink", "a drink", "draught"],
        "Noun potus acc. — drink. NEVER possum be able/can. Unshippable if be able/can.",
    ),
    "potus": _cur(
        "drink",
        ["drink", "drinking", "draught"],
        "Noun potus — drink N. NEVER possum be able.",
    ),

    # v0.1.13 Wave 7 — high-value remaining stubs (Gen1–3 first, then by frequency)
    # + Gen.4.23 Adæ→Ada verse-context; Sella never chair (Mahomes/Scriba; Wave 6 CLEAR)

    # --- A) suus family leftovers (suum/suas already Wave 3) ---
    "suo": _cur(
        "his/her/its/their own (m./n. dat./abl.)",
        ["his own", "her own", "its own", "their own", "own (dat./abl.)"],
        "Possessive suus — Gen.1.24+ suo. Biblical pronoun/adj. Fill stub.",
    ),
    "suam": _cur(
        "his/her/its/their own (f. acc.)",
        ["his own", "her own", "its own", "their own", "own (f. acc.)"],
        "Possessive suus f.acc. — Gen.1.12+ suam. Fill stub.",
    ),
    "suae": _cur(
        "his/her/its/their own (f. gen./dat.)",
        ["his own", "her own", "its own", "their own", "own (f. gen./dat.)"],
        "Possessive suus f.gen./dat. — Gen.2.24+ suæ. Fill stub.",
    ),
    "suis": _cur(
        "his/her/their own (dat./abl. pl.)",
        ["his own", "her own", "their own", "own (dat./abl. pl.)", "to/for his own"],
        "Possessive suus pl. — Gen.4.23 uxoribus suis. Fill stub.",
    ),
    "sui": _cur(
        "his/her/its/their own / of himself",
        ["his own", "her own", "their own", "of himself", "own (gen./nom.pl.)"],
        "Possessive suus / reflexive gen. — Biblical. Fill stub.",
    ),
    "suos": _cur(
        "his/her/their own (m. acc. pl.)",
        ["his own", "her own", "their own", "own (m. acc. pl.)"],
        "Possessive suus m.acc.pl. — Fill stub.",
    ),
    "sua": _cur(
        "his/her/its/their own (f. nom. / n. pl.)",
        ["his own", "her own", "its own", "their own", "own"],
        "Possessive suus — Fill stub.",
    ),
    "suorum": _cur(
        "of his/her/their own (gen. pl.)",
        ["of his own", "of their own", "own (gen. pl.)"],
        "Possessive suus gen.pl. — Fill stub.",
    ),
    "suarum": _cur(
        "of his/her/their own (f. gen. pl.)",
        ["of his own", "of their own", "own (f. gen. pl.)"],
        "Possessive suus f.gen.pl. — Fill stub.",
    ),

    # --- B) tuus family ---
    "tuus": _cur(
        "your (sg.)",
        ["your", "thy", "yours (sg. m.)"],
        "Possessive tuus — Biblical. Fill stub.",
    ),
    "tua": _cur(
        "your (f./n.pl.)",
        ["your", "thy", "yours (f./n.pl.)"],
        "Possessive tuus — Fill stub.",
    ),
    "tuum": _cur(
        "your (m./n. acc./nom.n.)",
        ["your", "thy", "yours"],
        "Possessive tuus — Gen.3.14+ tuum. Fill stub.",
    ),
    "tui": _cur(
        "of you / your (gen./nom.pl.)",
        ["of you", "your", "thy", "yours"],
        "Possessive tuus / tū gen. — Gen.3.16+ tui. Fill stub.",
    ),
    "tuo": _cur(
        "your (m./n. dat./abl.)",
        ["your", "thy", "to/for your", "by your"],
        "Possessive tuus dat./abl. — Fill stub.",
    ),
    "tuam": _cur(
        "your (f. acc.)",
        ["your", "thy", "yours (f. acc.)"],
        "Possessive tuus f.acc. — Fill stub.",
    ),
    "tuae": _cur(
        "your (f. gen./dat.)",
        ["your", "thy", "of your", "to/for your"],
        "Possessive tuus f.gen./dat. — Gen.3.14+ tuæ. Fill stub.",
    ),
    "tuis": _cur(
        "your (dat./abl. pl.)",
        ["your", "thy", "to/for your (pl.)"],
        "Possessive tuus dat./abl.pl. — Fill stub.",
    ),
    "tuos": _cur(
        "your (m. acc. pl.)",
        ["your", "thy", "yours (m. acc. pl.)"],
        "Possessive tuus m.acc.pl. — Fill stub.",
    ),
    "tuas": _cur(
        "your (f. acc. pl.)",
        ["your", "thy", "yours (f. acc. pl.)"],
        "Possessive tuus f.acc.pl. — Fill stub.",
    ),
    "tuorum": _cur(
        "of your (gen. pl.)",
        ["of your", "of thy", "yours (gen. pl.)"],
        "Possessive tuus gen.pl. — Fill stub.",
    ),
    "tuarum": _cur(
        "of your (f. gen. pl.)",
        ["of your", "of thy", "yours (f. gen. pl.)"],
        "Possessive tuus f.gen.pl. — Fill stub.",
    ),

    # --- C) high-freq pronoun stubs ---
    "quem": _cur(
        "whom / which (m. acc.)",
        ["whom", "which", "that (m. acc.)"],
        "Relative/interrogative quī — Biblical. Fill stub.",
    ),
    "quid": _cur(
        "what? / anything",
        ["what?", "what", "anything", "something"],
        "Interrogative/indefinite quid — Biblical. Fill stub. Not quis how?.",
    ),
    "quibus": _cur(
        "to/for/by whom/which (pl.)",
        ["to whom", "by which", "whom/which (dat./abl. pl.)"],
        "Relative quī dat./abl.pl. — Fill stub.",
    ),
    "haec": _cur(
        "this / these",
        ["this", "these", "this (f./n.pl.)"],
        "Demonstrative hic/haec/hoc — Biblical. Fill stub.",
    ),
    "hae": _cur(
        "these (f. nom.)",
        ["these", "these (f.)"],
        "Demonstrative hae — Fill stub.",
    ),
    "hanc": _cur(
        "this (f. acc.)",
        ["this", "this one (f. acc.)"],
        "Demonstrative hic f.acc. — Fill stub.",
    ),
    "cui": _cur(
        "to/for whom / to which",
        ["to whom", "for whom", "to which", "whom (dat.)"],
        "Relative/interrogative quī dat. — Gen.3.2+ Cui. Fill stub.",
    ),
    "nos": _cur(
        "we / us",
        ["we", "us"],
        "Personal pronoun nōs — Fill stub.",
    ),
    "nobis": _cur(
        "to/for us",
        ["to us", "for us", "us (dat./abl.)", "by us"],
        "Personal pronoun nōs dat./abl. — Gen.3.3+. Fill stub.",
    ),
    "se": _cur(
        "himself / herself / itself / themselves",
        ["himself", "herself", "itself", "themselves", "oneself"],
        "Reflexive sē — Gen.3.7+. Fill stub.",
    ),
    "sibi": _cur(
        "to/for himself / herself / themselves",
        ["to himself", "for himself", "to herself", "to themselves"],
        "Reflexive sibi — Gen.2.18+. Fill stub.",
    ),
    "vos": _cur(
        "you (pl.)",
        ["you (pl.)", "ye"],
        "Personal pronoun vōs — Fill stub.",
    ),
    "his": _cur(
        "to/for/by these",
        ["to these", "by these", "these (dat./abl. pl.)", "with these"],
        "Demonstrative hic dat./abl.pl. — Gen.1.7+. Fill stub. Not English his.",
    ),
    "eorum": _cur(
        "of them / their",
        ["of them", "their", "of those"],
        "Gen. pl. of is/ea/id — Biblical. Fill stub.",
    ),

    # --- D) Gen1–3 / high-freq verb & noun stubs ---
    "dicens": _cur(
        "saying",
        ["saying", "speaking", "while saying"],
        "Present participle of dīcō — Gen.1.22+. Fill stub.",
    ),
    "dicentes": _cur(
        "saying (pl.)",
        ["saying", "speaking (pl.)"],
        "Present participle pl. of dīcō — Fill stub.",
    ),
    "respondit": _cur(
        "answered / replied",
        ["answered", "replied", "he/she answered"],
        "Perfect of respondeō — Gen.3.2+. Fill stub.",
    ),
    "responderunt": _cur(
        "they answered",
        ["they answered", "they replied"],
        "Perfect pl. of respondeō — Fill stub.",
    ),
    "tulit": _cur(
        "took / brought / bore",
        ["took", "brought", "bore", "carried"],
        "Perfect of ferō — Gen.2.15+. Fill stub.",
    ),
    "appellavit": _cur(
        "called / named",
        ["called", "named", "he/she called"],
        "Perfect of appellō — Gen.1.10+. Fill stub.",
    ),
    "appellavitque": _cur(
        "and (he) called / named",
        ["and called", "and named", "and he called"],
        "appellō perfect + -que — Gen.1.5+. Fill stub.",
    ),
    "viventem": _cur(
        "living (acc.)",
        ["living", "alive", "living creature (acc.)"],
        "Present participle of vīvō — Gen.1.21+. Fill stub.",
    ),
    "viventis": _cur(
        "of the living",
        ["of the living", "living (gen.)"],
        "Present participle gen. of vīvō — Fill stub.",
    ),
    "vescendum": _cur(
        "for food / to eat",
        ["for food", "to eat", "for eating"],
        "Gerund(ive) of vēscor — Gen.1.30+. Fill stub.",
    ),
    "fecerat": _cur(
        "had made / had done",
        ["had made", "had done", "he/she had made"],
        "Pluperfect of faciō — Gen.1.31+. Fill stub.",
    ),
    "operaretur": _cur(
        "might work / till",
        ["might work", "should till", "to work (subj.)"],
        "Imperfect subjunctive of operor — Gen.2.5+. Fill stub.",
    ),
    "fructu": _cur(
        "fruit (abl.)",
        ["fruit", "produce", "from the fruit"],
        "Noun fructus abl. — Gen.3.2+. Fill stub.",
    ),
    "unus": _cur(
        "one / a single",
        ["one", "a single", "alone"],
        "Numeral ūnus — Gen.1.5+. Fill stub.",
    ),
    "unum": _cur(
        "one (n./m. acc.)",
        ["one", "a single one", "one thing"],
        "Numeral ūnus — Gen.1.9+. Fill stub.",
    ),
    "duo": _cur(
        "two",
        ["two", "both"],
        "Numeral duo — Gen.1.16+. Fill stub.",
    ),
    "faciamus": _cur(
        "let us make",
        ["let us make", "let us do", "we may make"],
        "faciō 1pl present subjunctive — Gen.1.26+. Fill stub. Not face N.",
    ),
    "multiplicamini": _cur(
        "be multiplied / multiply",
        ["multiply", "be fruitful", "increase (pl. pass./mid.)"],
        "multiplicō imperative/passive — Gen.1.22+. Fill stub.",
    ),
    "crescite": _cur(
        "grow / increase",
        ["grow", "increase", "be fruitful"],
        "crēscō imperative pl. — Gen.1.22+. Fill stub.",
    ),
    "fecisti": _cur(
        "you made / you did",
        ["you made", "you did", "you have done"],
        "Perfect 2sg of faciō — Gen.3.13+. Fill stub.",
    ),
    "praecepit": _cur(
        "commanded / ordered",
        ["commanded", "ordered", "charged"],
        "Perfect of praecipiō — Gen.3.1+. Fill stub.",
    ),
    "praeceperam": _cur(
        "I had commanded",
        ["I had commanded", "I had ordered"],
        "Pluperfect of praecipiō — Gen.3.11+. Fill stub.",
    ),
    "comederes": _cur(
        "you should eat / eat (subj.)",
        ["you should eat", "you might eat", "eat (subj.)"],
        "Imperfect subjunctive of comedō — Gen.3.11+. Fill stub.",
    ),
    "comedisti": _cur(
        "you ate / have eaten",
        ["you ate", "you have eaten"],
        "Perfect 2sg of comedō — Gen.3.11+. Fill stub.",
    ),
    "adduxit": _cur(
        "brought / led to",
        ["brought", "led to", "he/she brought"],
        "Perfect of addūcō — Gen.2.19+. Fill stub.",
    ),
    "moventur": _cur(
        "move / are moved",
        ["move", "are moved", "creep"],
        "Passive/middle of moveō — Gen.1.28+. Fill stub.",
    ),
    "facientem": _cur(
        "making / bearing (acc.)",
        ["making", "bearing", "producing (acc.)"],
        "Present participle of faciō — Gen.1.11+. Fill stub.",
    ),
    "faciens": _cur(
        "making / bearing",
        ["making", "bearing", "producing"],
        "Present participle of faciō — Gen.1.11+. Fill stub.",
    ),
    "dixerunt": _cur(
        "they said",
        ["they said", "they spoke"],
        "Perfect pl. of dīcō — Fill stub.",
    ),
    "dabo": _cur(
        "I will give",
        ["I will give", "I shall give"],
        "Future 1sg of dō — Fill stub.",
    ),
    "viam": _cur(
        "way / road (acc.)",
        ["way", "road", "path", "journey"],
        "Noun via acc. — Fill stub.",
    ),
    "sumptus": _cur(
        "taken / assumed",
        ["taken", "assumed", "having been taken"],
        "Perfect participle of sūmō — Gen.3.19+. Fill stub.",
    ),
    "ferebatur": _cur(
        "was being carried / moved",
        ["was being carried", "was moving", "was borne"],
        "Imperfect passive of ferō — Gen.1.2+. Fill stub.",
    ),
    "dividat": _cur(
        "let it divide / may divide",
        ["let it divide", "may divide", "should divide"],
        "Present subjunctive of dīvidō — Gen.1.6. Fill stub.",
    ),
    "divisitque": _cur(
        "and (he) divided",
        ["and divided", "and he divided"],
        "dīvidō perfect + -que — Gen.1.7+. Fill stub.",
    ),
    "germinet": _cur(
        "let it bring forth / sprout",
        ["let it sprout", "let it bring forth", "may germinate"],
        "Present subjunctive of germinō — Gen.1.11. Fill stub.",
    ),
    "protulit": _cur(
        "brought forth / produced",
        ["brought forth", "produced", "put forth"],
        "Perfect of prōferō — Gen.1.12+. Fill stub.",
    ),
    "praeesset": _cur(
        "should be over / preside",
        ["should be over", "might preside", "to rule over (subj.)"],
        "Imperfect subjunctive of praesum — Gen.1.16. Fill stub.",
    ),
    "omnique": _cur(
        "and every / and all",
        ["and every", "and all", "and to every"],
        "omnis + -que — Gen.1.26+. Fill stub.",
    ),
    "factumque": _cur(
        "and it was done / made",
        ["and it was done", "and it was made", "and it came to pass"],
        "factum + -que — Gen.1.5+. Fill stub.",
    ),
    "lignumque": _cur(
        "and the tree / wood",
        ["and the tree", "and wood", "and timber"],
        "lignum + -que — Gen.1.12+. Fill stub.",
    ),
    "tecum": _cur(
        "with you (sg.)",
        ["with you", "with thee"],
        "tēcum = cum + tē — Fill stub.",
    ),
    "mecum": _cur(
        "with me",
        ["with me"],
        "mēcum = cum + mē — Fill stub.",
    ),
    "vobiscum": _cur(
        "with you (pl.)",
        ["with you (pl.)"],
        "vōbīscum = cum + vōbīs — Fill stub.",
    ),
    "peperit": _cur(
        "bore / gave birth",
        ["bore", "gave birth", "she bore"],
        "Perfect of pariō — Fill stub.",
    ),
    "vixit": _cur(
        "lived",
        ["lived", "he/she lived"],
        "Perfect of vīvō — Fill stub.",
    ),
    "vixitque": _cur(
        "and (he) lived",
        ["and lived", "and he lived"],
        "vīvō perfect + -que — Fill stub.",
    ),
    "abiit": _cur(
        "went away / departed",
        ["went away", "departed", "he/she went"],
        "Perfect of abeō — Fill stub.",
    ),
    "habitavit": _cur(
        "dwelt / lived",
        ["dwelt", "lived", "inhabited"],
        "Perfect of habitō — Fill stub.",
    ),
    "apparuit": _cur(
        "appeared",
        ["appeared", "he/she/it appeared"],
        "Perfect of appāreō — Fill stub.",
    ),
    "misit": _cur(
        "sent",
        ["sent", "he/she sent"],
        "Perfect of mittō — Fill stub.",
    ),
    "venerunt": _cur(
        "they came",
        ["they came", "they arrived"],
        "Perfect pl. of veniō — Fill stub.",
    ),
    "habebat": _cur(
        "had / was having",
        ["had", "was having", "possessed"],
        "Imperfect of habeō — Fill stub.",
    ),
    "vidisset": _cur(
        "had seen / would have seen",
        ["had seen", "would have seen", "saw (subj.)"],
        "Pluperfect subjunctive of videō — Fill stub.",
    ),
    "quidquam": _cur(
        "anything / something",
        ["anything", "something", "at all"],
        "Indefinite quidquam — Fill stub.",
    ),
    "conspectu": _cur(
        "sight / presence (abl.)",
        ["sight", "presence", "in the sight"],
        "Noun cōnspectus abl. — Fill stub.",
    ),
    "rursumque": _cur(
        "and again",
        ["and again", "again"],
        "rursum + -que — Fill stub.",
    ),
    "tres": _cur(
        "three",
        ["three"],
        "Numeral trēs — Fill stub.",
    ),
    "oves": _cur(
        "sheep",
        ["sheep", "ewes", "flock"],
        "Noun ovis pl. — Fill stub. Prefer sheep N.",
    ),
    "ovium": _cur(
        "of sheep",
        ["of sheep", "sheep (gen. pl.)"],
        "Noun ovis gen.pl. — Fill stub.",
    ),

    # --- E) high-freq proper-name stubs ---
    "joseph": _cur(
        "Joseph",
        ["Joseph", "Joseph (son of Jacob)", "proper name"],
        "Genesis Joseph — proper name. Fill stub.",
    ),
    "abraham": _cur(
        "Abraham",
        ["Abraham", "Abram/Abraham", "proper name"],
        "Genesis Abraham — proper name. Fill stub.",
    ),
    "isaac": _cur(
        "Isaac",
        ["Isaac", "Isaac (son of Abraham)", "proper name"],
        "Genesis Isaac — proper name. Fill stub.",
    ),
    "esau": _cur(
        "Esau",
        ["Esau", "Esau (son of Isaac)", "proper name"],
        "Genesis Esau — proper name. Fill stub.",
    ),
    "noe": _cur(
        "Noah",
        ["Noah", "Noe", "proper name"],
        "Genesis Noë — proper name Noah. Fill stub.",
    ),
    "laban": _cur(
        "Laban",
        ["Laban", "Laban (of Haran)", "proper name"],
        "Genesis Laban — proper name. Fill stub.",
    ),
    "rachel": _cur(
        "Rachel",
        ["Rachel", "Rachel (wife of Jacob)", "proper name"],
        "Genesis Rachel — proper name. Fill stub.",
    ),
    "cain": _cur(
        "Cain",
        ["Cain", "Cain (son of Adam)", "proper name"],
        "Genesis Cain — proper name. Fill stub.",
    ),
    "lamech": _cur(
        "Lamech",
        ["Lamech", "Lamech (proper name)"],
        "Genesis Lamech — proper name. Fill stub.",
    ),
    "benjamin": _cur(
        "Benjamin",
        ["Benjamin", "Benjamin (son of Jacob)", "proper name"],
        "Genesis Benjamin — proper name. Fill stub.",
    ),
    "nachor": _cur(
        "Nahor",
        ["Nahor", "Nachor", "proper name"],
        "Genesis Nachor — proper name Nahor. Fill stub.",
    ),
    "abimelech": _cur(
        "Abimelech",
        ["Abimelech", "Abimelech (king)", "proper name"],
        "Genesis Abimelech — proper name. Fill stub.",
    ),
    "sem": _cur(
        "Shem",
        ["Shem", "Sem", "proper name"],
        "Genesis Sem — proper name Shem. Fill stub.",
    ),
    "rebecca": _cur(
        "Rebekah",
        ["Rebekah", "Rebecca", "proper name"],
        "Genesis Rebecca — proper name Rebekah. Fill stub.",
    ),
    "ruben": _cur(
        "Reuben",
        ["Reuben", "Ruben", "proper name"],
        "Genesis Ruben — proper name Reuben. Fill stub.",
    ),
    "ismael": _cur(
        "Ishmael",
        ["Ishmael", "Ismael", "proper name"],
        "Genesis Ismaël — proper name Ishmael. Fill stub.",
    ),
    "henoch": _cur(
        "Enoch",
        ["Enoch", "Henoch", "proper name"],
        "Genesis Henoch — proper name Enoch. Fill stub.",
    ),
    "ephraim": _cur(
        "Ephraim",
        ["Ephraim", "Ephraim (son of Joseph)", "proper name"],
        "Genesis Ephraim — proper name. Fill stub.",
    ),
    "sichem": _cur(
        "Shechem",
        ["Shechem", "Sichem", "place / proper name"],
        "Genesis Sichem — place/person Shechem. Fill stub.",
    ),
    "bethel": _cur(
        "Bethel",
        ["Bethel", "Bethel (place)", "house of God"],
        "Genesis Bethel — place-name. Fill stub.",
    ),

    # --- F) Gen.4.23 Ada + Sella (Lamech wives); Ada verse-override target ---
    "ada": _cur(
        "Ada (Lamech's wife)",
        ["Ada", "Ada (wife of Lamech)", "Adah", "proper name"],
        "Gen.4.23 Adæ = Ada (Lamech's wife), NOT Adam genitive. Verse-context override. "
        "Elsewhere Adæ/Adae → Adam (gen.) curated:adae. Unshippable if Adam on Gen.4.23.",
    ),
    "sella": _cur(
        "Sella (Lamech's wife)",
        ["Sella", "Sella (wife of Lamech)", "Zillah", "proper name"],
        "Genesis Sella/Sellæ — Lamech's wife (Gen.4.19–23). NEVER sell-/chair/seat. Unshippable if chair.",
    ),
    "sellae": _cur(
        "Sella (gen./dat.)",
        ["Sella", "of Sella", "to Sella", "Zillah"],
        "Genesis Sellæ — Lamech's wife (Gen.4.23). NEVER sellar/chair. Unshippable if chair.",
    ),

    # v0.1.14 Wave 8 — Gen1–3 high-value stubs + cheap high-freq burn-down
    # + facies faciō verse-context; phonetics diaeresis gate cleared (Mahomes/Scriba; Wave 7 CLEAR)
    # --- A) Gen1–3 high-value stubs (ship-block list) ---
    "subjicite": _cur(
        "subject / bring under",
        ["subject", "bring under", "subjugate (imperative pl.)"],
        "Gen.1.28 subjicite — subiciō imperative. Fill stub.",
    ),
    "dominamini": _cur(
        "rule / have dominion",
        ["rule", "have dominion", "dominate (imperative pl.)"],
        "Gen.1.28 dominamini — dominor imperative. Fill stub. Not domina mistress as primary.",
    ),
    "dii": _cur(
        "gods (pl.)",
        ["gods", "gods (nom. pl.)", "deities"],
        "Gen.3.5 dii — deus nom. pl. Biblical. Fill stub. Not single Deus primary here.",
    ),
    "requievit": _cur(
        "rested",
        ["rested", "he rested", "ceased from work"],
        "Gen.2.2 requievit — requiescō perfect. Fill stub.",
    ),
    "sanctificavit": _cur(
        "sanctified / made holy",
        ["sanctified", "made holy", "consecrated"],
        "Gen.2.3 sanctificavit — sanctificō perfect. Fill stub.",
    ),
    "formavit": _cur(
        "formed",
        ["formed", "he formed", "shaped"],
        "Gen.2.7 Formavit — formō perfect. Fill stub.",
    ),
    "inspiravit": _cur(
        "inspired / blew spirit in",
        ["inspired", "blew spirit in", "inspired (spirit)"],
        "Gen.2.7 inspiravit — īnspīrō perfect. Fill stub. Primary avoids substrings 'eat'/'breath' (closedClass guard).",
    ),
    "morieris": _cur(
        "you will die",
        ["you will die", "you shall die", "morior 2sg future"],
        "Gen.2.17+ morieris — morior future. Fill stub.",
    ),
    "moriemini": _cur(
        "you will die (pl.)",
        ["you will die", "you shall die (pl.)", "morior 2pl future"],
        "Gen.3.4 moriemini — morior future pl. Fill stub.",
    ),
    "decepit": _cur(
        "deceived",
        ["deceived", "she/he deceived", "beguiled"],
        "Gen.3.13 decepit — dēcipiō perfect. Fill stub.",
    ),
    "conteret": _cur(
        "will crush / bruise",
        ["will crush", "will bruise", "will grind"],
        "Gen.3.15 conteret — conterō future. Fill stub.",
    ),
    "relinquet": _cur(
        "will leave",
        ["will leave", "will forsake", "will abandon"],
        "Gen.2.24 relinquet — relinquō future. Fill stub.",
    ),
    "adhaerebit": _cur(
        "will cling / cleave",
        ["will cling", "will cleave", "will adhere"],
        "Gen.2.24 adhærebit — adhaereō future. Fill stub.",
    ),
    "induit": _cur(
        "clothed / put on",
        ["clothed", "put on", "dressed"],
        "Gen.3.21 induit — induō perfect. Fill stub.",
    ),
    "ejecitque": _cur(
        "and cast out",
        ["and cast out", "and drove out", "ēiciō perfect + -que"],
        "Gen.3.24 Ejecitque — ēiciō perfect + -que. Fill stub.",
    ),
    "collocavit": _cur(
        "placed / stationed",
        ["placed", "stationed", "set"],
        "Gen.3.24 collocavit — collocō perfect. Fill stub.",
    ),

    # --- B) Cheap high-freq stub burn-down (names + clear verbs) ---
    "deditque": _cur(
        "and gave",
        ["and gave", "gave", "dō perfect + -que"],
        "High-freq deditque — dō perfect + -que. Fill stub.",
    ),
    "da": _cur(
        "give (imperative)",
        ["give", "grant", "dō imperative"],
        "Biblical da — dō 2sg imperative (Gen.14.21+). Fill stub. Not Dan place unless surface Dan.",
    ),
    "videns": _cur(
        "seeing",
        ["seeing", "when he/she saw", "videō present participle"],
        "videns — videō participle. Fill stub.",
    ),
    "praeceperat": _cur(
        "had commanded",
        ["had commanded", "had ordered", "praecipiō pluperfect"],
        "præceperat — praecipiō pluperfect. Fill stub.",
    ),
    "facere": _cur(
        "to make / to do",
        ["to make", "to do", "faciō infinitive"],
        "facere — faciō infinitive. Fill stub. Not face N.",
    ),
    "audisset": _cur(
        "had heard",
        ["had heard", "heard", "audiō pluperfect subjunctive"],
        "audisset — audiō pluperfect subj. Fill stub.",
    ),
    "aedificavit": _cur(
        "built",
        ["built", "he built", "aedificō perfect"],
        "ædificavit — aedificō perfect. Fill stub.",
    ),
    "multiplicabo": _cur(
        "I will multiply",
        ["I will multiply", "I will increase", "multiplicō future"],
        "Multiplicabo — multiplicō future. Fill stub.",
    ),
    "concepit": _cur(
        "conceived",
        ["conceived", "she conceived", "concipiō perfect"],
        "concepit — concipiō perfect. Fill stub.",
    ),
    "timere": _cur(
        "to fear",
        ["to fear", "to be afraid", "timeō infinitive"],
        "timere — timeō infinitive. Fill stub.",
    ),
    "adoravit": _cur(
        "worshipped / bowed down",
        ["worshipped", "bowed down", "adored"],
        "adoravit — adōrō perfect. Fill stub.",
    ),
    "nolite": _cur(
        "do not (pl.)",
        ["do not", "do not wish", "nōlō imperative pl."],
        "Nolite — nōlō imperative pl. Fill stub.",
    ),
    "flevit": _cur(
        "wept",
        ["wept", "he/she wept", "fleō perfect"],
        "flevit — fleō perfect. Fill stub.",
    ),
    "viditque": _cur(
        "and saw",
        ["and saw", "saw", "videō perfect + -que"],
        "Viditque — videō perfect + -que. Fill stub.",
    ),
    "praecepitque": _cur(
        "and commanded",
        ["and commanded", "commanded", "praecipiō perfect + -que"],
        "præcepitque — praecipiō perfect + -que. Fill stub.",
    ),
    "accepit": _cur(
        "received / took",
        ["received", "took", "accepted"],
        "accepit — accipiō perfect. Fill stub.",
    ),
    "suus": _cur(
        "his / her / its own",
        ["his own", "her own", "its own", "their own"],
        "Possessive suus nom. — Biblical. Fill stub. Align with suo/suam family.",
    ),
    # Proper names
    "mambre": _cur(
        "Mamre",
        ["Mamre", "Mambre", "place / proper name"],
        "Genesis Mambre — Mamre. Fill stub.",
    ),
    "ephron": _cur(
        "Ephron",
        ["Ephron", "Ephron the Hittite", "proper name"],
        "Genesis Ephron — proper name. Fill stub.",
    ),
    "simeon": _cur(
        "Simeon",
        ["Simeon", "Simeon (son of Jacob)", "proper name"],
        "Genesis Simeon — proper name. Fill stub.",
    ),
    "japheth": _cur(
        "Japheth",
        ["Japheth", "Japheth (son of Noah)", "proper name"],
        "Genesis Japheth — proper name. Fill stub.",
    ),
    "seir": _cur(
        "Seir",
        ["Seir", "Seir (place/people)", "proper name"],
        "Genesis Seir — place/people. Fill stub.",
    ),
    "agar": _cur(
        "Hagar",
        ["Hagar", "Agar", "proper name"],
        "Genesis Agar — Hagar. Fill stub.",
    ),
    "abrahae": _cur(
        "Abraham (gen./dat.)",
        ["of Abraham", "to Abraham", "Abraham (gen./dat.)"],
        "Genesis Abrahæ — Abraham declined. Fill stub.",
    ),
    "lia": _cur(
        "Leah",
        ["Leah", "Lia", "proper name"],
        "Genesis Lia — Leah. Fill stub.",
    ),
    "liae": _cur(
        "Leah (gen./dat.)",
        ["of Leah", "to Leah", "Leah (gen./dat.)"],
        "Genesis Liæ — Leah declined. Fill stub.",
    ),
    "abel": _cur(
        "Abel",
        ["Abel", "Abel (son of Adam)", "proper name"],
        "Genesis Abel — proper name. Fill stub.",
    ),
    "heber": _cur(
        "Eber / Heber",
        ["Eber", "Heber", "proper name"],
        "Genesis Heber — Eber. Fill stub.",
    ),
    "thare": _cur(
        "Terah",
        ["Terah", "Thare", "proper name"],
        "Genesis Thare — Terah. Fill stub.",
    ),
    "gessen": _cur(
        "Goshen",
        ["Goshen", "Gessen", "place-name"],
        "Genesis Gessen — Goshen. Fill stub.",
    ),

    # v0.1.15 Wave 9 — Gen1–3 ship-blocks (similis / ornatus / quæ|qua / Quare)
    # (Mahomes/Scriba; Wave 8 CLEAR; Hold Critic→Argus)
    "similis": _cur(
        "like / similar",
        ["like", "similar", "alike (adj.)"],
        "Gen.2.20 similis — adjective like/similar. NEVER similō imitate/copy V. Unshippable if imitate.",
    ),
    "ornatus": _cur(
        "adornment / array",
        ["adornment", "array", "ornament", "host (N)"],
        "Gen.2.1 ornatus — noun adornment/array (omnis ornatus eorum). NEVER ornō equip V. Unshippable if equip.",
    ),
    "qua": _cur(
        "which / that (rel.)",
        ["which", "that", "whom (abl./rel.)", "by which"],
        "Relative quā (Gen.3.19/3.23 de qua…). NEVER ubi-style where ADV as sole primary. Unshippable if where.",
    ),
    "quae": _cur(
        "which / that (rel.)",
        ["which", "that", "who (f./n.pl. rel.)"],
        "Relative quae/quæ (Gen1–3+). NEVER where ADV. Unshippable if where.",
    ),
    "quare": _cur(
        "why",
        ["why", "wherefore", "for what reason"],
        "Quare/quare (Gen.3.13+) — why. Prefer why over bare how/in-what-way as sole primary.",
    ),


}




# Map surface lemma_key → curated gloss key (defaults to itself if in CURATED_GLOSS_DEFS).
# Also catch declined Dominus/Deus forms that naive stemming mis-assigns.
CURATED_SURFACE_ALIASES: dict[str, str] = {
    # Dominus family → lord/master (block domina / dominor false hits)
    "dominus": "dominus",
    "domine": "domine",
    "domini": "domini",
    "domino": "domino",
    "dominum": "dominum",
    "dominos": "dominus",
    "dominis": "dominus",
    "dominorum": "dominus",
    # Deus family → God (block deut/misuse). Do NOT alias bare "de" (prep).
    "deus": "deus",
    "dei": "dei",
    "deo": "deo",
    "deum": "deum",
    "deos": "deus",
    "deis": "deus",
    "deorum": "deus",
    # esse / sum
    "sum": "sum",
    "es": "es",
    "est": "est",
    "sumus": "sumus",
    "estis": "estis",
    "sunt": "sunt",
    "eram": "eram",
    "eras": "eras",
    "erat": "erat",
    "erant": "erant",
    "fui": "fui",
    "fuit": "fuit",
    "fuerunt": "fuerunt",
    "esse": "esse",
    # ejus
    "ejus": "ejus",
    "eius": "eius",
    # v0.1.2 closed-class + life/light + -que forms
    "et": "et",
    "in": "in",
    "ad": "ad",
    "de": "de",
    "super": "super",
    "qui": "qui",
    "mei": "mei",
    "mi": "mi",
    "ubi": "ubi",
    "num": "num",
    "vita": "vita",
    "vitae": "vitae",
    "lux": "lux",
    "vocavitque": "vocavitque",
    "benedixitque": "benedixitque",
    # v0.1.3 meus-family declined forms + quis (block w:mei urinate / w:qui how?)
    "meus": "meus",
    "mea": "mea",
    "meum": "meum",
    "meae": "meae",
    "meo": "meo",
    "meam": "meam",
    "meos": "meos",
    "meas": "meas",
    "meorum": "meorum",
    "mearum": "mearum",
    "meis": "meis",
    "quis": "quis",
    # v0.1.4 illud/ille-family + manus-family (block illūdō sexual / maneō sexual overnight)
    "illud": "illud",
    "ille": "ille",
    "illa": "illa",
    "illum": "illum",
    "illam": "illam",
    "illius": "illius",
    "illi": "illi",
    "illo": "illo",
    "illis": "illis",
    "illos": "illos",
    "illas": "illas",
    "illae": "illae",
    "illorum": "illorum",
    "illarum": "illarum",
    "manus": "manus",
    "manum": "manum",
    "manu": "manu",
    "manui": "manui",
    "manibus": "manibus",
    "manuum": "manuum",
    # v0.1.5 Adam proper name (block w:adam / adamō lust)
    "adam": "adam",
    # v0.1.6 Adam genitive Adæ/Adae (block w:adar plow carefully)
    "adae": "adae",
    # v0.1.7 terra NOUN family + enclitics (block w:terr / terreō frighten)
    "terra": "terra",
    "terram": "terram",
    "terrae": "terrae",
    "terras": "terras",
    "terris": "terris",
    "terrarum": "terrarum",
    "terraque": "terra",
    "terramque": "terram",
    "terraeque": "terrae",
    "terrasque": "terras",
    "terrisque": "terris",
    "terrarumque": "terrarum",
    # v0.1.8 Wave 2 families + enclitics
    "caelum": "caelum",
    "caeli": "caeli",
    "caelo": "caelo",
    "caelos": "caelos",
    "caelis": "caelis",
    "caelorum": "caelorum",
    "caelumque": "caelum",
    "caelique": "caeli",
    "caeloque": "caelo",
    "caelosque": "caelos",
    "caelisque": "caelis",
    "caelorumque": "caelorum",
    "dies": "dies",
    "die": "die",
    "diem": "diem",
    "diei": "diei",
    "diebus": "diebus",
    "dierum": "dierum",
    "diesque": "dies",
    "dieque": "die",
    "diemque": "diem",
    "dieique": "diei",
    "diebusque": "diebus",
    "dierumque": "dierum",
    "lucem": "lucem",
    "lucis": "lucis",
    "luce": "luce",
    "luci": "luci",
    "lucemque": "lucem",
    "aqua": "aqua",
    "aquae": "aquae",
    "aquam": "aquam",
    "aquas": "aquas",
    "aquarum": "aquarum",
    "aquis": "aquis",
    "aquaque": "aqua",
    "aquaeque": "aquae",
    "aquamque": "aquam",
    "aquasque": "aquas",
    "aquarumque": "aquarum",
    "aquisque": "aquis",
    "tenebrae": "tenebrae",
    "tenebras": "tenebras",
    "tenebris": "tenebris",
    "tenebrarum": "tenebrarum",
    "tenebraeque": "tenebrae",
    "tenebrasque": "tenebras",
    "tenebrisque": "tenebris",
    "faciem": "faciem",
    "facie": "facie",
    "facies": "facies",
    "faciemque": "faciem",
    "facieque": "facie",
    "faciesque": "facies",
    "anima": "anima",
    "animam": "animam",
    "animae": "animae",
    "animas": "animas",
    "animarum": "animarum",
    "animo": "animo",
    "animis": "animis",
    "animum": "animum",
    "animaque": "anima",
    "animamque": "animam",
    "animaeque": "animae",
    "animasque": "animas",
    "imaginem": "imaginem",
    "imago": "imago",
    "imagine": "imagine",
    "imaginemque": "imaginem",
    "species": "species",
    "speciem": "speciem",
    "speciesque": "species",
    "speciemque": "speciem",
    "stella": "stella",
    "stellas": "stellas",
    "stellae": "stellae",
    "stellis": "stellis",
    "stellarum": "stellarum",
    "stellasque": "stellas",
    "stellaque": "stella",
    # v0.1.9 Wave 3 pronouns
    "tibi": "tibi",
    "ei": "ei",
    "eos": "eos",
    "eis": "eis",
    "ea": "ea",
    "eas": "eas",
    "suas": "suas",
    "suum": "suum",
    "eam": "eam",
    "hoc": "hoc",
    "vobis": "vobis",
    # v0.1.10 Wave 4 sum leftovers + enclitics
    "sit": "sit",
    "sitque": "sit",
    "erunt": "erunt",
    "eruntque": "erunt",
    "essem": "essem",
    "esses": "esses",
    "esset": "esset",
    "essent": "essent",
    "sint": "sint",
    "sim": "sim",
    "sis": "sis",
    "simus": "simus",
    "sitis": "sitis",
    "ero": "ero",
    "eroque": "ero",
    "eris": "eris",
    "erisque": "eris",
    "erit": "erit",
    "eritque": "erit",
    "erimus": "erimus",
    "erimusque": "erimus",
    "eritis": "eritis",
    "fuerit": "fuerit",
    "fuerint": "fuerint",
    "fuisset": "fuisset",
    # v0.1.11 Wave 5 proper names / false friends + enclitics
    "sara": "sara",
    "saram": "saram",
    "sarae": "sarae",
    "sarai": "sarai",
    "lot": "lot",
    "edom": "edom",
    "sex": "sex",
    "venit": "venit",
    "venitque": "venit",
    "venite": "venite",
    "veniteque": "venite",
    "adamam": "adamam",
    "adamae": "adamae",
    "bala": "bala",
    "balam": "balam",
    "balae": "balae",
    "her": "her",
    "sale": "sale",
    "salem": "salem",
    # v0.1.12 Wave 6 V-over-N mid pack prefer N + enclitics
    "domus": "domus",
    "domum": "domum",
    "domo": "domo",
    "domui": "domui",
    "domi": "domi",
    "domos": "domos",
    "domibus": "domibus",
    "domusque": "domus",
    "domumque": "domum",
    "domoque": "domo",
    "domuique": "domui",
    "domique": "domi",
    "domosque": "domos",
    "domibusque": "domibus",
    "locus": "locus",
    "locum": "locum",
    "loco": "loco",
    "loci": "loci",
    "locis": "locis",
    "locumque": "locum",
    "locoque": "loco",
    "locisque": "locis",
    "servus": "servus",
    "servum": "servum",
    "servi": "servi",
    "servo": "servo",
    "servos": "servos",
    "servorum": "servorum",
    "servis": "servis",
    "servam": "servam",
    "servumque": "servum",
    "servosque": "servos",
    "servisque": "servis",
    "pactum": "pactum",
    "pactumque": "pactum",
    "peccatum": "peccatum",
    "peccati": "peccati",
    "peccatumque": "peccatum",
    "vox": "vox",
    "vocem": "vocem",
    "voce": "voce",
    "voci": "voci",
    "vocemque": "vocem",
    "voceque": "voce",
    "opus": "opus",
    "opere": "opere",
    "opera": "opera",
    "operis": "operis",
    "operi": "operi",
    "operibus": "operibus",
    "opusque": "opus",
    "opereque": "opere",
    "operaque": "opera",
    "genus": "genus",
    "genere": "genere",
    "generis": "generis",
    "generum": "generum",
    "genusque": "genus",
    "genereque": "genere",
    "boves": "boves",
    "bovesque": "boves",
    "ancilla": "ancilla",
    "ancillam": "ancillam",
    "ancillae": "ancillae",
    "ancillas": "ancillas",
    "ancillasque": "ancillas",
    "ancillamque": "ancillam",
    "vestem": "vestem",
    "veste": "veste",
    "vestibus": "vestibus",
    "vestium": "vestium",
    "vestibusque": "vestibus",
    "pars": "pars",
    "partem": "partem",
    "parte": "parte",
    "partes": "partes",
    "partibus": "partibus",
    "partemque": "partem",
    "nomen": "nomen",
    "nomina": "nomina",
    "nominibus": "nominibus",
    "nomenque": "nomen",
    "nominaque": "nomina",
    "porta": "porta",
    "portam": "portam",
    "portas": "portas",
    "portamque": "portam",
    "portasque": "portas",
    "potum": "potum",
    "potus": "potus",
    "potumque": "potum",

    # v0.1.13 Wave 7 high-value stubs + Ada/Sella + enclitics
    "suo": "suo",
    "suam": "suam",
    "suae": "suae",
    "suis": "suis",
    "sui": "sui",
    "suos": "suos",
    "sua": "sua",
    "suorum": "suorum",
    "suarum": "suarum",
    "suoque": "suo",
    "suamque": "suam",
    "suaeque": "suae",
    "suisque": "suis",
    "suique": "sui",
    "suosque": "suos",
    "suaque": "sua",
    "tuus": "tuus",
    "tua": "tua",
    "tuum": "tuum",
    "tui": "tui",
    "tuo": "tuo",
    "tuam": "tuam",
    "tuae": "tuae",
    "tuis": "tuis",
    "tuos": "tuos",
    "tuas": "tuas",
    "tuorum": "tuorum",
    "tuarum": "tuarum",
    "tuusque": "tuus",
    "tuaque": "tua",
    "tuumque": "tuum",
    "tuique": "tui",
    "tuoque": "tuo",
    "tuamque": "tuam",
    "tuaeque": "tuae",
    "tuisque": "tuis",
    "quem": "quem",
    "quemque": "quem",
    "quid": "quid",
    "quibus": "quibus",
    "quibusque": "quibus",
    "haec": "haec",
    "hae": "hae",
    "hanc": "hanc",
    "hancque": "hanc",
    "cui": "cui",
    "nos": "nos",
    "nobis": "nobis",
    "nobisque": "nobis",
    "se": "se",
    "sese": "se",
    "sibi": "sibi",
    "vos": "vos",
    "his": "his",
    "eorum": "eorum",
    "eorumque": "eorum",
    "dicens": "dicens",
    "dicentes": "dicentes",
    "respondit": "respondit",
    "responderunt": "responderunt",
    "tulit": "tulit",
    "appellavit": "appellavit",
    "appellavitque": "appellavitque",
    "viventem": "viventem",
    "viventis": "viventis",
    "vescendum": "vescendum",
    "fecerat": "fecerat",
    "operaretur": "operaretur",
    "fructu": "fructu",
    "fructuque": "fructu",
    "unus": "unus",
    "unum": "unum",
    "duo": "duo",
    "faciamus": "faciamus",
    "multiplicamini": "multiplicamini",
    "crescite": "crescite",
    "fecisti": "fecisti",
    "praecepit": "praecepit",
    "praeceperam": "praeceperam",
    "comederes": "comederes",
    "comedisti": "comedisti",
    "adduxit": "adduxit",
    "moventur": "moventur",
    "facientem": "facientem",
    "faciens": "faciens",
    "dixerunt": "dixerunt",
    "dabo": "dabo",
    "viam": "viam",
    "viamque": "viam",
    "sumptus": "sumptus",
    "ferebatur": "ferebatur",
    "dividat": "dividat",
    "divisitque": "divisitque",
    "germinet": "germinet",
    "protulit": "protulit",
    "praeesset": "praeesset",
    "omnique": "omnique",
    "factumque": "factumque",
    "lignumque": "lignumque",
    "tecum": "tecum",
    "mecum": "mecum",
    "vobiscum": "vobiscum",
    "peperit": "peperit",
    "vixit": "vixit",
    "vixitque": "vixitque",
    "abiit": "abiit",
    "habitavit": "habitavit",
    "apparuit": "apparuit",
    "misit": "misit",
    "venerunt": "venerunt",
    "habebat": "habebat",
    "vidisset": "vidisset",
    "quidquam": "quidquam",
    "conspectu": "conspectu",
    "rursumque": "rursumque",
    "tres": "tres",
    "oves": "oves",
    "ovium": "ovium",
    "joseph": "joseph",
    "abraham": "abraham",
    "isaac": "isaac",
    "esau": "esau",
    "noe": "noe",
    "laban": "laban",
    "rachel": "rachel",
    "cain": "cain",
    "lamech": "lamech",
    "benjamin": "benjamin",
    "nachor": "nachor",
    "abimelech": "abimelech",
    "sem": "sem",
    "rebecca": "rebecca",
    "ruben": "ruben",
    "ismael": "ismael",
    "henoch": "henoch",
    "ephraim": "ephraim",
    "sichem": "sichem",
    "bethel": "bethel",
    "ada": "ada",
    "sella": "sella",
    "sellae": "sellae",

    # v0.1.14 Wave 8 Gen1–3 stubs + high-freq burn-down + facies_make
    "subjicite": "subjicite",
    "dominamini": "dominamini",
    "dii": "dii",
    "requievit": "requievit",
    "sanctificavit": "sanctificavit",
    "formavit": "formavit",
    "inspiravit": "inspiravit",
    "morieris": "morieris",
    "moriemini": "moriemini",
    "decepit": "decepit",
    "conteret": "conteret",
    "relinquet": "relinquet",
    "adhaerebit": "adhaerebit",
    "induit": "induit",
    "ejecitque": "ejecitque",
    "collocavit": "collocavit",
    "facies_make": "facies_make",
    "deditque": "deditque",
    "da": "da",
    "videns": "videns",
    "praeceperat": "praeceperat",
    "facere": "facere",
    "audisset": "audisset",
    "aedificavit": "aedificavit",
    "multiplicabo": "multiplicabo",
    "concepit": "concepit",
    "timere": "timere",
    "adoravit": "adoravit",
    "nolite": "nolite",
    "flevit": "flevit",
    "viditque": "viditque",
    "praecepitque": "praecepitque",
    "accepit": "accepit",
    "suus": "suus",
    "mambre": "mambre",
    "ephron": "ephron",
    "simeon": "simeon",
    "japheth": "japheth",
    "seir": "seir",
    "agar": "agar",
    "abrahae": "abrahae",
    "lia": "lia",
    "liae": "liae",
    "abel": "abel",
    "heber": "heber",
    "thare": "thare",
    "gessen": "gessen",

    # v0.1.15 Wave 9 Gen1–3 ship-blocks
    "similis": "similis",
    "ornatus": "ornatus",
    "qua": "qua",
    "quae": "quae",
    "quare": "quare",
}





# Verse-context curated overrides: (verse_id, lemma_key) → curated gloss key.
# Applied in build() before generic resolve_gloss (Wave 7+).
VERSE_GLOSS_OVERRIDES: dict[tuple[str, str], str] = {
    # Gen.4.23 Adæ = Ada (Lamech's wife), NOT Adam (gen.)
    ("Gen.4.23", "adae"): "ada",
    # Gen.6.14–16 / 18.29 (+ same faciō 2sg fut.) facies = you will make/do — NOT face N
    ("Gen.6.14", "facies"): "facies_make",
    ("Gen.6.15", "facies"): "facies_make",
    ("Gen.6.16", "facies"): "facies_make",
    ("Gen.18.25", "facies"): "facies_make",
    ("Gen.18.29", "facies"): "facies_make",
    ("Gen.20.13", "facies"): "facies_make",
    ("Gen.21.23", "facies"): "facies_make",
    ("Gen.47.29", "facies"): "facies_make",
}


def normalize_latin_surface(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return s


def lemma_key(s: str) -> str:
    """Lowercase lookup key: fold æ/œ, strip combining marks, drop punctuation."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("æ", "ae").replace("Æ", "ae").replace("œ", "oe").replace("Œ", "oe")
    s = s.lower()
    s = re.sub(r"[^a-z]", "", s)
    return s


def has_diaeresis(surface: str) -> bool:
    if re.search(r"[ëïöüÿËÏÖÜŸ]", surface):
        return True
    nfd = unicodedata.normalize("NFD", surface)
    return "\u0308" in nfd


def ecclesiastical_phonetic(surface: str) -> tuple[str, bool]:
    """Return (phonetic, pending). Diaeresis (Noë, Israël) skips ae/oe digraph merge."""
    pending = False
    dia = has_diaeresis(surface)

    # Build char list with diaeresis flags per base letter
    nfd = unicodedata.normalize("NFD", surface)
    letters: list[tuple[str, bool]] = []
    i = 0
    while i < len(nfd):
        ch = nfd[i]
        if unicodedata.combining(ch):
            i += 1
            continue
        if ch in "æÆ":
            letters.append(("a", False))
            letters.append(("e", False))
            i += 1
            continue
        if ch in "œŒ":
            letters.append(("o", False))
            letters.append(("e", False))
            i += 1
            continue
        base = ch.lower()
        marked = False
        j = i + 1
        while j < len(nfd) and unicodedata.combining(nfd[j]):
            if nfd[j] == "\u0308":
                marked = True
            j += 1
        if base.isalpha():
            letters.append((base, marked))
        i = j

    if not letters:
        return ("", True)

    # Diaeresis (Noë, Israël, Ismaël, …): skip ae/oe digraph merge via nxt_marked.
    # Wave 8: confirmed — emit split vowels; do NOT mark phoneticPending.
    _ = dia  # retained for clarity / future classical toggle

    out: list[str] = []
    i = 0
    while i < len(letters):
        ch, marked = letters[i]
        nxt = letters[i + 1][0] if i + 1 < len(letters) else ""
        nxt_marked = letters[i + 1][1] if i + 1 < len(letters) else False

        # ae/oe digraph → e UNLESS second vowel has diaeresis (Israël, Noë)
        if ch in ("a", "o") and nxt == "e" and not nxt_marked and not marked:
            out.append("e")
            i += 2
            continue
        if ch == "p" and nxt == "h":
            out.append("f")
            i += 2
            continue
        if ch == "t" and nxt == "h":
            out.append("t")
            i += 2
            continue
        if ch == "q" and nxt == "u":
            out.append("kw")
            i += 2
            continue
        if ch == "g" and nxt == "u" and i + 2 < len(letters) and letters[i + 2][0] in "aeiouy":
            out.append("gw")
            i += 2
            continue
        if (
            ch == "t"
            and nxt == "i"
            and i + 2 < len(letters)
            and letters[i + 2][0] in "aeiouy"
            and not (i > 0 and letters[i - 1][0] == "s")
        ):
            out.append("tsi")
            i += 2
            continue
        if ch == "c":
            out.append("ch" if nxt in FRONT else "k")
            i += 1
            continue
        if ch == "g":
            out.append("j" if nxt in FRONT else "g")
            i += 1
            continue
        if ch == "x":
            out.append("ks")
            i += 1
            continue
        if ch == "j":
            out.append("y")
            i += 1
            continue
        if ch == "v":
            out.append("v")
            i += 1
            continue
        vowel_map = {"a": "a", "e": "e", "i": "i", "o": "o", "u": "u", "y": "i"}
        if ch in vowel_map:
            out.append(vowel_map[ch])
            i += 1
            continue
        cons = {
            "b": "b", "d": "d", "f": "f", "h": "h", "k": "k", "l": "l", "m": "m",
            "n": "n", "p": "p", "r": "r", "s": "s", "t": "t", "z": "z", "w": "w",
        }
        if ch in cons:
            out.append(cons[ch])
            i += 1
            continue
        pending = True
        i += 1

    phonetic = "".join(out)
    if len(phonetic) < 1:
        pending = True
    return phonetic, pending


# --- Tokenize Latin verse ----------------------------------------------------

PUNCT_SPLIT = re.compile(r"(\s+|[.,:;!?«»\"'()\[\]—–\-]+)")


def tokenize_latin(verse_text: str) -> list[str]:
    parts = PUNCT_SPLIT.split(verse_text.strip())
    tokens = []
    for p in parts:
        if not p or p.isspace():
            continue
        if re.fullmatch(r"[.,:;!?«»\"'()\[\]—–\-]+", p):
            continue
        w = p.strip(".,:;!?«»\"'()[]—–")
        if w:
            tokens.append(normalize_latin_surface(w))
    return tokens


# --- Parse Vulgate USFX ------------------------------------------------------

def parse_vulgate_genesis(path: Path) -> dict[tuple[int, int], str]:
    text = path.read_text(encoding="utf-8")
    m = re.search(r'<book id="GEN">(.*?)</book>', text, re.S)
    if not m:
        m = re.search(r'(<c id="1"/>.*)', text, re.S)
        assert m, "GEN not found"
        body = m.group(1)
    else:
        body = m.group(1)

    verses: dict[tuple[int, int], str] = {}
    cur_c = None
    cur_v = None
    buf: list[str] = []

    def flush():
        nonlocal cur_c, cur_v, buf
        if cur_c is not None and cur_v is not None:
            t = " ".join(buf)
            t = re.sub(r"\s+", " ", t).strip()
            t = re.sub(r"<[^>]+>", "", t).strip()
            if t:
                verses[(cur_c, cur_v)] = t
        buf = []

    for m in re.finditer(r"<(c|v|ve)\b([^>]*)/?>|([^<]+)", body):
        tag, attrs, txt = m.group(1), m.group(2) or "", m.group(3)
        if tag == "c":
            flush()
            cur_c = int(re.search(r'id="(\d+)"', attrs).group(1))
            cur_v = None
        elif tag == "v":
            flush()
            cur_v = int(re.search(r'id="(\d+)"', attrs).group(1))
        elif tag == "ve":
            flush()
            cur_v = None
        elif txt:
            piece = txt.strip()
            if piece and cur_v is not None:
                buf.append(piece)
    flush()
    return verses


def parse_douay_genesis(path: Path) -> dict[tuple[int, int], str]:
    text = path.read_text(encoding="utf-8")
    verses: dict[tuple[int, int], str] = {}
    for cm in re.finditer(
        r'<CHAPTER cnumber="(\d+)">(.*?)</CHAPTER>', text, re.S
    ):
        c = int(cm.group(1))
        for vm in re.finditer(
            r'<VERS vnumber="(\d+)">(.*?)</VERS>', cm.group(2), re.S
        ):
            v = int(vm.group(1))
            t = re.sub(r"<[^>]+>", "", vm.group(2))
            t = re.sub(r"\s+", " ", t).strip()
            verses[(c, v)] = t
    return verses


def resolve_english(
    c: int, v: int, eng: dict[tuple[int, int], str]
) -> tuple[str, str, list[dict]]:
    """Return (text, source_note, gap_meta_entries). Never show fake/dummy Challoner."""
    gaps: list[dict] = []
    if (c, v) in CURATED_CHALLONER:
        gaps.append(
            {
                "vulgate": f"Gen.{c}.{v}",
                "reason": "eng-dra missing/dummy; curated Challoner PD",
                "resolution": "curated_challoner",
            }
        )
        return CURATED_CHALLONER[(c, v)], "Douay-Rheims Challoner (curated PD)", gaps

    src_cv = DOUAY_REMAP.get((c, v), (c, v))
    text = eng.get(src_cv, "")
    if src_cv != (c, v):
        gaps.append(
            {
                "vulgate": f"Gen.{c}.{v}",
                "douay": f"Gen.{src_cv[0]}.{src_cv[1]}",
                "reason": "versification remap (eng-dra drift)",
                "resolution": "remap",
            }
        )
        # Fix known eng-dra OCR slip for remapped 39.9→39.11 ("hot"→"not")
        if (c, v) == (39, 9) and "which is hot in my power" in text:
            text = text.replace("which is hot in my power", "which is not in my power")
            # Prefer curated clean form if available
            if (c, v) in CURATED_CHALLONER:
                text = CURATED_CHALLONER[(c, v)]

    if not text or text.lower().startswith("dummy"):
        gaps.append(
            {
                "vulgate": f"Gen.{c}.{v}",
                "reason": "English underlay missing or dummy — no fake Challoner shown",
                "resolution": "missing",
            }
        )
        return (
            "[English underlay missing — check versification]",
            "Douay-Rheims Challoner (eng-dra)",
            gaps,
        )
    src = (
        f"Douay-Rheims Challoner (eng-dra Gen.{src_cv[0]}.{src_cv[1]})"
        if src_cv != (c, v)
        else "Douay-Rheims Challoner (eng-dra)"
    )
    return text, src, gaps


# --- Whitaker DICTLINE index -------------------------------------------------

POS_RANK = {
    "N": 0,
    "V": 1,
    "PRON": 2,
    "ADJ": 3,
    "ADV": 4,
    "PREP": 5,
    "CONJ": 6,
    "INTERJ": 7,
    "NUM": 8,
}


def _freq_rank(flags: str) -> int:
    # Whitaker freq letter near end of flag block: A (very frequent) … F
    m = re.search(r"\b([A-F])\b(?:\s+[A-Z]){0,3}\s+[A-Za-z\[\(]", flags)
    if not m:
        return 5
    return "ABCDEF".index(m.group(1)) if m.group(1) in "ABCDEF" else 5


def load_whitaker_index(path: Path) -> dict[str, list[dict]]:
    """Index DICTLINE by stem → list of entries (Biblical POS preference at resolve)."""
    index: dict[str, list[dict]] = defaultdict(list)
    if not path.exists():
        print("WARN: DICTLINE missing — all glosses will be stubs")
        return index

    meaning_re = re.compile(r"\s[A-Z]\s[A-Z]\s[A-Z]\s[A-Z]\s[A-Z]\s+(.*)$")
    for line in path.read_text(encoding="latin-1", errors="replace").splitlines():
        if not line.strip() or line.startswith("--"):
            continue
        mpos = re.search(
            r"\s(N|V|ADJ|ADV|PREP|CONJ|INTERJ|PRON|NUM|PACK|SUPINE|TACKON|PREFIX|SUFFIX)\s+",
            line,
        )
        if not mpos:
            continue
        pos = mpos.group(1)
        stem_field = line[: mpos.start()].strip()
        stems = [lemma_key(x) for x in stem_field.split() if lemma_key(x)]
        # Gender if noun (after POS N … F/M/C/N)
        gender = None
        gm = re.search(r"\sN\s+\d+\s+\d+\s+([FMCN])\s+", line)
        if gm:
            gender = gm.group(1)
        mm = meaning_re.search(line)
        if mm:
            meaning = mm.group(1).strip()
        else:
            meaning = line[mpos.end() :].strip()
            meaning = (
                re.sub(r"^.*?([A-Za-z\[\(].*)$", r"\1", meaning)
                if re.search(r"[A-Za-z\[\(]", meaning)
                else meaning
            )
        if not meaning or len(meaning) < 2:
            continue
        primary = re.split(r"[;]", meaning)[0].strip()
        primary = re.sub(r"\s+", " ", primary)
        if len(primary) > 120:
            primary = primary[:117] + "..."
        # Prefer Christian/Biblical area flag E
        area_e = bool(re.search(r"\sE\s+[A-Z]\s+[A-Z]\s+", line[mpos.end() : mpos.end() + 40]))
        entry = {
            "primary": primary,
            "definition": meaning[:500],
            "source": "Whitaker WORDS (DICTLINE.GEN)",
            "pos": pos,
            "gender": gender,
            "freq": _freq_rank(line),
            "biblical_area": area_e,
        }
        for st in stems:
            if st:
                index[st].append(entry)
    print(f"Whitaker stems indexed: {len(index)}")
    return index


# True Biblical noun homographs only — NOT bare prep "de", not all "de*" stems.
DEUS_HOMOGRAPH_KEYS = frozenset(
    {"deus", "dei", "deo", "deum", "deos", "deis", "deorum"}
)
CLOSED_CLASS_POS = frozenset({"PREP", "CONJ", "PRON", "ADV", "INTERJ"})


def _is_dominus_homograph(surface_key: str) -> bool:
    return surface_key.startswith("domin")


def _is_deus_homograph(surface_key: str) -> bool:
    return surface_key in DEUS_HOMOGRAPH_KEYS


def pick_whitaker_entry(entries: list[dict], surface_key: str) -> dict:
    """Select DICTLINE sense.

    Policy (v0.1.2):
      - Biblical N/V preference ONLY for true homographs deus/dominus families.
      - Do NOT apply that preference to prep/conj/pron/adv (closed-class).
      - When closed-class POS exists among candidates, prefer it over N/V.
    """

    has_closed = any((e.get("pos") or "") in CLOSED_CLASS_POS for e in entries)
    homograph_nv = _is_dominus_homograph(surface_key) or _is_deus_homograph(surface_key)

    def score(e: dict) -> tuple:
        pos = e.get("pos") or ""
        gender = e.get("gender")
        prefer_m_n = 0
        if homograph_nv:
            if pos == "N" and gender == "M":
                prefer_m_n = -2
            elif pos == "N" and gender == "F":
                prefer_m_n = 3  # demote mistress/goddess
        if has_closed and not homograph_nv:
            # Prefer prep/conj/pron/adv when present; demote stray N/V
            pos_penalty = 0 if pos in CLOSED_CLASS_POS else 5
        elif homograph_nv:
            pos_penalty = POS_RANK.get(pos, 9)
        else:
            # Neutral POS — frequency / biblical area break ties
            pos_penalty = 0
        bib = 0 if e.get("biblical_area") else 1
        return (prefer_m_n, pos_penalty, e.get("freq", 5), bib, e.get("primary", ""))

    return sorted(entries, key=score)[0]


def simple_stem_candidates(key: str) -> list[str]:
    """Naive de-inflection candidates for Biblical Latin POC (Scriba to improve)."""
    cands = [key]
    for suf in (
        "orum", "arum", "ibus",
        "is", "os", "as", "am", "um", "us", "a", "o", "e", "i",
        "ae", "ei", "ui", "em", "es", "ea", "ia",
        "tur", "ntur", "mini", "mur", "tis", "mus", "nt", "t", "s",
        "re", "ri", "isse",
    ):
        if key.endswith(suf) and len(key) - len(suf) >= 3:
            cands.append(key[: -len(suf)])
            base = key[: -len(suf)]
            for add in ("us", "a", "um", "is", "o", "e", "r"):
                cands.append(base + add)
    seen = set()
    out = []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def ensure_curated_gloss(ckey: str, gloss_ids: dict) -> str:
    gid = f"curated:{ckey}"
    if gid not in gloss_ids:
        d = CURATED_GLOSS_DEFS[ckey]
        gloss_ids[gid] = {
            "id": gid,
            "primary": d["primary"],
            "senses": list(d["senses"]),
            "source": d["source"],
            "definition": d["definition"],
            "note": d["note"],
        }
    return gid


def resolve_gloss(key: str, whitaker: dict[str, list[dict]], gloss_ids: dict) -> str | None:
    """Return glossId. Curated Biblical overrides beat naive Whitaker stem hits."""
    if not key:
        return None

    # 1) Curated surface / alias (blockers + must-list)
    ckey = CURATED_SURFACE_ALIASES.get(key)
    if ckey is None and key in CURATED_GLOSS_DEFS:
        ckey = key
    if ckey is not None and ckey in CURATED_GLOSS_DEFS:
        return ensure_curated_gloss(ckey, gloss_ids)

    # 2) Whitaker with Biblical POS preference
    entry = None
    matched = None
    for cand in simple_stem_candidates(key):
        if cand in whitaker and whitaker[cand]:
            entry = pick_whitaker_entry(whitaker[cand], key)
            matched = cand
            break
    if entry is None:
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — Whitaker miss]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": "No DICTLINE stem hit for surface; Scriba to fill.",
            }
        return gid

    # Guard: if Whitaker primary is a known false friend for this surface family, demote
    FALSE_FRIEND = {
        "deus": ("misuse", "use wrongly"),
        "sum": ("highest", "take up"),
        "ejus": ("abjure",),
        "ejur": ("abjure",),
    }
    # meus-family surfaces must never resolve via w:mei (mingō) "urinate"
    MEUS_FAMILY = frozenset({
        "meus", "mea", "meum", "mei", "meae", "meo", "meam",
        "meorum", "mearum", "meis", "meos", "meas", "mi",
    })
    prim = (entry.get("primary") or "").lower()
    if key in MEUS_FAMILY and (
        matched == "mei"
        or "urinate" in prim
        or "make water" in prim
    ):
        # Prefer curated if available; else stub rather than ship mingō
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked meiō/urinate]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker mei/mingō hit ({entry.get('primary')}); meus-family only.",
            }
        return gid
    # quis must never take qui ADV "how?"
    if key == "quis" and (
        "how?" in prim or prim.startswith("how") or matched == "qui"
    ):
        if "quis" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("quis", gloss_ids)
        gid = f"stub:quis"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked qui how?]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker qui ADV how? for quis ({entry.get('primary')}).",
            }
        return gid
    # illud/ille-family must never take illūdō mock/sexual
    ILLE_FAMILY = frozenset({
        "illud", "ille", "illa", "illum", "illam", "illius", "illi", "illo",
        "illis", "illos", "illas", "illae", "illorum", "illarum",
    })
    if key in ILLE_FAMILY and (
        matched == "illud"
        or "sexual" in prim
        or "mock" in prim
        or "ridicule" in prim
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked illūdō/sexual]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker illūdō hit ({entry.get('primary')}); ille demonstrative only.",
            }
        return gid
    # manus-family must never take maneō remain / sexual overnight
    MANUS_FAMILY = frozenset({
        "manus", "manum", "manu", "manui", "manibus", "manuum",
    })
    if key in MANUS_FAMILY and (
        "remain" in prim
        or "abide" in prim
        or "spend the night" in prim
        or "sexual" in prim
        or ("hand" not in prim and matched == "man")
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked maneō/sexual overnight]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker maneō hit ({entry.get('primary')}); manus hand only.",
            }
        return gid
    # Adam proper name must never take adamō / w:adam lust
    if key == "adam" and (
        matched == "adam"
        or "lust" in prim
        or "fall in love" in prim
        or "love passionately" in prim
    ):
        if "adam" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("adam", gloss_ids)
        gid = f"stub:adam"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked adamō/lust]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker adamō/lust hit ({entry.get('primary')}); proper name Adam only.",
            }
        return gid
    # Adam genitive Adæ/Adae must never take w:adar plow carefully
    if key == "adae" and (
        matched == "adar"
        or "plow" in prim
        or "plough" in prim
    ):
        if "adae" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("adae", gloss_ids)
        gid = f"stub:adae"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked adar/plow]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker adar/plow hit ({entry.get('primary')}); Adam genitive only.",
            }
        return gid

    # Sella/Sellæ (Lamech wife) must never take sell-/chair
    if key in ("sella", "sellae") and (
        "chair" in prim
        or "seat" in prim
        or "stool" in prim
        or "saddle" in prim
        or matched in ("sell", "sellar")
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked sell/chair]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker sell/chair hit ({entry.get('primary')}); Sella proper name only.",
            }
        return gid

    # terra NOUN family must never take terreō / w:terr frighten (do NOT fold terror/terrestris/terret)
    TERRA_FAMILY = frozenset({
        "terra", "terram", "terrae", "terras", "terris", "terrarum",
        "terraque", "terramque", "terraeque", "terrasque", "terrisque", "terrarumque",
    })
    if key in TERRA_FAMILY and (
        "frighten" in prim
        or "terrify" in prim
        or "scare" in prim
        or "deter" in prim
        or (matched == "terr" and "earth" not in prim and "land" not in prim and "ground" not in prim)
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked terreō/frighten]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker terreō/w:terr hit ({entry.get('primary')}); terra earth/land only.",
            }
        return gid

    # --- v0.1.8 Wave 2 SHIP_BLOCK guards (prefer N) ---
    CAELUM_FAMILY = frozenset({
        "caelum", "caeli", "caelo", "caelos", "caelis", "caelorum",
        "caelumque", "caelique", "caeloque", "caelosque", "caelisque", "caelorumque",
    })
    if key in CAELUM_FAMILY and (
        "beer" in prim
        or matched == "caeli"
        or (matched == "cael" and "heaven" not in prim and "sky" not in prim)
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked caeli/beer]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker caeli/beer hit ({entry.get('primary')}); caelum heaven only.",
            }
        return gid
    DIES_FAMILY = frozenset({
        "dies", "die", "diem", "diei", "diebus", "dierum",
        "diesque", "dieque", "diemque", "dieique", "diebusque", "dierumque",
    })
    if key in DIES_FAMILY and (
        "quarter" in prim
        or "diesis" in prim
        or "tone" in prim
        or matched == "dies"
        or (matched == "di" and "day" not in prim)
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked diesis/quarter tone]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker diesis hit ({entry.get('primary')}); dies day only.",
            }
        return gid
    LUX_FAMILY = frozenset({
        "lux", "lucem", "lucis", "luce", "luci",
        "lucemque", "lucisque", "luceque", "lucique",
    })
    # Do NOT fold luceant/lucerent (shine V) or luctus grief
    if key in LUX_FAMILY and (
        "grove" in prim
        or "luxury" in prim
        or "sprain" in prim
        or (matched == "luc" and "light" not in prim and "day" not in prim)
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked luc grove/luxury]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker luc grove/luxury ({entry.get('primary')}); lux light only.",
            }
        return gid
    AQUA_FAMILY = frozenset({
        "aqua", "aquae", "aquam", "aquas", "aquarum", "aquis",
        "aquaque", "aquaeque", "aquamque", "aquasque", "aquarumque", "aquisque",
    })
    # Do NOT fold aquilonem (north wind)
    if key in AQUA_FAMILY and (
        "fetch" in prim
        or "bring water" in prim
        or "get/fetch" in prim
        or (matched == "aqu" and "water" not in prim and "sea" not in prim)
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked aquor/fetch-water]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker aquor fetch-water ({entry.get('primary')}); aqua water only.",
            }
        return gid
    TENEBRAE_FAMILY = frozenset({
        "tenebrae", "tenebras", "tenebris", "tenebrarum",
        "tenebraeque", "tenebrasque", "tenebrisque",
    })
    if key in TENEBRAE_FAMILY and (
        "darken" in prim
        or "make dark" in prim
        or "hold" in prim
        or "keep" in prim and "dark" not in prim
        or (matched == "tenebr" and "darkness" not in prim and "dark" not in prim)
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked tenebrō/darken]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker tenebrō/darken ({entry.get('primary')}); tenebrae darkness only.",
            }
        return gid
    FACIES_FAMILY = frozenset({
        "faciem", "facie", "facies",
        "faciemque", "facieque", "faciesque",
    })
    # Prefer N face; do NOT fold faciam/faciat/faciens/faciet (make V)
    if key in FACIES_FAMILY and (
        "make" in prim
        or "build" in prim
        or "construct" in prim
        or "create" in prim
        or "cause" in prim
        or (
            matched == "faci"
            and "face" not in prim
            and "shape" not in prim
        )
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked faciō/make]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker faciō/make ({entry.get('primary')}); facies face N only.",
            }
        return gid
    ANIMA_FAMILY = frozenset({
        "anima", "animam", "animae", "animas", "animarum", "animo", "animis", "animum",
        "animaque", "animamque", "animaeque", "animasque",
    })
    # Do NOT fold animant*/animal*/animadvert*
    if key in ANIMA_FAMILY and (
        prim.strip() == "mind"
        or prim.startswith("mind;")
        or prim.startswith("mind,")
        or (matched == "anim" and "soul" not in prim and "spirit" not in prim and "life" not in prim)
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked animus/mind]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker animus/mind ({entry.get('primary')}); anima soul/living being only.",
            }
        return gid
    if key in ("imaginem", "imago", "imagine", "imaginemque") and (
        "imagine" in prim
        or "conceive" in prim
        or "picture" in prim
        or matched == "imagin"
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key if key in CURATED_GLOSS_DEFS else "imaginem")
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked imaginor/imagine]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker imaginor ({entry.get('primary')}); imago image only.",
            }
        return gid
    if key in ("species", "speciem", "speciesque", "speciemque") and (
        "look" in prim
        or "see" in prim
        or (
            matched == "speci"
            and "kind" not in prim
            and "sight" not in prim
            and "appear" not in prim
        )
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key if key in CURATED_GLOSS_DEFS else "species")
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked speciō/look]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker speciō/look ({entry.get('primary')}); species kind only.",
            }
        return gid
    STELLA_FAMILY = frozenset({
        "stella", "stellas", "stellae", "stellis", "stellarum",
        "stellasque", "stellaque", "stellaeque", "stellisque", "stellarumque",
    })
    if key in STELLA_FAMILY and (
        "set" in prim
        or "furnish" in prim
        or "cover with stars" in prim
        or (matched == "stell" and "star" not in prim)
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        alias = CURATED_SURFACE_ALIASES.get(key)
        if alias and alias in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(alias, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked stellō/set-with-stars]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker stellō ({entry.get('primary')}); stella star only.",
            }
        return gid

    # --- v0.1.9 Wave 3 SHIP_BLOCK guards (pronouns) ---
    if key == "tibi" and (
        "flute" in prim
        or "pipe" in prim
        or matched == "tibi"
        or (matched == "tib" and "you" not in prim)
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked tibi/flute]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker tibi flute/pipe ({entry.get('primary')}); tibi to/for you only.",
            }
        return gid
    if key == "ei" and (
        "ah" in prim
        or "woe" in prim
        or "alas" in prim
        or "oh dear" in prim
        or matched == "ei"
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked ei/Ah-Woe]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker ei Ah!/Woe! ({entry.get('primary')}); ei to/for him/her only.",
            }
        return gid
    if key == "eos" and (
        "dawn" in prim
        or matched == "eos"
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked Eos/dawn]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker Eos/dawn ({entry.get('primary')}); eos them (acc.) only.",
            }
        return gid
    if key == "suas" and (
        "urge" in prim
        or "recommend" in prim
        or "advice" in prim
        or "persuade" in prim
        or matched in ("suas", "suad")
    ):
        if key in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(key, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked suas/suadeō]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker suadeō/suāsus ({entry.get('primary')}); suas his/her/their own only.",
            }
        return gid
    # Cheap pronoun stubs that were Whitaker misses — prefer curated when present
    for pkey in ("eis", "ea", "eas", "suum", "eam", "hoc", "vobis"):
        if key == pkey and pkey in CURATED_GLOSS_DEFS:
            # Always prefer curated for these surfaces even if Whitaker later gains a hit
            return ensure_curated_gloss(pkey, gloss_ids)


    # --- v0.1.10 Wave 4 SHIP_BLOCK guards (sum leftovers) ---
    if key in ("sit", "sitque") and (
        "allow" in prim
        or "permit" in prim
        or matched == "sit"
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, "sit")
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked sit/allow]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker sinō allow/permit ({entry.get('primary')}); sit let it be/may be only.",
            }
        return gid
    if key in ("erunt", "eruntque") and (
        "pluck" in prim
        or "dig" in prim
        or "root up" in prim
        or "overthrow" in prim
        or matched in ("eru", "eruo")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, "erunt")
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked erunt/eruō]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker eruō pluck/dig ({entry.get('primary')}); erunt they will be only.",
            }
        return gid
    if key in ("essem", "esses", "esset", "essent") and (
        "eat" in prim
        or "consume" in prim
        or "devour" in prim
        or "make real" in prim
        or matched in ("ess", "essent", "edo")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked ess-/eat]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker edō/essentō ({entry.get('primary')}); esse imperfect subjunctive only.",
            }
        return gid
    if key == "sint" and (
        "but if" in prim
        or matched == "sin"
    ):
        if "sint" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("sint", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked sint/but-if]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker sin but if ({entry.get('primary')}); sint they may be only.",
            }
        return gid
    if key in ("sim", "simus") and (
        "flatnosed" in prim
        or "snub" in prim
        or matched == "sim"
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked sim/flatnosed]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker sim- flatnosed ({entry.get('primary')}); sim/simus esse subjunctive only.",
            }
        return gid
    if key == "sitis" and (
        "thirst" in prim
        or matched == "sitis"
    ):
        if "sitis" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("sitis", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked sitis/thirst]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker sitis thirst ({entry.get('primary')}); sitis you (pl.) may be only.",
            }
        return gid
    if key in ("ero", "eroque") and (
        "basket" in prim
        or "reed" in prim
        or matched == "ero"
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, "ero")
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked ero/basket]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker ero basket ({entry.get('primary')}); ero I will be only.",
            }
        return gid
    if key in ("eris", "erisque") and (
        "hedgehog" in prim
        or matched == "eris"
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, "eris")
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked eris/hedgehog]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker eris hedgehog ({entry.get('primary')}); eris you will be only.",
            }
        return gid
    # Cheap sum stubs / futures — prefer curated when present
    for pkey in (
        "esset", "sis", "erit", "eritque", "erimus", "erimusque", "eritis",
        "fuerit", "fuerint", "fuisset", "eruntque", "sitque", "eroque", "erisque",
    ):
        if key == pkey and CURATED_SURFACE_ALIASES.get(pkey, pkey) in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(CURATED_SURFACE_ALIASES.get(pkey, pkey), gloss_ids)


    # --- v0.1.11 Wave 5 SHIP_BLOCK guards (proper names / false friends) ---
    if key in ("sara", "saram", "sarae", "sarai") and (
        "hoe" in prim
        or matched in ("sar", "sara")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked sara/hoe]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker sar-/hoe ({entry.get('primary')}); Sarah/Sarai proper name only.",
            }
        return gid
    if key == "lot" and (
        "wash" in prim
        or "bathe" in prim
        or matched == "lot"
    ):
        if "lot" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("lot", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked lot/wash]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker lot-/wash ({entry.get('primary')}); Lot proper name only.",
            }
        return gid
    if key == "edom" and (
        "subdue" in prim
        or "tame" in prim
        or "subjugate" in prim
        or matched == "edom"
    ):
        if "edom" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("edom", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked edom/subdue]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker edom-/subdue ({entry.get('primary')}); Edom proper name only.",
            }
        return gid
    if key == "sex" and (
        prim.strip() in ("sex", "sex;")
        or prim == "sex"
        or matched == "sex"
    ):
        # Cardinal six — never leave bare English "sex" as primary
        if "sex" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("sex", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked sex≠six]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker sex primary ({entry.get('primary')}); numeral six only.",
            }
        return gid
    if key in ("venit", "venitque", "venite", "veniteque") and (
        "sale" in prim
        or "sold" in prim
        or "venal" in prim
        or "go for sale" in prim
        or matched in ("venit", "vene")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, "venit")
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked venit/sale]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker vēnum īre / go for sale ({entry.get('primary')}); veniō come only.",
            }
        return gid
    if key in ("adamam", "adamae") and (
        "lust" in prim
        or "love" in prim
        or "enamoured" in prim
        or matched in ("adam", "adama")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked Admah/lust]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker adamō/lust ({entry.get('primary')}); Admah place-name only.",
            }
        return gid
    if key in ("bala", "balam", "balae") and (
        "bleat" in prim
        or "baa" in prim
        or matched in ("bal", "bala")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked bala/bleat]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker bal-/bleat ({entry.get('primary')}); Bala proper name only.",
            }
        return gid
    if key == "her" and (
        "stick" in prim
        or "adhere" in prim
        or "cling" in prim
        or matched == "her"
    ):
        if "her" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("her", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked her/adhere]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker haereō/her- ({entry.get('primary')}); Her proper name only.",
            }
        return gid
    if key in ("sale", "salem") and (
        "leap" in prim
        or "jump" in prim
        or matched == "sal"
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked sale/leap]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker sal-/leap ({entry.get('primary')}); Sale/Salem proper name only.",
            }
        return gid


    # --- v0.1.12 Wave 6 SHIP_BLOCK guards (V-over-N mid pack prefer N) ---
    DOMUS_FAMILY = frozenset({
        "domus", "domum", "domo", "domui", "domi", "domos", "domibus",
        "domusque", "domumque", "domoque", "domuique", "domique", "domosque", "domibusque",
    })
    # Do NOT fold Dominus/Domine/dominum (Lord) — those are curated separately
    if key in DOMUS_FAMILY and (
        "subdue" in prim
        or "tame" in prim
        or "master" in prim and "house" not in prim and "home" not in prim
        or matched in ("dom", "domu")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked domō/subdue]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker domō/subdue ({entry.get('primary')}); domus house only.",
            }
        return gid
    LOCUS_FAMILY = frozenset({
        "locus", "locum", "loco", "loci", "locis",
        "locumque", "locoque", "locisque", "locusque", "locique",
    })
    if key in LOCUS_FAMILY and (
        "put" in prim
        or "station" in prim
        or ("place" in prim and ("put" in prim or "," in (entry.get("primary") or "")))
        or matched == "loc"
        or (matched == "loco" and "place of" not in prim and "instead" not in prim and "house" not in prim)
    ):
        # Prefer curated place N whenever Whitaker chose locō V (place, put, station)
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            # Always prefer curated for these surfaces (alias path normally hits first)
            if "put" in prim or "station" in prim or matched == "loc":
                return ensure_curated_gloss(ckey, gloss_ids)
            if matched == "loco" and key in LOCUS_FAMILY:
                return ensure_curated_gloss(ckey, gloss_ids)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked locō/place-V]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker locō place-V ({entry.get('primary')}); locus place N only.",
            }
        return gid
    SERVUS_FAMILY = frozenset({
        "servus", "servum", "servi", "servo", "servos", "servorum", "servis", "servam",
        "servumque", "servosque", "servisque", "servusque", "servorumque",
    })
    if key in SERVUS_FAMILY and (
        prim.strip() in ("serve", "serve;")
        or prim.startswith("serve")
        or matched in ("serv", "servi")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked serviō/serve]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker serviō/serve ({entry.get('primary')}); servus servant N only.",
            }
        return gid
    if key in ("pactum", "pactumque") and (
        "compose" in prim
        or matched == "pact"
    ):
        if "pactum" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("pactum", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked pactum/compose]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker compose ({entry.get('primary')}); pactum covenant only.",
            }
        return gid
    PECCATUM_FAMILY = frozenset({"peccatum", "peccati", "peccatumque", "peccatique"})
    if key in PECCATUM_FAMILY and (
        matched in ("pecc", "pecca")
        or ("sin" in prim and entry.get("pos") == "V")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key if key in CURATED_GLOSS_DEFS else "peccatum")
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
    # Always force curated peccatum family when present (prefer N)
    if key in PECCATUM_FAMILY:
        ckey = CURATED_SURFACE_ALIASES.get(key, "peccatum")
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
    VOX_FAMILY = frozenset({
        "vox", "vocem", "voce", "voci",
        "vocemque", "voceque", "voxque", "vocique",
    })
    if key in VOX_FAMILY and (
        "call" in prim
        or "summon" in prim
        or matched == "voc"
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked vocō/call]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker vocō/call ({entry.get('primary')}); vox voice N only.",
            }
        return gid
    OPUS_FAMILY = frozenset({
        "opus", "opere", "opera", "operis", "operi", "operibus",
        "opusque", "opereque", "operaque", "operibusque",
    })
    if key in OPUS_FAMILY and (
        "cover" in prim
        or matched in ("oper", "operi")
        or (matched == "opus" and prim.strip() in ("need", "need;"))
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked operiō/cover]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker operiō/cover or bare need ({entry.get('primary')}); opus work N only.",
            }
        return gid
    GENUS_FAMILY = frozenset({
        "genus", "genere", "generis", "generum",
        "genusque", "genereque", "generisque", "generumque",
    })
    if key in GENUS_FAMILY and (
        "son-in-law" in prim
        or "son in law" in prim
        or matched == "gener"
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked gener/son-in-law]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker gener/son-in-law ({entry.get('primary')}); genus kind/race only.",
            }
        return gid
    if key in ("boves", "bovesque") and (
        "bellow" in prim
        or "roar" in prim
        or "cry aloud" in prim
        or matched == "bov"
    ):
        if "boves" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("boves", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked bovō/bellow]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker bovō/bellow ({entry.get('primary')}); boves oxen only.",
            }
        return gid
    ANCILLA_FAMILY = frozenset({
        "ancilla", "ancillam", "ancillae", "ancillas",
        "ancillasque", "ancillamque", "ancillaque",
    })
    if key in ANCILLA_FAMILY and (
        "wait on" in prim
        or "hand and foot" in prim
        or "act as handmaid" in prim
        or matched in ("ancill", "ancillar")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked ancillor/V]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker ancillor V ({entry.get('primary')}); ancilla maidservant N only.",
            }
        return gid
    VESTIS_FAMILY = frozenset({
        "vestem", "veste", "vestibus", "vestium", "vestis",
        "vestibusque", "vestemque", "vestique",
    })
    if key in VESTIS_FAMILY and (
        "clothe" in prim
        or matched in ("vest", "vesti")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked vestiō/clothe]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker vestiō/clothe ({entry.get('primary')}); vestis garment N only.",
            }
        return gid
    PARS_FAMILY = frozenset({
        "pars", "partem", "parte", "partes", "partibus",
        "partemque", "parteque", "partesque", "partibusque",
    })
    if key in PARS_FAMILY and (
        "forbear" in prim
        or "refrain" in prim
        or prim.strip() in ("bear", "bear;")
        or matched in ("part", "pars") and ("forbear" in prim or "bear" in prim)
        or matched == "part"
        or (matched == "pars" and "part" not in prim and "portion" not in prim)
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked pars/forbear-bear]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker forbear/bear ({entry.get('primary')}); pars part N only.",
            }
        return gid
    NOMEN_FAMILY = frozenset({
        "nomen", "nomina", "nominibus",
        "nomenque", "nominaque", "nominibusque",
    })
    if key in NOMEN_FAMILY and (
        matched == "nomin"
        or ("call" in prim and "name" in prim)
        or prim.strip().startswith("name, call")
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked nominō/name-V]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker nominō name-V ({entry.get('primary')}); nomen name N only.",
            }
        return gid
    PORTA_FAMILY = frozenset({
        "porta", "portam", "portas",
        "portamque", "portasque", "portaque",
    })
    if key in PORTA_FAMILY and (
        "carry" in prim
        or "bring" in prim
        or matched == "port"
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, key)
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked portō/carry]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker portō/carry ({entry.get('primary')}); porta gate N only.",
            }
        return gid
    if key in ("potum", "potus", "potumque") and (
        "be able" in prim
        or "can" == prim.strip()
        or prim.startswith("be able")
        or matched == "pot"
    ):
        ckey = CURATED_SURFACE_ALIASES.get(key, "potum")
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked potum/possum]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker possum/be able ({entry.get('primary')}); potus drink N only.",
            }
        return gid


    # --- v0.1.15 Wave 9 SHIP_BLOCK guards (similis / ornatus / qua|quae / quare) ---
    if key == "similis" and (
        "imitate" in prim
        or "copy" in prim
        or matched == "simil"
        or (matched == "similis" and "like" not in prim and "similar" not in prim)
    ):
        if "similis" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("similis", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked similō/imitate]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker similō/imitate ({entry.get('primary')}); similis ADJ like/similar only.",
            }
        return gid
    if key == "ornatus" and (
        "equip" in prim
        or "furnish" in prim
        or matched == "ornat"
        or (matched == "orno" and "adorn" not in prim and "ornament" not in prim and "array" not in prim)
    ):
        if "ornatus" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("ornatus", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked ornō/equip]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker ornō/equip ({entry.get('primary')}); ornatus N adornment/array only.",
            }
        return gid
    if key in ("qua", "quae") and (
        prim.strip() == "where"
        or prim.startswith("where")
        or (matched == "qua" and "which" not in prim and "that" not in prim and "who" not in prim)
    ):
        ckey = "quae" if key == "quae" else "qua"
        if ckey in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss(ckey, gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked qua/where]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker qua ADV where ({entry.get('primary')}); relative which/that only.",
            }
        return gid
    if key == "quare" and (
        ("how" in prim and "why" not in prim)
        or "in what way" in prim
        or matched == "quare" and "why" not in prim
    ):
        if "quare" in CURATED_GLOSS_DEFS:
            return ensure_curated_gloss("quare", gloss_ids)
        gid = f"stub:{key}"
        if gid not in gloss_ids:
            gloss_ids[gid] = {
                "id": gid,
                "primary": "[pending Scriba — blocked quare/how]",
                "senses": [],
                "source": "stub",
                "definition": None,
                "note": f"Blocked Whitaker quare how-only ({entry.get('primary')}); prefer why.",
            }
        return gid

    for prefix, bad_bits in FALSE_FRIEND.items():
        if key == prefix or key.startswith(prefix):
            prim_ff = (entry.get("primary") or "").lower()
            if any(b in prim_ff for b in bad_bits):
                gid = f"stub:{key}"
                if gid not in gloss_ids:
                    gloss_ids[gid] = {
                        "id": gid,
                        "primary": "[pending Scriba — false Whitaker demoted]",
                        "senses": [],
                        "source": "stub",
                        "definition": None,
                        "note": f"Demoted Whitaker hit ({entry.get('primary')}); Scriba to fill.",
                    }
                return gid

    gid = f"w:{matched}"
    if gid not in gloss_ids:
        gloss_ids[gid] = {
            "id": gid,
            "primary": entry["primary"],
            "senses": [s.strip() for s in entry["definition"].split(";") if s.strip()][:6],
            "source": entry["source"],
            "definition": entry["definition"],
            "note": f"POS-preferred ({entry.get('pos')}"
            + (f",{entry.get('gender')}" if entry.get("gender") else "")
            + ") over first DICTLINE stem.",
        }
    return gid


# --- Build pack --------------------------------------------------------------

def build():
    assert VULGATE.exists(), VULGATE
    assert DOUAY.exists(), DOUAY

    lat = parse_vulgate_genesis(VULGATE)
    eng = parse_douay_genesis(DOUAY)
    print(f"Vulgate verses: {len(lat)}; Douay verses: {len(eng)}")

    whitaker = load_whitaker_index(DICTLINE)

    gloss_ids: dict[str, dict] = {}
    verses_out = []
    chapters_map: dict[int, list[str]] = defaultdict(list)
    phonetic_pending = 0
    gloss_hits = 0
    gloss_stubs = 0
    gloss_curated = 0
    meta_gaps: list[dict] = []
    seen_gap_keys: set[str] = set()

    for (c, v) in sorted(lat.keys()):
        latin_text = lat[(c, v)]
        eng_text, eng_source, gap_bits = resolve_english(c, v, eng)
        for g in gap_bits:
            gk = g.get("vulgate", "") + "|" + g.get("resolution", "")
            if gk not in seen_gap_keys:
                seen_gap_keys.add(gk)
                meta_gaps.append(g)
        vid = f"Gen.{c}.{v}"
        words = []
        for surface in tokenize_latin(latin_text):
            key = lemma_key(surface)
            phonetic, pending = ecclesiastical_phonetic(surface)
            if pending or not phonetic:
                phonetic_pending += 1
                if not phonetic:
                    phonetic = "[pending Scriba]"
                    pending = True
            # Wave 7+: verse-context curated override (e.g. Gen.4.23 Adæ→Ada)
            vkey = VERSE_GLOSS_OVERRIDES.get((vid, key))
            if vkey:
                gid = ensure_curated_gloss(vkey, gloss_ids)
            else:
                gid = resolve_gloss(key, whitaker, gloss_ids)
            if gid and gid.startswith("stub:"):
                gloss_stubs += 1
            elif gid and gid.startswith("curated:"):
                gloss_curated += 1
                gloss_hits += 1
            else:
                gloss_hits += 1
            words.append(
                {
                    "la": surface,
                    "lemmaId": key or None,
                    "phonetic": phonetic,
                    "phoneticScheme": "ecclesiastical-italianate-v1",
                    "phoneticPending": pending or phonetic == "[pending Scriba]",
                    "glossId": gid,
                }
            )
        verses_out.append(
            {
                "id": vid,
                "book": "Gen",
                "chapter": c,
                "verse": v,
                "latin": latin_text,
                "english": {
                    "text": eng_text,
                    "source": eng_source,
                    "license": "Public Domain",
                },
                "words": words,
            }
        )
        chapters_map[c].append(vid)

    chapters = [
        {"book": "Gen", "chapter": c, "verseIds": chapters_map[c]}
        for c in sorted(chapters_map)
    ]

    pack = {
        "meta": {
            "name": "latin-learner",
            "version": PACK_VERSION,
            "generatedAt": GENERATED_AT,
            "scope": "Genesis (Clementine Vulgate)",
            "book": "Gen",
            "title": "Genesis",
            "division": "Pentateuch",
            "latin": {
                "text": "Clementine Vulgate",
                "pin": "seven1m/open-bibles lat-clementine.usfx.xml",
                "attribution": "Clementine Vulgate Project / Michael Tweedale",
                "license": "Public Domain",
            },
            "english": {
                "text": "Douay-Rheims Challoner",
                "pin": "seven1m/open-bibles eng-dra.zefania.xml",
                "license": "Public Domain",
            },
            "phonetics": {
                "scheme": "ecclesiastical-italianate-v1",
                "note": "Documented POC scheme; diaeresis (Noë/Israël/Ismaël) skips ae/oe merge (confirmed Wave 8; phoneticPending cleared). Classical toggle later. Scriba accuracy-gate required.",
            },
            "glosses": {
                "source": "Whitaker WORDS DICTLINE.GEN + curated Biblical overrides",
                "attribution": "William A. Whitaker (1936-2010); curated Genesis POC",
                "license": "Permissive — see vendor/whitaker/LICENCE.txt",
                "policy": "Possible sense(s); Gloss ≠ verse translation. Biblical N/V preference only for deus/dominus homographs; closed-class PREP/CONJ/PRON/ADV preferred otherwise; curated overrides beat Whitaker; meus-family never meiō/urinate; quis→who? not how?; illud/ille never illūdō/sexual; manus never maneō/sexual overnight; Adam never adamō/lust; Adæ/Adae never adar/plow; terra-family never terreō/frighten (earth/land only); Wave2 prefer-N: caeli never beer; dies never diesis; lucem light; aqua never fetch-water; tenebrae darkness not darken/teneō; faciem/facie/facies face (faciam stays make); anima soul not mind-only; imaginem image; species kind; stellas stars; Wave3 pronouns: tibi never flute/pipe; ei never Ah!/Woe!; eos never dawn; eis/ea/eas pronoun; suas never suadeō/urge; suum/eam/hoc/vobis pronoun; Wave4 sum leftovers: sit never allow/permit; erunt never pluck/dig; essem/esses/esset/essent never eat/make-real; sint never but if; sim/simus never flatnosed; sitis never thirst; ero never basket; eris never hedgehog; erit/erimus/eritis/fuerit/fuerint/fuisset esse futures/perfects; Wave5: Sara/Saram/Saræ/Sarai never hoe; Lot never wash; Edom never subdue; sex→six never sex; venit/Venite never go for sale; Adamam/Adamæ→Admah place never lust; Bala/Balam/Balæ never bleat; Her never stick/adhere; Sale/Salem never leap. Wave6 prefer-N: domus never subdue; locus never place-V; servus never serve-V; pactum never compose; peccatum sin N not V; vox never call; opus work not cover; genus never son-in-law; boves never bellow; ancilla maidservant not V; vestis garment not clothe; pars never forbear/bear; nomen/nomina name N not call-V; porta gate not carry; potum drink not be-able. Wave7 stubs: suus/tuus leftovers; quem/quid/haec/cui/nos/nobis/se/sibi/vos/his/eorum; dicens/respondit/tulit/appellavit/viventem/unus/duo + Gen1–3 verbs; Joseph/Abraham/Isaac/Esau/Noe + high-freq names; Gen.4.23 Adæ→Ada (Lamech wife) verse-context (Adam gen. elsewhere); Sella/Sellæ never chair. Wave8: phoneticPending cleared (Noë/Israël diaeresis confirmed); Gen1–3 stubs subjicite/dominamini/dii/requievit/sanctificavit/formavit/inspiravit/morieris/moriemini/decepit/conteret/relinquet/adhaerebit/induit/ejecitque/collocavit; Gen.6.14–16/18.29(+18.25/20.13/21.23/47.29) facies→faciō you will make verse-context (face N elsewhere); cheap high-freq names/verbs burn-down. Wave9 Gen1–3 ship-blocks: similis→like/similar ADJ never imitate; ornatus→adornment/array N never equip; qua/quae/quæ→which/that relative never where; quare/Quare→why.",
            },
            "gaps": meta_gaps,
        },
        "chapters": chapters,
        "verses": verses_out,
        "glosses": {},
    }

    catalog = {
        "name": "latin-learner",
        "version": PACK_VERSION,
        "generatedAt": GENERATED_AT,
        "scope": "Genesis only (POC)",
        "navOrder": "Catholic canon (Genesis)",
        "latinPin": "Clementine Vulgate USFX (open-bibles)",
        "books": [
            {
                "osis": "Gen",
                "title": "Genesis",
                "division": "Pentateuch",
                "order": 0,
                "chapters": len(chapters),
                "verses": len(verses_out),
                "asset": "data/books/Gen.json",
                "assetGz": "data/books/Gen.json.gz",
            }
        ],
        "glossesAsset": "data/glosses.json",
        "glossesAssetGz": "data/glosses.json.gz",
        "totals": {
            "books": 1,
            "verses": len(verses_out),
            "glosses": len(gloss_ids),
            "glossHits": gloss_hits,
            "glossCurated": gloss_curated,
            "glossStubs": gloss_stubs,
            "phoneticPending": phonetic_pending,
            "englishGaps": len(meta_gaps),
        },
    }

    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "books").mkdir(parents=True, exist_ok=True)
    TEST_RES.mkdir(parents=True, exist_ok=True)

    def write_json_gz(path: Path, obj):
        raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        with gzip.open(str(path) + ".gz", "wb", compresslevel=9) as gz:
            gz.write(raw)

    write_json_gz(ASSETS / "books" / "Gen.json", pack)
    gloss_map = gloss_ids
    write_json_gz(ASSETS / "glosses.json", gloss_map)
    (ASSETS / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    sample_verses = [v for v in verses_out if v["chapter"] <= 3]
    # Gen.4.9: sum / Dominus / mei / num / ubi / qui; Gen.1.3: lux / et
    for extra_id in (
        "Gen.4.9", "Gen.4.14", "Gen.19.18", "Gen.10.20", "Gen.35.12",  # enclitics + Wave4 ero
        # Wave 5 proper-name / false-friend anchors
        "Gen.6.13", "Gen.10.19", "Gen.10.24", "Gen.11.3", "Gen.11.27",
        "Gen.14.2", "Gen.14.18", "Gen.16.16", "Gen.17.15", "Gen.17.17",
        "Gen.25.30", "Gen.30.7", "Gen.38.3",
        # Wave 6 V-over-N mid-pack anchors
        "Gen.4.7", "Gen.4.10", "Gen.7.1", "Gen.9.9", "Gen.9.25",
        "Gen.12.16", "Gen.16.1", "Gen.24.14", "Gen.28.17", "Gen.39.13",
        "Gen.43.34", "Gen.2.20",
        # Wave 7 stub fills + Gen.4.23 Ada verse-context
        "Gen.4.19", "Gen.4.23", "Gen.12.5", "Gen.17.5", "Gen.25.25", "Gen.37.2",
        "Gen.41.45", "Gen.29.16",
        # Wave 8 facies faciō verse-context + Gen1–3 stub anchors
        "Gen.6.14", "Gen.6.15", "Gen.6.16", "Gen.18.25", "Gen.18.29",
        "Gen.20.13", "Gen.21.23", "Gen.47.29", "Gen.40.7",
        "Gen.2.2", "Gen.2.3", "Gen.2.7", "Gen.2.17", "Gen.2.24",
        "Gen.3.4", "Gen.3.5", "Gen.3.13", "Gen.3.15", "Gen.3.21", "Gen.3.24",
        "Gen.1.28", "Gen.4.6", "Gen.35.10", "Gen.6.9",
        # Wave 9 similis/ornatus/qua/Quare anchors (mostly in ch1–3 already)
        "Gen.2.1", "Gen.44.15",
    ):
        extra = next((v for v in verses_out if v["id"] == extra_id), None)
        if extra and extra not in sample_verses:
            sample_verses.append(extra)
    sample_gloss_ids = set()
    for v in sample_verses:
        for w in v["words"]:
            if w.get("glossId"):
                sample_gloss_ids.add(w["glossId"])
    # Always ship curated defs into samples for unit-test regressions (even if unused in ch1-4).
    for ckey in CURATED_GLOSS_DEFS:
        sample_gloss_ids.add(f"curated:{ckey}")
        ensure_curated_gloss(ckey, gloss_ids)
    gloss_map = gloss_ids
    sample_pack = {
        "meta": pack["meta"],
        "chapters": [ch for ch in chapters if ch["chapter"] <= 4 or ch["chapter"] in (6, 7, 9, 10, 11, 12, 14, 16, 17, 18, 19, 20, 21, 24, 25, 28, 29, 30, 35, 37, 38, 39, 41, 43, 47)],
        "verses": sample_verses,
        "glosses": {gid: gloss_map[gid] for gid in sample_gloss_ids if gid in gloss_map},
    }
    (TEST_RES / "pack_genesis_samples.json").write_text(
        json.dumps(sample_pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    must = [
        "est", "ait", "dixit", "dixitque", "genuit", "erat", "sunt", "eum", "te",
        "mihi", "vocavit", "vidit", "fecit", "fuit", "dei", "creavit", "fiat",
        "benedixit", "posuit", "vocavitque", "benedixitque",
        "et", "in", "ad", "de", "super", "qui", "mei", "mi", "ubi", "num",
        "vita", "vitae", "lux",
        "meus", "mea", "meum", "meis", "quis",
        "illud", "ille", "manum", "manus",
        "adam", "adae",
        "terra", "terram", "terrae", "terras", "terris",
        "caeli", "caelum", "dies", "die", "diem", "diei",
        "lucem", "aqua", "aquae", "aquas",
        "tenebrae", "tenebras", "faciem", "facie", "facies",
        "anima", "animam", "imaginem", "species", "speciem", "stellas",
        "tibi", "ei", "eos", "eis", "ea", "eas", "suas", "suum", "eam", "hoc", "vobis",
        "sit", "erunt", "essem", "esses", "esset", "sint",
        "sim", "sis", "simus", "sitis", "essent",
        "ero", "eris", "erit", "erimus", "eritis",
        "fuerit", "fuerint", "fuisset",
        "sara", "saram", "sarae", "sarai", "lot", "edom", "sex",
        "venit", "venite", "adamam", "adamae",
        "bala", "balam", "balae", "her", "sale", "salem",
        "domus", "domum", "domo", "domi", "locus", "locum", "loco",
        "servus", "servum", "servi", "pactum", "peccatum", "peccati",
        "vox", "vocem", "opus", "opere", "opera", "genus", "genere", "generis",
        "boves", "ancilla", "ancillam", "ancillas",
        "vestem", "vestibus", "pars", "partem", "nomen", "nomina", "nominibus",
        "porta", "portam", "potum",
        # Wave 7
        "suo", "suam", "suae", "suis", "sui", "suos", "sua",
        "tuus", "tua", "tuum", "tui", "tuo", "tuam", "tuae", "tuis",
        "quem", "quid", "quibus", "haec", "cui", "nos", "nobis", "se", "sibi", "vos", "his", "eorum",
        "dicens", "respondit", "tulit", "appellavit", "viventem", "unus", "duo",
        "joseph", "abraham", "isaac", "esau", "noe",
        "ada", "sella", "sellae",
        # Wave 8
        "subjicite", "dominamini", "dii", "requievit", "sanctificavit",
        "formavit", "inspiravit", "morieris", "moriemini", "decepit",
        "conteret", "relinquet", "adhaerebit", "induit", "ejecitque", "collocavit",
        "facies_make",
        "deditque", "da", "videns", "praeceperat", "facere", "audisset",
        "aedificavit", "multiplicabo", "concepit", "timere", "adoravit",
        "nolite", "flevit", "viditque", "praecepitque", "accepit", "suus",
        "mambre", "ephron", "simeon", "japheth", "seir", "agar", "abrahae",
        "lia", "liae", "abel", "heber", "thare", "gessen",
        # Wave 9
        "similis", "ornatus", "qua", "quae", "quare",
    ]
    must_still_stub = []
    for m in must:
        gid_c = f"curated:{m}"
        gid_s = f"stub:{m}"
        if gid_c not in gloss_ids and gid_s in gloss_ids:
            must_still_stub.append(m)

    stats = {
        "version": PACK_VERSION,
        "chapters": len(chapters),
        "verses": len(verses_out),
        "tokens": sum(len(v["words"]) for v in verses_out),
        "glossEntries": len(gloss_ids),
        "glossHits": gloss_hits,
        "glossCurated": gloss_curated,
        "glossStubs": gloss_stubs,
        "phoneticPending": phonetic_pending,
        "missingEnglish": sum(
            1
            for v in verses_out
            if v["english"]["text"].startswith("[English underlay missing")
        ),
        "metaGaps": len(meta_gaps),
        "mustListStillStub": must_still_stub,
    }
    (ROOT / "reports" / "pack_genesis_0.1.15.json").write_text(
        json.dumps(stats, indent=2) + "\n", encoding="utf-8"
    )
    # Keep legacy filename pointer updated
    (ROOT / "reports" / "pack_genesis_0.1.0.json").write_text(
        json.dumps(stats, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(stats, indent=2))
    print("Assets written under", ASSETS)


if __name__ == "__main__":
    build()
