"""
parse_dataset.py
-----------------
Parses the Mendeley "Comprehensive Dataset of Tomato Plant Diseases" CSV
(Jagtap et al. 2025, DOI: 10.17632/ztncd79yhk.1) into cleaned candidate
statements per disease/category, for manual curation into KG nodes.

This does NOT try to fully automate symptom/treatment extraction into a
final KG (that still needs human judgment to pick representative, atomic
entries) - it does the mechanical cleaning: splitting free-text cells into
individual candidate statements, stripping noise, and deduplicating near-
identical lines, so curation starts from a clean list instead of raw
paragraphs.
"""
import csv
import re
from collections import defaultdict

def clean_lines(text):
    if not text:
        return []
    lines = [l.strip() for l in text.split("\n")]
    lines = [l for l in lines if len(l) > 8]  # drop empty/near-empty lines
    # dedupe near-identical lines (case-insensitive, whitespace-normalized)
    seen = set()
    out = []
    for l in lines:
        key = re.sub(r"\s+", " ", l.lower()).strip(" .")
        if key not in seen:
            seen.add(key)
            out.append(l)
    return out

def parse(csv_path):
    data = defaultdict(lambda: defaultdict(list))
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # header
        for row in reader:
            if not row or not row[0].strip():
                continue
            disease, feature, text = row[0].strip(), row[1].strip(), row[2] if len(row) > 2 else ""
            data[disease][feature].extend(clean_lines(text))
    return data

if __name__ == "__main__":
    import sys, json
    import os
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mendeley_tomato_dataset.csv")
    result = parse(sys.argv[1] if len(sys.argv) > 1 else default)
    for disease, features in result.items():
        print(f"\n{'='*70}\n{disease}\n{'='*70}")
        for feat, lines in features.items():
            print(f"\n--- {feat} ({len(lines)} candidate lines) ---")
            for l in lines[:6]:
                print(f"  - {l[:100]}")
            if len(lines) > 6:
                print(f"  ... +{len(lines)-6} more")
