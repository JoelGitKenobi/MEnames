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

CURRENT_CRUISERS_TEXT = r'''
"PFS Cipritine" "PFS Gythium" "PFS Perox" "PFS Palaven" "PFS Menae" "PFS Trebia" "PFS Apparus" "PFS Corinthe"
"PFS Valerius" "PFS Hieralon" "PFS Castamon" "PFS Menaeus" "PFS Trebian" "PFS Taetrian" "PFS Digeron" "PFS Pherion"
"PFS Gellarus" "PFS Rocavian" "PFS Galatan" "PFS Epyran" "PFS Bostran" "PFS Carthene" "PFS Quadiran" "PFS Syglaris"
"PFS Nimenes" "PFS Thracion" "PFS Macedra" "PFS Baetikon" "PFS Gothanes" "PFS Parthenus" "PFS Edessor" "PFS Solian"
"PFS Hespera" "PFS Corvani" "PFS Taurena" "PFS Primoria" "PFS Turiava" "PFS Vallonis" "PFS Iratian" "PFS Spaedra"
'''

# Lore-adjacent city / colony seeds for cruiser-style toponyms.
CRUISER_CITY_SEEDS = [
    "Cipritine", "Gythium", "Perox", "Palaven", "Menae", "Trebia",
    "Taetrus", "Digeris", "Pheiros", "Gellix", "Aephus",
    "Corinthe", "Hespera", "Taurena", "Vallonis", "Spaedra",
]

# Block the other classes' core feel.
CORVETTE_FORBIDDEN_ROOTS = {
    "taetr", "diger", "pheir", "gell", "goth", "parth", "edess", "baetik",
    "maced", "galat", "rocam", "bostr", "thrac", "epyr", "aeph", "tiber",
    "castr", "pelag", "treb", "palav", "anap", "avent", "lacid", "vall",
    "cipr", "gyth", "taur", "hesper", "spaed", "perox", "caesis", "corvani"
}

FRIGATE_FORBIDDEN_ROOTS = {
    "hav", "tor", "verr", "vict", "vaka", "arte", "pall", "kand", "chel",
    "fedo", "cast", "varr", "corv", "sept", "sare", "nyre", "deso", "hier",
    "tari", "latr", "ursi", "sidon", "spart", "partin", "vakar", "koril",
    "irvin", "param", "ravid", "quarn", "daphn"
}

DESTROYER_FORBIDDEN_ROOTS = {
    "ira", "kas", "elu", "quin", "lupi", "ind", "can", "ign", "sei", "cae",
    "prot", "victol", "hort", "senr", "veli", "bellan", "garin", "eudon",
    "adjun", "calpod", "regip", "flot", "furip", "cices", "posmi", "heri",
    "potv", "galgi", "murm", "cnae", "kaem", "capir", "vibir", "dardar"
}

# Cruiser-specific phonetic inventory: broader, more monumental, more civic/toponymic.
ONSETS = [
    ("ae", 2), ("app", 3), ("bae", 4), ("car", 5), ("cip", 5), ("cor", 6),
    ("dig", 5), ("ede", 4), ("epi", 3), ("gal", 5), ("gel", 4), ("goth", 4),
    ("gyth", 5), ("hes", 5), ("hier", 4), ("ira", 3), ("mac", 5), ("men", 6),
    ("nim", 4), ("pal", 7), ("par", 5), ("per", 6), ("phe", 5), ("pri", 4),
    ("qua", 5), ("roc", 4), ("sol", 4), ("spae", 4), ("syg", 3), ("tae", 6),
    ("tau", 4), ("thr", 5), ("tre", 6), ("tur", 4), ("val", 4), ("vall", 4)
]

NUCLEI = [
    ("a", 7), ("e", 7), ("i", 5), ("o", 5), ("u", 3),
    ("ae", 5), ("ea", 3), ("ei", 2), ("eo", 2), ("ia", 5), ("ie", 2),
    ("io", 4), ("oa", 1), ("oe", 1), ("ou", 1), ("ua", 2)
]

MEDIALS = [
    ("b", 1), ("br", 2), ("c", 1), ("d", 1), ("dr", 2), ("g", 1),
    ("gl", 3), ("l", 3), ("ll", 3), ("lon", 3), ("m", 1), ("men", 4),
    ("mon", 3), ("n", 2), ("nes", 3), ("on", 4), ("ph", 3), ("r", 2),
    ("ran", 3), ("rav", 2), ("rion", 4), ("ron", 3), ("s", 1), ("ss", 2),
    ("t", 1), ("tan", 4), ("the", 3), ("then", 3), ("thi", 2), ("tion", 4),
    ("ton", 3), ("v", 1), ("van", 4), ("ven", 5), ("via", 3), ("vor", 2),
    ("x", 1), ("xor", 2), ("z", 1)
]

