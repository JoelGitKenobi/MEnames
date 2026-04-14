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

CURRENT_BATTLESHIPS_TEXT = r'''
"THS Hierarchy Fist" "THS Indomitable" "THS Resolute" "THS Undaunted" "THS Invictus" "THS Victrix" "THS Triumphalis" "THS Vindicator"
"THS Judicator" "THS Tempestas" "THS Imperator" "THS Victor" "THS Gloria" "THS Vindicta" "THS Ultor" "THS Praeventor"
"THS Executor" "THS Gladiator" "THS Castellan" "THS Dominus" "THS Defiant" "THS Vigilant" "THS Unification" "THS Ascendant"
"THS Iron Standard" "THS Hierarchy's Due" "THS Shield of Trebia" "THS Spear of Menae" "THS Talon Ascendant" "THS Primarch's Will"
'''

# Keep battleships tonally separate from the other ship classes.
CORVETTE_FORBIDDEN_ROOTS = {
    "taetr", "diger", "pheir", "gell", "goth", "parth", "edess", "baetik",
    "maced", "galat", "rocam", "bostr", "thrac", "epyr", "aeph", "tiber",
    "castr", "pelag", "treb", "palav", "anap", "avent", "lacid", "vall",
    "cipr", "gyth", "taur", "hesper", "spaed", "perox", "caesis", "corvani"
}

FRIGATE_FORBIDDEN_ROOTS = {
    "hav", "tor", "verr", "victus", "vakar", "arter", "pall", "kandr", "chel",
    "fedor", "septim", "corvin", "latron", "sidon", "spart", "partin", "quarn",
    "param", "koril", "irvin", "ravid", "daphn", "ursin"
}

DESTROYER_FORBIDDEN_ROOTS = {
    "irat", "kasat", "elur", "quinc", "lupir", "indril", "canlin", "ignac",
    "seim", "caena", "protac", "victol", "hort", "senria", "velin", "bellan",
    "eudon", "adjun", "calpod", "regip", "flot", "furip", "cices", "posmi",
    "heri", "potv", "galgi", "murm", "cnaen", "kaem", "capir", "vibir", "dardar"
}

CRUISER_FORBIDDEN_ROOTS = {
    "ciprit", "gythi", "perox", "palav", "menae", "trebia", "appar", "corinth",
    "hieral", "castam", "taetri", "diger", "pheri", "gellar", "rocav", "galat",
    "epyr", "bostr", "carthen", "quadir", "syglar", "thrac", "maced", "baetik",
    "gothan", "parthen", "edessor", "solian", "hesper", "corvani", "tauren",
    "primor", "turiava", "vallonis", "spaedra"
}

# Battleship one-word titles are built from many small pieces but kept readable.
TITLE_FAMILIES: list[tuple[str, list[tuple[str, int]]]] = [
    ("Indomit", [("able", 8), ("or", 1), ("rix", 1)]),
    ("Resolut", [("e", 8), ("ion", 2)]),
    ("Invict", [("us", 7), ("or", 2), ("rix", 1)]),
    ("Victr", [("ix", 8), ("or", 2)]),
    ("Triumph", [("alis", 7), ("or", 1), ("ant", 2)]),
    ("Vindic", [("ator", 7), ("or", 2), ("ta", 1)]),
    ("Judic", [("ator", 7), ("ant", 2), ("ium", 1)]),
    ("Tempest", [("as", 6), ("or", 1), ("ate", 3)]),
    ("Imper", [("ator", 8), ("ium", 1), ("ial", 1)]),
    ("Vict", [("or", 6), ("rix", 2), ("us", 2)]),
    ("Glor", [("ia", 6), ("ium", 1), ("iant", 3)]),
    ("Vindict", [("a", 7), ("or", 2), ("um", 1)]),
    ("Ult", [("or", 8), ("rix", 1), ("us", 1)]),
    ("Praevent", [("or", 8), ("rix", 1), ("ium", 1)]),
    ("Execu", [("tor", 8), ("trix", 1), ("tion", 1)]),
    ("Gladi", [("ator", 8), ("us", 2)]),
    ("Castell", [("an", 6), ("um", 2), ("or", 2)]),
    ("Domin", [("us", 7), ("ion", 2), ("ator", 1)]),
    ("Defi", [("ant", 8), ("ance", 2)]),
    ("Vigil", [("ant", 8), ("ance", 2)]),
    ("Unificat", [("ion", 8), ("or", 2)]),
    ("Ascend", [("ant", 8), ("ancy", 2)]),
    ("Praesid", [("ium", 7), ("or", 2), ("ial", 1)]),
    ("Mandat", [("or", 6), ("um", 3), ("e", 1)]),
    ("Custod", [("ian", 5), ("or", 3), ("ium", 2)]),
    ("Fortit", [("ude", 6), ("or", 2), ("as", 2)]),
    ("Sentin", [("el", 8), ("or", 2)]),
    ("Tribun", [("al", 8), ("e", 1), ("or", 1)]),
    ("Primarch", [("al", 4), ("ate", 4), ("ion", 2)]),
    ("Aegid", [("or", 5), ("ium", 3), ("us", 2)]),
    ("Rect", [("or", 8), ("rix", 2)]),
]

