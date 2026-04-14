#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path


QUOTED_STRING_RE = re.compile(r'"([^"]+)"')
WORD_RE = re.compile(r"[A-Za-z]+")
SHIP_PREFIX_RE = re.compile(r"^(?:PFS|THS|THV|SSV|JFV)\s+", re.IGNORECASE)
STOPWORDS = {"of", "the", "and"}
BLOCKED_ROOT_WORDS = {
    "accord", "algorithm", "amber", "archive", "array", "ash", "azure", "balance", "barren",
    "basin", "bay", "blackened", "blue", "book", "bright", "broker", "burned", "calm", "cinder",
    "civic", "cold", "contract", "convoy", "core", "credit", "current", "dead", "deep", "dividend",
    "dock", "drill", "dry", "dust", "echo", "emerald", "engine", "exchange", "extractor", "far",
    "fallen", "forge", "fortune", "foundry", "frame", "freight", "frozen", "gain", "gaze", "glacial",
    "gold", "golden", "great", "grey", "guard", "haven", "high", "hollow", "horizon", "ice",
    "index", "industrial", "jewel", "keeper", "lattice", "ledger", "lift", "logic", "long", "machine",
    "margin", "market", "matrix", "means", "measure", "meadow", "merchant", "mild", "militia", "node",
    "north", "observer", "open", "ore", "outer", "pale", "patrol", "peak", "planetary", "pressure",
    "prime", "processor", "profit", "prospect", "pure", "quiet", "reach", "reef", "register", "relief",
    "remote", "reserve", "rest", "return", "ridge", "rimed", "ruin", "ruined", "scar", "screen",
    "sea", "security", "settlement", "shield", "shining", "silent", "silver", "spine", "survey",
    "tariff", "treasury", "vault", "venture", "verdant", "vigil", "wall", "wake", "watch", "watcher",
    "witness", "works",
}

HONOR_SUFFIXES = [
    "aresh", "avar", "avel", "edor", "ekan", "elor", "emar", "enor", "eran",
    "eshar", "eth", "evor", "ian", "ikar", "ilan", "inar", "ior", "oran",
    "oren", "oris", "ovar", "uris", "vash", "ven", "vesh",
]

SECONDARY_ENDINGS = [
    "ban", "cal", "dao", "din", "for", "ker", "kur", "mar", "non", "olar",
    "osca", "sab", "ser", "shol", "tor", "tun", "wen", "yap",
]

INSERTS = ["r", "l", "n", "v", "s", "th", "sh", "sk", "vr", "lk", "nd", "rk", "zh"]


def parse_quoted_names(text: str) -> list[str]:
    return [match.group(1).strip() for match in QUOTED_STRING_RE.finditer(text) if match.group(1).strip()]


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def project_root() -> Path:
    return script_dir().parent


def default_volus_path() -> Path:
    return project_root() / "common" / "name_lists" / "13_MEG_Volus.txt"


def default_turian_path() -> Path:
    return project_root() / "common" / "name_lists" / "05_MEG_Turian.txt"


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def title_case(name: str) -> str:
    parts = normalize_spaces(name).split(" ")
    return " ".join(part[:1].upper() + part[1:].lower() for part in parts if part)


def canonical(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title_case(name).lower())


def strip_ship_prefix(name: str) -> str:
    return SHIP_PREFIX_RE.sub("", name).strip()


def normalize_word(word: str) -> str:
    return re.sub(r"[^A-Za-z]", "", word).lower()


def extract_block(text: str, label: str) -> str:
    match = re.search(rf"\b{re.escape(label)}\s*=\s*\{{", text)
    if not match:
        return ""
    start = match.end() - 1
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return ""


def extract_names_from_block(text: str, label: str) -> list[str]:
    block = extract_block(text, label)
    if not block:
        return []
    return parse_quoted_names(block)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_words(names: list[str]) -> list[str]:
    words: list[str] = []
    for name in names:
        bare = strip_ship_prefix(name)
        for word in WORD_RE.findall(bare):
            lower = normalize_word(word)
            if lower in STOPWORDS or lower in BLOCKED_ROOT_WORDS or len(lower) < 3:
                continue
            words.append(lower)
    return words


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = canonical(item)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(title_case(item))
    return result


