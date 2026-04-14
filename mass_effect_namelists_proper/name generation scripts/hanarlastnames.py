#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import re
import sys


QUOTED_STRING_RE = re.compile(r'"([^"]+)"')


EXAMPLES_TEXT = r'''
"(Regards the Works of the Enkindlers in Despair)"
"(Regards the Gift of the Language in Patience)"
"(Regards the Speech of the Kahje in Wonder)"
"(Regards the Silence of the Shallows in Patience)"
"(Regards the Currents of the Enkindlers in Wonder)"
"(Illuminates the Works of the Language in Wonder)"
"(Illuminates the Gift of the Kahje in Despair)"
"(Illuminates the Speech of the Shallows in Patience)"
"(Illuminates the Silence of the Enkindlers in Wonder)"
"(Illuminates the Currents of the Language in Despair)"
"(Interprets the Works of the Kahje in Patience)"
"(Interprets the Gift of the Shallows in Wonder)"
"(Interprets the Speech of the Enkindlers in Despair)"
"(Interprets the Silence of the Language in Patience)"
"(Interprets the Currents of the Kahje in Wonder)"
"(Catalogues the Works of the Shallows in Despair)"
"(Catalogues the Gift of the Enkindlers in Wonder)"
"(Catalogues the Speech of the Language in Patience)"
"(Catalogues the Silence of the Kahje in Despair)"
"(Catalogues the Currents of the Shallows in Wonder)"
"(Measures the Works of the Enkindlers in Wonder)"
"(Measures the Gift of the Language in Despair)"
"(Measures the Speech of the Kahje in Patience)"
"(Measures the Silence of the Shallows in Wonder)"
"(Measures the Currents of the Enkindlers in Patience)"
'''


VERBS = [
    "Regards", "Illuminates", "Interprets", "Catalogues", "Measures",
    "Witnesses", "Attends", "Honors", "Reads", "Recalls",
    "Carries", "Hears", "Shelters", "Names", "Weighs",
    "Discerns", "Chronicles", "Guards", "Follows", "Tends",
    "Keeps", "Answers", "Receives", "Searches", "Observes",
    "Traces", "Invokes", "Mirrors", "Offers", "Mourns",
    "Adorns", "Tethers", "Navigates", "Remembers", "Preserves",
    "Translates", "Bears", "Studies", "Surveys", "Contemplates",
    "Reveres", "Questions", "Deciphers", "Takes Measure of", "Listens to",
    "Returns to", "Surrenders to", "Meditates upon", "Passes through", "Waits upon",
    "Records", "Tends to", "Echoes", "Conveys", "Intercedes for",
    "Recounts", "Frames", "Stewards", "Receives Word of", "Kneels before",
    "Passes beneath", "Dreams of", "Recites", "Embraces", "Fathoms",
    "Tastes", "Learns from", "Watches", "Inherits", "Sanctifies",
    "Consecrates", "Accepts", "Offers Witness to", "Holds Fast to", "Returns Word of",
    "Buries", "Raises", "Enshrines", "Extends", "Seeks Passage through",
]

OBJECTS = [
    "Works", "Gift", "Speech", "Silence", "Currents",
    "Memory", "Mercy", "Promise", "Witness", "Lament",
    "Song", "Prayer", "Question", "Answer", "Dream",
    "Hush", "Burden", "Ritual", "Breath", "Tide",
    "Echo", "Light", "Shadow", "Horizon", "Pilgrimage",
    "Remembrance", "Stillness", "Calling", "Shelter", "Warning",
    "Drowning Light", "First Question", "Final Answer", "Patient Flame", "Buried Song",
    "Tidal Memory", "Glass Silence", "Ashen Prayer", "Witnessing Tide", "Hidden Mercy",
    "Sacred Drift", "Low Hymn", "Fathom Song", "Veiled Truth", "Last Tide",
    "Quiet Warning", "Living Silence", "Open Memory", "Night Prayer", "Trembling Witness",
    "Hollow Mercy", "Long Vigil", "Watching Song", "Distant Promise", "Inner Tide",
    "Broken Prayer", "Low Answer", "Old Question", "Cleansing Silence", "Lantern Song",
    "Pilgrim Memory", "Graven Hush", "Tidal Witness", "Salt Mercy", "Soft Lament",
    "Ancient Calling", "Final Silence", "Deep Prayer", "Merciful Burden", "Shaped Stillness",
    "Bright Warning", "Sacred Witness", "Open Question", "Lost Answer", "Inner Horizon",
    "Fathomless Dream", "Buried Promise", "Long Mercy", "Patient Song", "Hushed Pilgrimage",
]

