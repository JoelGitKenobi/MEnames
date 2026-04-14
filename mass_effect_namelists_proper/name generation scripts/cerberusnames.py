#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path


QUOTED_STRING_RE = re.compile(r'"([^"]+)"')
NON_NAME_CHARS_RE = re.compile(r"[^A-Za-zÀ-ÿ'’\-\s]")
MULTISPACE_RE = re.compile(r"\s+")
MULTIHYPHEN_RE = re.compile(r"-{2,}")


CURRENT_CERBERUS_CHARACTER_NAMES_TEXT = r'''
"Jack Harper" "Miranda Lawson" "Kai Leng" "Jacob Taylor"
"Maya Brooks" "Oleg Petrovsky" "Henry Lawson" "Paul Grayson" "Eva Coré"
'''

STYLE_SEEDS = [
    "Jack Harper",
    "Miranda Lawson",
    "Kai Leng",
    "Jacob Taylor",
    "Maya Brooks",
    "Oleg Petrovsky",
    "Henry Lawson",
    "Paul Grayson",
    "Eva Coré",
]

EXISTING_FIRST_NAMES = {
    "Jack", "Miranda", "Kai", "Jacob", "Maya", "Oleg", "Henry", "Paul", "Eva"
}

EXISTING_LAST_NAMES = {
    "Harper", "Lawson", "Leng", "Taylor", "Brooks", "Petrovsky", "Grayson", "Coré"
}

# Human, international, Cerberus-suitable first-name building blocks.
FIRST_PREFIXES_MASC = [
    ("Ja", 5), ("Jac", 3), ("Jon", 2), ("Ka", 4), ("Ky", 2), ("Lu", 2),
    ("Ma", 4), ("Mae", 1), ("Mi", 3), ("Nik", 2), ("Ol", 3), ("Pa", 3),
    ("Ra", 2), ("Re", 2), ("Ro", 2), ("Ta", 2), ("Ty", 1), ("Vi", 1),
    ("Ad", 2), ("Al", 2), ("An", 2), ("Da", 2), ("De", 1), ("El", 1),
    ("Ga", 1), ("Le", 2), ("Mar", 1), ("Se", 1), ("Te", 1), ("Za", 1),
]

FIRST_CORES_MASC = [
    ("ck", 3), ("cob", 2), ("den", 1), ("el", 2), ("en", 3), ("ian", 2),
    ("ik", 2), ("ai", 3), ("am", 3), ("as", 3), ("att", 2), ("aul", 2),
    ("auld", 1), ("eg", 2), ("ek", 2), ("en", 3), ("er", 2), ("iel", 1),
    ("ob", 2), ("ol", 2), ("on", 2), ("or", 1), ("ul", 2), ("us", 1),
    ("ai", 2), ("ei", 1), ("len", 1), ("ren", 1), ("son", 1), ("ton", 1),
]

FIRST_SUFFIXES_MASC = [
    ("", 6), ("ael", 1), ("an", 3), ("ar", 2), ("as", 2), ("en", 4),
    ("er", 2), ("ias", 1), ("in", 3), ("is", 1), ("o", 2), ("on", 4),
    ("or", 2), ("us", 1), ("yn", 1),
]

FIRST_PREFIXES_FEM = [
    ("Mi", 4), ("Mir", 3), ("Ma", 5), ("May", 2), ("Ev", 3), ("El", 3),
    ("Al", 2), ("Am", 2), ("An", 3), ("Ara", 1), ("Ca", 2), ("Ce", 2),
    ("Cor", 2), ("Da", 1), ("Em", 2), ("Ir", 1), ("Ka", 2), ("La", 2),
    ("Li", 2), ("Lu", 1), ("Na", 2), ("No", 1), ("Ol", 1), ("Ra", 2),
    ("Sa", 2), ("Se", 2), ("Ta", 1), ("Val", 1), ("Vi", 2), ("Zha", 1),
]

FIRST_CORES_FEM = [
    ("a", 5), ("ai", 3), ("an", 3), ("and", 2), ("ara", 2), ("aya", 3),
    ("e", 3), ("el", 3), ("en", 2), ("era", 2), ("eva", 2), ("i", 1),
    ("ia", 5), ("ida", 1), ("ila", 2), ("ina", 4), ("ira", 3), ("isa", 2),
    ("iya", 1), ("ora", 2), ("ri", 2), ("rin", 2), ("sha", 2), ("ya", 3),
]

FIRST_SUFFIXES_FEM = [
    ("", 5), ("a", 6), ("ah", 1), ("e", 3), ("ea", 1), ("el", 2),
    ("ena", 2), ("ia", 5), ("ina", 4), ("ira", 2), ("is", 1), ("lyn", 1),
    ("ra", 2), ("sa", 1), ("ya", 2),
]

