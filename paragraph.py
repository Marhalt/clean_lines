#!/usr/bin/env python3
"""
paragraph.py — Insert paragraph breaks into poorly-paragraphed story text.

Usage (single file):  python paragraph.py <file.txt>
  Output: <stem>_p.txt in the same directory.

Usage (directory):    python paragraph.py <directory>
  Output: all .txt files written with original names into <directory>/cleaned/

Rules applied (in priority order per sentence):
  1. Preserve existing double-newline paragraph breaks.
  2. Break before any sentence that opens with a quote character (new speaker).
  3. Break before sentences that begin with a time/scene transition phrase.
  4. Break when narrative prose immediately follows a dialogue sentence.
"""

import re
import sys
from pathlib import Path

# Abbreviations whose trailing period is NOT a sentence boundary.
_ABBREV_RE = re.compile(
    r'\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|Rev|Lt|Col|Gen|Sgt|Cpl|Pvt|vs|etc)\.',
    re.IGNORECASE,
)

# Phrases that almost always open a new paragraph in fiction.
_TRANSITION_RE = re.compile(
    r'^(?:'
    r'Later[,\s]|Meanwhile[,\s]|Suddenly[,\s]|Soon[,\s]|'
    r'Eventually[,\s]|Finally[,\s]|Afterwards?[,\s]|'
    r'Outside[,\s]|Upstairs[,\s]|Downstairs[,\s]|'
    r'The next\s|The following\s|'
    r'That night\b|That morning\b|That afternoon\b|That evening\b|'
    r'(?:Hours?|Minutes?|Days?|Weeks?|Months?|Years?) later\b'
    r')'
)

# Straight and curly quote characters.
_OPEN_QUOTE_RE = re.compile(r'^["“‘]')
_ANY_QUOTE_RE  = re.compile(r'["“”‘’]')


def _split_sentences(text: str) -> list[str]:
    # Mask periods inside known abbreviations so they don't trigger splits.
    masked = _ABBREV_RE.sub(lambda m: m.group(0).replace('.', '\x00'), text)
    # Split after sentence-ending punctuation followed by whitespace + capital/quote.
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z“‘"])', masked)
    return [p.replace('\x00', '.').strip() for p in parts if p.strip()]


def _paragraph_block(text: str) -> list[str]:
    """Re-paragraph a single block of prose; returns a list of paragraph strings."""
    sentences = _split_sentences(' '.join(text.split()))
    paragraphs: list[str] = []
    current: list[str] = []
    prev_has_dialogue = False

    for sent in sentences:
        opens_with_quote = bool(_OPEN_QUOTE_RE.match(sent))
        has_dialogue     = bool(_ANY_QUOTE_RE.search(sent))
        is_transition    = bool(_TRANSITION_RE.match(sent))

        should_break = (
            opens_with_quote
            or is_transition
            or (prev_has_dialogue and not has_dialogue)
        )

        if current and should_break:
            paragraphs.append(' '.join(current))
            current = []

        current.append(sent)
        prev_has_dialogue = has_dialogue

    if current:
        paragraphs.append(' '.join(current))

    return paragraphs


def _process_one(src: Path, dest: Path) -> None:
    text = src.read_text(encoding='utf-8')
    raw_blocks = re.split(r'\n\s*\n', text)
    all_paragraphs: list[str] = []
    for block in raw_blocks:
        block = block.strip()
        if block:
            all_paragraphs.extend(_paragraph_block(block))
    dest.write_text('\n\n'.join(all_paragraphs), encoding='utf-8')
    print(f"  {src.name} → {dest}  ({len(all_paragraphs)} paragraphs)")


def process(input_path: str) -> None:
    path = Path(input_path)
    if not path.exists():
        sys.exit(f"Error: path not found: {input_path}")

    if path.is_dir():
        txt_files = sorted(path.glob('*.txt'))
        if not txt_files:
            sys.exit(f"No .txt files found in {path}")
        out_dir = path / 'cleaned'
        out_dir.mkdir(exist_ok=True)
        print(f"Processing {len(txt_files)} file(s) → {out_dir}/")
        for src in txt_files:
            _process_one(src, out_dir / src.name)
    else:
        out_path = path.parent / (path.stem + '_p' + path.suffix)
        _process_one(path, out_path)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(f"Usage: python {Path(sys.argv[0]).name} <file_or_directory>")
    process(sys.argv[1])
