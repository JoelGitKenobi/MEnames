#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path


QUOTED_STRING_RE = re.compile(r'"([^"]+)"')
NON_ALPHA_RE = re.compile(r"[^A-Za-z0-9\s\-]")
MULTISPACE_RE = re.compile(r"\s+")
MULTIHYPHEN_RE = re.compile(r"-{2,}")

# Seed examples / blacklist anchors.
# Populate this with the actual names you want to reserve before using the generator.
CURRENT_CERBERUS_PLANET_NAMES_TEXT = r'''
"Aite" "Atlas" "Avernus" "Binthu" "Cronos" "Gellix" "Hermes" "Horizon"
"Lazarus" "Minuteman" "Nepheron" "Omega" "Ontarom" "Pragia" "Prometheus"
"Sanctuary" "Sanctum" "Teltin" "Trident" "Vulcan"
'''

STYLE_SEEDS = [
    "Aite",
    "Atlas",
    "Avernus",
    "Binthu",
    "Cronos",
    "Gellix",
    "Hermes",
    "Horizon",
    "Lazarus",
    "Nepheron",
    "Ontarom",
    "Pragia",
    "Prometheus",
    "Sanctuary",
    "Sanctum",
    "Teltin",
    "Trident",
    "Vulcan",
]

# Greek / pseudo-Greek / Cerberus-appropriate morphemes.
# Intentionally mixed between mythic, scientific, militarized, institutional, and colonial tones.

PREFIXES = [
    ("A", 3), ("Ae", 2), ("Ai", 2), ("Al", 2), ("An", 3), ("Apo", 1),
    ("Ar", 4), ("As", 2), ("At", 3), ("Au", 1), ("Cera", 1), ("Chry", 1),
    ("Chron", 2), ("Cry", 1), ("Del", 2), ("Dys", 1), ("E", 2), ("Ek", 1),
    ("El", 2), ("En", 2), ("Ep", 1), ("Eri", 1), ("Eu", 2), ("Ex", 2),
    ("Gal", 1), ("Hel", 3), ("Her", 2), ("Hier", 1), ("Hy", 1), ("I", 1),
    ("Ka", 2), ("Kall", 1), ("Kar", 1), ("Kry", 1), ("Laz", 2), ("Le", 1),
    ("Lys", 2), ("Mela", 1), ("Meta", 2), ("Neo", 3), ("Nex", 1), ("Ny", 1),
    ("O", 2), ("Om", 2), ("On", 2), ("Or", 2), ("Pa", 1), ("Pra", 2),
    ("Pseu", 1), ("Py", 2), ("Rha", 1), ("Sanc", 2), ("Sel", 1), ("Syn", 2),
    ("Tel", 2), ("Tha", 1), ("Ther", 2), ("Ty", 1), ("Xe", 1), ("Xy", 1),
]

CORES = [
    ("ta", 5), ("te", 3), ("to", 3), ("tra", 3), ("tri", 3), ("tron", 3),
    ("ther", 2), ("thon", 2), ("dar", 2), ("dor", 2), ("dex", 2), ("dria", 2),
    ("gen", 3), ("gyn", 1), ("gos", 1), ("gon", 2), ("gyr", 1), ("lix", 4),
    ("lon", 3), ("los", 3), ("loss", 1), ("mes", 2), ("met", 3), ("mon", 2),
    ("nar", 3), ("nax", 2), ("neth", 1), ("nix", 2), ("nom", 2), ("nor", 2),
    ("pher", 4), ("phor", 1), ("phos", 2), ("pyr", 3), ("rax", 1), ("reon", 1),
    ("rios", 1), ("rion", 2), ("ris", 2), ("ros", 2), ("san", 3), ("sel", 2),
    ("tal", 2), ("tan", 2), ("tel", 3), ("tem", 2), ("ter", 3), ("thal", 1),
    ("therm", 1), ("thon", 1), ("tin", 3), ("tom", 2), ("tor", 2), ("trax", 1),
    ("tyr", 1), ("vak", 1), ("var", 2), ("ven", 1), ("vul", 2), ("xis", 2),
    ("xon", 2), ("zar", 1), ("zel", 1), ("zor", 1),
]

