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

PACK_VERSION = "0.1.5-poc"
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

    # If diaeresis present, mark pending for Scriba (non-block) while emitting split vowels.
    if dia:
        pending = True

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
                "note": "Documented POC scheme; diaeresis (Noë/Israël) skips ae/oe merge and marks pending. Classical toggle later. Scriba accuracy-gate required.",
            },
            "glosses": {
                "source": "Whitaker WORDS DICTLINE.GEN + curated Biblical overrides",
                "attribution": "William A. Whitaker (1936-2010); curated Genesis POC",
                "license": "Permissive — see vendor/whitaker/LICENCE.txt",
                "policy": "Possible sense(s); Gloss ≠ verse translation. Biblical N/V preference only for deus/dominus homographs; closed-class PREP/CONJ/PRON/ADV preferred otherwise; curated overrides beat Whitaker; meus-family never meiō/urinate; quis→who? not how?; illud/ille never illūdō/sexual; manus never maneō/sexual overnight; Adam never adamō/lust.",
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
    for extra_id in ("Gen.4.9", "Gen.19.18"):  # Gen.19.18 has "domine mi"
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
        "chapters": [ch for ch in chapters if ch["chapter"] <= 4 or ch["chapter"] == 19],
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
        "adam",
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
    (ROOT / "reports" / "pack_genesis_0.1.5.json").write_text(
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
