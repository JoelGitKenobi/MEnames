#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path


QUOTED_STRING_RE = re.compile(r'"([^"]+)"')
PREFIX_RE = re.compile(r"^(?:CSV)\s+", re.IGNORECASE)
NON_ALPHA_RE = re.compile(r"[^A-Za-z0-9\s\-]")
MULTISPACE_RE = re.compile(r"\s+")
MULTIHYPHEN_RE = re.compile(r"-{2,}")


CURRENT_CERBERUS_SHIP_NAMES_TEXT = r'''
"CSV Elbrus" "CSV Phoenix" "CSV Mindoir" "CSV Akuze"
"CSV Shanxi" "CSV Elysium" "CSV Concord" "CSV Lexington"
'''

STYLE_SEEDS = [
    "Elbrus",
    "Phoenix",
    "Mindoir",
    "Akuze",
    "Shanxi",
    "Elysium",
    "Concord",
    "Lexington",
]

# Cerberus ship names should feel human, militarized, black-ops, ideological,
# and often Hellenic / mythic / campaign-like rather than alien or flowery.

PREFIXES = [
    ("Ae", 1), ("Al", 2), ("An", 2), ("Ar", 4), ("As", 2), ("At", 2),
    ("Au", 1), ("Bel", 1), ("Cal", 2), ("Car", 1), ("Cer", 1), ("Chron", 1),
    ("Con", 3), ("Cor", 2), ("Del", 2), ("E", 1), ("El", 4), ("En", 1),
    ("Ely", 3), ("Ex", 2), ("Fal", 1), ("Hel", 3), ("Her", 2), ("Hex", 1),
    ("I", 1), ("Ka", 1), ("Kor", 1), ("Lex", 4), ("Ly", 2), ("Mar", 1),
    ("Mer", 1), ("Min", 3), ("Mor", 2), ("Myr", 1), ("Ne", 1), ("Nex", 2),
    ("No", 1), ("Ny", 1), ("Or", 1), ("Phae", 1), ("Phe", 1), ("Pho", 4),
    ("Prae", 2), ("Pro", 3), ("Py", 2), ("Rex", 1), ("Sal", 1), ("San", 2),
    ("Sel", 1), ("Sha", 3), ("Tar", 1), ("Tel", 2), ("Ther", 2), ("Tri", 2),
    ("Ty", 1), ("Val", 1), ("Vex", 1), ("Xan", 1), ("Zer", 1),
]

CORES = [
    ("bar", 1), ("ber", 3), ("bron", 1), ("cord", 5), ("cron", 2), ("dor", 2),
    ("dras", 1), ("drix", 1), ("dyn", 1), ("el", 3), ("eon", 1), ("eros", 1),
    ("eth", 1), ("eus", 2), ("fal", 1), ("gis", 1), ("gon", 1), ("gor", 1),
    ("hex", 1), ("ion", 4), ("ixar", 1), ("kon", 1), ("las", 2), ("lix", 2),
    ("lon", 2), ("lux", 1), ("med", 1), ("meth", 1), ("mir", 1), ("mon", 2),
    ("mor", 2), ("nax", 1), ("neth", 1), ("nor", 2), ("phon", 2), ("phor", 1),
    ("rax", 1), ("reon", 1), ("rex", 1), ("rion", 2), ("ros", 2), ("san", 2),
    ("sel", 1), ("sium", 1), ("tan", 1), ("tel", 2), ("ter", 2), ("thal", 1),
    ("thon", 2), ("tor", 2), ("tri", 2), ("tyr", 1), ("var", 1), ("vex", 1),
    ("xis", 1), ("xon", 2), ("zar", 1), ("zor", 1),
]

SUFFIXES = [
    ("a", 2), ("ae", 1), ("ai", 1), ("an", 3), ("ar", 3), ("as", 5),
    ("ax", 2), ("e", 2), ("ea", 1), ("eon", 2), ("er", 3), ("eron", 2),
    ("es", 4), ("ia", 2), ("ian", 3), ("ion", 7), ("ios", 2), ("is", 5),
    ("ix", 4), ("on", 6), ("or", 4), ("ora", 1), ("orn", 1), ("os", 7),
    ("um", 1), ("us", 6), ("ys", 1),
]

