#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path


QUOTED_STRING_RE = re.compile(r'"([^"]+)"')
PREFIX_RE = re.compile(r"^(?:PFS|THS|THV)\s+", re.IGNORECASE)

CURRENT_DESTROYERS_TEXT = r'''
"PFS Vallum" "PFS Iratiana" "PFS Spaedar" "PFS Madra" "PFS Kasatum" "PFS Eluria" "PFS Anapondus" "PFS Aventen"
"PFS Quinculus" "PFS Veraria" "PFS Caesis" "PFS Lupirius" "PFS Indril" "PFS Canlinus" "PFS Ignacus" "PFS Seimia"
"PFS Caena" "PFS Protacius" "PFS Victolin" "PFS Cailio" "PFS Varrinus" "PFS Lacidia" "PFS Hortenso" "PFS Senria"
"PFS Velinion" "PFS Varetia" "PFS Quaril" "PFS Bellanian" "PFS Garinian" "PFS Eudonian" "PFS Caepdas" "PFS Adjunion"
"PFS Calpodonis" "PFS Regipanus" "PFS Flotion" "PFS Varilin" "PFS Septivea" "PFS Furiponia" "PFS Cicesia" "PFS Posmius"
"PFS Heriius" "PFS Potvus" "PFS Galgius" "PFS Murmus" "PFS Cnaena" "PFS Kaemus" "PFS Capiril" "PFS Vibiruns"
"PFS Dardaraka" "PFS Caeion"
'''

# Destroyer-only stylistic anchors. These shape the class identity.
ANCHOR_NAMES = [
    "Vallum", "Iratiana", "Kasatum", "Quinculus", "Lupirius", "Canlinus",
    "Ignacus", "Protacius", "Victolin", "Varrinus", "Velinion", "Bellanian",
    "Eudonian", "Calpodonis", "Regipanus", "Flotion", "Septivea", "Posmius",
    "Galgius", "Capiril", "Vibiruns", "Dardaraka", "Caeion", "Hortenso",
]

# Explicitly keep destroyers away from corvette cadence.
CORVETTE_FORBIDDEN_ROOTS = {
    "taetr", "diger", "pheir", "gell", "goth", "parth", "edess", "baetik",
    "maced", "galat", "rocam", "bostr", "thrac", "epyr", "aeph", "tiber",
    "castr", "pelag", "treb", "palav", "anap", "avent", "lacid", "vall",
    "cipr", "gyth", "taur", "hesper", "spaed", "perox", "caesis", "corvani"
}

CORVETTE_FORBIDDEN_STARTS = {
    "ta", "tae", "dig", "phe", "gel", "got", "par", "ede", "bae", "mac",
    "gal", "bos", "thr", "aep", "tib", "cas", "pel", "tre", "pal", "ana",
    "ave", "lac", "cip", "gyt", "tau", "hes", "spa"
}

# Explicitly keep destroyers away from frigate surname/cognomen cadence.
FRIGATE_FORBIDDEN_ROOTS = {
    "hav", "tor", "verr", "vict", "vaka", "arte", "pall", "kand", "chel",
    "fedo", "cast", "varr", "corv", "sept", "sare", "nyre", "deso", "hier",
    "tari", "latr", "ursi", "sidon", "spart", "partin", "vakar", "koril",
    "irvin", "param", "ravid", "quarn", "daphn"
}

# Destroyer-specific sound inventories.
# These are not reused from the corvette/frigate logic.
ONSETS = [
    ("adj", 4), ("bel", 4), ("cae", 5), ("cal", 6), ("cap", 5), ("cic", 4),
    ("cna", 2), ("dar", 5), ("eud", 4), ("flo", 4), ("fur", 5), ("gal", 6),
    ("gen", 4), ("her", 4), ("hort", 5), ("ign", 6), ("ind", 5), ("ira", 6),
    ("kas", 6), ("kae", 4), ("lup", 5), ("mad", 4), ("mur", 5), ("pos", 5),
    ("pot", 4), ("pro", 6), ("quin", 6), ("reg", 6), ("sei", 3), ("sen", 5),
    ("sep", 5), ("var", 6), ("vel", 6), ("vib", 5), ("ver", 4)
]

