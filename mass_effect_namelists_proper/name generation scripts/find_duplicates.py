#!/usr/bin/env python3
"""Find and resolve duplicate quoted names across namelist .txt files.

Scans all .txt files under the given directory (default: ../common/name_lists)
for strings enclosed in double quotes.  When a name appears in more than one
file the user is prompted to choose which file keeps it; the name is removed
from all other files and the files are rewritten in place.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

QUOTED_RE = re.compile(r'"([^"]+)"')


def read_file(path: Path) -> str:
    """Read a text file, trying common encodings."""
    for enc in ("utf-8-sig", "utf-8", "utf-16-le", "utf-16"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return path.read_text(encoding="latin-1")


def collect_names(files: list[Path]) -> dict[str, list[Path]]:
    """Return a mapping of name -> list of files that contain it."""
    name_to_files: dict[str, list[Path]] = defaultdict(list)
    for f in files:
        text = read_file(f)
        seen_in_file: set[str] = set()
        for m in QUOTED_RE.finditer(text):
            name = m.group(1)
            if name not in seen_in_file:
                seen_in_file.add(name)
                name_to_files[name].append(f)
    return name_to_files


def remove_name_from_file(path: Path, name: str) -> None:
    """Remove one occurrence of \"name\" from *path* and rewrite the file."""
    text = read_file(path)
    # Match the quoted token, optional trailing whitespace
    pattern = re.compile(r'\"' + re.escape(name) + r'\"[ \t]*')
    new_text, count = pattern.subn("", text, count=1)
    if count:
        # Clean up any resulting double-space / blank lines
        new_text = re.sub(r'[ \t]+\n', '\n', new_text)
        new_text = re.sub(r'\n{3,}', '\n\n', new_text)
        # Detect original encoding for rewrite
        raw = path.read_bytes()
        if raw[:3] == b'\xef\xbb\xbf':
            enc = "utf-8-sig"
        elif raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
            enc = "utf-16"
        else:
            enc = "utf-8"
        path.write_text(new_text, encoding=enc)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory",
        nargs="?",
        default=str(Path(__file__).resolve().parent.parent / "common" / "name_lists"),
        help="Directory to scan for .txt namelist files (default: ../common/name_lists)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report duplicates; do not modify any files.",
    )
    args = parser.parse_args()

    scan_dir = Path(args.directory)
    if not scan_dir.is_dir():
        print(f"Error: {scan_dir} is not a directory.", file=sys.stderr)
        sys.exit(1)

    files = sorted(scan_dir.rglob("*.txt"))
    if not files:
        print("No .txt files found.")
        return

    print(f"Scanning {len(files)} file(s) in {scan_dir} ...\n")

    name_to_files = collect_names(files)
    duplicates = {n: fs for n, fs in name_to_files.items() if len(fs) > 1}

    if not duplicates:
        print("No duplicate names found.")
        return

    print(f"Found {len(duplicates)} duplicate name(s).\n")

    if args.dry_run:
        for name, paths in sorted(duplicates.items()):
            fnames = ", ".join(p.name for p in paths)
            print(f'  "{name}"  ->  {fnames}')
        return

    resolved = 0
    skipped = 0

    for i, (name, paths) in enumerate(sorted(duplicates.items()), 1):
        print(f"--- Duplicate {i}/{len(duplicates)} ---")
        print(f'  Name: "{name}"')
        print("  Found in:")
        for idx, p in enumerate(paths, 1):
            print(f"    [{idx}] {p.name}")
        print(f"    [s] Skip")
        print(f"    [q] Quit\n")

        while True:
            choice = input(f"  Keep in which file? [1-{len(paths)}/s/q]: ").strip().lower()
            if choice == "q":
                print(f"\nStopped. Resolved {resolved}, skipped {skipped}.")
                return
            if choice == "s":
                skipped += 1
                print()
                break
            if choice.isdigit() and 1 <= int(choice) <= len(paths):
                keep_idx = int(choice) - 1
                for j, p in enumerate(paths):
                    if j != keep_idx:
                        remove_name_from_file(p, name)
                        print(f'    Removed from {p.name}')
                resolved += 1
                print()
                break
            print("  Invalid choice, try again.")

    print(f"Done. Resolved {resolved}, skipped {skipped}.")


if __name__ == "__main__":
    main()