# Surname building blocks.
LAST_PREFIXES = [
    ("Har", 4), ("Law", 4), ("Gray", 3), ("Brook", 3), ("Pet", 2), ("Leng", 2),
    ("Tay", 3), ("Cor", 2), ("Ash", 2), ("Black", 2), ("Brenn", 2), ("Cross", 2),
    ("Dane", 1), ("Drex", 1), ("Ell", 1), ("Fal", 1), ("Fen", 1), ("Garr", 1),
    ("Hale", 2), ("Kade", 1), ("Keir", 1), ("Merc", 1), ("North", 2), ("Pry", 1),
    ("Reed", 2), ("Slo", 1), ("Stone", 2), ("Thorn", 2), ("Vale", 1), ("Ward", 2),
    ("West", 2), ("Voss", 1), ("Rook", 1), ("Dray", 1), ("Marl", 1), ("Kell", 1),
]

LAST_CORES = [
    ("er", 4), ("per", 2), ("son", 5), ("sen", 2), ("ton", 4), ("man", 2),
    ("ley", 4), ("lin", 2), ("lan", 2), ("len", 2), ("don", 2), ("mond", 1),
    ("monds", 1), ("ward", 2), ("well", 1), ("wood", 1), ("field", 1), ("ford", 2),
    ("croft", 1), ("brook", 2), ("grave", 1), ("graye", 1), ("gray", 2), ("son", 4),
    ("sky", 3), ("ovsky", 2), ("ev", 1), ("ova", 1), ("ovic", 1), ("evich", 1),
    ("rov", 1), ("rovsky", 2), ("kov", 1), ("kov", 1), ("rell", 1), ("rick", 1),
]

LAST_SUFFIXES = [
    ("", 7), ("s", 4), ("e", 2), ("er", 4), ("ers", 2), ("ey", 2), ("ian", 1),
    ("in", 2), ("ky", 2), ("ov", 1), ("ova", 1), ("sky", 3), ("son", 4),
    ("ton", 2), ("well", 1), ("wood", 1), ("worth", 1),
]

ACCENTABLE_ENDINGS = {
    "Core": "Coré",
    "Rene": "René",
    "Andre": "André",
    "Mate": "Maté",
}

FIRST_IDENTITY_CLUSTERS = {
    "jack", "mira", "kai", "jac", "maya", "oleg", "hen", "paul", "eva",
    "mir", "kay", "ole", "tay", "mar", "luc", "nik", "ara", "val"
}

LAST_IDENTITY_CLUSTERS = {
    "harp", "laws", "leng", "tayl", "brook", "petro", "gray", "core",
    "ward", "stone", "cross", "reed", "thorn", "west", "voss", "hale", "north"
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
        mod_root() / "common" / "name_lists" / "cerberus_character_names.txt",
        mod_root() / "common" / "name_lists" / "00_cerberus_character_names.txt",
        mod_root() / "common" / "name_lists" / "zz_cerberus_character_names.txt",
        mod_root() / "common" / "namelists" / "cerberus_character_names.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def weighted_choice(rng: random.Random, pairs: list[tuple[str, int]]) -> str:
    items = [item for item, _ in pairs]
    weights = [weight for _, weight in pairs]
    return rng.choices(items, weights=weights, k=1)[0]


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )


def normalize_spaces_and_hyphens(name: str) -> str:
    name = NON_NAME_CHARS_RE.sub("", name)
    name = MULTISPACE_RE.sub(" ", name).strip()
    name = MULTIHYPHEN_RE.sub("-", name)
    name = re.sub(r"\s*-\s*", "-", name)
    return name


def normalize_word(word: str) -> str:
    if not word:
        return ""
    if word.isupper() and len(word) <= 4:
        return word
    return word[:1].upper() + word[1:].lower()


def maybe_restore_accent(name: str) -> str:
    return ACCENTABLE_ENDINGS.get(name, name)


def normalize_name(name: str) -> str:
    name = normalize_spaces_and_hyphens(name)
    if not name:
        return ""

    parts = []
    for token in name.split(" "):
        if "-" in token:
            subparts = [normalize_word(x) for x in token.split("-") if x]
            token = "-".join(subparts)
        else:
            token = normalize_word(token)
        parts.append(maybe_restore_accent(token))

    return " ".join(parts).strip()


def canonical(name: str) -> str:
    lowered = strip_accents(name).lower()
    return re.sub(r"[^a-z]", "", lowered)


