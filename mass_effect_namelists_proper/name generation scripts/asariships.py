#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path


QUOTED_STRING_RE = re.compile(r'"([^"]+)"')
PREFIX_RE = re.compile(r"^(?:ARV|PFS|THS|THV|JFV)\s+", re.IGNORECASE)

# Fallback style pool if no asari namelist file exists yet.
# Keep this representative, not exhaustive.
FALLBACK_STYLE_TEXT = r'''
"Oseros" "Malvaes" "Lipera" "Satanna" "Eleclae" "Sebane" "Leapnai" "Secana"
"Driria" "Falassa" "Miyadri" "Ithyra" "Saelira" "Vashira" "Illyra" "Nythera"
"Tessara" "Selyne" "Lysaria" "Thalara" "Rhyssia" "Aestira" "Mirellya" "Shalena"
"Aeshara" "Veloria" "Elyndra" "Thesyra" "Pelaris" "Maelena" "Viravara" "Irinara"
"Nysanora" "Shaerena" "Raelira" "Naethira" "Laelira" "Zaerena" "Pheralyra" "Raelyra"
"Monarch" "Aleria" "Nythara" "Thaesira" "Talyra" "Laeloria" "Gelasyra" "Lyravena"
"Shaetena" "Kelatesha" "Kyraphira" "Maevara" "Mirazeris" "Esamaris" "Vaelavara"
"Therathene" "Maephira" "Shaevessa" "Velathene" "Kelatena" "Raelatha" "Lyrasela"
"Cybaen" "Saeri" "Thasus" "Aesthira" "Velanthe" "Nyrassia" "Myritha" "Elarisse"
"Calystria" "Vaeloria" "Myralora" "Nyssoria" "Keloria" "Vaenyra" "Ariovessa"
"Velavenessa" "Nysamereth" "Telatevaris" "Pheravalis" "Ysapheria" "Kelalythia"
"Lyrapheria" "Kyrapheria" "Ahlatania" "Kilitea" "Cethyse" "Ceryphia" "Ishtharae"
"Sarekane" "Myrarix" "Benezia" "Thaloryn" "Aesharis" "Lethanira" "Celestria"
"Pherasia" "Infinite Reverie" "Radiant Horizon" "Luminous Oath" "Silent Exultation"
"Raerelessa" "Cyrapheria" "Celezorya" "Naepheria" "Pheravalora" "Aetharia"
"Pelanythessa" "Esavirania" "Kyratevaria" "Celephorane" "Myrayssoria"
"Destiny Ascension" "T'Soni" "T'Loak" "Thessia" "Illium" "Tevos"
'''

# English ceremonial words exist in your battleship pool, but generic output
# should only use them rarely and deliberately.
CEREMONIAL_ADJECTIVES = [
    ("Celestine", 4), ("Infinite", 3), ("Radiant", 3), ("Luminous", 3),
    ("Seraphic", 2), ("Eternal", 3), ("Sovereign", 2), ("Halcyon", 2),
    ("Timeless", 2), ("Silent", 2), ("Lucent", 2), ("Silver", 1),
    ("Resplendent", 3), ("Immaculate", 2), ("Transcendent", 3), ("Ascendant", 3),
    ("Serene", 3), ("Sublime", 2), ("Prismatic", 2), ("Ethereal", 3),
    ("Astral", 2), ("Empyrean", 2), ("Boundless", 2), ("Iridescent", 2),
    ("Undying", 2), ("Gilded", 2), ("Starlit", 2), ("Sacred", 2),
    ("Benevolent", 2), ("Exalted", 2), ("Hallowed", 2), ("Veiled", 1),
]

CEREMONIAL_NOUNS = [
    ("Grace", 4), ("Reverie", 3), ("Horizon", 3), ("Oath", 3),
    ("Crown", 2), ("Chorus", 2), ("Memory", 2), ("Covenant", 2),
    ("Promise", 2), ("Vigil", 2), ("Apotheosis", 1), ("Dominion", 1),
    ("Ascension", 3), ("Radiance", 3), ("Splendor", 2), ("Serenity", 3),
    ("Solace", 2), ("Eternity", 3), ("Aurora", 3), ("Zenith", 2),
    ("Elegy", 2), ("Anthem", 2), ("Aria", 3), ("Resonance", 2),
    ("Eminence", 2), ("Firmament", 2), ("Eclipse", 2), ("Destiny", 2),
    ("Requiem", 1), ("Benediction", 2), ("Cadence", 2), ("Vesper", 2),
]