# Optional second elements. Used sparingly so names still feel like ship names.
SECOND_WORDS = [
    ("Ascendant", 1),
    ("Resolute", 2),
    ("Vigil", 2),
    ("Peregrine", 1),
    ("Aegis", 2),
    ("Sentinel", 2),
    ("Harbinger", 1),
    ("Vanguard", 2),
    ("Prime", 2),
]

ROMAN_NUMERALS = ["II", "III", "IV", "V"]

IDENTITY_CLUSTERS = {
    "elbr", "pho", "mind", "aku", "shan", "ely", "con", "lex",
    "ion", "os", "us", "cord", "ber", "tel", "ther", "tri", "nex", "pho"
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
        mod_root() / "common" / "name_lists" / "cerberus_ship_names.txt",
        mod_root() / "common" / "name_lists" / "00_cerberus_ship_names.txt",
        mod_root() / "common" / "name_lists" / "zz_cerberus_ship_names.txt",
        mod_root() / "common" / "namelists" / "cerberus_ship_names.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def strip_prefix(name: str) -> str:
    return PREFIX_RE.sub("", name).strip()


def weighted_choice(rng: random.Random, pairs: list[tuple[str, int]]) -> str:
    items = [item for item, _ in pairs]
    weights = [weight for _, weight in pairs]
    return rng.choices(items, weights=weights, k=1)[0]


def normalize_spaces_and_hyphens(name: str) -> str:
    name = NON_ALPHA_RE.sub("", name)
    name = MULTISPACE_RE.sub(" ", name).strip()
    name = MULTIHYPHEN_RE.sub("-", name)
    name = re.sub(r"\s*-\s*", "-", name)
    return name


def normalize_word(word: str) -> str:
    if not word:
        return ""
    if word.isupper() and len(word) <= 4:
        return word
    if word.isdigit():
        return word
    return word[:1].upper() + word[1:].lower()


def normalize_name(name: str) -> str:
    name = normalize_spaces_and_hyphens(name)
    if not name:
        return ""

    parts = []
    for token in name.split(" "):
        if "-" in token:
            subparts = [normalize_word(x) for x in token.split("-") if x]
            parts.append("-".join(subparts))
        else:
            parts.append(normalize_word(token))
    return " ".join(parts).strip()


def canonical(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", strip_prefix(name).lower())


def vowel_groups(name: str) -> int:
    return len(re.findall(r"[aeiouy]+", canonical(name)))


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
        if right.startswith(("i", "o", "u")):
            return left + right
        right = right[1:] or "i"

    return left + right


def clean_constructed(raw: str) -> str:
    raw = normalize_name(raw)
    raw = re.sub(r"(.)\1\1+", r"\1\1", raw, flags=re.IGNORECASE)
    return raw


def load_blacklist(path: Path | None) -> set[str]:
    names = {strip_prefix(x) for x in parse_quoted_names(CURRENT_CERBERUS_SHIP_NAMES_TEXT)}

    if path is not None and path.exists():
        text = path.read_text(encoding="utf-8")
        names |= {strip_prefix(x) for x in parse_quoted_names(text)}

    names |= set(STYLE_SEEDS)
    return {canonical(x) for x in names if x}


def has_identity(name: str) -> bool:
    lower = canonical(name)
    return any(cluster in lower for cluster in IDENTITY_CLUSTERS)


def is_viable(name: str) -> bool:
    lower = canonical(name)

    if not (5 <= len(lower) <= 22):
        return False

    if vowel_groups(name) < 2 or vowel_groups(name) > 7:
        return False

    if re.search(r"[bcdfghjklmnpqrstvwxyz]{5}", lower):
        return False

    if re.search(r"(.)\1\1", lower):
        return False

    if re.search(r"\b(station|facility|outpost|complex|array|site|node|colony)\b", name, re.IGNORECASE):
        return False

    if not has_identity(name):
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

        if len(key) >= 5 and len(other) >= 5 and key[:5] == other[:5]:
            return True

        if len(key) >= 7 and len(other) >= 7 and key[:3] == other[:3] and key[-3:] == other[-3:]:
            return True

        if key_skel and key_skel == skeleton(other):
            return True

        if SequenceMatcher(None, key, other).ratio() >= 0.90:
            return True

    return False


def make_single_word_name(rng: random.Random) -> str:
    raw = weighted_choice(rng, PREFIXES)

    segment_count = rng.choices([1, 2, 3], weights=[40, 45, 15], k=1)[0]
    for _ in range(segment_count):
        raw = fix_join(raw, weighted_choice(rng, CORES))
        if rng.random() < 0.28:
            raw = fix_join(raw, rng.choice(["a", "e", "i", "o"]))

    raw = fix_join(raw, weighted_choice(rng, SUFFIXES))
    return clean_constructed(raw)


def make_seed_blend_name(rng: random.Random) -> str:
    a = canonical(rng.choice(STYLE_SEEDS))
    b = canonical(rng.choice(STYLE_SEEDS))
    while b == a:
        b = canonical(rng.choice(STYLE_SEEDS))

    a_cut = rng.randint(2, max(2, min(5, len(a) - 2)))
    b_start = rng.randint(max(1, len(b) // 2 - 1), max(2, len(b) - 2))
    raw = a[:a_cut] + b[b_start:]

    if rng.random() < 0.45:
        raw = fix_join(raw, weighted_choice(rng, SUFFIXES))

    return clean_constructed(raw)


def make_two_word_name(rng: random.Random) -> str:
    first = make_single_word_name(rng)
    second_mode = rng.choices(["title", "roman"], weights=[75, 25], k=1)[0]

    if second_mode == "title":
        return clean_constructed(f"{first} {weighted_choice(rng, SECOND_WORDS)}")

    return clean_constructed(f"{first} {rng.choice(ROMAN_NUMERALS)}")


def make_candidate(rng: random.Random) -> str:
    mode = rng.choices(
        population=["single", "blend", "two_word"],
        weights=[58, 22, 20],
        k=1,
    )[0]

    for _ in range(1000):
        if mode == "single":
            candidate = make_single_word_name(rng)
        elif mode == "blend":
            candidate = make_seed_blend_name(rng)
        else:
            candidate = make_two_word_name(rng)

        if is_viable(candidate):
            return candidate

    raise RuntimeError("Failed to generate a viable Cerberus ship-name candidate.")


def generate_cerberus_ship_names(
    count: int,
    seed: int | None = None,
    blacklist_path: Path | None = None,
    include_prefix: bool = True,
    max_attempts_multiplier: int = 30000,
) -> list[str]:
    rng = random.Random(seed)

    blacklist = load_blacklist(blacklist_path)
    results: list[str] = []
    seen_local: set[str] = set()

    attempts = 0
    max_attempts = max(count * max_attempts_multiplier, 1000)

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        bare = make_candidate(rng)
        key = canonical(bare)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(bare, blacklist | seen_local):
            continue

        seen_local.add(key)
        results.append(f"CSV {bare}" if include_prefix else bare)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique Cerberus ship names after {attempts} attempts."
        )

    return results


def format_as_array(names: list[str], per_line: int = 6) -> str:
    lines = ["["]
    for i in range(0, len(names), per_line):
        chunk = names[i:i + per_line]
        lines.append("    " + " ".join(f'"{name}"' for name in chunk))
    lines.append("]")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Cerberus-style human ship names with CSV prefix, using a mythic-militarized "
            "human naming tone and avoiding duplicates from an existing namelist file."
        )
    )
    parser.add_argument("--count", type=int, default=60, help="Number of names to generate. Default: 60")
    parser.add_argument("--seed", type=int, default=42, help="Random seed. Default: 42")
    parser.add_argument("--per-line", type=int, default=6, help="Names per output line. Default: 6")
    parser.add_argument(
        "--blacklist-file",
        type=Path,
        default=default_blacklist_path(),
        help="Optional namelist file to blacklist existing Cerberus ship names from.",
    )
    parser.add_argument(
        "--max-attempts-multiplier",
        type=int,
        default=30000,
        help="Attempt budget multiplier. Total attempts = count * multiplier. Default: 30000",
    )
    parser.add_argument(
        "--no-prefix",
        action="store_true",
        help="Output bare names without the CSV prefix.",
    )
    args = parser.parse_args()

    names = generate_cerberus_ship_names(
        count=args.count,
        seed=args.seed,
        blacklist_path=args.blacklist_file,
        include_prefix=not args.no_prefix,
        max_attempts_multiplier=args.max_attempts_multiplier,
    )
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())