CODAS = [
    ("", 10), ("l", 4), ("n", 6), ("r", 5), ("s", 4), ("th", 2), ("x", 2)
]

# Monumental / place-like endings. Much less personal than frigates, less compact than corvettes.
TOPONYM_ENDINGS = [
    ("ae", 5), ("aeon", 1), ("aeus", 2), ("an", 4), ("ane", 3), ("anis", 2),
    ("ara", 4), ("aris", 4), ("aron", 2), ("ava", 3), ("aven", 6),
    ("bia", 5), ("dra", 3), ("ea", 3), ("eia", 2), ("ena", 5), ("enes", 3),
    ("eon", 5), ("era", 4), ("eris", 3), ("essa", 2), ("eth", 2), ("eus", 4),
    ("ia", 5), ("ian", 6), ("ikon", 3), ("ine", 7), ("ion", 8), ("ira", 3),
    ("is", 3), ("ithe", 2), ("ium", 5), ("ivea", 2), ("on", 4), ("onis", 4),
    ("ora", 5), ("oria", 4), ("oris", 3), ("os", 2), ("ox", 2),
    ("um", 3), ("une", 2), ("us", 3), ("ym", 2), ("yr", 1)
]

RARE_ENDINGS = [
    ("alon", 2), ("amon", 2), ("athe", 2), ("eron", 2), ("etha", 1), ("oriae", 1)
]

VOWEL_MUTATIONS = {
    "a": ["a", "e", "ae"],
    "e": ["e", "i", "ae"],
    "i": ["i", "y", "e", "ia"],
    "o": ["o", "u", "io"],
    "u": ["u", "o"],
    "y": ["y", "i"],
}

INSERT_CLUSTERS = [
    "r", "l", "n", "s", "th", "ph", "gl", "ll", "ss", "men", "van",
    "rion", "tion", "the", "ven", "mon", "tan", "nes", "via", "dra"
]

