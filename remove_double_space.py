#!/usr/bin/env python3
"""Remove double line-spacing from .txt files in a directory tree.

Every line in the source is separated by a blank line (\n\n). This script
collapses those to single \n, but uses sentence-ending punctuation as a
heuristic to detect real paragraph breaks and preserve them as \n\n.

A blank line is kept when the preceding line ends with: . ! ? " ' ) … or
their Unicode curly-quote equivalents — i.e. it looks like the end of a
sentence/paragraph. Otherwise the blank line is removed (wrapped line).

Usage:
    python remove_double_space.py /path/to/dir [--dry-run] [--verbose]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Characters that typically end a sentence / paragraph.
_SENTENCE_END = re.compile(r'[.!?"\'\u2019\u201d\u2026)]\s*$')


def fix_spacing(text: str) -> str:
    # Split on every \n\n; each segment is one line of the double-spaced file.
    segments = text.split("\n\n")
    parts = []
    for i, seg in enumerate(segments):
        parts.append(seg)
        if i < len(segments) - 1:
            # Use \n\n (paragraph break) if this line looks like a sentence end,
            # otherwise \n (continuation of a wrapped paragraph).
            last_line = seg.rstrip("\n").rsplit("\n", 1)[-1]
            if _SENTENCE_END.search(last_line):
                parts.append("\n\n")
            else:
                parts.append("\n")
    return "".join(parts)


def process_file(path: Path, dry_run: bool = False) -> bool:
    """Return True if the file was (or would be) changed."""
    raw = path.read_bytes()

    if b'\r' in raw:
        print(f"Warning: {path} contains CR bytes — run dos2unix first, skipping.", file=sys.stderr)
        return False

    original = raw.decode("utf-8")
    cleaned = fix_spacing(original)

    if cleaned == original:
        return False

    if not dry_run:
        path.write_text(cleaned, encoding="utf-8", newline="")
    return True


def walk_and_process(root: Path, dry_run: bool = False, verbose: bool = False) -> tuple[int, int]:
    total = 0
    changed = 0

    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if not name.lower().endswith(".txt"):
                continue

            total += 1
            file_path = Path(dirpath) / name
            was_changed = process_file(file_path, dry_run=dry_run)
            if was_changed:
                changed += 1
                if verbose:
                    print(f"  {'[dry-run] ' if dry_run else ''}fixed: {file_path}")

    return total, changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove double line-spacing from .txt files, preserving paragraph breaks."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without modifying files.")
    parser.add_argument("--verbose", action="store_true", help="Print each file that is changed.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)

    if not root.exists():
        print(f"Error: path does not exist: {root}", file=sys.stderr)
        return 1

    if root.is_file():
        if not root.name.lower().endswith(".txt"):
            print(f"Warning: {root} is not a .txt file — skipping.", file=sys.stderr)
            return 1
        changed = process_file(root, dry_run=args.dry_run)
        if changed:
            action = "Would fix" if args.dry_run else "Fixed"
            print(f"{action}: {root}")
        else:
            print(f"{root} — no double-spacing found.")
        return 0

    if not root.is_dir():
        print(f"Error: {root} is neither a file nor a directory.", file=sys.stderr)
        return 1

    total, changed = walk_and_process(root, dry_run=args.dry_run, verbose=args.verbose)

    if total == 0:
        print(f"No .txt files found under: {root}")
        return 0

    print(f"Scanned {total} .txt files.")
    action = "Would fix" if args.dry_run else "Fixed"
    print(f"{action} {changed} files.")
    print(f"Already clean: {total - changed} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
