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


SEED_ROOTS = [
    "Taetrus", "Digeris", "Pheiros", "Gellix", "Gothis", "Parthia", "Edessan",
    "Baetika", "Magna", "Macedyn", "Galatana", "Rocam", "Chatti", "Bostra",
    "Thracia", "Epyrus", "Aephus", "Tiberon", "Castrum", "Nicon", "Pelagia",
    "Trebia", "Menae", "Palaven", "Anapondus", "Aventen", "Caesis", "Lacidia",
    "Vallum", "Perox", "Cipritine", "Gythium", "Taetrian", "Digeron", "Pherion",
    "Taurena", "Corvani", "Hespera", "Vallonis", "Spaedra", "Ravuna", "Natanus",
]

# Kompakta, hårdare slut för mindre turianska skrov.
# Undviker mer "stora" och latin-tunga slut som -ium, -oria, -anus, -ae osv.
COMPACT_ENDINGS = [
    ("ac", 3), ("ad", 2), ("al", 4), ("an", 7), ("ar", 8), ("as", 5), ("ax", 6),
    ("ec", 2), ("el", 5), ("en", 8), ("er", 8), ("es", 5), ("ex", 5),
    ("ic", 4), ("id", 2), ("il", 3), ("in", 8), ("ir", 4), ("is", 8), ("ix", 8),
    ("oc", 1), ("ol", 2), ("on", 9), ("or", 8), ("os", 5),
    ("uc", 1), ("ul", 1), ("un", 4), ("ur", 4), ("us", 6), ("yx", 2),
]

HEAVY_ENDINGS = (
    "orium", "arian", "arium", "orius", "orias", "orian", "andus", "endus",
    "ondus", "tine", "thium", "gium", "phium", "eum", "eus", "ium", "ian",
    "iae", "aea", "oria", "oris", "anus", "enus", "ae", "ia", "io", "oa",
)

MANUAL_STARTS = {
    "ta", "tae", "taet", "di", "dig", "phe", "gel", "got", "par", "ede",
    "bae", "mac", "gal", "roc", "bos", "thr", "epy", "aep", "tib", "cas",
    "nic", "pel", "tre", "men", "pal", "ana", "ave", "cae", "lac", "val",
    "per", "cip", "gyth", "tau", "cor", "hes", "spa", "rav", "nat", "sep",
    "can", "bel", "var", "pro", "ign", "reg",
}

MANUAL_MIDS = {
    "tr", "dr", "gr", "ct", "ph", "th", "vr", "nt", "rt", "st", "sk", "rk",
    "ll", "rr", "ss", "rn", "rd", "ric", "var", "tor", "dar", "ter", "ven",
    "len", "tir", "cal", "mer", "can", "gel", "vex", "pra", "sav", "cor",
    "gyr", "dor", "nar", "tas", "vyr", "kar", "rex", "tal",
}

MANUAL_TAILS = {
    "tr", "dr", "gr", "ct", "ph", "th", "nt", "rt", "rn", "rd", "ric", "tor",
    "dar", "ven", "len", "tir", "cor", "sav", "vyr", "kar", "tas",
}

VOWEL_MUTATIONS = {
    "a": ["a", "e", "ae"],
    "e": ["e", "i", "ae"],
    "i": ["i", "y", "e"],
    "o": ["o", "u"],
    "u": ["u", "o"],
    "y": ["y", "i"],
}

INSERT_CLUSTERS = ["r", "t", "n", "v", "l", "x", "ct", "tr", "dr", "gr", "th", "ph", "sk", "rt", "rk"]
HARD_START_BOOST = ("ta", "tre", "dig", "phe", "cas", "cor", "val", "rav", "cip", "gyth", "hes", "sep", "var")


def parse_quoted_names(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in QUOTED_STRING_RE.finditer(text)
        if match.group(1).strip()
    }


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def project_root() -> Path:
    return script_dir().parent


def default_blacklist_path() -> Path:
    return project_root() / "common" / "name_lists" / "05_MEG_Turian.txt"


def strip_prefix(name: str) -> str:
    return PREFIX_RE.sub("", name).strip()


def normalize(name: str) -> str:
    name = re.sub(r"[^A-Za-z]", "", name)
    if not name:
        return ""
    return name[0].upper() + name[1:].lower()


def canonical(name: str) -> str:
    return normalize(strip_prefix(name)).lower()


def vowel_groups(name: str) -> int:
    return len(re.findall(r"[aeiouy]+", name.lower()))


def weighted_choice(rng: random.Random, pairs: list[tuple[str, int]]) -> str:
    items = [item for item, _ in pairs]
    weights = [weight for _, weight in pairs]
    return rng.choices(items, weights=weights, k=1)[0]