IDENTITY_CLUSTERS = {
    "ae", "app", "bia", "cip", "cor", "dig", "ea", "ena", "eon", "eria",
    "gal", "gel", "gyth", "hes", "hier", "ikon", "ine", "ion", "men",
    "onis", "ora", "oria", "pal", "per", "phe", "qua", "roc", "sol",
    "spae", "tae", "thr", "tre", "vall"
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
    return {normalize(strip_prefix(x)) for x in parse_quoted_names(CURRENT_CRUISERS_TEXT)}


def load_blacklist(path: Path | None) -> set[str]:
    names = parse_current_bare_names()

    if path is not None and path.exists():
        text = path.read_text(encoding="utf-8")
        names |= {normalize(strip_prefix(x)) for x in parse_quoted_names(text)}

    names |= {normalize(x) for x in CRUISER_CITY_SEEDS}
    return {canonical(x) for x in names if x}


def sounds_like_corvette(text: str) -> bool:
    lower = text.lower()
    if any(lower.startswith(x) for x in CORVETTE_FORBIDDEN_STARTS):
        return True
    if any(root in lower for root in CORVETTE_FORBIDDEN_ROOTS):
        return True
    return False


def sounds_like_frigate(text: str) -> bool:
    lower = text.lower()
    if any(root in lower for root in FRIGATE_FORBIDDEN_ROOTS):
        return True
    return False


def sounds_like_destroyer(text: str) -> bool:
    lower = text.lower()
    if any(root in lower for root in DESTROYER_FORBIDDEN_ROOTS):
        return True
    return False


def strip_toponym_ending(name: str) -> str:
    name = normalize(name)
    lower = name.lower()

    endings = (
        "oriae", "oria", "onis", "ium", "ikon", "aven", "eion", "eus",
        "aria", "eris", "aris", "ania", "enus", "eon", "ena", "ine",
        "ion", "ian", "bia", "ava", "ara", "ora", "ae", "ia", "um",
        "us", "is", "on", "an", "a", "e"
    )

    for suffix in endings:
        if lower.endswith(suffix) and len(name) - len(suffix) >= 4:
            return normalize(name[:-len(suffix)])

    return name


def style_seed_names() -> set[str]:
    seeds = parse_current_bare_names() | {normalize(x) for x in CRUISER_CITY_SEEDS}
    return {x for x in seeds if x}


def build_style_sources() -> list[str]:
    seeds = style_seed_names()
    derived = set()

    for name in seeds:
        derived.add(strip_toponym_ending(name))
        if len(name) >= 6:
            derived.add(normalize(name[:-1]))
        if len(name) >= 7:
            derived.add(normalize(name[:-2]))

    all_sources = seeds | derived

    filtered = {
        x for x in all_sources
        if 4 <= len(x) <= 12
        and not sounds_like_destroyer(x.lower())
        and not sounds_like_frigate(x.lower())
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
                if not sounds_like_destroyer(frag) and not sounds_like_frigate(frag):
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
        "ae", "app", "bae", "car", "cip", "cor", "dig", "ede", "epi", "gal",
        "gel", "goth", "gyth", "hes", "hier", "ira", "mac", "men", "nim",
        "pal", "par", "per", "phe", "pri", "qua", "roc", "sol", "spae",
        "syg", "tae", "tau", "thr", "tre", "tur", "val", "vall"
    }

    mids |= {
        "gl", "ll", "lon", "men", "mon", "nes", "on", "ph", "ran", "rion",
        "ron", "ss", "tan", "the", "then", "thi", "tion", "ton", "van",
        "ven", "via", "vor", "xor"
    }

    tails |= {
        "aven", "bia", "dra", "eon", "eris", "essa", "ikon", "ine", "ion",
        "onis", "ora", "oria", "oris", "ox", "the", "um", "us"
    }

    starts = {x for x in starts if re.fullmatch(r"[a-z]{2,5}", x)}
    mids = {x for x in mids if re.fullmatch(r"[a-z]{2,4}", x)}
    tails = {x for x in tails if re.fullmatch(r"[a-z]{2,5}", x)}

    return sorted(starts), sorted(mids), sorted(tails)


def cruiser_ending(rng: random.Random) -> str:
    if rng.random() < 0.08:
        return weighted_choice(rng, RARE_ENDINGS)
    return weighted_choice(rng, TOPONYM_ENDINGS)


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

    if len(s) >= 6 and rng.random() < 0.25:
        s = s[:-1]

    if len(s) >= 7 and rng.random() < 0.10:
        s = s[:-1]

    if rng.random() < 0.35:
        positions = [i for i, ch in enumerate(s) if ch in VOWEL_MUTATIONS]
        if positions:
            pos = rng.choice(positions)
            repl = rng.choice(VOWEL_MUTATIONS[s[pos]])
            s = s[:pos] + repl + s[pos + 1:]

    if rng.random() < 0.28:
        pos = rng.randint(1, max(1, len(s) - 1))
        s = s[:pos] + rng.choice(INSERT_CLUSTERS) + s[pos:]

    if rng.random() < 0.14 and len(s) > 6:
        pos = rng.randint(1, len(s) - 2)
        s = s[:pos] + s[pos + 1:]

    return clean_name(s)


def make_toponymic_name(rng: random.Random) -> str:
    raw = weighted_choice(rng, ONSETS)
    raw = fix_join(raw, weighted_choice(rng, NUCLEI))
    raw = fix_join(raw, weighted_choice(rng, MEDIALS))
    raw = fix_join(raw, weighted_choice(rng, NUCLEI))

    if rng.random() < 0.72:
        raw = fix_join(raw, weighted_choice(rng, CODAS))

    raw = fix_join(raw, cruiser_ending(rng))
    return clean_name(raw)


def make_fragment_name(starts: list[str], mids: list[str], tails: list[str], rng: random.Random) -> str:
    raw = rng.choice(starts)

    mid_count = rng.choices([1, 2, 3], weights=[16, 46, 38], k=1)[0]
    for _ in range(mid_count):
        raw = fix_join(raw, rng.choice(mids))

    if rng.random() < 0.70:
        raw = fix_join(raw, rng.choice(tails))

    raw = fix_join(raw, cruiser_ending(rng))
    return clean_name(raw)


def make_city_root_name(style_sources: list[str], rng: random.Random) -> str:
    base = strip_toponym_ending(rng.choice(style_sources))

    if rng.random() < 0.45 and len(base) > 5:
        base = base[:-rng.choice([1, 1, 2])]

    if rng.random() < 0.22:
        base = fix_join(base, rng.choice(["r", "l", "n", "the", "ven", "mon", "tion", "dra"]))

    raw = fix_join(base, cruiser_ending(rng))
    return clean_name(raw)


def make_compound_city_name(style_sources: list[str], rng: random.Random) -> str:
    a = strip_toponym_ending(rng.choice(style_sources))
    b = strip_toponym_ending(rng.choice(style_sources))
    while b == a:
        b = strip_toponym_ending(rng.choice(style_sources))

    a_cut = rng.randint(2, max(2, min(5, len(a) - 2)))
    b_start = rng.randint(max(1, len(b) // 2 - 1), max(2, len(b) - 2))

    raw = a[:a_cut] + b[b_start:]

    if rng.random() < 0.80:
        raw = fix_join(raw, cruiser_ending(rng))

    return clean_name(raw)


def make_demonymic_name(style_sources: list[str], rng: random.Random) -> str:
    base = strip_toponym_ending(rng.choice(style_sources)).lower()

    special_endings = [
        ("ian", 6), ("ean", 3), ("aran", 3), ("enes", 3), ("oran", 2),
        ("eron", 3), ("atis", 2), ("ikon", 2), ("eus", 2)
    ]

    if len(base) >= 6:
        raw = base[:rng.randint(3, 5)]
    else:
        raw = base

    if rng.random() < 0.40:
        raw = fix_join(raw, rng.choice(["th", "r", "l", "n", "ven", "the", "mon", "dra"]))

    raw = fix_join(raw, weighted_choice(rng, special_endings))
    return clean_name(raw)


def make_mutated_name(style_sources: list[str], rng: random.Random) -> str:
    base = rng.choice(style_sources)
    raw = mutate_base(base, rng)

    if rng.random() < 0.84:
        raw = fix_join(raw, cruiser_ending(rng))

    return clean_name(raw)


def has_cruiser_identity(name: str) -> bool:
    lower = canonical(name)
    return any(cluster in lower for cluster in IDENTITY_CLUSTERS)


def is_viable(name: str) -> bool:
    lower = name.lower()
    length = len(name)

    if not (7 <= length <= 13):
        return False

    if vowel_groups(name) < 2 or vowel_groups(name) > 6:
        return False

    if re.search(r"[aeiouy]{4}", lower):
        return False

    if re.search(r"[bcdfghjklmnpqrstvwxyz]{4}", lower):
        return False

    if re.search(r"(.)\1\1", lower):
        return False

    if not has_cruiser_identity(lower):
        return False

    if sounds_like_frigate(lower) or sounds_like_destroyer(lower):
        return False

    # Cruiser names may overlap with city roots, so no corvette hard-reject here.
    # Their blacklist still prevents exact collisions.

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


def too_frigate_like(name: str) -> bool:
    key = canonical(name)
    if sounds_like_frigate(key):
        return True
    if key.endswith(("rius", "rianus", "ctus", "vian", "tarian", "arius")):
        return True
    return False


def too_destroyer_like(name: str) -> bool:
    key = canonical(name)
    if sounds_like_destroyer(key):
        return True
    if key.endswith(("ulus", "imus")) and len(key) <= 10:
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
        population=["toponymic", "city_root", "compound", "fragment", "demonymic", "mutated"],
        weights=[24, 18, 18, 16, 14, 10],
        k=1,
    )[0]

    for _ in range(800):
        if mode == "toponymic":
            candidate = make_toponymic_name(rng)
        elif mode == "city_root":
            candidate = make_city_root_name(style_sources, rng)
        elif mode == "compound":
            candidate = make_compound_city_name(style_sources, rng)
        elif mode == "fragment":
            candidate = make_fragment_name(starts, mids, tails, rng)
        elif mode == "demonymic":
            candidate = make_demonymic_name(style_sources, rng)
        else:
            candidate = make_mutated_name(style_sources, rng)

        if is_viable(candidate) and not too_frigate_like(candidate) and not too_destroyer_like(candidate):
            return candidate

    raise RuntimeError("Failed to generate a viable cruiser candidate.")


def generate_cruiser_names(
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
    max_attempts = count * 22000

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        bare = make_candidate(style_sources, starts, mids, tails, rng)
        key = canonical(bare)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(key, blacklist | seen_local):
            continue

        if too_frigate_like(key) or too_destroyer_like(key):
            continue

        seen_local.add(key)
        results.append(f"PFS {bare}" if include_prefix else bare)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique Turian cruiser names after {attempts} attempts."
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
            "Generate lore-adjacent Turian cruiser names with a distinct city/colony tone, "
            "using cruiser-only style material and avoiding frigate/destroyer cadence."
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

    names = generate_cruiser_names(
        count=args.count,
        seed=args.seed,
        blacklist_path=args.blacklist_file,
        include_prefix=not args.no_prefix,
    )
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())