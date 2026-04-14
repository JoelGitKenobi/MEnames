
#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import re
import sys


# Source-inspired seed names and general phonetic shape.
# No blacklist on purpose.

SEED_NAMES = [
    "Zymandis", "Hallaylise", "Haseriuldir", "Henalshiir", "Houllinor",
    "Carascadeil", "Cosindius", "Dandralyon", "Deealidahir", "Delaimanar",
    "Gassilisol", "Janellishean", "Laykalar", "Melanar", "Moisetsho",
    "Momorran", "Monestarj", "Ochai", "Qualateros", "Quylid",
    "Shalasti", "Stezenyn", "Tithmenani", "Whendiolynn", "Yarlmeknasi",
    "Zenarias", "Ziomat", "Ayurangliathu", "Beethyeel", "Flessinkyl",
    "Glaudioutartiou", "Kasumarba", "Nisandandantir", "Qunisalyod",
    "Syacindil", "Telosynzethar", "Tiyallania", "Ysses",
]

# Extra classical / literary bases for the "lop off first syllable" style.
BASE_NAMES = [
    "Ulysses", "Anastasius", "Aurelian", "Demetrius", "Valerian", "Coriolanus",
    "Cassian", "Octavian", "Isidore", "Eurydice", "Heliodorus", "Theodora",
    "Aemilian", "Iphigenia", "Evander", "Leonidas", "Melisande", "Ophelia",
    "Aurelius", "Cassiopeia", "Erasmus", "Horatio", "Lucian", "Oberon",
    "Persephone", "Theophilus", "Andromeda", "Calliope", "Dorian", "Lysander",
    "Meridian", "Orianna", "Pelagius", "Seraphine", "Tiberius", "Valentina",
    "Zenobia", "Ariadne", "Belladonna", "Celestine", "Damocles", "Elysian",
    "Fabian", "Galatea", "Hadrian", "Illyria", "Jovian", "Leandros",
    "Marcellus", "Nereida", "Orsino", "Phineas", "Quintilian", "Rhiannon",
    "Sylvanus", "Thelonius", "Umbriel", "Viridian", "Xanthe", "Ysabeau",
]

ONSETS = [
    "z", "s", "sh", "sy", "th", "t", "d", "l", "ly", "ll", "h", "hy",
    "wh", "w", "q", "qu", "k", "c", "ch", "m", "n", "ny", "r", "v",
    "y", "j", "g", "gl", "st", "sk", "x",
]

VOWELS = [
    "a", "e", "i", "o", "u", "y", "ae", "ai", "ea", "ei", "ia", "io",
    "oi", "ou", "ui", "yy", "aa", "ee",
]

MEDIALS = [
    "l", "ll", "ly", "lsh", "ls", "ld", "ldr", "nd", "ndr", "n", "nn",
    "ns", "nth", "r", "rr", "rl", "rn", "rd", "rs", "rt", "sh", "ss",
    "st", "str", "sk", "sm", "th", "tr", "ty", "dyr", "dir", "ndar",
    "man", "mar", "shi", "she", "sol", "sid", "syn", "zan", "zi", "yl",
    "yd", "yon", "tar", "tor", "lin", "lor", "nar", "nir", "shiir", "lys",
]

SUFFIXES = [
    "is", "ys", "es", "as", "os", "us", "id", "yd", "ik", "yk", "il", "yl",
    "in", "yn", "ir", "yr", "or", "ar", "an", "ynn", "ior", "eil", "ean",
    "ian", "ius", "ios", "ion", "yon", "ael", "aen", "eth", "oth", "ath",
    "dir", "dir", "dys", "dil", "nar", "nor", "shiir", "sol", "sol", "tar",
]

MUTATION_VOWELS = {
    "a": ["a", "ae", "ai", "e"],
    "e": ["e", "ea", "i", "ae"],
    "i": ["i", "y", "ia", "e"],
    "o": ["o", "ou", "u", "io"],
    "u": ["u", "ou", "y", "o"],
    "y": ["y", "i", "yy", "e"],
}