OBJECT_MODIFIERS = [
    "Quiet", "Luminous", "Hidden", "Buried", "Patient",
    "Sacred", "Distant", "First", "Final", "Living",
    "Fathomless", "Ashen", "Veiled", "Tidal", "Hollow",
    "Open", "Still", "Ancient", "Broken", "Glass",
    "Low", "Tender", "Graven", "Inner", "Outer",
    "Watchful", "Cold", "Bright", "Silent", "Unspoken",
    "Merciful", "Lantern", "Salt", "Pilgrim", "Soft",
    "Deep", "Long", "Frail", "Reverent", "Cleansing",
    "Shaped", "Lost", "Last", "Elder", "Hushed",
]

SUBJECTS = [
    "Enkindlers", "Language", "Kahje", "Shallows", "Depths",
    "Tides", "Pilgrims", "Singers", "Witnesses", "Reefs",
    "Open Sea", "Silent Reef", "Elder Tide", "First Current",
    "Hollow Choir", "Living Waters", "Broken Reef", "Deep Chorus",
    "Old Light", "Outer Water", "Inner Sea", "Distant Shoals",
    "Trembling Tide", "First Silence", "Last Horizon", "Fathomless Choir",
    "Lantern Tides", "Ancestor Reef", "Buried Current", "Watching Dark",
    "Patient Deep", "Glass Waters", "Veiled Shallows", "Remembrance Reef",
    "Tidal Choir", "Long Water", "Sleeping Current", "Drowned Sky",
    "Luminous Deep", "Calling Shoals", "Cleansing Tide", "Sacred Silence",
    "Pilgrim Waters", "Hushed Current", "Witness Reef", "Merciful Tide",
    "Outer Shoals", "Inner Reef", "Broken Waters", "Crowned Tide",
    "Open Silence", "Night Waters", "Hollow Deep", "Low Horizon",
    "Ancestor Choir", "Listening Sea", "Buried Shoals", "Far Reef",
    "Reverent Tides", "Unspoken Deep", "Vigilant Waters", "Glass Tide",
    "Living Reef", "Sacred Waters", "Trembling Shoals", "Final Current",
    "Merciful Shallows", "Pilgrim Choir", "Long Silence", "Forgotten Reef",
    "Deep Waters", "Elder Shoals", "Hushed Sea", "Watching Tide",
    "Lantern Reef", "Cleansing Waters", "Witnessing Current", "Ancient Shallows",
]

SUBJECT_MODIFIERS = [
    "Silent", "Ancient", "Living", "Veiled", "Distant",
    "Sacred", "Broken", "Hollow", "Merciful", "Pilgrim",
    "Lantern", "Listening", "Open", "Buried", "Witnessing",
    "Final", "Elder", "Glass", "Low", "Hushed",
]

STATES = [
    "Patience", "Wonder", "Despair", "Reverence", "Silence",
    "Mercy", "Witness", "Stillness", "Devotion", "Longing",
    "Dread", "Awe", "Vigil", "Lament", "Clarity",
    "Faith", "Grace", "Surrender", "Distance", "Hunger",
    "Ash", "Memory", "Renewal", "Penitence", "Listening",
    "Tidal Calm", "Sacred Dread", "Patient Witness", "Mourning", "Cold Hope",
    "Bright Sorrow", "Low Grace", "Endurance", "Quiet Faith", "Solemn Wonder",
    "Tender Grief", "Open Devotion", "Last Patience", "Watchful Silence", "Ancient Mercy",
    "Fathomless Awe", "Measured Sorrow", "Gentle Dread", "Buried Faith", "Inner Silence",
    "Pilgrim Grace", "Salt Mourning", "Long Reverence", "Still Devotion", "Witnessing Calm",
    "Old Mercy", "Soft Lament", "Deep Patience", "Merciful Silence", "Listening Awe",
    "Tidal Grief", "Distant Faith", "Sacred Longing", "Hushed Wonder", "Final Witness",
]

ENDING_LINKERS = [
    ("in", 60),
    ("with", 20),
    ("through", 10),
    ("amid", 6),
    ("beyond", 2),
    ("without", 2),
]