def compact_ending(rng: random.Random) -> str:
    return weighted_choice(rng, COMPACT_ENDINGS)


def strip_heavy_ending(name: str) -> str:
    name = normalize(name)
    lower = name.lower()

    for suffix in sorted(HEAVY_ENDINGS, key=len, reverse=True):
        if lower.endswith(suffix) and len(name) - len(suffix) >= 4:
            return normalize(name[:-len(suffix)])

    # Lite konservativ fallback för vanlig loreform.
    for suffix in ("us", "um", "on", "or", "os", "is", "ix", "an", "en", "a", "e"):
        if lower.endswith(suffix) and len(name) - len(suffix) >= 4:
            return normalize(name[:-len(suffix)])

    return name


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


def is_viable(name: str) -> bool:
    lower = name.lower()
    length = len(name)

    if not (5 <= length <= 10):
        return False

    if vowel_groups(name) < 2 or vowel_groups(name) > 4:
        return False

    if re.search(r"[aeiouy]{3}", lower):
        return False

    if re.search(r"[bcdfghjklmnpqrstvwxyz]{4}", lower):
        return False

    if re.search(r"(.)\1\1", lower):
        return False

    if any(lower.endswith(suffix) for suffix in HEAVY_ENDINGS):
        return False

    # Corvette-känsla: undvik namn som slutar för öppet/mjukt.
    if lower.endswith(("a", "e", "ia", "ae", "io")):
        return False

    return True