NUCLEI = [
    ("a", 8), ("e", 7), ("i", 7), ("o", 4), ("u", 4),
    ("ae", 3), ("ia", 4), ("io", 4), ("ei", 2), ("ua", 2)
]

MEDIALS = [
    ("b", 1), ("c", 1), ("ct", 4), ("d", 2), ("dr", 4), ("dur", 2),
    ("g", 1), ("gin", 4), ("l", 2), ("lg", 3), ("lin", 7), ("lio", 3),
    ("m", 1), ("mon", 5), ("mur", 3), ("n", 2), ("nad", 3), ("nor", 2),
    ("p", 1), ("pan", 4), ("pod", 6), ("pon", 2), ("prot", 3), ("q", 1),
    ("r", 2), ("ran", 4), ("reg", 3), ("rin", 6), ("rion", 4), ("ris", 3),
    ("s", 1), ("sen", 5), ("sept", 3), ("t", 2), ("tan", 4), ("ten", 5),
    ("ter", 4), ("tion", 3), ("ton", 4), ("tor", 4), ("tur", 3),
    ("v", 1), ("var", 5), ("ven", 4), ("vib", 3), ("vil", 4)
]

CODAS = [
    ("d", 2), ("k", 2), ("l", 5), ("m", 4), ("n", 8), ("nd", 4), ("ns", 3),
    ("r", 7), ("rn", 4), ("s", 5), ("t", 5), ("th", 2), ("x", 2), ("", 10)
]

DESTROYER_ENDINGS = [
    ("a", 2), ("ac", 2), ("ad", 2), ("al", 4), ("am", 2), ("an", 8), ("ar", 7), ("as", 5),
    ("ea", 2), ("ec", 2), ("el", 4), ("en", 8), ("er", 6), ("es", 4),
    ("ia", 4), ("ian", 4), ("ias", 2), ("ic", 3), ("id", 2), ("il", 4), ("in", 7),
    ("ine", 2), ("ion", 9), ("is", 5), ("ix", 3),
    ("on", 9), ("or", 7), ("os", 4),
    ("um", 7), ("un", 6), ("ur", 5), ("us", 7),
    ("anus", 3), ("enus", 3), ("atis", 3), ("ulus", 3), ("imus", 2)
]

# Rare destroyer softness. Present, but not dominant.
RARE_ENDINGS = [
    ("aria", 1), ("eia", 1), ("inia", 1), ("onia", 1), ("oria", 1), ("eon", 2)
]

VOWEL_MUTATIONS = {
    "a": ["a", "e", "ae"],
    "e": ["e", "i", "ae"],
    "i": ["i", "y", "e"],
    "o": ["o", "u", "io"],
    "u": ["u", "o"],
    "y": ["y", "i"],
}

INSERT_CLUSTERS = [
    "r", "t", "d", "n", "l", "v", "m", "s", "c", "p",
    "tr", "dr", "ct", "rn", "rd", "lg", "ll", "rr",
    "pod", "gin", "lin", "don", "var", "sen", "prot", "cap", "reg", "cal",
    "fur", "sep", "vib", "pos", "mur", "gal", "hort", "quin", "adj", "cae"
]

PLACEISH_ENDINGS = ("ium", "eum", "aeum", "orium", "arium")
TOO_SOFT_ENDINGS = ("ae", "oa", "ioa")
OVERLY_FRIGATEISH_ENDINGS = ("ctus", "rius", "rian", "vian", "tarian")

# Destroyer identity markers. At least one should usually be present.
IDENTITY_CLUSTERS = {
    "adj", "bell", "cae", "cal", "cap", "cic", "dar", "eud", "flo", "fur",
    "gal", "gen", "hort", "ign", "ind", "ira", "kas", "lup", "mad", "mur",
    "pos", "pot", "pro", "quin", "reg", "sei", "sen", "sep", "var", "vel",
    "vib", "pod", "gin", "lin", "tion", "mon", "ran", "rion"
}