def split_full_names(full_names: set[str]) -> tuple[set[str], set[str]]:
    firsts: set[str] = set()
    lasts: set[str] = set()

    for full_name in full_names:
        parts = full_name.split()
        if len(parts) >= 2:
            firsts.add(parts[0])
            lasts.add(parts[-1])

    return firsts, lasts


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


def load_blacklists(path: Path | None) -> tuple[set[str], set[str]]:
    names = parse_quoted_names(CURRENT_CERBERUS_CHARACTER_NAMES_TEXT)

    if path is not None and path.exists():
        text = path.read_text(encoding="utf-8")
        names |= parse_quoted_names(text)

    names |= set(STYLE_SEEDS)

    parsed_firsts, parsed_lasts = split_full_names(names)

    first_blacklist = {canonical(x) for x in (parsed_firsts | EXISTING_FIRST_NAMES) if x}
    last_blacklist = {canonical(x) for x in (parsed_lasts | EXISTING_LAST_NAMES) if x}
    return first_blacklist, last_blacklist


def vowel_groups(name: str) -> int:
    return len(re.findall(r"[aeiouy]+", canonical(name)))


def has_identity(name: str, clusters: set[str]) -> bool:
    lower = canonical(name)
    return any(cluster in lower for cluster in clusters)


def is_viable_first_name(name: str) -> bool:
    lower = canonical(name)

    if not (3 <= len(lower) <= 12):
        return False

    if vowel_groups(name) < 1 or vowel_groups(name) > 5:
        return False

    if re.search(r"[bcdfghjklmnpqrstvwxyz]{5}", lower):
        return False

    if re.search(r"(.)\1\1", lower):
        return False

    if not has_identity(name, FIRST_IDENTITY_CLUSTERS):
        return False

    return True


def is_viable_last_name(name: str) -> bool:
    lower = canonical(name)

    if not (4 <= len(lower) <= 14):
        return False

    if vowel_groups(name) < 1 or vowel_groups(name) > 5:
        return False

    if re.search(r"[bcdfghjklmnpqrstvwxyz]{6}", lower):
        return False

    if re.search(r"(.)\1\1", lower):
        return False

    if not has_identity(name, LAST_IDENTITY_CLUSTERS):
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

        if len(key) >= 6 and len(other) >= 6 and key[:3] == other[:3] and key[-2:] == other[-2:]:
            return True

        if key_skel and key_skel == skeleton(other):
            return True

        if SequenceMatcher(None, key, other).ratio() >= 0.90:
            return True

    return False


def make_first_name(rng: random.Random) -> str:
    gender_mode = rng.choices(
        ["masc", "fem", "blend"],
        weights=[42, 42, 16],
        k=1,
    )[0]

    if gender_mode == "masc":
        raw = weighted_choice(rng, FIRST_PREFIXES_MASC)
        segment_count = rng.choices([1, 2], weights=[65, 35], k=1)[0]
        for _ in range(segment_count):
            raw = fix_join(raw, weighted_choice(rng, FIRST_CORES_MASC))
        if rng.random() < 0.6:
            raw = fix_join(raw, weighted_choice(rng, FIRST_SUFFIXES_MASC))

    elif gender_mode == "fem":
        raw = weighted_choice(rng, FIRST_PREFIXES_FEM)
        segment_count = rng.choices([1, 2], weights=[70, 30], k=1)[0]
        for _ in range(segment_count):
            raw = fix_join(raw, weighted_choice(rng, FIRST_CORES_FEM))
        if rng.random() < 0.7:
            raw = fix_join(raw, weighted_choice(rng, FIRST_SUFFIXES_FEM))

    else:
        raw = rng.choice([
            fix_join(weighted_choice(rng, FIRST_PREFIXES_MASC), weighted_choice(rng, FIRST_CORES_FEM)),
            fix_join(weighted_choice(rng, FIRST_PREFIXES_FEM), weighted_choice(rng, FIRST_CORES_MASC)),
        ])
        if rng.random() < 0.65:
            raw = fix_join(raw, rng.choice([
                weighted_choice(rng, FIRST_SUFFIXES_MASC),
                weighted_choice(rng, FIRST_SUFFIXES_FEM),
            ]))

    return clean_constructed(raw)


