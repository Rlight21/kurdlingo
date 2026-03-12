#!/usr/bin/env python3
"""
slice_dictionary.py
-------------------
Slices the Kaikki.org Kurdish JSONL dump into a lean Kurmanji MVP dataset.

Streams line-by-line to avoid loading 721MB into RAM.
Filters, scores by completeness, and outputs the top 10,000 entries.

Input:  ./data/raw/kaikki_kurdish.jsonl
Output: ./data/processed/kurmanji_lean.json  (target < 30MB)

Usage:
    python scripts/slice_dictionary.py
    python scripts/slice_dictionary.py --limit 5000 --input data/raw/kaikki_kurdish.jsonl
"""

import json
import heapq
import argparse
import sys
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1252 crash on Kurdish characters)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_INPUT  = Path("data/raw/kaikki_kurdish.jsonl")
DEFAULT_OUTPUT = Path("data/processed/kurmanji_lean.json")
DEFAULT_LIMIT  = 10_000

# Kaikki's Kurdish Wiktionary dump uses Kurmancî as the lang name, "ku" as code
# (ku = macro-code that maps to Kurmancî/Kurmanji on Wiktionary)
LANG_NAMES = {"Kurmancî", "Kurmanji", "Kurmanji Kurdish", "Northern Kurdish"}
LANG_CODE  = "ku"   # lang_code used by this specific Kaikki dump

# Only keep these parts of speech for MVP vocabulary
KEEP_POS = {"noun", "verb", "adj", "adv"}


# ---------------------------------------------------------------------------
# Scoring — higher score = more complete/useful entry
# ---------------------------------------------------------------------------

def score_entry(entry: dict) -> int:
    """
    Score an entry by how much useful data it carries.
    Used to rank and select the top N entries.
    """
    score = 0
    for sense in entry.get("senses", []):
        score += len(sense.get("glosses", []))        # +1 per English definition
        score += len(sense.get("examples", [])) * 2   # +2 per example sentence (high value)
        score += len(sense.get("tags", []))            # +1 per semantic tag

    if entry.get("sounds"):       score += 2  # has IPA / audio
    if entry.get("forms"):        score += 2  # has inflected forms (plurals, conjugations)
    if entry.get("etymology_text"): score += 1

    return score


# ---------------------------------------------------------------------------
# Extraction — keep only the fields the app needs
# ---------------------------------------------------------------------------

def extract_lean(entry: dict) -> dict:
    """
    Strip an entry down to the fields needed for the Kurdlingo content pipeline.
    Drops raw Wiktionary markup noise.
    """
    lean: dict = {
        "word": entry.get("word", ""),
        "pos":  entry.get("pos", ""),
    }

    # Collect glosses (English translations/definitions)
    glosses: list[str] = []
    examples: list[dict] = []

    for sense in entry.get("senses", []):
        for g in sense.get("glosses", []):
            if g and g not in glosses:
                glosses.append(g)
        for ex in sense.get("examples", []):
            kurmanji_text  = ex.get("text", "").strip()
            english_text   = ex.get("english", "").strip()
            if kurmanji_text and {"text": kurmanji_text} not in examples:
                examples.append({
                    "text":        kurmanji_text,
                    "translation": english_text or None,
                })

    lean["glosses"] = glosses
    if examples:
        lean["examples"] = examples[:2]  # cap at 2 per entry to keep file small

    # IPA pronunciation (first available)
    ipa_list = [s["ipa"] for s in entry.get("sounds", []) if s.get("ipa")]
    if ipa_list:
        lean["ipa"] = ipa_list[0]

    # Inflected forms (plurals, verb conjugations, etc.) — cap at 8
    raw_forms = entry.get("forms", [])
    if raw_forms:
        lean["forms"] = [
            {"form": f.get("form", ""), "tags": f.get("tags", [])}
            for f in raw_forms[:8]
            if f.get("form")
        ]

    # Semantic tags from first sense (e.g. "colloquial", "anatomy", etc.)
    first_tags = entry.get("senses", [{}])[0].get("tags", [])
    if first_tags:
        lean["tags"] = first_tags

    return lean


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main(input_path: Path, output_path: Path, limit: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Input : {input_path}  ({input_path.stat().st_size / 1e6:.0f} MB)")
    print(f"Output: {output_path}")
    print(f"Target: top {limit:,} Kurmanji entries\n")

    # Min-heap of (score, tiebreak_index, lean_entry).
    # Keeping only `limit` items means RAM usage stays constant
    # regardless of how many Kurmanji entries the file contains.
    heap: list[tuple[int, int, dict]] = []

    total_lines = 0
    skipped_lang = 0
    skipped_pos  = 0
    skipped_gloss = 0
    matched = 0

    with open(input_path, "r", encoding="utf-8") as fh:
        for raw_line in fh:
            total_lines += 1

            if total_lines % 200_000 == 0:
                print(f"  {total_lines:>9,} lines scanned | "
                      f"{matched:>6,} Kurmanji matched | "
                      f"heap size: {len(heap):,}")

            raw_line = raw_line.strip()
            if not raw_line:
                continue

            try:
                entry = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            # --- Filter 1: language ---
            if (entry.get("lang", "") not in LANG_NAMES
                    and entry.get("lang_code", "") != LANG_CODE):
                skipped_lang += 1
                continue

            # --- Filter 2: part of speech ---
            if entry.get("pos", "").lower() not in KEEP_POS:
                skipped_pos += 1
                continue

            # --- Filter 3: must have at least one gloss ---
            has_gloss = any(
                sense.get("glosses")
                for sense in entry.get("senses", [])
            )
            if not has_gloss:
                skipped_gloss += 1
                continue

            matched += 1
            score = score_entry(entry)
            lean  = extract_lean(entry)

            if len(heap) < limit:
                heapq.heappush(heap, (score, matched, lean))
            elif score > heap[0][0]:
                heapq.heapreplace(heap, (score, matched, lean))

    # Sort descending by score for output
    results = sorted(heap, key=lambda x: x[0], reverse=True)
    output_entries = [item[2] for item in results]

    # Write JSON
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(output_entries, fh, ensure_ascii=False, indent=2)

    size_mb = output_path.stat().st_size / (1024 * 1024)

    # Summary
    print(f"\n{'='*55}")
    print(f"  Total lines scanned : {total_lines:>10,}")
    print(f"  Skipped (language)  : {skipped_lang:>10,}")
    print(f"  Skipped (POS)       : {skipped_pos:>10,}")
    print(f"  Skipped (no gloss)  : {skipped_gloss:>10,}")
    print(f"  Matched Kurmanji    : {matched:>10,}")
    print(f"  Written to output   : {len(output_entries):>10,}")
    print(f"  Output size         : {size_mb:>9.1f} MB")
    print(f"{'='*55}")

    pos_counts: dict[str, int] = {}
    for e in output_entries:
        pos_counts[e["pos"]] = pos_counts.get(e["pos"], 0) + 1
    print("\nPOS breakdown in output:")
    for pos, count in sorted(pos_counts.items(), key=lambda x: -x[1]):
        print(f"  {pos:<6} {count:,}")

    print(f"\n✓ Saved → {output_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Slice Kaikki Kurdish JSONL to lean Kurmanji dataset")
    parser.add_argument("--input",  type=Path, default=DEFAULT_INPUT,  help="Path to raw JSONL file")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path for output JSON")
    parser.add_argument("--limit",  type=int,  default=DEFAULT_LIMIT,  help="Max entries to output")
    args = parser.parse_args()

    main(args.input, args.output, args.limit)