SUFFIXES = [
    ("a", 6), ("ae", 3), ("ai", 2), ("e", 5), ("ea", 2), ("eia", 3), ("eon", 2),
    ("eron", 3), ("eros", 2), ("es", 2), ("ia", 8), ("ias", 2), ("ides", 1),
    ("ikon", 1), ("ion", 8), ("ios", 3), ("is", 5), ("ium", 6), ("ix", 3),
    ("on", 7), ("or", 2), ("ora", 2), ("oros", 1), ("os", 8), ("ra", 2),
    ("ros", 2), ("um", 3), ("us", 5), ("ys", 1),
]

SECOND_WORDS = [
    ("Station", 4),
    ("Colony", 2),
    ("Outpost", 3),
    ("Sanctum", 2),
    ("Sanctuary", 1),
    ("Facility", 3),
    ("Complex", 2),
    ("Array", 2),
    ("Nexus", 2),
    ("Reach", 1),
    ("Vault", 1),
    ("Node", 1),
    ("Prime", 3),
    ("Sigma", 1),
    ("Alpha", 1),
    ("Gamma", 1),
    ("Beta", 1),
]

ASSIGNMENT_PREFIXES = [
    ("Site", 4),
    ("Station", 3),
    ("Facility", 3),
    ("Colony", 2),
    ("Outpost", 2),
    ("Node", 1),
    ("Array", 1),
]

ASSIGNMENT_JOINERS = [
    ("-", 8),
    (" ", 2),
]

ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

