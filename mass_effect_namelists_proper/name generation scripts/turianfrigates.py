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


CURRENT_FRIGATES_TEXT = r'''
"PFS Havincaw" "PFS Torelen" "PFS Verrikan" "PFS Ravuna" "PFS Natanus" "PFS Victus" "PFS Vakarian" "PFS Arterius"
"PFS Aurelos" "PFS Oraka" "PFS Tiron" "PFS Actus" "PFS Haliat" "PFS Nazario" "PFS Gavorn" "PFS Kryik"
"PFS Sidonis" "PFS Kuril" "PFS Coronati" "PFS Pallin" "PFS Talid" "PFS Palanurus" "PFS Quarn" "PFS Davaria"
"PFS Kandros" "PFS Sahira" "PFS Emperus" "PFS Vyrnnus" "PFS Chellick" "PFS Fedorian" "PFS Corinthus" "PFS Haron"
"PFS Invectus" "PFS Vidinos" "PFS Valen" "PFS Scartos" "PFS Saneraxis" "PFS Hanus" "PFS Sylvatus" "PFS Partinax"
"PFS Relius" "PFS Tanus" "PFS Antivus" "PFS Tertius" "PFS Septimax" "PFS Machaera" "PFS Pagasi" "PFS Dianix"
"PFS Iheras" "PFS Partainis" "PFS Satorim" "PFS Ravidus" "PFS Daphnon" "PFS Nyrek" "PFS Korilius" "PFS Irvinus"
"PFS Siyan" "PFS Iherax" "PFS Sycoram" "PFS Septimas" "PFS Squaron" "PFS Riten" "PFS Spartarus" "PFS Quentiys"
"PFS Ursinus" "PFS Paramon" "PFS Borlin" "PFS Darikun" "PFS Latronus" "PFS Korlick" "PFS Patathor" "PFS Vadus"
"PFS Genchak" "PFS Raedun" "PFS Rubicum" "PFS Bartus" "PFS Egnadus" "PFS Primax" "PFS Castellan" "PFS Varro"
"PFS Tetranus" "PFS Corvinus" "PFS Palatin"
'''

# Citizen / surname / cognomen style anchors.
ANCHOR_NAMES = [
    "Havincaw", "Torelen", "Verrikan", "Victus", "Vakarian", "Arterius",
    "Pallin", "Kandros", "Chellick", "Fedorian", "Castellan", "Varro",
    "Corvinus", "Septimus", "Victus", "Vakarian", "Nyreen", "Saren",
    "Desolas", "Tarquin", "Adrien", "Hierax", "Corvin", "Tironis",
]

# Explicitly block the corvette/place-root territory.
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

# Frigate endings: more cognomen / surname than corvette hulls.
FRIGATE_ENDINGS = [
    ("an", 5), ("ar", 4), ("as", 4), ("ax", 4),
    ("ek", 2), ("el", 4), ("en", 6), ("er", 5), ("es", 3),
    ("ian", 9), ("iar", 2), ("ias", 2), ("ic", 3), ("id", 3), ("ik", 4),
    ("il", 2), ("in", 7), ("inus", 8), ("ion", 4), ("ior", 3), ("ir", 3),
    ("is", 6), ("ius", 9), ("ix", 5),
    ("on", 5), ("or", 5), ("os", 3),
    ("um", 2), ("un", 3), ("ur", 3), ("us", 8), ("yn", 2), ("ys", 2),
    ("atus", 3), ("ectus", 3), ("enus", 4), ("eran", 3), ("eron", 4),
    ("aris", 4), ("orin", 3), ("orian", 3), ("idan", 2), ("ivar", 2),
    ("imus", 3), ("imax", 3), ("inax", 3), ("orius", 2), ("avian", 2),
]

# Rare softer ends allowed for frigates, but low frequency.
RARE_SOFT_ENDINGS = [
    ("ira", 2), ("aria", 2), ("aera", 1), ("oria", 1), ("ara", 2), ("aya", 1)
]

FORBIDDEN_PLACE_ENDINGS = (
    "ium", "eum", "aeum", "oriae", "orium", "arium", "ae", "io"
)

