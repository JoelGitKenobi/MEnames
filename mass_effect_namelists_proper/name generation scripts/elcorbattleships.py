#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path


QUOTED_STRING_RE = re.compile(r'"([^"]+)"')
PREFIX_RE = re.compile(r"^(?:JFV|PFS|THS|THV)\s+", re.IGNORECASE)

CURRENT_ELCOR_BATTLESHIPS_TEXT = r'''
"JFV Denaususnomun" "JFV Oribosanti" "JFV Wonnumetenro" "JFV Or-Gyclyn" "JFV Ralmonisuuk" "JFV Raxuu"
'''

# Style anchors from the known / lore-adjacent examples.
# The last three are mythic figures rather than firmly attested dreadnought hulls,
# but they are useful as tonal anchors.
STYLE_SEEDS = [
    "Denaususnomun",
    "Oribosanti",
    "Wonnumetenro",
    "Or-Gyclyn",
    "Ralmonisuuk",
    "Raxuu",
    "Moireturanum",   # continuation cruiser example, useful tonal anchor
    "Droriuntavilusium",  # continuation frigate example, useful tonal anchor
]

# Optional hard fences against obvious turian drift.
TURIANISH_ROOTS = {
    "taetr", "diger", "pheir", "gell", "goth", "parth", "edess", "baetik",
    "maced", "galat", "rocam", "bostr", "thrac", "epyr", "aeph", "tiber",
    "hav", "tor", "verr", "vict", "vaka", "arte", "pall", "kand", "chel",
    "fedo", "sept", "corvin", "latron", "param", "quarn", "daphn",
    "ciprit", "gythi", "perox", "palav", "menae", "trebia", "corinthe",
    "hieral", "castam", "taetri", "pheri", "gellar", "rocav", "hesper",
}

# Elcor-specific sound motor:
# long, weighty, resonant, often nasal / liquid / rounded, occasional harsh cluster.
ONSETS = [
    ("or", 8), ("ra", 7), ("wo", 6), ("de", 6), ("mo", 4), ("dro", 4),
    ("su", 5), ("nu", 5), ("ru", 5), ("xa", 4), ("za", 3), ("yo", 2),
    ("ka", 4), ("ko", 4), ("ta", 3), ("to", 3), ("la", 4), ("lo", 4),
    ("ma", 5), ("na", 5), ("ni", 4), ("no", 4), ("ri", 5), ("ro", 5),
    ("va", 3), ("vo", 3), ("ulu", 2), ("onu", 2), ("shi", 2), ("thu", 2),
]

NUCLEI = [
    ("a", 8), ("o", 7), ("u", 7), ("i", 4), ("e", 3),
    ("aa", 2), ("oo", 2), ("uu", 3), ("ai", 1), ("oa", 1), ("ou", 2),
    ("io", 2), ("ui", 2), ("uo", 2),
]

MEDIALS_LIGHT = [
    ("l", 5), ("r", 6), ("m", 5), ("n", 7), ("s", 4), ("v", 2),
    ("sh", 2), ("th", 2), ("k", 2), ("g", 2),
]

MEDIALS_HEAVY = [
    ("mon", 6), ("mun", 6), ("nom", 5), ("num", 5), ("suu", 4), ("suk", 4),
    ("bos", 3), ("san", 4), ("ten", 4), ("tur", 5), ("tar", 4), ("vil", 3),
    ("lyn", 4), ("cly", 2), ("gyc", 2), ("rian", 2), ("dor", 3), ("ran", 4),
    ("lum", 4), ("lis", 3), ("von", 3), ("ruk", 3), ("thon", 2), ("zuun", 2),
    ("wau", 2), ("rau", 2), ("sha", 2), ("nor", 3), ("los", 2), ("mir", 2),
]

CODAS = [
    ("n", 8), ("m", 6), ("r", 4), ("k", 3), ("s", 4), ("th", 2), ("x", 1), ("", 8)
]

ENDINGS = [
    ("uu", 5), ("uuk", 4), ("uun", 5), ("um", 8), ("un", 8), ("unom", 5),
    ("anti", 5), ("enti", 3), ("aro", 3), ("ero", 4), ("oro", 4),
    ("eti", 3), ("isi", 3), ("isium", 1), ("isuuk", 3), ("etenro", 2),
    ("eten", 3), ("iten", 2), ("ira", 2), ("iros", 1), ("osanti", 2),
    ("onum", 3), ("onium", 1), ("orum", 2), ("anum", 4), ("enum", 3),
    ("ulon", 2), ("avil", 2), ("usnomun", 2), ("nomun", 4), ("monun", 2),
    ("axuu", 2), ("xuu", 4), ("yclyn", 2),
]

