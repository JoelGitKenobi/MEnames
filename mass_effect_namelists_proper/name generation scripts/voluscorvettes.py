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

VOLUS_ENDINGS = [
    "ban", "cal", "dao", "din", "for", "ker", "kur", "mar", "non", "olar",
    "orun", "osca", "sab", "ser", "shol", "tor", "tun", "urun", "varr",
    "vol", "wen", "yap",
]

LIQUID_INSERTS = ["r", "l", "n", "v", "s", "th", "sh", "sk", "vr", "lk"]
VOWEL_SWAP = {"a": "e", "e": "a", "i": "e", "o": "u", "u": "o", "y": "i"}


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


def build_native_roots(volus_text: str) -> list[str]:
    names = (
        extract_names_from_block(volus_text, "corvette")
        + extract_names_from_block(volus_text, "full_names")
        + extract_names_from_block(volus_text, "first_names_male")
        + extract_names_from_block(volus_text, "first_names_female")
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
    names = parse_quoted_names(turian_text)
    roots: list[str] = []
    for word in source_words(names):
        if len(word) < 4:
            continue
        roots.append(word)
    return unique_preserve_order(roots)


def build_fragments(roots: list[str]) -> tuple[list[str], list[str], list[str]]:
    starts: set[str] = set()
    middles: set[str] = set()
    ends: set[str] = set(VOLUS_ENDINGS)
    for root in roots:
        plain = normalize_word(root)
        if len(plain) < 3:
            continue
        for size in (2, 3, 4):
            if len(plain) >= size:
                starts.add(plain[:size])
                ends.add(plain[-size:])
        for index in range(1, len(plain) - 1):
            for size in (2, 3):
                if index + size <= len(plain) - 1:
                    frag = plain[index:index + size]
                    middles.add(frag)
    starts = {value for value in starts if re.fullmatch(r"[a-z]{2,4}", value)}
    middles = {value for value in middles if re.fullmatch(r"[a-z]{2,3}", value)}
    ends = {value for value in ends if re.fullmatch(r"[a-z]{2,5}", value)}
    return sorted(starts), sorted(middles), sorted(ends)


def clean_single(name: str) -> str:
    name = re.sub(r"[^A-Za-z]", "", name)
    name = re.sub(r"(.)\1\1+", r"\1\1", name)
    if not name:
        return ""
    return name[:1].upper() + name[1:].lower()


def tweak_vowel(text: str, rng: random.Random) -> str:
    positions = [index for index, char in enumerate(text) if char in VOWEL_SWAP]
    if not positions:
        return text
    index = rng.choice(positions)
    return text[:index] + VOWEL_SWAP[text[index]] + text[index + 1:]


def volify_foreign_root(root: str, rng: random.Random) -> str:
    word = normalize_word(root)
    for suffix in ("ius", "ium", "ian", "aris", "anus", "orus", "orus", "us", "is", "or", "on", "ax", "ix"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[:-len(suffix)]
            break
    if len(word) > 5 and rng.random() < 0.6:
        word = word[:-1]
    if rng.random() < 0.45:
        word = tweak_vowel(word, rng)
    if rng.random() < 0.35:
        insert_at = rng.randint(1, max(1, len(word) - 1))
        word = word[:insert_at] + rng.choice(LIQUID_INSERTS) + word[insert_at:]
    word += rng.choice(VOLUS_ENDINGS)
    return clean_single(word)


def build_native_pair(roots: list[str], rng: random.Random) -> str:
    left = normalize_word(rng.choice(roots))
    right = normalize_word(rng.choice(roots))
    if len(left) > 5:
        left = left[: rng.randint(2, 4)]
    if len(right) > 5:
        right = right[-rng.randint(2, 5):]
    return title_case(f"{left} {right}")


def build_blend(roots: list[str], rng: random.Random) -> str:
    left = normalize_word(rng.choice(roots))
    right = normalize_word(rng.choice(roots))
    left_cut = left[: rng.randint(2, min(4, len(left)))]
    right_cut = right[-rng.randint(2, min(4, len(right))):]
    return clean_single(left_cut + right_cut)


def build_fragment_name(starts: list[str], middles: list[str], ends: list[str], rng: random.Random) -> str:
    raw = rng.choice(starts)
    for _ in range(rng.choices([1, 2, 3], weights=[35, 45, 20], k=1)[0]):
        raw += rng.choice(middles)
    raw += rng.choice(ends)
    return clean_single(raw)


def build_mutated_native(roots: list[str], rng: random.Random) -> str:
    root = normalize_word(rng.choice(roots))
    if len(root) >= 5 and rng.random() < 0.7:
        root = root[:-1]
    if rng.random() < 0.4:
        root = tweak_vowel(root, rng)
    if rng.random() < 0.35:
        insert_at = rng.randint(1, max(1, len(root) - 1))
        root = root[:insert_at] + rng.choice(LIQUID_INSERTS) + root[insert_at:]
    root += rng.choice(VOLUS_ENDINGS)
    return clean_single(root)


def is_viable_single(name: str) -> bool:
    lower = name.lower()
    if not (4 <= len(name) <= 10):
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
        if len(key) >= 6 and len(prior) >= 6 and key[:3] == prior[:3] and key[-2:] == prior[-2:]:
            return True
        if SequenceMatcher(None, key, prior).ratio() >= 0.9:
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
    native_roots = build_native_roots(volus_text)
    foreign_roots = build_foreign_roots(turian_text)
    starts, middles, ends = build_fragments(native_roots)
    blacklist = load_blacklist(volus_text, turian_text)

    results: list[str] = []
    seen_local: set[str] = set()
    attempts = 0
    max_attempts = count * 18000

    while len(results) < count and attempts < max_attempts:
        attempts += 1
        mode = rng.choices(
            population=["native_pair", "blend", "fragment", "mutated", "borrowed"],
            weights=[34, 18, 18, 18, 12],
            k=1,
        )[0]

        if mode == "native_pair":
            candidate = build_native_pair(native_roots, rng)
        elif mode == "blend":
            candidate = build_blend(native_roots, rng)
        elif mode == "fragment":
            candidate = build_fragment_name(starts, middles, ends, rng)
        elif mode == "mutated":
            candidate = build_mutated_native(native_roots, rng)
        else:
            candidate = volify_foreign_root(rng.choice(foreign_roots), rng)

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
        raise RuntimeError(f"Could only generate {len(results)} unique Volus corvette names after {attempts} attempts.")
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
            "Generate Volus corvette names by constructing native clan/place style names and a small "
            "protectorate-borrowed layer adapted from Turian roots."
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
