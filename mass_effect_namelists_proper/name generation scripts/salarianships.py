#!/usr/bin/env python3

from __future__ import annotations

import argparse
import random
import re
import sys


QUOTED_STRING_RE = re.compile(r'"([^"]+)"')


EXAMPLES_TEXT = r'''
"Anoleis" "Kirrahe" "Vorleon" "Rentola" "Linron" "Palon" "Saleon" "Imness" "Bau" "Holin" "Tolan" "Heplorn" "Avot"
"Solus" "Hanok" "Uwan" "Dalu" "Chalben" "Dezen" "Girlan" "Gaezik" "Olorn" "Oponi" "Eluso" "Tozeni" "Aerajii" "Ehei"
"Jorhart" "Saezze" "Waerow" "Tuzore" "Faebar" "Ulana" "Sartop" "Jimori" "Faedann" "Iluse" "Irgop" "Porajio"
"Maerlum" "Ulua" "Waebop" "Zamali" "Omal" "Faerlane" "Jebern" "Yemoro" "Mustar" "Zaenmorne" "Cimum" "Derlane"
"Badirn" "Cerbano" "Calum" "Weralo" "Aegok" "Haemina" "Cirgol" "Jaeljio" "Aerorth" "Firixe" "Resar" "Iwani"
"Mirborm" "Cazalo" "Hiwirn" "Nussa" "Irpann" "Onis" "Wasoln" "Daraji" "Uson" "Fedrok" "Yawin" "Hazal" "Laerbum" "Baeral"
"Gewar" "Baemal" "Jepaw" "Aenik" "Burann" "Rudrok" "Jaemann" "Julu" "Pubart" "Jarlan" "Obart" "Baessi" "Bumok" "Taekse"
"Modorth" "Jezika" "Lerlarp" "Gonise" "Ostirn" "Sajia" "Alern" "Yawane" "Vaernum" "Jorjio" "Dotall" "Buhee" "Lirtol" "Irjio"
"Haemarth" "Gomala" "Jorparp" "Wazom" "Sarstal" "Romin" "Zerbarf" "Lizz" "Linarp" "Beral" "Sistin" "Olon" "Horirn" "Elban"
"Derwarf" "Zelben" "Wegok" "Hewan" "Dedaw" "Nonorm" "Sural" "Valern" "Wiks" "Jath" "Kallo" "Esheel" "Inoste" "Todrok"
"Current One" "Current Two" "Current Three" "Observation One" "Observation Two" "Vector One" "Vector Two" "Survey Three" "Analysis Four"
"Rapid Inference" "Silent Calculus" "Thin Horizon" "Bright Enzyme" "Glass Current" "Wet Logic" "Quick Trial" "Open Secret"
"Spectral Wake" "Transit Memory" "Vigilant Thesis" "Ablative Proof" "Delta Spiral" "Signal Marsh" "Apex Estuary" "Shaded Delta"
"Saelun" "Tevorn" "Kelvass" "Marolin" "Jesarn" "Vaetol" "Nerix" "Torwen" "Galis" "Pelor"
"Rethan" "Sivarn" "Joreth" "Kaevik" "Melnor" "Orlann" "Tirgol" "Weran" "Zalith" "Haelon"
"Irven" "Dorex" "Lethan" "Corvass" "Fejol" "Nesari" "Velorn" "Taerik" "Ulen" "Borveth"
"Selonn" "Jezarn" "Kalori" "Navor" "Ressik" "Torass" "Weylin" "Darvok" "Helari" "Ossirn"
"Maevol" "Cerian" "Lurass" "Pavern" "Risal" "Venlor" "Taless" "Yorvin" "Jeloran" "Firnass"
"Gaelor" "Heskan" "Irelon" "Jassik" "Keloran" "Lomirn" "Merass" "Nelvok" "Orsali" "Pernix"
"Queron" "Raless" "Senvik" "Tervan" "Ulrenn" "Varoli" "Welass" "Xevorn" "Yelari" "Zorven"
"Aesirn" "Baelor" "Cenori" "Dovass" "Elarin" "Fenvor" "Gessik" "Harven" "Ithori" "Jalvok"
"Kessan" "Lorvik" "Marel" "Norass" "Olevan" "Parnok" "Qelari" "Rovann" "Selnor" "Tassik"
"Uverin" "Varnol" "Wesari" "Xalenn" "Yorek" "Zevass" "Cipher Current" "Silent Vector" "Measured Delta" "Rapid Marsh"
"Dry Estuary" "Proof of Rain" "Thin Salient" "Hidden Wetwork" "Marsh Thesis" "Lattice Inference" "Quiet Predicate" "Delta Ledger"
"Reflex Archive" "Tidal Formula" "Prime Salient" "Brackish Signal" "Swift Axiom" "Green Inference" "Shrouded Survey" "Marsh Cipher"
"Clear Transit" "Night Vector" "Inferential Wake" "Coastal Proof" "Bright Ledger" "Open Lattice" "Silent Enzyme" "Wetwork Spiral"
'''


PREFIXES = [
    "Ael", "Aer", "Ari", "Ash", "Avo", "Bae", "Bel", "Ber", "Cer", "Cor",
    "Dar", "Del", "Dre", "Eli", "Ere", "Fal", "Fen", "Fir", "Gal", "Gor",
    "Hal", "Har", "Hel", "Ire", "Ith", "Jae", "Jor", "Kae", "Kel", "Kor",
    "Lae", "Lar", "Lor", "Mae", "Mal", "Mer", "Nal", "Ner", "Olo", "Orv",
    "Pae", "Pel", "Qel", "Ral", "Ren", "Sar", "Sel", "Sor", "Tal", "Tar",
    "Tev", "Tor", "Ule", "Ulr", "Val", "Var", "Vel", "Vor", "Wae", "Wes",
    "Xal", "Xev", "Yel", "Yor", "Zae", "Zor",
]