IDENTITY_CLUSTERS = {
    "aite", "atlas", "avern", "cron", "gell", "herm", "horiz", "lazar",
    "neph", "onta", "prag", "prom", "sanct", "telt", "trident", "vulc",
    "pher", "lix", "ion", "ium", "os", "on", "tel", "ther", "nex", "prime"
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
        mod_root() / "common" / "name_lists" / "cerberus_planet_names.txt",
        mod_root() / "common" / "name_lists" / "00_cerberus_planet_names.txt",
        mod_root() / "common" / "name_lists" / "zz_cerberus_planet_names.txt",
        mod_root() / "common" / "namelists" / "cerberus_planet_names.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


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
    return re.sub(r"[^a-z0-9]", "", name.lower())


def canonical_words(name: str) -> str:
    return re.sub(r"[^a-z0-9\s]", "", name.lower()).strip()


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
        if right.startswith(("i", "o")):
            return left + right
        right = right[1:] or "i"

    return left + right


def clean_constructed(raw: str) -> str:
    raw = normalize_name(raw)
    raw = re.sub(r"(.)\1\1+", r"\1\1", raw, flags=re.IGNORECASE)
    return raw


def load_blacklist(path: Path | None) -> set[str]:
    names = parse_quoted_names(CURRENT_CERBERUS_PLANET_NAMES_TEXT)

    if path is not None and path.exists():
        text = path.read_text(encoding="utf-8")
        names |= parse_quoted_names(text)

    names |= set(STYLE_SEEDS)
    return {canonical(x) for x in names if x}


def has_identity(name: str) -> bool:
    lower = canonical(name)
    return any(cluster in lower for cluster in IDENTITY_CLUSTERS)


def looks_too_plain_english(name: str) -> bool:
    lower_words = canonical_words(name).split()
    plain = {
        "base", "camp", "home", "world", "land", "star", "moon", "point",
        "center", "centre", "lab", "research", "command", "division", "sector"
    }
    return any(word in plain for word in lower_words)


def is_viable(name: str) -> bool:
    lower = canonical(name)
    if not (4 <= len(lower) <= 24):
        return False

    if vowel_groups(name) < 2 or vowel_groups(name) > 8:
        return False

    if re.search(r"[bcdfghjklmnpqrstvwxyz]{5}", lower):
        return False

    if re.search(r"(.)\1\1", lower):
        return False

    if looks_too_plain_english(name):
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

    segment_count = rng.choices([1, 2, 3], weights=[35, 45, 20], k=1)[0]
    for _ in range(segment_count):
        raw = fix_join(raw, weighted_choice(rng, CORES))
        if rng.random() < 0.35:
            raw = fix_join(raw, rng.choice(["a", "e", "i", "o", "y"]))

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

    if rng.random() < 0.55:
        raw = fix_join(raw, weighted_choice(rng, SUFFIXES))

    return clean_constructed(raw)


def make_two_word_name(rng: random.Random) -> str:
    first = make_single_word_name(rng)

    second_mode = rng.choices(
        ["title", "roman", "coded"],
        weights=[65, 20, 15],
        k=1,
    )[0]

    if second_mode == "title":
        second = weighted_choice(rng, SECOND_WORDS)
        return clean_constructed(f"{first} {second}")

    if second_mode == "roman":
        second = rng.choice(ROMAN_NUMERALS)
        return clean_constructed(f"{first} {second}")

    code = f"{rng.choice(['A', 'B', 'C', 'D', 'E', 'K', 'X'])}-{rng.randint(2, 9)}"
    return clean_constructed(f"{first} {code}")


def make_assignment_name(rng: random.Random) -> str:
    left = weighted_choice(rng, ASSIGNMENT_PREFIXES)
    joiner = weighted_choice(rng, ASSIGNMENT_JOINERS)

    base_mode = rng.choices(["word", "seed_blend", "serial"], weights=[60, 25, 15], k=1)[0]

    if base_mode == "word":
        right = make_single_word_name(rng)
    elif base_mode == "seed_blend":
        right = make_seed_blend_name(rng)
    else:
        right = f"{rng.choice(['T', 'K', 'R', 'X', 'N'])}{rng.randint(10, 99)}"

    if rng.random() < 0.18:
        right = f"{right}{joiner}{rng.choice(ROMAN_NUMERALS)}"

    return clean_constructed(f"{left}{joiner}{right}")


def make_candidate(rng: random.Random) -> str:
    mode = rng.choices(
        population=["single", "blend", "two_word", "assignment"],
        weights=[42, 18, 28, 12],
        k=1,
    )[0]

    for _ in range(1000):
        if mode == "single":
            candidate = make_single_word_name(rng)
        elif mode == "blend":
            candidate = make_seed_blend_name(rng)
        elif mode == "two_word":
            candidate = make_two_word_name(rng)
        else:
            candidate = make_assignment_name(rng)

        if is_viable(candidate):
            return candidate

    raise RuntimeError("Failed to generate a viable Cerberus planet-name candidate.")


def generate_cerberus_planet_names(
    count: int,
    seed: int | None = None,
    blacklist_path: Path | None = None,
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

        candidate = make_candidate(rng)
        key = canonical(candidate)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(candidate, blacklist | seen_local):
            continue

        seen_local.add(key)
        results.append(candidate)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique Cerberus planet names after {attempts} attempts."
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
            "Generate Cerberus-style planet / colony / station / facility names with a Greek-leaning, "
            "scientific-militarized tone, avoiding duplicates from an existing namelist file."
        )
    )
    parser.add_argument("--count", type=int, default=60, help="Number of names to generate. Default: 60")
    parser.add_argument("--seed", type=int, default=42, help="Random seed. Default: 42")
    parser.add_argument("--per-line", type=int, default=6, help="Names per output line. Default: 6")
    parser.add_argument(
        "--blacklist-file",
        type=Path,
        default=default_blacklist_path(),
        help="Optional namelist file to blacklist existing Cerberus names from.",
    )
    parser.add_argument(
        "--max-attempts-multiplier",
        type=int,
        default=30000,
        help="Attempt budget multiplier. Total attempts = count * multiplier. Default: 30000",
    )
    args = parser.parse_args()

    names = generate_cerberus_planet_names(
        count=args.count,
        seed=args.seed,
        blacklist_path=args.blacklist_file,
        max_attempts_multiplier=args.max_attempts_multiplier,
    )
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())