def build_first_roots(volus_text: str) -> list[str]:
    names = (
        extract_names_from_block(volus_text, "first_names_male")
        + extract_names_from_block(volus_text, "first_names_female")
        + extract_names_from_block(volus_text, "full_names")
    )
    roots: list[str] = []
    for word in source_words(names):
        roots.append(word)
        if len(word) >= 5:
            roots.append(word[:-1])
    return [root for root in unique_preserve_order(roots) if len(normalize_word(root)) >= 4]


def build_second_roots(volus_text: str) -> list[str]:
    names = extract_names_from_block(volus_text, "second_names")
    roots: list[str] = []
    for word in source_words(names):
        roots.append(word)
        if len(word) >= 5:
            roots.append(word[:-1])
    return [root for root in unique_preserve_order(roots) if len(normalize_word(root)) >= 4]


def build_honor_roots(volus_text: str) -> list[str]:
    names = (
        extract_names_from_block(volus_text, "corvette")
        + extract_names_from_block(volus_text, "full_names")
        + extract_names_from_block(volus_text, "second_names")
    )
    roots: list[str] = []
    for word in source_words(names):
        roots.append(word)
        if len(word) >= 5:
            roots.append(word[:-1])
        if len(word) >= 6:
            roots.append(word[:-2])
    return [root for root in unique_preserve_order(roots) if len(normalize_word(root)) >= 4]


def build_foreign_roots(turian_text: str) -> list[str]:
    return [word for word in unique_preserve_order([word for word in source_words(parse_quoted_names(turian_text)) if len(word) >= 5])]


def clean_single(name: str) -> str:
    name = re.sub(r"[^A-Za-z]", "", name)
    name = re.sub(r"(.)\1\1+", r"\1\1", name)
    if not name:
        return ""
    return name[:1].upper() + name[1:].lower()


def build_generated_full_name(first_roots: list[str], second_roots: list[str], rng: random.Random) -> str:
    first = normalize_word(rng.choice(first_roots))
    second = normalize_word(rng.choice(second_roots))
    if len(first) > 5 and rng.random() < 0.55:
        first = first[:-1]
    if len(second) > 6 and rng.random() < 0.6:
        second = second[:-1]
    if rng.random() < 0.35:
        first += rng.choice(["a", "e", "i", "o"])
    if rng.random() < 0.25:
        second += rng.choice(["k", "r", "s", "n"])
    return title_case(f"{clean_single(first)} {clean_single(second)}")


def build_honor_name(honor_roots: list[str], rng: random.Random) -> str:
    left = normalize_word(rng.choice(honor_roots))
    right = normalize_word(rng.choice(honor_roots))
    left_cut = left[: rng.randint(2, min(5, len(left)))]
    right_cut = right[-rng.randint(2, min(5, len(right))):]
    return clean_single(left_cut + right_cut + rng.choice(HONOR_SUFFIXES))