def parse_quoted_names(text: str) -> set[str]:
    return {
        m.group(1).strip()
        for m in QUOTED_STRING_RE.finditer(text)
        if m.group(1).strip()
    }


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def mod_root() -> Path:
    return script_dir().parent


def default_blacklist_path() -> Path:
    candidates = [
        mod_root() / "common" / "name_lists" / "05_MEG_Turian.txt",
        mod_root() / "common" / "namelists" / "05_MEG_Turian.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def strip_prefix(name: str) -> str:
    return PREFIX_RE.sub("", name).strip()


def normalize(name: str) -> str:
    name = re.sub(r"[^A-Za-z]", "", name)
    if not name:
        return ""
    return name[:1].upper() + name[1:].lower()


def canonical(name: str) -> str:
    return normalize(strip_prefix(name)).lower()


def weighted_choice(rng: random.Random, pairs: list[tuple[str, int]]) -> str:
    items = [item for item, _ in pairs]
    weights = [weight for _, weight in pairs]
    return rng.choices(items, weights=weights, k=1)[0]


def vowel_groups(name: str) -> int:
    return len(re.findall(r"[aeiouy]+", name.lower()))


def parse_current_bare_names() -> set[str]:
    return {normalize(strip_prefix(x)) for x in parse_quoted_names(CURRENT_DESTROYERS_TEXT)}


def load_blacklist(path: Path | None) -> set[str]:
    names = parse_current_bare_names()

    if path is not None and path.exists():
        text = path.read_text(encoding="utf-8")
        names |= {normalize(strip_prefix(x)) for x in parse_quoted_names(text)}

    names |= {normalize(x) for x in ANCHOR_NAMES}
    return {canonical(x) for x in names if x}


def sounds_like_corvette_root(text: str) -> bool:
    lower = text.lower()

    if any(lower.startswith(x) for x in CORVETTE_FORBIDDEN_STARTS):
        return True

    if any(root in lower for root in CORVETTE_FORBIDDEN_ROOTS):
        return True

    for root in CORVETTE_FORBIDDEN_ROOTS:
        if len(lower) >= 4 and len(root) >= 4:
            if lower[:3] == root[:3] and SequenceMatcher(None, lower, root).ratio() >= 0.72:
                return True

    return False


def sounds_like_frigate_root(text: str) -> bool:
    lower = text.lower()

    if any(root in lower for root in FRIGATE_FORBIDDEN_ROOTS):
        return True

    for root in FRIGATE_FORBIDDEN_ROOTS:
        if len(lower) >= 4 and len(root) >= 4:
            if lower[:3] == root[:3] and SequenceMatcher(None, lower, root).ratio() >= 0.76:
                return True

    return False


def strip_destroyer_ending(name: str) -> str:
    name = normalize(name)
    lower = name.lower()

    endings = (
        "ation", "onian", "inian", "arian", "oria", "eia", "anus", "enus", "ulus",
        "imus", "atis", "ine", "ian", "ion", "ius", "um", "us", "on", "or",
        "ar", "is", "ix", "en", "an", "ia", "a", "e"
    )

    for suffix in endings:
        if lower.endswith(suffix) and len(name) - len(suffix) >= 4:
            return normalize(name[:-len(suffix)])

    return name


def style_seed_names() -> set[str]:
    seeds = parse_current_bare_names() | {normalize(x) for x in ANCHOR_NAMES}
    return {x for x in seeds if x}


def build_style_sources() -> list[str]:
    seeds = style_seed_names()
    derived = set()

    for name in seeds:
        derived.add(strip_destroyer_ending(name))
        if len(name) >= 6:
            derived.add(normalize(name[:-1]))
        if len(name) >= 7:
            derived.add(normalize(name[:-2]))

    all_sources = seeds | derived

    filtered = {
        x for x in all_sources
        if 4 <= len(x) <= 12
        and not sounds_like_corvette_root(x.lower())
        and not sounds_like_frigate_root(x.lower())
    }
    return sorted(filtered)


def build_fragment_pools(style_sources: list[str]) -> tuple[list[str], list[str], list[str]]:
    starts: set[str] = set()
    mids: set[str] = set()
    tails: set[str] = set()

    for source in style_sources:
        s = source.lower()
        if len(s) < 4:
            continue

        for n in (2, 3, 4, 5):
            if len(s) >= n + 1:
                frag = s[:n]
                if not sounds_like_corvette_root(frag) and not sounds_like_frigate_root(frag):
                    starts.add(frag)

        for i in range(1, max(2, len(s) - 2)):
            for n in (2, 3, 4):
                if i + n <= len(s) - 1:
                    frag = s[i:i + n]
                    if re.search(r"[aeiouy]", frag) or re.search(r"[bcdfghjklmnpqrstvwxyz]{2}", frag):
                        mids.add(frag)

        for n in (2, 3, 4):
            if len(s) >= n + 1:
                tails.add(s[-n:])

    starts |= {
        "adj", "bell", "cae", "cal", "cap", "cic", "cna", "dar", "eud", "flo", "fur",
        "gal", "gen", "her", "hort", "ign", "ind", "ira", "kas", "kae", "lup", "mad",
        "mur", "pos", "pot", "pro", "quin", "reg", "sei", "sen", "sep", "var", "vel",
        "vib", "ver"
    }

    mids |= {
        "ct", "dr", "dur", "gin", "lg", "lin", "lio", "mon", "mur", "nad", "nor",
        "pan", "pod", "pon", "prot", "ran", "reg", "rin", "rion", "ris", "sen", "sept",
        "tan", "ten", "ter", "tion", "ton", "tor", "tur", "var", "ven", "vib", "vil"
    }

    tails |= {
        "don", "dus", "gus", "lin", "mon", "nus", "pan", "pod", "ril", "rin",
        "rion", "ron", "rus", "sen", "tas", "ten", "tor", "tum", "tus", "var"
    }

    starts = {x for x in starts if re.fullmatch(r"[a-z]{2,5}", x)}
    mids = {x for x in mids if re.fullmatch(r"[a-z]{2,4}", x)}
    tails = {x for x in tails if re.fullmatch(r"[a-z]{2,4}", x)}

    return sorted(starts), sorted(mids), sorted(tails)


def destroyer_ending(rng: random.Random) -> str:
    if rng.random() < 0.08:
        return weighted_choice(rng, RARE_ENDINGS)
    return weighted_choice(rng, DESTROYER_ENDINGS)


def fix_join(left: str, right: str) -> str:
    if not left:
        return right
    if not right:
        return left

    a = left[-1].lower()
    b = right[0].lower()

    if a == b:
        right = right[1:] or "a"

    if a in "aeiouy" and b in "aeiouy":
        right = right[1:] or "n"

    return left + right


def clean_name(raw: str) -> str:
    raw = normalize(raw)
    raw = re.sub(r"(.)\1\1+", r"\1\1", raw)
    return raw


def mutate_base(base: str, rng: random.Random) -> str:
    s = base.lower()

    if len(s) >= 6 and rng.random() < 0.35:
        s = s[:-1]

    if len(s) >= 7 and rng.random() < 0.15:
        s = s[:-1]

    if rng.random() < 0.35:
        positions = [i for i, ch in enumerate(s) if ch in VOWEL_MUTATIONS]
        if positions:
            pos = rng.choice(positions)
            repl = rng.choice(VOWEL_MUTATIONS[s[pos]])
            s = s[:pos] + repl + s[pos + 1:]

    if rng.random() < 0.35:
        pos = rng.randint(1, max(1, len(s) - 1))
        s = s[:pos] + rng.choice(INSERT_CLUSTERS) + s[pos:]

    if rng.random() < 0.18 and len(s) > 6:
        pos = rng.randint(1, len(s) - 2)
        s = s[:pos] + s[pos + 1:]

    return clean_name(s)


def make_phonotactic_name(rng: random.Random) -> str:
    raw = weighted_choice(rng, ONSETS)
    raw = fix_join(raw, weighted_choice(rng, NUCLEI))
    raw = fix_join(raw, weighted_choice(rng, MEDIALS))
    raw = fix_join(raw, weighted_choice(rng, NUCLEI))

    if rng.random() < 0.65:
        raw = fix_join(raw, weighted_choice(rng, CODAS))

    raw = fix_join(raw, destroyer_ending(rng))
    return clean_name(raw)


def make_fragment_name(starts: list[str], mids: list[str], tails: list[str], rng: random.Random) -> str:
    raw = rng.choice(starts)

    mid_count = rng.choices([1, 2, 3], weights=[18, 46, 36], k=1)[0]
    for _ in range(mid_count):
        raw = fix_join(raw, rng.choice(mids))

    if rng.random() < 0.68:
        raw = fix_join(raw, rng.choice(tails))

    raw = fix_join(raw, destroyer_ending(rng))
    return clean_name(raw)


def make_operational_name(style_sources: list[str], rng: random.Random) -> str:
    base = strip_destroyer_ending(rng.choice(style_sources))

    if rng.random() < 0.55 and len(base) > 5:
        base = base[:-rng.choice([1, 1, 2])]

    if rng.random() < 0.30:
        base = fix_join(base, rng.choice(["r", "t", "d", "n", "m", "ct", "pod", "gin", "lin", "var"]))

    raw = fix_join(base, destroyer_ending(rng))
    return clean_name(raw)


def make_compound_name(style_sources: list[str], rng: random.Random) -> str:
    a = strip_destroyer_ending(rng.choice(style_sources))
    b = strip_destroyer_ending(rng.choice(style_sources))
    while b == a:
        b = strip_destroyer_ending(rng.choice(style_sources))

    a_cut = rng.randint(2, max(2, min(5, len(a) - 2)))
    b_start = rng.randint(max(1, len(b) // 2 - 1), max(2, len(b) - 2))

    raw = a[:a_cut] + b[b_start:]

    if rng.random() < 0.78:
        raw = fix_join(raw, destroyer_ending(rng))

    return clean_name(raw)


def make_mutated_name(style_sources: list[str], rng: random.Random) -> str:
    base = rng.choice(style_sources)
    raw = mutate_base(base, rng)

    if rng.random() < 0.82:
        raw = fix_join(raw, destroyer_ending(rng))

    return clean_name(raw)


def make_hybrid_command_name(style_sources: list[str], rng: random.Random) -> str:
    base = strip_destroyer_ending(rng.choice(style_sources))
    lower = base.lower()

    if len(lower) >= 6:
        left = lower[:rng.randint(2, 4)]
        mid = lower[len(lower) // 2 - 1: len(lower) // 2 + rng.choice([1, 2])]
        raw = fix_join(left, mid)
    else:
        raw = lower

    if rng.random() < 0.55:
        raw = fix_join(raw, rng.choice(["pod", "lin", "var", "mon", "gin", "ria", "nus", "tor", "ten"]))

    raw = fix_join(raw, destroyer_ending(rng))
    return clean_name(raw)


def has_destroyer_identity(name: str) -> bool:
    lower = canonical(name)
    return any(cluster in lower for cluster in IDENTITY_CLUSTERS)


def is_viable(name: str) -> bool:
    lower = name.lower()
    length = len(name)

    if not (6 <= length <= 12):
        return False

    if vowel_groups(name) < 2 or vowel_groups(name) > 5:
        return False

    if re.search(r"[aeiouy]{3}", lower):
        return False

    if re.search(r"[bcdfghjklmnpqrstvwxyz]{4}", lower):
        return False

    if re.search(r"(.)\1\1", lower):
        return False

    if any(lower.endswith(x) for x in PLACEISH_ENDINGS):
        return False

    if any(lower.endswith(x) for x in TOO_SOFT_ENDINGS):
        return False

    if any(lower.endswith(x) for x in OVERLY_FRIGATEISH_ENDINGS):
        return False

    if sounds_like_corvette_root(lower) or sounds_like_frigate_root(lower):
        return False

    if not has_destroyer_identity(lower):
        return False

    return True


def skeleton(name: str) -> str:
    s = canonical(name)
    if not s:
        return ""
    return s[:1] + re.sub(r"[aeiouy]", "", s[1:])


def too_similar(name: str, existing: set[str]) -> bool:
    key = canonical(name)
    key_skel = skeleton(name)

    for other in existing:
        if key == other:
            return True

        if len(key) >= 4 and len(other) >= 4 and key[:4] == other[:4]:
            return True

        if len(key) >= 6 and len(other) >= 6 and key[:3] == other[:3] and key[-3:] == other[-3:]:
            return True

        if key_skel and key_skel == skeleton(other):
            return True

        if abs(len(key) - len(other)) <= 1 and SequenceMatcher(None, key, other).ratio() >= 0.88:
            return True

    return False


def too_corvette_like(name: str) -> bool:
    key = canonical(name)

    if sounds_like_corvette_root(key):
        return True

    if len(key) <= 9 and key.endswith(("ac", "ec", "ex", "yx", "ax")):
        return True

    if vowel_groups(key) <= 2 and len(key) <= 8:
        return True

    return False


def too_frigate_like(name: str) -> bool:
    key = canonical(name)

    if sounds_like_frigate_root(key):
        return True

    if key.endswith(("rius", "rian", "ctus", "vian", "tarian", "arius")):
        return True

    return False


def make_candidate(
    style_sources: list[str],
    starts: list[str],
    mids: list[str],
    tails: list[str],
    rng: random.Random,
) -> str:
    mode = rng.choices(
        population=["phonotactic", "operational", "compound", "fragment", "mutated", "hybrid"],
        weights=[22, 18, 18, 18, 12, 12],
        k=1,
    )[0]

    for _ in range(700):
        if mode == "phonotactic":
            candidate = make_phonotactic_name(rng)
        elif mode == "operational":
            candidate = make_operational_name(style_sources, rng)
        elif mode == "compound":
            candidate = make_compound_name(style_sources, rng)
        elif mode == "fragment":
            candidate = make_fragment_name(starts, mids, tails, rng)
        elif mode == "mutated":
            candidate = make_mutated_name(style_sources, rng)
        else:
            candidate = make_hybrid_command_name(style_sources, rng)

        if is_viable(candidate) and not too_corvette_like(candidate) and not too_frigate_like(candidate):
            return candidate

    raise RuntimeError("Failed to generate a viable destroyer candidate.")


def generate_destroyer_names(
    count: int,
    seed: int | None = None,
    blacklist_path: Path | None = None,
    include_prefix: bool = True,
) -> list[str]:
    rng = random.Random(seed)

    blacklist = load_blacklist(blacklist_path)
    style_sources = build_style_sources()
    starts, mids, tails = build_fragment_pools(style_sources)

    results: list[str] = []
    seen_local: set[str] = set()

    attempts = 0
    max_attempts = count * 20000

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        bare = make_candidate(style_sources, starts, mids, tails, rng)
        key = canonical(bare)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(key, blacklist | seen_local):
            continue

        if too_corvette_like(key) or too_frigate_like(key):
            continue

        seen_local.add(key)
        results.append(f"PFS {bare}" if include_prefix else bare)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique Turian destroyer names after {attempts} attempts."
        )

    return results


def format_as_array(names: list[str], per_line: int = 8) -> str:
    lines = ["["]
    for i in range(0, len(names), per_line):
        chunk = names[i:i + per_line]
        lines.append("    " + " ".join(f'"{name}"' for name in chunk))
    lines.append("]")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate lore-adjacent Turian destroyer names with a distinct mid-weight military tone, "
            "using destroyer-only style material and avoiding both corvette and frigate cadence."
        )
    )
    parser.add_argument("--count", type=int, default=120, help="Number of names to generate. Default: 120")
    parser.add_argument("--seed", type=int, default=42, help="Random seed. Default: 42")
    parser.add_argument("--per-line", type=int, default=8, help="Names per output line. Default: 8")
    parser.add_argument(
        "--blacklist-file",
        type=Path,
        default=default_blacklist_path(),
        help="Optional namelist file to blacklist existing Turian names from.",
    )
    parser.add_argument(
        "--no-prefix",
        action="store_true",
        help="Output bare names without the PFS prefix.",
    )
    args = parser.parse_args()

    names = generate_destroyer_names(
        count=args.count,
        seed=args.seed,
        blacklist_path=args.blacklist_file,
        include_prefix=not args.no_prefix,
    )
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())