#!/usr/bin/env python3
"""Build Genesis offline pack for Latin Learner POC.

Sources (see docs/SOURCES.md):
  - Clementine Vulgate USFX (seven1m/open-bibles)
  - Douay–Rheims Challoner (eng-dra zefania, open-bibles)
  - Whitaker's WORDS DICTLINE.GEN (permissive)

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

PACK_VERSION = "0.1.0-poc"
GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# --- Ecclesiastical (Italianate) phonetics ---------------------------------
# Documented scheme for POC. Classical toggle is future work.
# Scriba: please review edge cases (ti+vowel, soft g, ae/oe, proper names).

FRONT = set("eiy")


def normalize_latin_surface(s: str) -> str:
    """Preserve orthography for display; NFC + common ligatures kept as æ/œ."""
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


def ecclesiastical_phonetic(surface: str) -> tuple[str, bool]:
    """Return (phonetic, pending). pending=True → Scriba must review.

    Scheme (Italianate / Church Latin, approx.):
      ae/æ, oe/œ → e
      c before e/i/y/ae/oe → ch ; else k
      g before e/i/y/ae/oe → soft j-ish (ĝ → j) ; else g
      ti + vowel → tsi (except sti-)
      ph → f ; th → t ; ch (etym) → k when not soft-c
      v → v ; j → y ; qu → kw
      vowels roughly: a ah, e eh, i ee, o oh, u oo, y ee
    """
    raw = unicodedata.normalize("NFKD", surface)
    raw = "".join(c for c in raw if not unicodedata.combining(c))
    raw = raw.replace("æ", "ae").replace("Æ", "Ae").replace("œ", "oe").replace("Œ", "Oe")
    # Keep letters only for phonetic engine; remember if we dropped marks
    pending = bool(re.search(r"[^A-Za-zæœÆŒ\-\']", surface)) and bool(
        re.search(r"[0-9]", surface)
    )

    s = raw
    # Work lowercase for rules, preserve nothing — output lowercase syllables-ish
    s = s.lower()
    s = re.sub(r"[^a-z]", "", s)
    if not s:
        return ("", True)

    out: list[str] = []
    i = 0
    while i < len(s):
        # digraphs / multigraphs
        if s.startswith("ae", i) or s.startswith("oe", i):
            out.append("e")
            i += 2
            continue
        if s.startswith("ph", i):
            out.append("f")
            i += 2
            continue
        if s.startswith("th", i):
            out.append("t")
            i += 2
            continue
        if s.startswith("qu", i):
            out.append("kw")
            i += 2
            continue
        if s.startswith("gu", i) and i + 2 < len(s) and s[i + 2] in "aeiouy":
            out.append("gw")
            i += 2
            continue
        # ti + vowel → tsi (not after s)
        if (
            s[i] == "t"
            and i + 1 < len(s)
            and s[i + 1] == "i"
            and i + 2 < len(s)
            and s[i + 2] in "aeiouy"
            and not (i > 0 and s[i - 1] == "s")
        ):
            out.append("tsi")
            i += 2
            continue
        ch = s[i]
        nxt = s[i + 1] if i + 1 < len(s) else ""
        # soft c/g: also peek ae/oe already folded to single e above at this point
        if ch == "c":
            if nxt in FRONT:
                out.append("ch")
            else:
                out.append("k")
            i += 1
            continue
        if ch == "g":
            if nxt in FRONT:
                out.append("j")
            else:
                out.append("g")
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
        # vowels
        vowel_map = {"a": "a", "e": "e", "i": "i", "o": "o", "u": "u", "y": "i"}
        if ch in vowel_map:
            out.append(vowel_map[ch])
            i += 1
            continue
        # consonants
        cons = {
            "b": "b",
            "d": "d",
            "f": "f",
            "h": "h",
            "k": "k",
            "l": "l",
            "m": "m",
            "n": "n",
            "p": "p",
            "r": "r",
            "s": "s",
            "t": "t",
            "z": "z",
            "w": "w",
        }
        if ch in cons:
            out.append(cons[ch])
            i += 1
            continue
        pending = True
        i += 1

    phonetic = "".join(out)
    # Heuristic: very short or empty → pending
    if len(phonetic) < 1:
        pending = True
    return phonetic, pending


# --- Tokenize Latin verse ----------------------------------------------------

PUNCT_SPLIT = re.compile(r"(\s+|[.,:;!?«»\"'()\[\]—–\-]+)")


def tokenize_latin(verse_text: str) -> list[str]:
    """Split into word tokens; drop pure punctuation/whitespace."""
    parts = PUNCT_SPLIT.split(verse_text.strip())
    tokens = []
    for p in parts:
        if not p or p.isspace():
            continue
        if re.fullmatch(r"[.,:;!?«»\"'()\[\]—–\-]+", p):
            continue
        # Strip surrounding punctuation attached to words
        w = p.strip(".,:;!?«»\"'()[]—–")
        if w:
            tokens.append(normalize_latin_surface(w))
    return tokens


# --- Parse Vulgate USFX ------------------------------------------------------

def parse_vulgate_genesis(path: Path) -> dict[tuple[int, int], str]:
    text = path.read_text(encoding="utf-8")
    m = re.search(r'<book id="GEN">(.*?)</book>', text, re.S)
    if not m:
        # already extracted file may wrap differently
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
            # strip residual tags
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


# --- Whitaker DICTLINE index -------------------------------------------------

def load_whitaker_index(path: Path) -> dict[str, dict]:
    """Index DICTLINE by stem key → first gloss entry.

    DICTLINE.GEN layout (approx fixed-width):
      cols 1-76ish: stem forms (space-padded)
      then POS codes ...
      meaning starts after frequency/age codes near end.
    We take the stem (first whitespace-delimited token region) and the
    trailing gloss after the last single-letter flag cluster.
    """
    index: dict[str, dict] = {}
    if not path.exists():
        print("WARN: DICTLINE missing — all glosses will be stubs")
        return index

    # Meaning typically after age/area/geo/freq codes: pattern like " X X X A O meaning"
    meaning_re = re.compile(
        r"\s[A-Z]\s[A-Z]\s[A-Z]\s[A-Z]\s[A-Z]\s+(.*)$"
    )
    # Simpler fallback: last long alphabetic run after codes
    for line in path.read_text(encoding="latin-1", errors="replace").splitlines():
        if not line.strip() or line.startswith("--"):
            continue
        # Stem is left-padded field; take first token(s) before POS keyword
        # POS keywords appear as N/V/ADJ/ADV/PREP/CONJ/INTERJ/PRON/NUM/PACK/SUPINE/TACKON/PREFIX/SUFFIX
        mpos = re.search(
            r"\s(N|V|ADJ|ADV|PREP|CONJ|INTERJ|PRON|NUM|PACK|SUPINE|TACKON|PREFIX|SUFFIX)\s+",
            line,
        )
        if not mpos:
            continue
        stem_field = line[: mpos.start()].strip()
        stems = [lemma_key(x) for x in stem_field.split() if lemma_key(x)]
        mm = meaning_re.search(line)
        if mm:
            meaning = mm.group(1).strip()
        else:
            # take everything after POS block — heuristic: from last ' X ' cluster
            meaning = line[mpos.end() :].strip()
            meaning = re.sub(
                r"^.*?([A-Za-z\[\(].*)$", r"\1", meaning
            ) if re.search(r"[A-Za-z\[\(]", meaning) else meaning
        if not meaning or len(meaning) < 2:
            continue
        # Primary = first sense before ; or ,
        primary = re.split(r"[;]", meaning)[0].strip()
        primary = re.sub(r"\s+", " ", primary)
        if len(primary) > 120:
            primary = primary[:117] + "..."
        entry = {
            "primary": primary,
            "definition": meaning[:500],
            "source": "Whitaker WORDS (DICTLINE.GEN)",
        }
        for st in stems:
            if st and st not in index:
                index[st] = entry
    print(f"Whitaker stems indexed: {len(index)}")
    return index


def simple_stem_candidates(key: str) -> list[str]:
    """Naive de-inflection candidates for Biblical Latin POC (Scriba to improve)."""
    cands = [key]
    # common noun/adj endings
    for suf in (
        "orum", "arum", "ibus", "ibus", "orum", "arum",
        "is", "os", "as", "am", "um", "us", "a", "o", "e", "i",
        "ae", "ei", "ui", "em", "es", "ea", "ia",
        "tur", "ntur", "mini", "mur", "tis", "mus", "nt", "t", "s",
        "re", "ri", "isse", "isse",
    ):
        if key.endswith(suf) and len(key) - len(suf) >= 3:
            cands.append(key[: -len(suf)])
            # try +a / +um / +us reconstructions
            base = key[: -len(suf)]
            for add in ("us", "a", "um", "is", "o", "e", "r"):
                cands.append(base + add)
    # dedupe preserve order
    seen = set()
    out = []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def resolve_gloss(key: str, whitaker: dict[str, dict], gloss_ids: dict) -> str | None:
    """Return glossId, creating entry in gloss_ids if needed."""
    if not key:
        return None
    entry = None
    matched = None
    for cand in simple_stem_candidates(key):
        if cand in whitaker:
            entry = whitaker[cand]
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
    gid = f"w:{matched}"
    if gid not in gloss_ids:
        gloss_ids[gid] = {
            "id": gid,
            "primary": entry["primary"],
            "senses": [s.strip() for s in entry["definition"].split(";") if s.strip()][:6],
            "source": entry["source"],
            "definition": entry["definition"],
            "note": None,
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

    for (c, v) in sorted(lat.keys()):
        latin_text = lat[(c, v)]
        eng_text = eng.get((c, v), "")
        if not eng_text:
            eng_text = "[English underlay missing — check versification]"
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
                    "source": "Douay-Rheims Challoner (eng-dra)",
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
                "note": "Documented POC scheme; classical toggle later. Scriba accuracy-gate required.",
            },
            "glosses": {
                "source": "Whitaker WORDS DICTLINE.GEN",
                "attribution": "William A. Whitaker (1936-2010)",
                "license": "Permissive — see vendor/whitaker/LICENCE.txt",
            },
            "gaps": [],
        },
        "chapters": chapters,
        "verses": verses_out,
        "glosses": {},  # shared gloss catalog file
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
            "glossStubs": gloss_stubs,
            "phoneticPending": phonetic_pending,
        },
    }

    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "books").mkdir(parents=True, exist_ok=True)
    TEST_RES.mkdir(parents=True, exist_ok=True)

    def write_json_gz(path: Path, obj):
        raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        # Ship gzip only under assets (lean); PackRepository falls back if aapt2 strips .gz
        with gzip.open(str(path) + ".gz", "wb", compresslevel=9) as gz:
            gz.write(raw)

    # Pack without embedded glosses map (shared file)
    write_json_gz(ASSETS / "books" / "Gen.json", pack)
    gloss_map = gloss_ids  # already id→Gloss
    write_json_gz(ASSETS / "glosses.json", gloss_map)
    (ASSETS / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Test fixture: Gen 1–3 sample + shared glosses subset
    sample_verses = [v for v in verses_out if v["chapter"] <= 3]
    sample_gloss_ids = set()
    for v in sample_verses:
        for w in v["words"]:
            if w.get("glossId"):
                sample_gloss_ids.add(w["glossId"])
    sample_pack = {
        "meta": pack["meta"],
        "chapters": [ch for ch in chapters if ch["chapter"] <= 3],
        "verses": sample_verses,
        "glosses": {gid: gloss_map[gid] for gid in sample_gloss_ids if gid in gloss_map},
    }
    (TEST_RES / "pack_genesis_samples.json").write_text(
        json.dumps(sample_pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    stats = {
        "chapters": len(chapters),
        "verses": len(verses_out),
        "tokens": sum(len(v["words"]) for v in verses_out),
        "glossEntries": len(gloss_ids),
        "glossHits": gloss_hits,
        "glossStubs": gloss_stubs,
        "phoneticPending": phonetic_pending,
        "missingEnglish": sum(
            1
            for v in verses_out
            if v["english"]["text"].startswith("[English underlay missing")
        ),
    }
    (ROOT / "reports" / "pack_genesis_0.1.0.json").write_text(
        json.dumps(stats, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(stats, indent=2))
    print("Assets written under", ASSETS)


if __name__ == "__main__":
    build()