TITLE_PREFIXES = [
    ("In", 2), ("Im", 2), ("Inv", 5), ("Vic", 4), ("Vind", 5), ("Jud", 4),
    ("Prae", 5), ("Ex", 2), ("Cast", 3), ("Dom", 4), ("Ult", 3), ("Tri", 5),
    ("Glor", 4), ("Resol", 3), ("Asc", 3), ("Vig", 3), ("Def", 3), ("Unif", 2),
    ("Imper", 4), ("Praes", 2), ("Fort", 2), ("Sent", 2), ("Mand", 2), ("Cust", 2),
    ("Rect", 1), ("Aeg", 1),
]

TITLE_CORES = [
    ("ict", 4), ("dict", 3), ("vict", 4), ("vent", 4), ("secut", 2), ("domin", 4),
    ("judic", 4), ("vindic", 5), ("gladi", 4), ("glor", 3), ("imper", 4),
    ("resolut", 4), ("ascend", 4), ("vigil", 4), ("defian", 4), ("unificat", 3),
    ("praevent", 4), ("castell", 3), ("triumph", 4), ("praesid", 3), ("fortit", 2),
    ("mandat", 3), ("custod", 2), ("rect", 2), ("tribun", 2), ("sentin", 2),
]

TITLE_SUFFIXES = [
    ("or", 8), ("ator", 6), ("itor", 3), ("ant", 5), ("ent", 4), ("alis", 4),
    ("us", 5), ("um", 3), ("ion", 4), ("rix", 2), ("ance", 2), ("ude", 1),
    ("ium", 2), ("e", 1), ("a", 1),
]

# Phrase-name pools. These are grammatical and institutional, not just cool+cool.
AUTHORITIES = [
    ("Hierarchy", 10), ("Primarch", 8), ("Palaven", 4), ("Trebia", 3), ("Menae", 3),
    ("Turiava", 2), ("Vallonis", 2), ("Corinthe", 2), ("Primoria", 2)
]

PLACES = [
    ("Trebia", 6), ("Menae", 6), ("Palaven", 5), ("Turiava", 3),
    ("Vallonis", 3), ("Corinthe", 3), ("Primoria", 2)
]

WEAPONS = [
    ("Fist", 8), ("Spear", 8), ("Shield", 8), ("Talon", 7), ("Hammer", 5),
    ("Lance", 5), ("Aegis", 6), ("Standard", 6), ("Banner", 4), ("Bulwark", 4),
    ("Pike", 2), ("Crown", 2)
]

RELICS = [
    ("Will", 8), ("Due", 6), ("Mandate", 8), ("Charge", 7), ("Judgment", 7),
    ("Edict", 7), ("Oath", 6), ("Command", 7), ("Claim", 5), ("Burden", 4),
    ("Sentence", 4), ("Directive", 4), ("Pledge", 4), ("Right", 5), ("Measure", 3),
    ("Tribune", 2), ("Writ", 3)
]

MATERIALS = [
    ("Iron", 8), ("Steel", 5), ("Brazen", 3), ("Stone", 2), ("High", 2), ("First", 2)
]

BANNER_NOUNS = [
    ("Standard", 9), ("Edict", 7), ("Mandate", 7), ("Aegis", 6), ("Banner", 5),
    ("Directive", 4), ("Order", 3)
]

STATES = [
    ("Ascendant", 7), ("Victorious", 4), ("Unbroken", 4), ("Resolute", 4),
    ("Implacable", 2), ("Imperial", 3)
]

CONNECTIVE_PARTS = [
    ("High", 2), ("First", 2), ("Final", 1), ("Iron", 3), ("Brazen", 1)
]