MIDDLES = [
    "ar", "al", "an", "av", "ax", "el", "en", "er", "eth", "ev",
    "ia", "iel", "ik", "il", "in", "ir", "is", "iv", "ok", "ol",
    "om", "on", "or", "os", "ov", "rak", "ral", "ren", "reth", "rik",
    "rin", "rok", "rol", "ron", "sar", "sel", "sor", "tal", "tar", "ten",
    "thal", "tor", "ul", "ur", "vak", "val", "var", "vek", "vel", "vor",
]

SUFFIXES = [
    "ael", "ak", "al", "an", "ar", "arn", "as", "ass", "ek", "el",
    "en", "eon", "er", "eth", "ev", "ial", "ik", "il", "in", "ir",
    "is", "ix", "ok", "ol", "on", "or", "orn", "os", "oth", "ul",
    "um", "une", "ur", "vak", "val", "var", "vek", "vel", "ven", "vor",
]

PHRASE_LEFT = [
    "Acute", "Ablative", "Amber", "Arc", "Ashen", "Austere", "Azure", "Binary",
    "Brackish", "Brisk", "Clear", "Cold", "Coastal", "Coded", "Crisp", "Deep",
    "Discrete", "Distant", "Dry", "Exact", "Filtered", "Finite", "Fleet", "Focused",
    "Formal", "Glass", "Grey", "Hidden", "Layered", "Linear", "Local", "Lucent",
    "Lucid", "Luminous", "Measured", "Muted", "Night", "Open", "Outer", "Pale",
    "Patient", "Phased", "Prime", "Quiet", "Rapid", "Reactive", "Remote", "Rational",
    "Sable", "Scarlet", "Shaded", "Shallow", "Silent", "Solar", "Sparse", "Spectral",
    "Still", "Stark", "Steady", "Subtle", "Swift", "Tactical", "Terse", "Thin",
    "Tidal", "Tuned", "Veiled", "Vigilant", "Wary", "Zero",
]

PHRASE_RIGHT = [
    "Archive", "Array", "Axiom", "Basin", "Beacon", "Boundary", "Cadence", "Canal",
    "Cascade", "Channel", "Cipher", "Circuit", "Conduit", "Current", "Datum", "Delta",
    "Doctrine", "Drift", "Enzyme", "Equation", "Estuary", "Facet", "Filter", "Formula",
    "Framework", "Gradient", "Harbor", "Horizon", "Index", "Inference", "Instance", "Kernel",
    "Lattice", "Ledger", "Mandate", "Marsh", "Measure", "Mire", "Model", "Node",
    "Paradox", "Pattern", "Predicate", "Proof", "Proxy", "Pulse", "Registry", "Relay",
    "Rationale", "Secret", "Shelf", "Shoal", "Signal", "Span", "Spiral", "Survey",
    "Surveyor", "Synthesis", "Theory", "Thread", "Thesis", "Tide", "Trace", "Transit",
    "Undertow", "Vault", "Vector", "Wake", "Weather", "Wetwork",
]


def parse_quoted_names(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in QUOTED_STRING_RE.finditer(text)
        if match.group(1).strip()
    }


BLACKLIST = parse_quoted_names(EXAMPLES_TEXT)


def normalize_generated_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z ]+", "", name)
    name = re.sub(r"\s+", " ", name).strip()

    if " " in name:
        parts = name.split(" ")
        return " ".join(part[:1].upper() + part[1:].lower() for part in parts)

    return name[:1].upper() + name[1:].lower()


def make_single_name(rng: random.Random) -> str:
    parts = [rng.choice(PREFIXES)]

    if rng.random() < 0.78:
        parts.append(rng.choice(MIDDLES))

    if rng.random() < 0.28:
        parts.append(rng.choice(MIDDLES))

    parts.append(rng.choice(SUFFIXES))

    name = "".join(parts)
    name = re.sub(r"(.)\1\1+", r"\1\1", name)
    name = normalize_generated_name(name)

    if len(name) < 4 or len(name) > 12:
        return make_single_name(rng)

    return name


def make_phrase_name(rng: random.Random) -> str:
    return normalize_generated_name(f"{rng.choice(PHRASE_LEFT)} {rng.choice(PHRASE_RIGHT)}")


def generate_names(count: int, seed: int | None = None) -> list[str]:
    rng = random.Random(seed)
    results: list[str] = []
    used = set(BLACKLIST)

    attempts = 0
    max_attempts = count * 3000

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        candidate = make_phrase_name(rng) if rng.random() < 0.16 else make_single_name(rng)

        if candidate in used:
            continue

        used.add(candidate)
        results.append(candidate)

    if len(results) < count:
        raise RuntimeError(
            f"Kunde bara generera {len(results)} unika namn efter {attempts} försök."
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
    parser = argparse.ArgumentParser(
        description="Generera Salarian-liknande skeppsnamn utan exakta träffar mot blacklist i scriptet."
    )
    parser.add_argument("--count", type=int, default=1000, help="Antal namn. Default: 1000")
    parser.add_argument("--seed", type=int, default=42, help="Seed. Default: 42")
    parser.add_argument("--per-line", type=int, default=12, help="Antal per rad. Default: 12")
    args = parser.parse_args()

    names = generate_names(args.count, seed=args.seed)
    print(format_as_array(names, per_line=args.per_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())