def load_existing_bare_names(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()

    text = path.read_text(encoding="utf-8")
    names = {normalize(strip_prefix(name)) for name in parse_quoted_names(text)}
    return {name for name in names if name}


def build_style_sources(existing_bare: set[str]) -> list[str]:
    sources = set()

    for seed in SEED_ROOTS:
        sources.add(normalize(seed))
        sources.add(strip_heavy_ending(seed))

    for name in existing_bare:
        sources.add(normalize(name))
        sources.add(strip_heavy_ending(name))

    return sorted(x for x in sources if 4 <= len(x) <= 12)


def build_fragment_pools(style_sources: list[str]) -> tuple[list[str], list[str], list[str]]:
    starts: set[str] = set(MANUAL_STARTS)
    mids: set[str] = set(MANUAL_MIDS)
    tails: set[str] = set(MANUAL_TAILS)

    for source in style_sources:
        s = source.lower()
        if len(s) < 4:
            continue

        for n in (2, 3, 4):
            if len(s) >= n + 1:
                starts.add(s[:n])

        for i in range(1, max(2, len(s) - 2)):
            for n in (2, 3):
                if i + n <= len(s) - 1:
                    frag = s[i:i + n]
                    if not re.fullmatch(r"[aeiouy]+", frag):
                        mids.add(frag)

        for n in (2, 3, 4):
            if len(s) >= n + 1:
                tails.add(s[-n:])

    # Rensa extremt mjuka eller konstiga fragment.
    starts = {x for x in starts if re.fullmatch(r"[a-z]{2,4}", x)}
    mids = {x for x in mids if re.fullmatch(r"[a-z]{2,3}", x)}
    tails = {x for x in tails if re.fullmatch(r"[a-z]{2,4}", x)}

    return sorted(starts), sorted(mids), sorted(tails)


def load_blacklist(path: Path | None) -> set[str]:
    blacklist: set[str] = set()

    existing_bare = load_existing_bare_names(path)
    blacklist |= {canonical(name) for name in existing_bare}

    # Blocka också rena lore-rötter och avskalade former, så listan faktiskt expanderas.
    blacklist |= {canonical(seed) for seed in SEED_ROOTS}
    blacklist |= {canonical(strip_heavy_ending(seed)) for seed in SEED_ROOTS}

    return {x for x in blacklist if x}


def mutate_root(root: str, rng: random.Random) -> str:
    s = root.lower()

    if len(s) >= 5 and rng.random() < 0.55:
        s = s[:-1]

    if len(s) >= 6 and rng.random() < 0.20:
        s = s[:-1]

    if rng.random() < 0.40:
        positions = [i for i, ch in enumerate(s) if ch in VOWEL_MUTATIONS]
        if positions:
            pos = rng.choice(positions)
            repl = rng.choice(VOWEL_MUTATIONS[s[pos]])
            s = s[:pos] + repl + s[pos + 1:]

    if rng.random() < 0.30:
        pos = rng.randint(1, max(1, len(s) - 1))
        s = s[:pos] + rng.choice(INSERT_CLUSTERS) + s[pos:]

    if rng.random() < 0.20 and len(s) > 5:
        pos = rng.randint(1, len(s) - 2)
        s = s[:pos] + s[pos + 1:]

    return clean_name(s)


def make_clipped_name(style_sources: list[str], rng: random.Random) -> str:
    base = strip_heavy_ending(rng.choice(style_sources))

    if rng.random() < 0.65 and len(base) > 5:
        base = base[:-rng.choice([1, 1, 2])]

    if rng.random() < 0.22 and len(base) >= 4:
        base = fix_join(base, rng.choice(["r", "t", "v", "l", "th", "ph"]))

    raw = fix_join(base, compact_ending(rng))
    return clean_name(raw)


def make_blended_name(style_sources: list[str], rng: random.Random) -> str:
    a = strip_heavy_ending(rng.choice(style_sources))
    b = strip_heavy_ending(rng.choice(style_sources))

    while b == a:
        b = strip_heavy_ending(rng.choice(style_sources))

    a_cut = rng.randint(2, max(2, min(4, len(a) - 2)))
    b_start = rng.randint(max(1, len(b) // 2 - 1), max(2, len(b) - 2))

    raw = a[:a_cut] + b[b_start:]

    if rng.random() < 0.75:
        raw = fix_join(raw, compact_ending(rng))

    return clean_name(raw)


def make_fragment_name(starts: list[str], mids: list[str], tails: list[str], rng: random.Random) -> str:
    raw = rng.choice(starts)

    mid_count = rng.choices([0, 1, 2, 3], weights=[20, 45, 28, 7], k=1)[0]
    for _ in range(mid_count):
        raw = fix_join(raw, rng.choice(mids))

    if rng.random() < 0.55:
        raw = fix_join(raw, rng.choice(tails))

    raw = fix_join(raw, compact_ending(rng))
    return clean_name(raw)


def make_mutated_name(style_sources: list[str], rng: random.Random) -> str:
    base = strip_heavy_ending(rng.choice(style_sources))
    raw = mutate_root(base, rng)

    if rng.random() < 0.80:
        raw = fix_join(raw, compact_ending(rng))

    return clean_name(raw)


def make_echo_name(existing_bare: set[str], rng: random.Random) -> str:
    base = strip_heavy_ending(rng.choice(sorted(existing_bare or set(SEED_ROOTS))))
    lower = base.lower()

    if len(lower) >= 6:
        left = lower[:rng.randint(2, 4)]
        mid_start = rng.randint(1, max(1, len(lower) - 3))
        mid = lower[mid_start:mid_start + rng.choice([2, 3])]
        raw = fix_join(left, mid)
    else:
        raw = lower

    if rng.random() < 0.35:
        raw = fix_join(raw, rng.choice(["tr", "dr", "ct", "ph", "th", "vr", "nt"]))

    raw = fix_join(raw, compact_ending(rng))
    return clean_name(raw)


def make_candidate(
    existing_bare: set[str],
    style_sources: list[str],
    starts: list[str],
    mids: list[str],
    tails: list[str],
    rng: random.Random,
) -> str:
    mode = rng.choices(
        population=["clipped", "blended", "fragment", "mutated", "echo"],
        weights=[28, 20, 26, 14, 12],
        k=1,
    )[0]

    for _ in range(300):
        if mode == "clipped":
            candidate = make_clipped_name(style_sources, rng)
        elif mode == "blended":
            candidate = make_blended_name(style_sources, rng)
        elif mode == "fragment":
            candidate = make_fragment_name(starts, mids, tails, rng)
        elif mode == "mutated":
            candidate = make_mutated_name(style_sources, rng)
        else:
            candidate = make_echo_name(existing_bare, rng)

        if is_viable(candidate):
            return candidate

    raise RuntimeError("Failed to generate a viable candidate.")


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

        if len(key) >= 5 and len(other) >= 5 and key[:3] == other[:3] and key[-2:] == other[-2:]:
            return True

        if key_skel and key_skel == skeleton(other):
            return True

        if abs(len(key) - len(other)) <= 1 and SequenceMatcher(None, key, other).ratio() >= 0.88:
            return True

    return False


def generate_corvette_names(
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
    max_attempts = count * 15000

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        bare = make_candidate(existing_bare, style_sources, starts, mids, tails, rng)
        key = canonical(bare)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(key, blacklist | seen_local):
            continue

        seen_local.add(key)
        results.append(f"PFS {bare}" if include_prefix else bare)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique Turian corvette names after {attempts} attempts."
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
            "Generate compact, lore-adjacent Turian corvette names with blacklist checking "
            "against the actual namelist file."
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

    names = generate_corvette_names(
        args.count,
        seed=args.seed,
        blacklist_path=args.blacklist_file,
        include_prefix=not args.no_prefix,
    )
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())