PARTICLES = [
    ("Or", 9), ("Ul", 2), ("Ra", 2), ("Vo", 1), ("Na", 1)
]

# Identity clusters so the names stay in the same tonal family.
IDENTITY_CLUSTERS = {
    "uu", "uuk", "nom", "mun", "mon", "anti", "eten", "tenro", "suu",
    "suk", "lyn", "cly", "gyc", "xuu", "ral", "won", "ori", "dena", "num"
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
        mod_root() / "common" / "name_lists" / "05_MEG_Elcor.txt",
        mod_root() / "common" / "name_lists" / "05_MEG_Elcor_namelist.txt",
        mod_root() / "common" / "namelists" / "05_MEG_Elcor.txt",
        mod_root() / "common" / "namelists" / "05_MEG_Elcor_namelist.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def strip_prefix(name: str) -> str:
    return PREFIX_RE.sub("", name).strip()


def normalize_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z\-]", "", name)
    name = re.sub(r"-{2,}", "-", name).strip("-")
    if not name:
        return ""

    if "-" in name:
        parts = [p for p in name.split("-") if p]
        return "-".join(part[:1].upper() + part[1:].lower() for part in parts)

    return name[:1].upper() + name[1:].lower()


def canonical(name: str) -> str:
    return re.sub(r"[^a-z]", "", strip_prefix(name).lower())


def weighted_choice(rng: random.Random, pairs: list[tuple[str, int]]) -> str:
    items = [item for item, _ in pairs]
    weights = [weight for _, weight in pairs]
    return rng.choices(items, weights=weights, k=1)[0]


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

    # elcor names tolerate vowel adjacency more than the turian ones,
    # so soften it rather than always stripping it.
    if a in "aeiouy" and b in "aeiouy":
        if right.startswith(("u", "o")):
            return left + right
        right = right[1:] or "u"

    return left + right


def clean_constructed(raw: str) -> str:
    raw = normalize_name(raw)
    raw = re.sub(r"(.)\1\1+", r"\1\1", raw)
    return raw


def load_blacklist(path: Path | None) -> set[str]:
    names = {strip_prefix(x) for x in parse_quoted_names(CURRENT_ELCOR_BATTLESHIPS_TEXT)}

    if path is not None and path.exists():
        text = path.read_text(encoding="utf-8")
        names |= {strip_prefix(x) for x in parse_quoted_names(text)}

    names |= set(STYLE_SEEDS)
    return {canonical(x) for x in names if x}


def sounds_too_turian(name: str) -> bool:
    lower = canonical(name)
    return any(root in lower for root in TURIANISH_ROOTS)


def has_elcor_identity(name: str) -> bool:
    lower = canonical(name)
    return any(cluster in lower for cluster in IDENTITY_CLUSTERS)


def is_viable(name: str) -> bool:
    lower = canonical(name)
    length = len(lower)

    if not (5 <= length <= 18):
        return False

    if vowel_groups(name) < 2 or vowel_groups(name) > 7:
        return False

    if re.search(r"[bcdfghjklmnpqrstvwxyz]{5}", lower):
        return False

    if re.search(r"(.)\1\1", lower):
        return False

    # avoid obvious Latin / English war-title drift
    if lower.endswith(("tor", "torium", "ator", "us", "ix", "ant", "ent", "oria")):
        return False

    if sounds_too_turian(name):
        return False

    if not has_elcor_identity(name):
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


def mutate_vowels(raw: str, rng: random.Random) -> str:
    chars = list(raw)
    positions = [i for i, ch in enumerate(chars) if ch in "aeiou"]
    if positions and rng.random() < 0.35:
        pos = rng.choice(positions)
        chars[pos] = rng.choice(["a", "e", "i", "o", "u", "uu", "oo"])
    return "".join(chars)