BATTLESHIP_IDENTITY = {
    "indom", "invict", "victr", "triumph", "vindic", "judic", "tempest",
    "imper", "glor", "ult", "praevent", "exec", "gladi", "castell", "domin",
    "defi", "vigil", "unificat", "ascend", "mandat", "primarch", "hierarchy",
    "shield", "spear", "talon", "standard", "edict", "aegis", "will", "due"
}


def parse_quoted_names(text: str) -> set[str]:
    return {m.group(1).strip() for m in QUOTED_STRING_RE.finditer(text) if m.group(1).strip()}


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


def normalize_word(name: str) -> str:
    name = re.sub(r"[^A-Za-z]", "", name)
    if not name:
        return ""
    return name[:1].upper() + name[1:].lower()


def canonical(name: str) -> str:
    return re.sub(r"[^a-z]", "", strip_prefix(name).lower())


def weighted_choice(rng: random.Random, pairs: list[tuple[str, int]]) -> str:
    items = [item for item, _ in pairs]
    weights = [weight for _, weight in pairs]
    return rng.choices(items, weights=weights, k=1)[0]


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


def clean_title(raw: str) -> str:
    raw = normalize_word(raw)
    raw = re.sub(r"(.)\1\1+", r"\1\1", raw)
    return raw


def parse_current_bare_names() -> set[str]:
    return {strip_prefix(x) for x in parse_quoted_names(CURRENT_BATTLESHIPS_TEXT)}


def load_blacklist(path: Path | None) -> set[str]:
    names = parse_current_bare_names()

    if path is not None and path.exists():
        text = path.read_text(encoding="utf-8")
        names |= {strip_prefix(x) for x in parse_quoted_names(text)}

    return {canonical(x) for x in names if x}


def sounds_like_other_class(text: str) -> bool:
    lower = text.lower()
    if any(root in lower for root in CORVETTE_FORBIDDEN_ROOTS):
        return True
    if any(root in lower for root in FRIGATE_FORBIDDEN_ROOTS):
        return True
    if any(root in lower for root in DESTROYER_FORBIDDEN_ROOTS):
        return True
    if any(root in lower for root in CRUISER_FORBIDDEN_ROOTS):
        return True
    return False


def has_battleship_identity(name: str) -> bool:
    lower = canonical(name)
    return any(x in lower for x in BATTLESHIP_IDENTITY)


def vowel_groups(name: str) -> int:
    return len(re.findall(r"[aeiouy]+", canonical(name)))


def make_family_title(rng: random.Random) -> str:
    root, suffixes = rng.choice(TITLE_FAMILIES)
    title = clean_title(root + weighted_choice(rng, suffixes))
    return title


def make_blended_title(rng: random.Random) -> str:
    left = weighted_choice(rng, TITLE_PREFIXES)
    core = weighted_choice(rng, TITLE_CORES)
    suffix = weighted_choice(rng, TITLE_SUFFIXES)

    raw = fix_join(left, core)
    raw = fix_join(raw, suffix)
    return clean_title(raw)


def make_augmented_title(rng: random.Random) -> str:
    root, suffixes = rng.choice(TITLE_FAMILIES)
    raw = root

    if rng.random() < 0.35:
        raw = fix_join(raw, rng.choice(["r", "n", "t", "v", "l"]))

    if rng.random() < 0.35:
        positions = [i for i, ch in enumerate(raw.lower()) if ch in "aeiouy"]
        if positions:
            pos = rng.choice(positions)
            repl = rng.choice(["a", "e", "i", "o", "u", "ae"])
            raw = raw[:pos] + repl + raw[pos + 1:]

    raw = fix_join(raw, weighted_choice(rng, suffixes))
    return clean_title(raw)


def make_possessive_phrase(rng: random.Random) -> str:
    authority = weighted_choice(rng, AUTHORITIES)
    relic = weighted_choice(rng, RELICS)
    return f"{authority}'s {relic}"


def make_of_phrase(rng: random.Random) -> str:
    noun = weighted_choice(rng, WEAPONS if rng.random() < 0.65 else RELICS)
    place = weighted_choice(rng, PLACES)
    return f"{noun} of {place}"


def make_standard_phrase(rng: random.Random) -> str:
    material = weighted_choice(rng, MATERIALS)
    noun = weighted_choice(rng, BANNER_NOUNS)
    return f"{material} {noun}"