LETTER_REPLACEMENTS = [
    ("ph", "f"),
    ("c", "k"),
    ("x", "z"),
    ("v", "w"),
    ("qu", "q"),
    ("th", "t"),
    ("s", "ss"),
    ("i", "y"),
    ("e", "ae"),
]


def normalize(name: str) -> str:
    name = re.sub(r"[^A-Za-z]", "", name)
    if not name:
        return ""
    return name[0].upper() + name[1:]


def has_vowel(s: str) -> bool:
    return any(ch in "aeiouyAEIOUY" for ch in s)


def lop_first_syllable(name: str, rng: random.Random) -> str:
    s = re.sub(r"[^A-Za-z]", "", name)
    if len(s) < 5:
        return normalize(s)

    lower = s.lower()

    # Build several cut candidates and pick one.
    cuts: list[int] = []

    # Cut after first vowel cluster.
    i = 0
    while i < len(lower) and lower[i] not in "aeiouy":
        i += 1
    while i < len(lower) and lower[i] in "aeiouy":
        i += 1
    if 1 < i < len(lower) - 2:
        cuts.append(i)

    # Cut after first vowel cluster + one consonant.
    j = i
    if j < len(lower) and lower[j] not in "aeiouy":
        j += 1
        if j < len(lower) - 2:
            cuts.append(j)

    # Conservative 2-char / 3-char cuts.
    if len(lower) > 5:
        cuts.append(2)
    if len(lower) > 6:
        cuts.append(3)

    candidates = []
    for cut in cuts:
        piece = normalize(s[cut:])
        if 4 <= len(piece) <= 14 and has_vowel(piece):
            candidates.append(piece)

    if not candidates:
        return normalize(s)

    return rng.choice(candidates)


def mutate_name(name: str, rng: random.Random) -> str:
    s = name.lower()

    # Apply 1-3 mutations.
    for _ in range(rng.randint(1, 3)):
        mode = rng.choice(["replace", "vowel", "double", "drop", "insert"])

        if mode == "replace":
            old, new = rng.choice(LETTER_REPLACEMENTS)
            if old in s:
                s = s.replace(old, new, 1)

        elif mode == "vowel":
            positions = [i for i, ch in enumerate(s) if ch in MUTATION_VOWELS]
            if positions:
                pos = rng.choice(positions)
                repl = rng.choice(MUTATION_VOWELS[s[pos]])
                s = s[:pos] + repl + s[pos + 1:]

        elif mode == "double" and len(s) > 3:
            positions = [i for i, ch in enumerate(s[:-1]) if ch.isalpha() and ch not in "aeiou"]
            if positions:
                pos = rng.choice(positions)
                s = s[:pos] + s[pos] + s[pos:]

        elif mode == "drop" and len(s) > 5:
            pos = rng.randrange(1, len(s) - 1)
            s = s[:pos] + s[pos + 1:]

        elif mode == "insert":
            pos = rng.randrange(1, len(s))
            insert = rng.choice(["a", "e", "i", "y", "l", "n", "r", "sh", "th"])
            s = s[:pos] + insert + s[pos:]

    s = normalize(s)
    if not (4 <= len(s) <= 14):
        return normalize(name)
    return s