TEMPLATES = [
    ("{verb} the {obj} of the {subj}{ending}", 32),
    ("{verb} the {obj} beneath the {subj}{ending}", 7),
    ("{verb} the {obj} before the {subj}{ending}", 5),
    ("{verb} the {obj} under the {subj}{ending}", 5),
    ("{verb} the {obj} beyond the {subj}{ending}", 3),
    ("{verb} the {obj} within the {subj}{ending}", 6),
    ("{verb} the {obj} among the {subj}{ending}", 4),
    ("{verb} the {obj} carried by the {subj}{ending}", 6),
    ("{verb} the {obj} kept by the {subj}{ending}", 5),
    ("{verb} the {obj} spoken by the {subj}{ending}", 4),
    ("{verb} the {obj} heard in the {subj}{ending}", 4),
    ("{verb} the {obj} between the {subj1} and the {subj2}{ending}", 8),
    ("{verb} the {obj} of the {subj1} and the {subj2}{ending}", 5),
    ("{verb} the {obj} passed to the {subj}{ending}", 3),
    ("{verb} the {obj} returned by the {subj}{ending}", 2),
    ("{verb} the {obj} drawn from the {subj}{ending}", 3),
    ("{verb} the {obj} entrusted to the {subj}{ending}", 2),
    ("{verb} the {obj} remembered by the {subj}{ending}", 3),
    ("{verb} the {obj} sheltered by the {subj}{ending}", 3),
    ("{verb} the {obj} beneath the gaze of the {subj}{ending}", 2),
]


def parse_quoted_names(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in QUOTED_STRING_RE.finditer(text)
        if match.group(1).strip()
    }


BLACKLIST = parse_quoted_names(EXAMPLES_TEXT)


def weighted_choice(rng: random.Random, items_with_weights: list[tuple[str, int]]) -> str:
    items = [item for item, _ in items_with_weights]
    weights = [weight for _, weight in items_with_weights]
    return rng.choices(items, weights=weights, k=1)[0]


def maybe_modified_object(rng: random.Random) -> str:
    base = rng.choice(OBJECTS)

    modifiers = []
    if rng.random() < 0.42:
        mod1 = rng.choice(OBJECT_MODIFIERS)
        if not base.startswith(mod1 + " "):
            modifiers.append(mod1)

    if rng.random() < 0.12:
        mod2 = rng.choice(OBJECT_MODIFIERS)
        if mod2 not in modifiers and not base.startswith(mod2 + " "):
            modifiers.append(mod2)

    if modifiers:
        return " ".join(modifiers + [base])

    return base


def maybe_modified_subject(rng: random.Random) -> str:
    base = rng.choice(SUBJECTS)

    if rng.random() < 0.22:
        mod = rng.choice(SUBJECT_MODIFIERS)
        if not base.startswith(mod + " "):
            return f"{mod} {base}"

    return base


def distinct_subjects(rng: random.Random) -> tuple[str, str]:
    a = maybe_modified_subject(rng)
    b = maybe_modified_subject(rng)
    while b == a:
        b = maybe_modified_subject(rng)
    return a, b


def make_ending(rng: random.Random, omit_tail_rate: float) -> str:
    if rng.random() < omit_tail_rate:
        return ""

    linker = weighted_choice(rng, ENDING_LINKERS)
    state = rng.choice(STATES)
    return f" {linker} {state}"


def clean_phrase(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("the the ", "the ")
    text = text.replace("of the the ", "of the ")
    return text


def generate_one(rng: random.Random, omit_tail_rate: float) -> str:
    template = weighted_choice(rng, TEMPLATES)
    subj1, subj2 = distinct_subjects(rng)

    phrase = template.format(
        verb=rng.choice(VERBS),
        obj=maybe_modified_object(rng),
        subj=maybe_modified_subject(rng),
        subj1=subj1,
        subj2=subj2,
        ending=make_ending(rng, omit_tail_rate),
    )

    phrase = clean_phrase(phrase)
    return f"({phrase})"


def generate_names(count: int, seed: int | None = None, omit_tail_rate: float = 0.38) -> list[str]:
    rng = random.Random(seed)
    used = set(BLACKLIST)
    results: list[str] = []

    attempts = 0
    max_attempts = count * 8000

    while len(results) < count and attempts < max_attempts:
        attempts += 1
        candidate = generate_one(rng, omit_tail_rate=omit_tail_rate)

        if candidate in used:
            continue

        used.add(candidate)
        results.append(candidate)

    if len(results) < count:
        raise RuntimeError(
            f"Kunde bara generera {len(results)} unika namn efter {attempts} försök."
        )

    return results


def format_output(names: list[str], indent: str = "\t\t\t\t") -> str:
    return "\n".join(f'{indent}"{name}"' for name in names)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate varied Hanar soul names in Stellaris-friendly quoted format."
    )
    parser.add_argument("--count", type=int, default=200, help="How many names to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible output")
    parser.add_argument(
        "--omit-tail-rate",
        type=float,
        default=0.38,
        help="Chance to omit the final ending like 'in Patience'. Default: 0.38"
    )
    args = parser.parse_args()

    if not (0.0 <= args.omit_tail_rate <= 1.0):
        raise ValueError("--omit-tail-rate måste vara mellan 0.0 och 1.0")

    names = generate_names(
        args.count,
        seed=args.seed,
        omit_tail_rate=args.omit_tail_rate,
    )
    print(format_output(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())