def build_adapted_foreign(root: str, rng: random.Random) -> str:
    word = normalize_word(root)
    for suffix in ("orius", "arian", "ectus", "atus", "inus", "ian", "ius", "ion", "us", "is", "or", "on", "ax", "ix"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[:-len(suffix)]
            break
    if len(word) > 5 and rng.random() < 0.65:
        word = word[:-1]
    if rng.random() < 0.45:
        insert_at = rng.randint(1, max(1, len(word) - 1))
        word = word[:insert_at] + rng.choice(INSERTS) + word[insert_at:]
    word += rng.choice(HONOR_SUFFIXES)
    return clean_single(word)


def build_short_honor_pair(first_roots: list[str], second_roots: list[str], rng: random.Random) -> str:
    left = normalize_word(rng.choice(first_roots))
    right = normalize_word(rng.choice(second_roots))
    left = left[: rng.randint(2, min(4, len(left)))]
    right = right[-rng.randint(2, min(4, len(right))):]
    return title_case(f"{clean_single(left + rng.choice(['a', 'e', 'i']))} {clean_single(right + rng.choice(SECONDARY_ENDINGS))}")


def is_viable_single(name: str) -> bool:
    lower = name.lower()
    if not (7 <= len(name) <= 14):
        return False
    if re.search(r"[aeiouy]{3}", lower):
        return False
    if re.search(r"[bcdfghjklmnpqrstvwxyz]{4}", lower):
        return False
    return True


def load_blacklist(volus_text: str, turian_text: str) -> set[str]:
    all_names = parse_quoted_names(volus_text) + parse_quoted_names(turian_text)
    return {canonical(strip_ship_prefix(name)) for name in all_names}


def too_similar(candidate: str, used: set[str]) -> bool:
    key = canonical(candidate)
    for prior in used:
        if key == prior:
            return True
        if len(key) >= 8 and len(prior) >= 8 and key[:4] == prior[:4]:
            return True
        if SequenceMatcher(None, key, prior).ratio() >= 0.88:
            return True
    return False


def generate_names(
    count: int,
    seed: int | None = None,
    volus_path: Path | None = None,
    turian_path: Path | None = None,
) -> list[str]:
    rng = random.Random(seed)
    volus_text = load_text(volus_path or default_volus_path())
    turian_text = load_text(turian_path or default_turian_path())
    first_roots = build_first_roots(volus_text)
    second_roots = build_second_roots(volus_text)
    honor_roots = build_honor_roots(volus_text)
    foreign_roots = build_foreign_roots(turian_text)
    blacklist = load_blacklist(volus_text, turian_text)

    results: list[str] = []
    seen_local: set[str] = set()
    attempts = 0
    max_attempts = count * 26000

    while len(results) < count and attempts < max_attempts:
        attempts += 1
        mode = rng.choices(
            population=["full_name", "honor_name", "borrowed", "short_pair"],
            weights=[34, 30, 22, 14],
            k=1,
        )[0]

        if mode == "full_name":
            candidate = build_generated_full_name(first_roots, second_roots, rng)
        elif mode == "honor_name":
            candidate = build_honor_name(honor_roots, rng)
        elif mode == "borrowed":
            candidate = build_adapted_foreign(rng.choice(foreign_roots), rng)
        else:
            candidate = build_short_honor_pair(first_roots, second_roots, rng)

        if " " not in candidate and not is_viable_single(candidate):
            continue
        key = canonical(candidate)
        if key in blacklist or key in seen_local:
            continue
        if too_similar(candidate, blacklist | seen_local):
            continue
        seen_local.add(key)
        results.append(candidate)

    if len(results) < count:
        raise RuntimeError(f"Could only generate {len(results)} unique Volus cruiser names after {attempts} attempts.")
    return results


def format_as_array(names: list[str], per_line: int = 8) -> str:
    lines = ["["]
    for index in range(0, len(names), per_line):
        chunk = names[index:index + per_line]
        lines.append("    " + " ".join(f'"{name}"' for name in chunk))
    lines.append("]")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Volus cruiser names as prestige full names and honor-names, with a smaller adapted protectorate layer."
        )
    )
    parser.add_argument("--count", type=int, default=120, help="Number of names to generate. Default: 120")
    parser.add_argument("--seed", type=int, default=42, help="Random seed. Default: 42")
    parser.add_argument("--per-line", type=int, default=8, help="Names per line. Default: 8")
    parser.add_argument("--volus-file", type=Path, default=default_volus_path(), help="Volus source namelist.")
    parser.add_argument("--turian-file", type=Path, default=default_turian_path(), help="Turian source namelist.")
    args = parser.parse_args()

    names = generate_names(args.count, seed=args.seed, volus_path=args.volus_file, turian_path=args.turian_file)
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())