CEREMONIAL_OF_NOUNS = [
    ("Stars", 4), ("Ages", 3), ("Thessia", 5), ("Light", 3),
    ("Dawn", 3), ("Eternity", 3), ("Silence", 2), ("Dreams", 3),
    ("the Matriarchs", 3), ("Twilight", 2), ("Athame", 4), ("Dusk", 2),
    ("Tides", 2), ("Aeons", 2), ("Memory", 2), ("the Goddess", 3),
    ("the Void", 2), ("the Deep", 2), ("Moons", 2), ("Night", 2),
    ("the Ancients", 2), ("a Thousand Suns", 1), ("Sorrows", 1),
]

CEREMONIAL_EPITHETS = [
    ("Ascending", 3), ("Resplendent", 3), ("Triumphant", 2), ("Reborn", 2),
    ("Unbroken", 2), ("Undying", 2), ("Transcendent", 2), ("Exalted", 2),
    ("Eternal", 2), ("Awakened", 1), ("Unchained", 1), ("Everlasting", 1),
    ("Unbowed", 1), ("Supreme", 1), ("Gloriana", 1), ("Invicta", 1),
]

CEREMONIAL_POSSESSORS = [
    ("Athame", 5), ("Thessia", 4), ("The Goddess", 3), ("The Matriarch", 3),
    ("Janiri", 2), ("Lucen", 2),
]

CEREMONIAL_STOPWORDS = {
    word for pool in (
        CEREMONIAL_ADJECTIVES, CEREMONIAL_NOUNS, CEREMONIAL_EPITHETS,
        CEREMONIAL_POSSESSORS,
    )
    for word, _ in pool
} | {
    word
    for phrase, _ in CEREMONIAL_OF_NOUNS
    for word in phrase.split()
} | {
    "Dawn", "Harmonic", "Symphonic", "Exultation", "the", "of", "a",
    "Who", "Where", "Beyond", "Before", "Among",
}

# Generic asari identity: soft, melodic, liquid, vowel-rich, light sibilance.
MANUAL_ONSETS = [
    ("ae", 3), ("aes", 4), ("ale", 3), ("ari", 5), ("ash", 4), ("ave", 4),
    ("cae", 5), ("cal", 5), ("cel", 6), ("cyr", 5), ("dae", 4), ("del", 5),
    ("ely", 4), ("eri", 5), ("esa", 5), ("gel", 5), ("ili", 4), ("iri", 6),
    ("ith", 4), ("kae", 3), ("kel", 5), ("kyr", 5), ("lae", 5), ("lir", 5),
    ("lys", 4), ("lyr", 6), ("mae", 5), ("mir", 5), ("myr", 6), ("nae", 4),
    ("nys", 6), ("pel", 4), ("pher", 6), ("rae", 5), ("rav", 3), ("rhen", 6),
    ("sae", 5), ("sael", 7), ("sel", 6), ("shae", 6), ("tal", 3), ("tel", 4),
    ("tey", 7), ("thal", 5), ("ther", 6), ("tir", 3), ("tyr", 6), ("ula", 2),
    ("vae", 4), ("vael", 7), ("vel", 7), ("vir", 5), ("vory", 3), ("ysa", 4),
    ("zae", 4),
]

NUCLEI = [
    ("a", 7), ("e", 7), ("i", 5), ("o", 2), ("u", 1),
    ("ae", 8), ("ea", 5), ("ei", 3), ("ia", 7), ("ie", 3),
    ("io", 2), ("oa", 1), ("oe", 1), ("ui", 1), ("y", 2)
]