INSERT_CLUSTERS = [
    "r", "t", "d", "n", "l", "v", "k", "x", "m",
    "tr", "dr", "gr", "ct", "th", "ph", "rn", "rd", "lk", "rr", "ll",
    "var", "tor", "dar", "rik", "vin", "kor", "vak", "sid", "tal", "ven",
    "mar", "dor", "ren", "lin", "the", "sar"
]

MUTATION_VOWELS = {
    "a": ["a", "e", "ae"],
    "e": ["e", "i", "ae"],
    "i": ["i", "y", "e"],
    "o": ["o", "u"],
    "u": ["u", "o"],
    "y": ["y", "i"],
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
    # script is assumed to live in: <mod root>/name generation scripts/
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
    return name[0].upper() + name[1:].lower()


def canonical(name: str) -> str:
    return normalize(strip_prefix(name)).lower()


def weighted_choice(rng: random.Random, pairs: list[tuple[str, int]]) -> str:
    items = [item for item, _ in pairs]
    weights = [weight for _, weight in pairs]
    return rng.choices(items, weights=weights, k=1)[0]


def vowel_groups(name: str) -> int:
    return len(re.findall(r"[aeiouy]+", name.lower()))


def parse_current_bare_names() -> set[str]:
    return {normalize(strip_prefix(x)) for x in parse_quoted_names(CURRENT_FRIGATES_TEXT)}


def load_existing_bare_names(path: Path | None) -> set[str]:
    names = set(parse_current_bare_names())

    if path is not None and path.exists():
        text = path.read_text(encoding="utf-8")
        names |= {normalize(strip_prefix(x)) for x in parse_quoted_names(text)}

    names |= {normalize(x) for x in ANCHOR_NAMES}
    return {x for x in names if x}


def load_blacklist(path: Path | None) -> set[str]:
    return {canonical(x) for x in load_existing_bare_names(path)}


def strip_citizen_ending(name: str) -> str:
    name = normalize(name)
    lower = name.lower()

    endings = (
        "orius", "arian", "erian", "avian", "ectus", "atus", "imus", "imax",
        "inax", "inus", "ian", "ius", "ion", "ior", "aris", "eron", "enus",
        "ous", "ax", "ix", "us", "is", "or", "on", "en", "an", "a", "e"
    )

    for suffix in endings:
        if lower.endswith(suffix) and len(name) - len(suffix) >= 4:
            return normalize(name[:-len(suffix)])

    return name


def build_style_sources(existing_bare: set[str]) -> list[str]:
    sources = set(existing_bare)
    sources |= {normalize(x) for x in ANCHOR_NAMES}

    derived = set()
    for name in sources:
        derived.add(strip_citizen_ending(name))
        if len(name) >= 6:
            derived.add(normalize(name[:-1]))
        if len(name) >= 7:
            derived.add(normalize(name[:-2]))

    all_sources = sources | derived

    filtered = {
        x for x in all_sources
        if 4 <= len(x) <= 12 and not sounds_like_corvette_root(x.lower())
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

        for n in (2, 3, 4):
            if len(s) >= n + 1:
                frag = s[:n]
                if not sounds_like_corvette_root(frag):
                    starts.add(frag)

        for i in range(1, max(2, len(s) - 2)):
            for n in (2, 3):
                if i + n <= len(s) - 1:
                    frag = s[i:i + n]
                    if re.search(r"[aeiouy]", frag) or re.search(r"[bcdfghjklmnpqrstvwxyz]{2}", frag):
                        mids.add(frag)

        for n in (2, 3, 4):
            if len(s) >= n + 1:
                tails.add(s[-n:])

    starts |= {
        "hav", "tor", "ver", "vak", "art", "pal", "kan", "che", "fed",
        "sep", "cor", "var", "lat", "sid", "kor", "dar", "gen", "bar",
        "val", "san", "vid", "tal", "han", "tir", "nyr", "sar", "des",
        "tar", "adr", "hier", "par", "rub", "quen", "urs", "daph"
    }

    mids |= {
        "ct", "tr", "dr", "gr", "ll", "rr", "th", "ph", "rn", "rd", "rik",
        "vin", "dor", "tor", "dar", "vak", "kan", "sid", "tal", "ver", "ran",
        "lin", "sar", "ven", "mar", "ren", "the", "cor", "var", "fed"
    }

    tails |= {
        "rik", "ron", "ran", "lin", "dor", "tor", "dar", "nus", "tus",
        "rix", "lik", "vin", "rian", "dros", "llin", "tius", "rion", "rin"
    }

    starts = {x for x in starts if re.fullmatch(r"[a-z]{2,4}", x) and not sounds_like_corvette_root(x)}
    mids = {x for x in mids if re.fullmatch(r"[a-z]{2,4}", x)}
    tails = {x for x in tails if re.fullmatch(r"[a-z]{2,4}", x)}

    return sorted(starts), sorted(mids), sorted(tails)


def frigate_ending(rng: random.Random, soft_bias: float = 0.08) -> str:
    if rng.random() < soft_bias:
        return weighted_choice(rng, RARE_SOFT_ENDINGS)
    return weighted_choice(rng, FRIGATE_ENDINGS)


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

    if len(s) >= 5 and rng.random() < 0.45:
        s = s[:-1]

    if len(s) >= 6 and rng.random() < 0.20:
        s = s[:-1]

    if rng.random() < 0.35:
        positions = [i for i, ch in enumerate(s) if ch in MUTATION_VOWELS]
        if positions:
            pos = rng.choice(positions)
            repl = rng.choice(MUTATION_VOWELS[s[pos]])
            s = s[:pos] + repl + s[pos + 1:]

    if rng.random() < 0.30:
        pos = rng.randint(1, max(1, len(s) - 1))
        s = s[:pos] + rng.choice(INSERT_CLUSTERS) + s[pos:]

    if rng.random() < 0.15 and len(s) > 5:
        pos = rng.randint(1, len(s) - 2)
        s = s[:pos] + s[pos + 1:]

    return clean_name(s)


def sounds_like_corvette_root(text: str) -> bool:
    lower = text.lower()

    if any(lower.startswith(x) for x in CORVETTE_FORBIDDEN_STARTS):
        return True

    if any(x in lower for x in CORVETTE_FORBIDDEN_ROOTS):
        return True

    for root in CORVETTE_FORBIDDEN_ROOTS:
        if len(lower) >= 4 and len(root) >= 4:
            if lower[:3] == root[:3] and SequenceMatcher(None, lower, root).ratio() >= 0.72:
                return True

    return False


def make_cognomen_name(style_sources: list[str], rng: random.Random) -> str:
    base = strip_citizen_ending(rng.choice(style_sources))

    if rng.random() < 0.55 and len(base) > 5:
        base = base[:-rng.choice([1, 1, 2])]

    if rng.random() < 0.28:
        base = fix_join(base, rng.choice(["r", "t", "d", "n", "k", "ct", "th", "rik", "tor", "ven"]))

    raw = fix_join(base, frigate_ending(rng))
    return clean_name(raw)


def make_house_name(style_sources: list[str], rng: random.Random) -> str:
    a = strip_citizen_ending(rng.choice(style_sources))
    b = strip_citizen_ending(rng.choice(style_sources))
    while b == a:
        b = strip_citizen_ending(rng.choice(style_sources))

    a_cut = rng.randint(2, max(2, min(5, len(a) - 2)))
    b_start = rng.randint(max(1, len(b) // 2 - 1), max(2, len(b) - 2))

    raw = a[:a_cut] + b[b_start:]

    if rng.random() < 0.75:
        raw = fix_join(raw, frigate_ending(rng))

    return clean_name(raw)


def make_fragment_name(starts: list[str], mids: list[str], tails: list[str], rng: random.Random) -> str:
    raw = rng.choice(starts)

    mid_count = rng.choices([1, 2, 3], weights=[28, 47, 25], k=1)[0]
    for _ in range(mid_count):
        raw = fix_join(raw, rng.choice(mids))

    if rng.random() < 0.62:
        raw = fix_join(raw, rng.choice(tails))

    raw = fix_join(raw, frigate_ending(rng))
    return clean_name(raw)


def make_mutated_name(style_sources: list[str], rng: random.Random) -> str:
    base = rng.choice(style_sources)
    raw = mutate_base(base, rng)

    if rng.random() < 0.85:
        raw = fix_join(raw, frigate_ending(rng))

    return clean_name(raw)


def make_lineage_name(style_sources: list[str], rng: random.Random) -> str:
    base = strip_citizen_ending(rng.choice(style_sources))
    lower = base.lower()

    if len(lower) >= 6:
        left = lower[:rng.randint(2, 4)]
        right = lower[-rng.choice([2, 3, 4]):]
        raw = fix_join(left, right)
    else:
        raw = lower

    if rng.random() < 0.45:
        raw = fix_join(raw, rng.choice(["ar", "er", "in", "or", "us", "ix", "ian", "ius", "enus", "ax"]))

    return clean_name(raw)


def make_rare_soft_name(style_sources: list[str], rng: random.Random) -> str:
    base = strip_citizen_ending(rng.choice(style_sources))
    lower = base.lower()

    if len(lower) >= 5:
        raw = lower[:rng.randint(2, 4)]
    else:
        raw = lower

    if rng.random() < 0.65:
        raw = fix_join(raw, rng.choice(["hav", "sah", "dav", "ria", "sha", "ira", "ara", "ven", "lia", "mar"]))

    raw = fix_join(raw, weighted_choice(rng, RARE_SOFT_ENDINGS))
    return clean_name(raw)


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

    if any(lower.endswith(x) for x in FORBIDDEN_PLACE_ENDINGS):
        return False

    if sounds_like_corvette_root(lower):
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

    # Reject compact escort-hull cadence.
    if len(key) <= 9 and key.endswith(("ac", "ec", "ex", "oc", "ul", "yx")):
        return True

    if vowel_groups(key) <= 2 and len(key) <= 8:
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
        population=["cognomen", "house", "fragment", "mutated", "lineage", "soft"],
        weights=[24, 20, 22, 16, 12, 6],
        k=1,
    )[0]

    for _ in range(500):
        if mode == "cognomen":
            candidate = make_cognomen_name(style_sources, rng)
        elif mode == "house":
            candidate = make_house_name(style_sources, rng)
        elif mode == "fragment":
            candidate = make_fragment_name(starts, mids, tails, rng)
        elif mode == "mutated":
            candidate = make_mutated_name(style_sources, rng)
        elif mode == "lineage":
            candidate = make_lineage_name(style_sources, rng)
        else:
            candidate = make_rare_soft_name(style_sources, rng)

        if is_viable(candidate) and not too_corvette_like(candidate):
            return candidate

    raise RuntimeError("Failed to generate a viable frigate candidate.")


def generate_frigate_names(
    count: int,
    seed: int | None = None,
    blacklist_path: Path | None = None,
    include_prefix: bool = True,
) -> list[str]:
    rng = random.Random(seed)

    existing_bare = load_existing_bare_names(blacklist_path)
    blacklist = load_blacklist(blacklist_path)
    style_sources = build_style_sources(existing_bare)
    starts, mids, tails = build_fragment_pools(style_sources)

    results: list[str] = []
    seen_local: set[str] = set()

    attempts = 0
    max_attempts = count * 18000

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        bare = make_candidate(style_sources, starts, mids, tails, rng)
        key = canonical(bare)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(key, blacklist | seen_local):
            continue

        if too_corvette_like(key):
            continue

        seen_local.add(key)
        results.append(f"PFS {bare}" if include_prefix else bare)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique Turian frigate names after {attempts} attempts."
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
            "Generate lore-adjacent Turian frigate names with a citizen/cognomen tone, "
            "while explicitly avoiding corvette/place-root phonetics."
        )
    )
    parser.add_argument("--count", type=int, default=120, help="Number of names to generate. Default: 120")
    parser.add_argument("--seed", type=int, default=42, help="Random seed. Default: 42")
    parser.add_argument("--per-line", type=int, default=8, help="Names per output line. Default: 8")
    parser.add_argument(
        "--blacklist-file",
        type=Path,
        default=default_blacklist_path(),
        help="Optional namelist file to blacklist existing Turian names from and use as a style source.",
    )
    parser.add_argument(
        "--no-prefix",
        action="store_true",
        help="Output bare names without the PFS prefix.",
    )
    args = parser.parse_args()

    names = generate_frigate_names(
        count=args.count,
        seed=args.seed,
        blacklist_path=args.blacklist_file,
        include_prefix=not args.no_prefix,
    )
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())