def make_chain_name(rng: random.Random) -> str:
    raw = weighted_choice(rng, ONSETS)

    segment_count = rng.choices([2, 3, 4], weights=[20, 50, 30], k=1)[0]
    for _ in range(segment_count):
        raw = fix_join(raw, weighted_choice(rng, NUCLEI))
        raw = fix_join(raw, weighted_choice(rng, MEDIALS_HEAVY if rng.random() < 0.65 else MEDIALS_LIGHT))

    if rng.random() < 0.60:
        raw = fix_join(raw, weighted_choice(rng, CODAS))

    raw = fix_join(raw, weighted_choice(rng, ENDINGS))
    raw = mutate_vowels(raw, rng)
    return clean_constructed(raw)


def make_legendary_name(rng: random.Random) -> str:
    raw = weighted_choice(rng, ONSETS)
    raw = fix_join(raw, weighted_choice(rng, MEDIALS_HEAVY))
    raw = fix_join(raw, weighted_choice(rng, NUCLEI))
    raw = fix_join(raw, weighted_choice(rng, MEDIALS_HEAVY))
    raw = fix_join(raw, weighted_choice(rng, ENDINGS))
    return clean_constructed(raw)


def make_hyphenated_name(rng: random.Random) -> str:
    particle = weighted_choice(rng, PARTICLES)

    core = weighted_choice(rng, ONSETS)
    core = fix_join(core, weighted_choice(rng, MEDIALS_HEAVY))
    if rng.random() < 0.50:
        core = fix_join(core, weighted_choice(rng, NUCLEI))
    core = fix_join(core, weighted_choice(rng, ENDINGS))

    return clean_constructed(f"{particle}-{core}")


def make_seed_blend_name(rng: random.Random) -> str:
    a = rng.choice(STYLE_SEEDS)
    b = rng.choice(STYLE_SEEDS)
    while b == a:
        b = rng.choice(STYLE_SEEDS)

    a_clean = canonical(a)
    b_clean = canonical(b)

    a_cut = rng.randint(2, max(2, min(6, len(a_clean) - 2)))
    b_start = rng.randint(max(1, len(b_clean) // 2 - 1), max(2, len(b_clean) - 2))

    raw = a_clean[:a_cut] + b_clean[b_start:]
    if rng.random() < 0.55:
        raw = fix_join(raw, weighted_choice(rng, ENDINGS))

    return clean_constructed(raw)


def make_candidate(rng: random.Random) -> str:
    mode = rng.choices(
        population=["chain", "legendary", "hyphen", "seed_blend"],
        weights=[42, 28, 10, 20],
        k=1,
    )[0]

    for _ in range(1000):
        if mode == "chain":
            candidate = make_chain_name(rng)
        elif mode == "legendary":
            candidate = make_legendary_name(rng)
        elif mode == "hyphen":
            candidate = make_hyphenated_name(rng)
        else:
            candidate = make_seed_blend_name(rng)

        if is_viable(candidate):
            return candidate

    raise RuntimeError("Failed to generate a viable elcor battleship candidate.")


def generate_elcor_battleship_names(
    count: int,
    seed: int | None = None,
    blacklist_path: Path | None = None,
    include_prefix: bool = True,
) -> list[str]:
    rng = random.Random(seed)

    blacklist = load_blacklist(blacklist_path)
    results: list[str] = []
    seen_local: set[str] = set()

    attempts = 0
    max_attempts = count * 30000

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        bare = make_candidate(rng)
        key = canonical(bare)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(key, blacklist | seen_local):
            continue

        seen_local.add(key)
        results.append(f"JFV {bare}" if include_prefix else bare)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique Elcor battleship names after {attempts} attempts."
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
            "Generate constructible Elcor battleship/dreadnought names with a mythic native-name tone, "
            "using many small building blocks and avoiding Turian-style title drift."
        )
    )
    parser.add_argument("--count", type=int, default=60, help="Number of names to generate. Default: 60")
    parser.add_argument("--seed", type=int, default=42, help="Random seed. Default: 42")
    parser.add_argument("--per-line", type=int, default=6, help="Names per output line. Default: 6")
    parser.add_argument(
        "--blacklist-file",
        type=Path,
        default=default_blacklist_path(),
        help="Optional namelist file to blacklist existing Elcor names from.",
    )
    parser.add_argument(
        "--no-prefix",
        action="store_true",
        help="Output bare names without the JFV prefix.",
    )
    args = parser.parse_args()

    names = generate_elcor_battleship_names(
        count=args.count,
        seed=args.seed,
        blacklist_path=args.blacklist_file,
        include_prefix=not args.no_prefix,
    )
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())