def make_first_name_from_seed_blend(rng: random.Random) -> str:
    seeds = list(EXISTING_FIRST_NAMES)
    a = canonical(rng.choice(seeds))
    b = canonical(rng.choice(seeds))
    while b == a:
        b = canonical(rng.choice(seeds))

    a_cut = rng.randint(2, max(2, min(4, len(a) - 1)))
    b_start = rng.randint(max(1, len(b) // 2 - 1), max(2, len(b) - 1))
    raw = a[:a_cut] + b[b_start:]
    return clean_constructed(raw)


def make_last_name(rng: random.Random) -> str:
    raw = weighted_choice(rng, LAST_PREFIXES)
    segment_count = rng.choices([1, 2], weights=[72, 28], k=1)[0]

    for _ in range(segment_count):
        raw = fix_join(raw, weighted_choice(rng, LAST_CORES))

    if rng.random() < 0.6:
        raw = fix_join(raw, weighted_choice(rng, LAST_SUFFIXES))

    return clean_constructed(raw)


def make_last_name_from_seed_blend(rng: random.Random) -> str:
    seeds = list(EXISTING_LAST_NAMES)
    a = canonical(rng.choice(seeds))
    b = canonical(rng.choice(seeds))
    while b == a:
        b = canonical(rng.choice(seeds))

    a_cut = rng.randint(2, max(2, min(5, len(a) - 1)))
    b_start = rng.randint(max(1, len(b) // 2 - 1), max(2, len(b) - 1))
    raw = a[:a_cut] + b[b_start:]
    return clean_constructed(raw)


def make_first_candidate(rng: random.Random) -> str:
    mode = rng.choices(["constructed", "seed_blend"], weights=[82, 18], k=1)[0]

    for _ in range(1000):
        candidate = make_first_name(rng) if mode == "constructed" else make_first_name_from_seed_blend(rng)
        if is_viable_first_name(candidate):
            return candidate

    raise RuntimeError("Failed to generate a viable Cerberus first-name candidate.")


def make_last_candidate(rng: random.Random) -> str:
    mode = rng.choices(["constructed", "seed_blend"], weights=[80, 20], k=1)[0]

    for _ in range(1000):
        candidate = make_last_name(rng) if mode == "constructed" else make_last_name_from_seed_blend(rng)
        if is_viable_last_name(candidate):
            return candidate

    raise RuntimeError("Failed to generate a viable Cerberus last-name candidate.")


def generate_first_names(
    count: int,
    rng: random.Random,
    blacklist: set[str],
    max_attempts_multiplier: int,
) -> list[str]:
    results: list[str] = []
    seen_local: set[str] = set()

    attempts = 0
    max_attempts = max(count * max_attempts_multiplier, 1000)

    while len(results) < count and attempts < max_attempts:
        attempts += 1
        candidate = make_first_candidate(rng)
        key = canonical(candidate)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(candidate, blacklist | seen_local):
            continue

        seen_local.add(key)
        results.append(candidate)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique Cerberus first names after {attempts} attempts."
        )

    return results


def generate_last_names(
    count: int,
    rng: random.Random,
    blacklist: set[str],
    max_attempts_multiplier: int,
) -> list[str]:
    results: list[str] = []
    seen_local: set[str] = set()

    attempts = 0
    max_attempts = max(count * max_attempts_multiplier, 1000)

    while len(results) < count and attempts < max_attempts:
        attempts += 1
        candidate = make_last_candidate(rng)
        key = canonical(candidate)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(candidate, blacklist | seen_local):
            continue

        seen_local.add(key)
        results.append(candidate)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique Cerberus last names after {attempts} attempts."
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
            "Generate Cerberus-style human character names as two separate lists: first names and last names. "
            "Avoids duplicates from an existing name list file."
        )
    )
    parser.add_argument("--first-count", type=int, default=40, help="Number of first names to generate. Default: 40")
    parser.add_argument("--last-count", type=int, default=60, help="Number of last names to generate. Default: 60")
    parser.add_argument("--seed", type=int, default=42, help="Random seed. Default: 42")
    parser.add_argument("--per-line", type=int, default=6, help="Names per output line. Default: 6")
    parser.add_argument(
        "--blacklist-file",
        type=Path,
        default=default_blacklist_path(),
        help="Optional character namelist file to blacklist existing Cerberus names from.",
    )
    parser.add_argument(
        "--max-attempts-multiplier",
        type=int,
        default=30000,
        help="Attempt budget multiplier. Total attempts = count * multiplier. Default: 30000",
    )
    args = parser.parse_args()

    first_blacklist, last_blacklist = load_blacklists(args.blacklist_file)
    rng = random.Random(args.seed)

    first_names = generate_first_names(
        count=args.first_count,
        rng=rng,
        blacklist=first_blacklist,
        max_attempts_multiplier=args.max_attempts_multiplier,
    )

    last_names = generate_last_names(
        count=args.last_count,
        rng=rng,
        blacklist=last_blacklist,
        max_attempts_multiplier=args.max_attempts_multiplier,
    )

    print("first_names = " + format_as_array(first_names, per_line=args.per_line))
    print()
    print("last_names = " + format_as_array(last_names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())