MEDIALS = [
    ("l", 6), ("ll", 3), ("ly", 6), ("m", 3), ("n", 5), ("nn", 2),
    ("ph", 5), ("r", 5), ("rh", 2), ("rr", 2), ("s", 4), ("ss", 4),
    ("sh", 5), ("th", 6), ("v", 3), ("y", 2), ("z", 2),
    ("lyr", 4), ("neth", 5), ("phir", 4), ("ris", 3), ("ressa", 3),
    ("sel", 3), ("syr", 3), ("tesh", 3), ("thar", 4), ("thene", 3),
    ("vess", 4), ("zeri", 3), ("lyth", 4), ("meli", 2), ("nora", 2),
    ("phor", 2), ("ravi", 2), ("sael", 3), ("ther", 3), ("vira", 3),
]

CODAS = [
    ("", 10), ("l", 3), ("m", 1), ("n", 5), ("r", 4), ("s", 4), ("th", 2), ("x", 1)
]

ENDINGS = [
    ("a", 4), ("ae", 3), ("ais", 1), ("ane", 4), ("anthe", 3), ("ara", 6),
    ("aria", 5), ("aris", 3), ("asha", 2), ("ath", 2), ("atha", 2), ("ava", 4),
    ("avelis", 2), ("dessa", 3), ("demira", 2), ("e", 2), ("ea", 2), ("elia", 2),
    ("elis", 3), ("eloria", 2), ("elyra", 2), ("ena", 6), ("ene", 4), ("enessa", 2),
    ("era", 5), ("eria", 5), ("eris", 4), ("essa", 8), ("eth", 4), ("etha", 4),
    ("ethene", 2), ("ethra", 5), ("ia", 7), ("iane", 2), ("ilia", 2), ("ilyth", 2),
    ("ine", 5), ("ineth", 2), ("ira", 7), ("iris", 2), ("is", 3), ("issa", 5),
    ("ith", 5), ("itha", 4), ("ityss", 1), ("latha", 2), ("lyra", 8), ("lythe", 6),
    ("maris", 2), ("melia", 3), ("mera", 2), ("navis", 2), ("neth", 6), ("netha", 4),
    ("nora", 4), ("noreth", 2), ("oria", 6), ("oris", 3), ("phessa", 3), ("phira", 5),
    ("ressa", 7), ("rinna", 4), ("sela", 4), ("selene", 2), ("syra", 7), ("talia", 3),
    ("taris", 2), ("tesha", 4), ("tevara", 2), ("thara", 4), ("thene", 5), ("vara", 5),
    ("vela", 3), ("vena", 4), ("vena", 4), ("vessa", 7), ("virena", 2), ("yra", 6),
    ("yssoria", 2), ("zeris", 5), ("zorya", 2),
]

APOSTROPHE_PARTICLES = [
    ("T", 10), ("M", 4), ("D", 3), ("V", 2), ("N", 2), ("S", 2), ("K", 1), ("R", 1)
]

IDENTITY_CLUSTERS = {
    "ae", "ael", "aes", "cel", "cyr", "dae", "del", "gel", "iri", "ith", "kel",
    "kyr", "lae", "lir", "lyr", "mae", "mir", "myr", "nae", "nys", "pher",
    "rhen", "sael", "sel", "shae", "tey", "thal", "ther", "tyr", "vael", "vel",
    "vir", "ysa", "zae", "lyth", "neth", "phir", "vess", "zeris", "syra", "lyra",
    "ethra", "thene", "phessa", "phira"
}


def parse_quoted_names(text: str) -> set[str]:
    return {m.group(1).strip() for m in QUOTED_STRING_RE.finditer(text) if m.group(1).strip()}


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def mod_root() -> Path:
    return script_dir().parent