def make_state_phrase(rng: random.Random) -> str:
    noun = weighted_choice(rng, WEAPONS if rng.random() < 0.7 else RELICS)
    state = weighted_choice(rng, STATES)
    return f"{noun} {state}"


def make_authority_phrase(rng: random.Random) -> str:
    authority = "Hierarchy" if rng.random() < 0.7 else "Primarch"
    noun = weighted_choice(rng, WEAPONS)
    return f"{authority} {noun}"


def make_mandate_phrase(rng: random.Random) -> str:
    first = weighted_choice(rng, CONNECTIVE_PARTS)
    second = weighted_choice(rng, BANNER_NOUNS)
    return f"{first} {second}"


def make_phrase_name(rng: random.Random) -> str:
    mode = rng.choices(
        population=["possessive", "of", "standard", "state", "authority", "mandate"],
        weights=[28, 26, 18, 12, 8, 8],
        k=1,
    )[0]

    if mode == "possessive":
        return make_possessive_phrase(rng)
    if mode == "of":
        return make_of_phrase(rng)
    if mode == "standard":
        return make_standard_phrase(rng)
    if mode == "state":
        return make_state_phrase(rng)
    if mode == "authority":
        return make_authority_phrase(rng)
    return make_mandate_phrase(rng)


def is_phrase(name: str) -> bool:
    return " " in name


def phrase_word_count(name: str) -> int:
    return len(name.split())


def is_viable_title(name: str) -> bool:
    lower = canonical(name)

    if not (7 <= len(lower) <= 15):
        return False

    if vowel_groups(name) < 2 or vowel_groups(name) > 6:
        return False

    if re.search(r"[aeiouy]{4}", lower):
        return False

    if re.search(r"[bcdfghjklmnpqrstvwxyz]{5}", lower):
        return False

    if re.search(r"(.)\1\1", lower):
        return False

    if sounds_like_other_class(lower):
        return False

    # Keep battleship titles abstract / institutional, not citylike or surname-like.
    if lower.endswith(("ria", "oria", "onis", "eon", "aven", "ikon", "bia", "dra")):
        return False

    if lower.endswith(("rius", "rian", "inus", "aris", "ulus", "imus")):
        return False

    if not has_battleship_identity(name):
        return False

    return True


def is_viable_phrase(name: str) -> bool:
    lower = canonical(name)

    if phrase_word_count(name) < 2 or phrase_word_count(name) > 3:
        return False

    if sounds_like_other_class(lower):
        return False

    if not has_battleship_identity(name):
        return False

    # Avoid generic "cool word + cool word" output by only accepting grammatical patterns.
    valid = (
        re.fullmatch(r"[A-Za-z]+'s [A-Za-z]+", name)
        or re.fullmatch(r"[A-Za-z]+ of [A-Za-z]+", name)
        or re.fullmatch(r"[A-Za-z]+ [A-Za-z]+", name)
    )
    return bool(valid)


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


def make_candidate(rng: random.Random) -> str:
    mode = rng.choices(
        population=["family", "blended", "augmented", "phrase"],
        weights=[34, 22, 20, 24],
        k=1,
    )[0]

    for _ in range(800):
        if mode == "family":
            candidate = make_family_title(rng)
            if is_viable_title(candidate):
                return candidate
        elif mode == "blended":
            candidate = make_blended_title(rng)
            if is_viable_title(candidate):
                return candidate
        elif mode == "augmented":
            candidate = make_augmented_title(rng)
            if is_viable_title(candidate):
                return candidate
        else:
            candidate = make_phrase_name(rng)
            if is_viable_phrase(candidate):
                return candidate

    raise RuntimeError("Failed to generate a viable battleship candidate.")


def generate_battleship_names(
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
    max_attempts = count * 25000

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        bare = make_candidate(rng)
        key = canonical(bare)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(key, blacklist | seen_local):
            continue

        seen_local.add(key)
        results.append(f"THS {bare}" if include_prefix else bare)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique Turian battleship names after {attempts} attempts."
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
            "Generate lore-adjacent Turian battleship names with a heavy institutional tone, "
            "using many small building blocks while avoiding other class cadences."
        )
    )
    parser.add_argument("--count", type=int, default=60, help="Number of names to generate. Default: 60")
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
        help="Output bare names without the THS prefix.",
    )
    args = parser.parse_args()

    names = generate_battleship_names(
        count=args.count,
        seed=args.seed,
        blacklist_path=args.blacklist_file,
        include_prefix=not args.no_prefix,
    )
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())