def blend_names(a: str, b: str, rng: random.Random) -> str:
    a = re.sub(r"[^A-Za-z]", "", a)
    b = re.sub(r"[^A-Za-z]", "", b)

    if len(a) < 4 or len(b) < 4:
        return normalize(a or b)

    cut_a = rng.randint(max(2, len(a) // 3), max(2, (2 * len(a)) // 3))
    cut_b = rng.randint(max(1, len(b) // 4), max(2, len(b) // 2))

    candidate = normalize(a[:cut_a] + b[cut_b:])
    if not (4 <= len(candidate) <= 14):
        candidate = normalize(a[:-2] + b[-4:])
    return candidate


def phonetic_name(rng: random.Random) -> str:
    parts = [rng.choice(ONSETS), rng.choice(VOWELS)]

    syllables = rng.choices([1, 2, 3], weights=[20, 55, 25], k=1)[0]
    for _ in range(syllables):
        parts.append(rng.choice(MEDIALS))
        parts.append(rng.choice(VOWELS))

    parts.append(rng.choice(SUFFIXES))
    candidate = normalize("".join(parts))

    if len(candidate) < 4:
        candidate += rng.choice(["is", "yn", "ar", "or"])
    if len(candidate) > 14:
        candidate = candidate[:14]

    return normalize(candidate)


def ornate_name(rng: random.Random) -> str:
    start = rng.choice(["Ha", "He", "Hi", "Ho", "Hu", "Qua", "Zy", "Xy", "Ly", "Sha", "The", "Ya"])
    middle_count = rng.choices([2, 3, 4], weights=[30, 50, 20], k=1)[0]
    bits = [start]

    for _ in range(middle_count):
        bits.append(rng.choice([
            "la", "le", "li", "lo", "ly", "na", "ne", "ni", "no", "ny",
            "ra", "re", "ri", "ro", "ry", "sha", "she", "shi", "sol",
            "the", "thi", "dir", "dar", "zor", "yal", "dio", "thar"
        ]))

    bits.append(rng.choice(["is", "yn", "or", "ar", "ean", "ius", "eth", "ael", "dir"]))
    candidate = normalize("".join(bits))
    if len(candidate) > 14:
        candidate = candidate[:14]
    return candidate


def generate_one(rng: random.Random) -> str:
    mode = rng.choices(
        ["lop", "mutate_seed", "blend", "phonetic", "ornate", "mutate_lop"],
        weights=[26, 18, 16, 22, 8, 10],
        k=1,
    )[0]

    if mode == "lop":
        base = rng.choice(BASE_NAMES + SEED_NAMES)
        return lop_first_syllable(base, rng)

    if mode == "mutate_seed":
        base = rng.choice(SEED_NAMES)
        return mutate_name(base, rng)

    if mode == "blend":
        a = rng.choice(SEED_NAMES + BASE_NAMES)
        b = rng.choice(SEED_NAMES + BASE_NAMES)
        while b == a:
            b = rng.choice(SEED_NAMES + BASE_NAMES)
        return blend_names(lop_first_syllable(a, rng), b, rng)

    if mode == "phonetic":
        return phonetic_name(rng)

    if mode == "ornate":
        return ornate_name(rng)

    if mode == "mutate_lop":
        base = rng.choice(BASE_NAMES)
        return mutate_name(lop_first_syllable(base, rng), rng)

    return phonetic_name(rng)


def generate_names(count: int, seed: int | None = None) -> list[str]:
    rng = random.Random(seed)
    results: list[str] = []
    used: set[str] = set()

    attempts = 0
    max_attempts = count * 4000

    while len(results) < count and attempts < max_attempts:
        attempts += 1
        candidate = generate_one(rng)
        candidate = normalize(candidate)

        if not candidate:
            continue
        if not (4 <= len(candidate) <= 14):
            continue
        if not re.fullmatch(r"[A-Z][a-zA-Z]+", candidate):
            continue
        if candidate in used:
            continue

        used.add(candidate)
        results.append(candidate)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique names after {attempts} attempts."
        )

    return results


def format_as_array(names: list[str], per_line: int = 12) -> str:
    lines = ["["]
    for i in range(0, len(names), per_line):
        chunk = names[i:i + per_line]
        lines.append("    " + " ".join(f'"{name}"' for name in chunk))
    lines.append("]")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Hanar face names.")
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--per-line", type=int, default=12)
    args = parser.parse_args()

    names = generate_names(args.count, seed=args.seed)
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())