def default_asari_file() -> Path:
    candidates = [
        mod_root() / "common" / "name_lists" / "05_MEG_Asari.txt",
        mod_root() / "common" / "name_lists" / "05_MEG_Asari_namelist.txt",
        mod_root() / "common" / "namelists" / "05_MEG_Asari.txt",
        mod_root() / "common" / "namelists" / "05_MEG_Asari_namelist.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def normalize_piece(piece: str) -> str:
    piece = re.sub(r"[^A-Za-z]", "", piece)
    if not piece:
        return ""
    return piece[:1].upper() + piece[1:].lower()


def normalize_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z' ]", "", name)
    name = re.sub(r"\s+", " ", name).strip()

    if not name:
        return ""

    words = []
    for word in name.split(" "):
        if "'" in word:
            parts = [p for p in word.split("'") if p]
            if not parts:
                continue
            if len(parts) == 2:
                left = normalize_piece(parts[0])
                right = normalize_piece(parts[1])
                words.append(f"{left}'{right}")
            else:
                words.append("".join(normalize_piece(p) for p in parts))
        else:
            words.append(normalize_piece(word))

    return " ".join(words)


def canonical(name: str) -> str:
    return re.sub(r"[^a-z]", "", strip_prefix(name).lower())


def strip_prefix(name: str) -> str:
    return PREFIX_RE.sub("", name).strip()


def weighted_choice(rng: random.Random, pairs: list[tuple[str, int]]) -> str:
    items = [item for item, _ in pairs]
    weights = [weight for _, weight in pairs]
    return rng.choices(items, weights=weights, k=1)[0]


def vowel_groups(name: str) -> int:
    return len(re.findall(r"[aeiouy]+", canonical(name)))


def has_asari_identity(name: str) -> bool:
    lower = canonical(name)
    return any(cluster in lower for cluster in IDENTITY_CLUSTERS)


def is_ceremonial_word(word: str) -> bool:
    return normalize_piece(word) in CEREMONIAL_STOPWORDS


def parse_fallback_names() -> set[str]:
    return {strip_prefix(x) for x in parse_quoted_names(FALLBACK_STYLE_TEXT)}


def load_names_from_file(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    return {strip_prefix(x) for x in parse_quoted_names(text)}


def common_strip_ending(name: str) -> str:
    name = normalize_name(name)
    lower = name.lower()
    endings = (
        "yssoria", "demira", "virania", "thene", "tevara", "phessa", "phira",
        "zeris", "nethis", "maris", "lythe", "vessa", "selene", "ethra",
        "loria", "oria", "lyra", "syra", "ressa", "netha", "neth", "thara",
        "talia", "tesha", "vara", "vena", "vira", "sela", "essa", "eria",
        "aria", "ira", "ena", "yne", "yne", "ane", "eth", "ith", "is", "a", "e"
    )
    for suffix in endings:
        if lower.endswith(suffix) and len(name) - len(suffix) >= 4:
            return normalize_name(name[:-len(suffix)])
    return name


def load_style_names(style_file: Path | None) -> set[str]:
    names = load_names_from_file(style_file)
    if not names:
        names = parse_fallback_names()

    # add a few lore-adjacent anchors without letting ceremonial English dominate
    names |= {"T'Soni", "T'Loak", "Benezia", "Thessia", "Illium", "Tevos"}

    clean: set[str] = set()
    for name in names:
        n = normalize_name(name)
        if n:
            clean.add(n)

    return clean


def build_style_sources(style_names: set[str]) -> list[str]:
    sources: set[str] = set()

    for name in style_names:
        if " " not in name and len(name) >= 4:
            sources.add(name)
            sources.add(common_strip_ending(name))

        for word in name.split():
            if is_ceremonial_word(word):
                continue
            if "'" in word:
                parts = [normalize_piece(p) for p in word.split("'") if p]
                for p in parts:
                    if 3 <= len(p) <= 12:
                        sources.add(p)
                        sources.add(common_strip_ending(p))
            else:
                w = normalize_piece(word)
                if 3 <= len(w) <= 12:
                    sources.add(w)
                    sources.add(common_strip_ending(w))

    return sorted(
        x for x in sources
        if 3 <= len(x) <= 12 and not is_ceremonial_word(x)
    )


def build_fragment_pools(style_sources: list[str]) -> tuple[list[str], list[str], list[str]]:
    starts: set[str] = set()
    mids: set[str] = set()
    tails: set[str] = set()

    for source in style_sources:
        s = canonical(source)
        if len(s) < 4:
            continue

        for n in (2, 3, 4, 5):
            if len(s) >= n + 1:
                starts.add(s[:n])

        for i in range(1, max(2, len(s) - 2)):
            for n in (2, 3, 4):
                if i + n <= len(s) - 1:
                    frag = s[i:i + n]
                    if re.search(r"[aeiouy]", frag) or re.search(r"[bcdfghjklmnpqrstvwxyz]{2}", frag):
                        mids.add(frag)

        for n in (2, 3, 4, 5):
            if len(s) >= n + 1:
                tails.add(s[-n:])

    starts = {x for x in starts if re.fullmatch(r"[a-z]{2,5}", x)}
    mids = {x for x in mids if re.fullmatch(r"[a-z]{2,4}", x)}
    tails = {x for x in tails if re.fullmatch(r"[a-z]{2,5}", x)}

    return sorted(starts), sorted(mids), sorted(tails)


def load_blacklist(blacklist_file: Path | None, style_names: set[str]) -> set[str]:
    names = set(style_names)
    names |= load_names_from_file(blacklist_file)
    return {canonical(x) for x in names if x}


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
        if b in "iy":
            return left + right
        right = right[1:] or "i"

    return left + right


def clean_constructed(raw: str) -> str:
    raw = normalize_name(raw)
    raw = re.sub(r"(.)\1\1+", r"\1\1", raw)
    return raw


def mutate_vowels(raw: str, rng: random.Random) -> str:
    chars = list(raw)
    positions = [i for i, ch in enumerate(chars) if ch in "aeiouy"]
    if positions and rng.random() < 0.30:
        pos = rng.choice(positions)
        chars[pos] = rng.choice(["a", "e", "i", "ae", "ia", "y"])
    return "".join(chars)


def make_melodic_name(rng: random.Random) -> str:
    raw = weighted_choice(rng, MANUAL_ONSETS)
    raw = fix_join(raw, weighted_choice(rng, NUCLEI))
    raw = fix_join(raw, weighted_choice(rng, MEDIALS))
    raw = fix_join(raw, weighted_choice(rng, NUCLEI))

    if rng.random() < 0.60:
        raw = fix_join(raw, weighted_choice(rng, CODAS))

    if rng.random() < 0.55:
        raw = fix_join(raw, weighted_choice(rng, MEDIALS))

    raw = fix_join(raw, weighted_choice(rng, ENDINGS))
    raw = mutate_vowels(raw, rng)
    return clean_constructed(raw)


def make_fragment_name(starts: list[str], mids: list[str], tails: list[str], rng: random.Random) -> str:
    raw = rng.choice(starts)

    mid_count = rng.choices([1, 2, 3], weights=[20, 48, 32], k=1)[0]
    for _ in range(mid_count):
        raw = fix_join(raw, rng.choice(mids))

    if rng.random() < 0.65:
        raw = fix_join(raw, rng.choice(tails))

    raw = fix_join(raw, weighted_choice(rng, ENDINGS))
    return clean_constructed(raw)


def make_blended_name(style_sources: list[str], rng: random.Random) -> str:
    a = canonical(rng.choice(style_sources))
    b = canonical(rng.choice(style_sources))
    while b == a:
        b = canonical(rng.choice(style_sources))

    a_cut = rng.randint(2, max(2, min(5, len(a) - 2)))
    b_start = rng.randint(max(1, len(b) // 2 - 1), max(2, len(b) - 2))

    raw = a[:a_cut] + b[b_start:]

    if rng.random() < 0.75:
        raw = fix_join(raw, weighted_choice(rng, ENDINGS))

    return clean_constructed(raw)


def make_apostrophe_name(style_sources: list[str], rng: random.Random) -> str:
    particle = weighted_choice(rng, APOSTROPHE_PARTICLES)
    base = canonical(rng.choice(style_sources))

    if len(base) >= 6:
        core = base[:rng.randint(3, 5)]
    else:
        core = base

    if rng.random() < 0.55:
        core = fix_join(core, rng.choice(["ra", "la", "sa", "ria", "ly", "th", "va", "ni"]))

    if rng.random() < 0.70:
        core = fix_join(core, weighted_choice(rng, ENDINGS))

    return clean_constructed(f"{particle}'{core}")


def make_short_asari_word(
    starts: list[str], mids: list[str], tails: list[str], rng: random.Random,
) -> str:
    """Build a short Asari-sounding word for ceremonial hybrid names."""
    raw = rng.choice(starts)
    if rng.random() < 0.5:
        raw = fix_join(raw, rng.choice(mids))
    raw = fix_join(raw, weighted_choice(rng, ENDINGS))
    result = clean_constructed(raw)
    if len(result) < 5 or len(result) > 11:
        raw = weighted_choice(rng, MANUAL_ONSETS)
        raw = fix_join(raw, weighted_choice(rng, NUCLEI))
        raw = fix_join(raw, weighted_choice(rng, MEDIALS))
        raw = fix_join(raw, weighted_choice(rng, ENDINGS))
        result = clean_constructed(raw)
    return result


def make_ceremonial_name(
    starts: list[str], mids: list[str], tails: list[str], rng: random.Random,
) -> str:
    """Generate a ceremonial multi-word name for large Asari warships."""
    pattern = rng.choices(
        population=[
            "adj_noun",          # Radiant Grace
            "noun_of_noun",      # Crown of Stars
            "asari_epithet",     # Vaelessa Ascending
            "asari_possessive",  # Myraseth's Vigil
            "the_adj_asari",     # The Eternal Nysereth
            "asari_of_noun",     # Thessira of the Deep
            "possessor_noun",    # Athame's Covenant
            "the_adj_noun",      # The Serene Horizon
        ],
        weights=[14, 13, 16, 12, 10, 13, 9, 13],
        k=1,
    )[0]

    if pattern == "adj_noun":
        return f"{weighted_choice(rng, CEREMONIAL_ADJECTIVES)} {weighted_choice(rng, CEREMONIAL_NOUNS)}"
    elif pattern == "noun_of_noun":
        return f"{weighted_choice(rng, CEREMONIAL_NOUNS)} of {weighted_choice(rng, CEREMONIAL_OF_NOUNS)}"
    elif pattern == "asari_epithet":
        asari = make_short_asari_word(starts, mids, tails, rng)
        return f"{asari} {weighted_choice(rng, CEREMONIAL_EPITHETS)}"
    elif pattern == "asari_possessive":
        asari = make_short_asari_word(starts, mids, tails, rng)
        return f"{asari}'s {weighted_choice(rng, CEREMONIAL_NOUNS)}"
    elif pattern == "the_adj_asari":
        adj = weighted_choice(rng, CEREMONIAL_ADJECTIVES)
        asari = make_short_asari_word(starts, mids, tails, rng)
        return f"The {adj} {asari}"
    elif pattern == "asari_of_noun":
        asari = make_short_asari_word(starts, mids, tails, rng)
        return f"{asari} of {weighted_choice(rng, CEREMONIAL_OF_NOUNS)}"
    elif pattern == "possessor_noun":
        owner = weighted_choice(rng, CEREMONIAL_POSSESSORS)
        return f"{owner}'s {weighted_choice(rng, CEREMONIAL_NOUNS)}"
    else:
        return f"The {weighted_choice(rng, CEREMONIAL_ADJECTIVES)} {weighted_choice(rng, CEREMONIAL_NOUNS)}"


def is_viable(name: str, allow_ceremonial: bool) -> bool:
    lower = canonical(name)
    length = len(lower)

    if " " in name:
        if not allow_ceremonial:
            return False
        wc = phrase_word_count(name)
        if wc < 2 or wc > 5:
            return False
        return True

    if not (5 <= length <= 14):
        return False

    if vowel_groups(name) < 2 or vowel_groups(name) > 7:
        return False

    if re.search(r"[bcdfghjklmnpqrstvwxyz]{5}", lower):
        return False

    if re.search(r"(.)\1\1", lower):
        return False

    # avoid too much turian / latin drift
    if lower.endswith(("tor", "ator", "trix", "ctus", "ium", "orius", "anus", "enus", "us", "ix")):
        return False

    if not has_asari_identity(name):
        return False

    return True


def phrase_word_count(name: str) -> int:
    return len(name.split())


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

        if SequenceMatcher(None, key, other).ratio() >= 0.89:
            return True

    return False


def make_candidate(
    style_sources: list[str],
    starts: list[str],
    mids: list[str],
    tails: list[str],
    rng: random.Random,
    apostrophe_rate: float,
    ceremonial_rate: float,
) -> str:
    mode_roll = rng.random()

    if mode_roll < ceremonial_rate:
        mode = "ceremonial"
    elif mode_roll < ceremonial_rate + apostrophe_rate:
        mode = "apostrophe"
    else:
        mode = rng.choices(
            population=["melodic", "fragment", "blend"],
            weights=[46, 32, 22],
            k=1,
        )[0]

    for _ in range(900):
        if mode == "melodic":
            candidate = make_melodic_name(rng)
        elif mode == "fragment":
            candidate = make_fragment_name(starts, mids, tails, rng)
        elif mode == "blend":
            candidate = make_blended_name(style_sources, rng)
        elif mode == "apostrophe":
            candidate = make_apostrophe_name(style_sources, rng)
        else:
            candidate = make_ceremonial_name(starts, mids, tails, rng)

        if is_viable(candidate, allow_ceremonial=ceremonial_rate > 0):
            return candidate

    raise RuntimeError("Failed to generate a viable asari candidate.")


def generate_asari_generic_names(
    count: int,
    seed: int | None = None,
    style_file: Path | None = None,
    blacklist_file: Path | None = None,
    prefix: str = "",
    apostrophe_rate: float = 0.06,
    ceremonial_rate: float = 0.03,
) -> list[str]:
    rng = random.Random(seed)

    style_names = load_style_names(style_file)
    blacklist = load_blacklist(blacklist_file, style_names)
    style_sources = build_style_sources(style_names)
    starts, mids, tails = build_fragment_pools(style_sources)

    results: list[str] = []
    seen_local: set[str] = set()

    attempts = 0
    max_attempts = count * 5000

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        bare = make_candidate(
            style_sources=style_sources,
            starts=starts,
            mids=mids,
            tails=tails,
            rng=rng,
            apostrophe_rate=apostrophe_rate,
            ceremonial_rate=ceremonial_rate,
        )

        key = canonical(bare)

        if key in blacklist or key in seen_local:
            continue

        if too_similar(key, blacklist | seen_local):
            continue

        seen_local.add(key)
        results.append(f"{prefix}{bare}" if prefix else bare)

    if len(results) < count:
        raise RuntimeError(
            f"Could only generate {len(results)} unique asari names after {attempts} attempts."
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
            "Generate generic Asari ship names with a melodic, vowel-rich tone, "
            "using the existing asari namelist as both style source and blacklist."
        )
    )
    parser.add_argument("--count", type=int, default=200, help="Number of names to generate. Default: 200")
    parser.add_argument("--seed", type=int, default=42, help="Random seed. Default: 42")
    parser.add_argument("--per-line", type=int, default=8, help="Names per output line. Default: 8")
    parser.add_argument(
        "--style-file",
        type=Path,
        default=default_asari_file(),
        help="Asari namelist file to use as style source. Defaults to ../common/name_lists or ../common/namelists.",
    )
    parser.add_argument(
        "--blacklist-file",
        type=Path,
        default=default_asari_file(),
        help="Asari namelist file to blacklist existing names from. Default: same as style file.",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="",
        help="Optional prefix, e.g. 'ARV '. Default: none",
    )
    parser.add_argument(
        "--apostrophe-rate",
        type=float,
        default=0.06,
        help="Chance of apostrophe names like T'Xxxxx. Default: 0.06",
    )
    parser.add_argument(
        "--ceremonial-rate",
        type=float,
        default=0.03,
        help="Chance of rare ceremonial two-word names. Default: 0.03",
    )
    args = parser.parse_args()

    if not (0.0 <= args.apostrophe_rate <= 1.0):
        raise ValueError("--apostrophe-rate must be between 0.0 and 1.0")

    if not (0.0 <= args.ceremonial_rate <= 1.0):
        raise ValueError("--ceremonial-rate must be between 0.0 and 1.0")

    names = generate_asari_generic_names(
        count=args.count,
        seed=args.seed,
        style_file=args.style_file,
        blacklist_file=args.blacklist_file,
        prefix=args.prefix,
        apostrophe_rate=args.apostrophe_rate,
        ceremonial_rate=args.ceremonial_rate,
    )
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())