"""Convert kurmanji_lean.json to NotebookLM-friendly text files, split by POS."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

with open("data/processed/kurmanji_lean.json", encoding="utf-8") as f:
    entries = json.load(f)

def fmt(e):
    pos     = e.get("pos", "").upper()
    word    = e.get("word", "")
    glosses = " / ".join(e.get("glosses", [])[:2])
    ipa     = f" [{e['ipa']}]" if e.get("ipa") else ""
    ex = ""
    if e.get("examples"):
        ex0 = e["examples"][0]
        ex = f" | ex: {ex0.get('text', '')}"
        if ex0.get("translation"):
            ex += f" ({ex0['translation']})"
    return f"{pos}: {word}{ipa} | {glosses}{ex}"

nouns = [e for e in entries if e.get("pos") != "verb"]
verbs = [e for e in entries if e.get("pos") == "verb"][:2500]

noun_lines = [
    "KURDLINGO — KURMANJI NOUNS, ADJECTIVES & ADVERBS",
    f"{len(nouns):,} entries from Kaikki.org (Wiktionary), scored by completeness",
    "=" * 60, ""
] + [fmt(e) for e in nouns]

verb_lines = [
    "KURDLINGO — KURMANJI VERBS (top 2,500 by completeness score)",
    "Source: Kaikki.org (Wiktionary)",
    "=" * 60, ""
] + [fmt(e) for e in verbs]

noun_text = "\n".join(noun_lines)
verb_text = "\n".join(verb_lines)

Path("data/processed/kurmanji_nouns.txt").write_text(noun_text, encoding="utf-8")
Path("data/processed/kurmanji_verbs.txt").write_text(verb_text, encoding="utf-8")

print(f"Nouns/adj/adv : {len(nouns):,} entries — {len(noun_text):,} chars")
print(f"Verbs         : {len(verbs):,} entries — {len(verb_text):,} chars")
print("Done.")
