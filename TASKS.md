# Kurdlingo — Task List

> Last updated: 2026-03-13

---

## Research Phase — Complete ✓

All documentation is merged to `main`. These are done and ready for reference.

| Deliverable | File | Status |
|---|---|---|
| Architecture decisions (10 ADRs) | `docs/architecture/ADR.md` | ✓ Done |
| FSRS v4 spec + Dart skeleton | `docs/architecture/srs-spec.md` | ✓ Done |
| Supabase schema + SQL migration | `docs/architecture/schema.md` | ✓ Done |
| Sprint 1 coding handoff | `docs/architecture/poc-spec.md` | ✓ Done |
| Exercise type inventory | `docs/design/exercise-types.md` | ✓ Done |
| UI wireframes (char picker + skill tree) | `docs/design/ui-spec.md` | ✓ Done |
| Gamification spec | `docs/design/gamification-spec.md` | ✓ Done |
| A1 curriculum draft + 200 words | `docs/content/curriculum-v0.md` | ✓ Draft — needs your review |
| Competitive analysis | `docs/research/competitive-analysis.md` | ✓ Done |
| Vocabulary data pipeline | `data/processed/kurmanji_lean.json` | ✓ Done — 10,000 entries |
| NotebookLM libraries | 4 notebooks, 30+ sources | ✓ Done |

---

## Needs You — Native Speaker Tasks 🔴

These cannot be done by AI. They require your knowledge as a native Kurmanji speaker.
**The coding phase cannot start until item 1 is complete.**

### 1. Write `docs/content/linguistic-spec.md` 🔴 BLOCKING
This is the single document that can only come from you.

What to include:
- **Alphabet** — all 31 Kurmanji letters in order, each with a pronunciation note in plain language (e.g., "ê sounds like the 'a' in 'cake'")
- **Special characters** — ê, î, û, ç, ş: when they appear, how they affect pronunciation
- **Vowel harmony / vowel length** — if applicable
- **Verb system** — present stem vs past stem pattern, 3–5 regular examples and 3–5 irregular ones (e.g., *hatin* → *tê / hat*)
- **Ezafe construction** — when and how to use, 5 example phrases
- **Noun gender** — masculine/feminine patterns, how a learner can often guess
- **SOV word order** — brief note with examples
- **Common diaspora learner mistakes** — things second-generation speakers get wrong
- **Register notes** — formal vs informal, any regional variation relevant to A1 level

→ Even rough bullet notes are fine. I can format it properly afterward.

### 2. Review `docs/content/curriculum-v0.md` 🟡 Important
Check the 200 A1 vocabulary words and lesson groupings:
- Are the words natural for a diaspora beginner?
- Any missing high-frequency words?
- Are the lesson group names natural in Kurmanji context?

### 3. Approve `docs/architecture/poc-spec.md` 🟡 Important
Before Sprint 1 starts, confirm:
- The 5-card "Greetings" lesson is the right starting point
- The 5 seed vocabulary items in Appendix A are correct (word + gender + gloss)
- Sprint 1 scope (auth, 1 lesson, FSRS sync, char picker) matches your vision

---

## Future Research (Post-PoC) 🔵

These are not blocking Sprint 1 but should happen in parallel with early coding.

### Verb Inflection Analysis
The researcher agent will:
- Scan the `forms` field in `data/processed/kurmanji_lean.json`
- Classify regular vs irregular present stem derivations
- Cross-validate with Thackston grammar (Notebook 1)
- Produce a structured morphology report for backend to build conjugation exercises

### Audio Validation
- KurdishTTS.com API generates bulk audio
- You listen and flag any words with wrong accent or wrong dialect form
- Produces an approved word list for Sprint 2 audio pipeline

---

## Sprint 1 — PoC (Ready to Start After linguistic-spec.md) ⚡

18 tasks from `docs/architecture/poc-spec.md` — approximately 40–48 hours of dev work.

**Goal:** One working lesson. 5 multiple-choice vocabulary cards. Auth. FSRS saves locally and syncs to Supabase. Character picker bar in typing exercise. Skill tree shows 1 unlocked unit.

| # | Task | Size |
|---|---|---|
| 1 | Supabase project setup + migration run | S |
| 2 | FSRS v4 unit tests (Dart) | M |
| 3 | Drift schema + DAOs | M |
| 4 | Supabase auth (email/password) | S |
| 5 | Vocabulary seed data (5 Greetings items) | S |
| 6 | Lesson service (FSRS scheduling) | M |
| 7 | Multiple choice exercise widget | M |
| 8 | Character picker bar widget | S |
| 9 | Skill tree screen | L |
| 10 | Lesson session flow | L |
| 11 | Progress sync (Drift → Supabase) | L |
| 12 | Offline-first smoke test | M |
| 13–18 | Polish, navigation, error states, CI setup | M |

Full detail: `docs/architecture/poc-spec.md` § Section 6

---

## Roadmap

```
[DONE] Research Phase
  └── All architecture, design, curriculum, data pipeline complete

[BLOCKING ON YOU] Write linguistic-spec.md
  └── Once done → Sprint 1 starts immediately

[Sprint 1 — PoC]
  └── ~40-48h: 1 lesson, FSRS, auth, skill tree, char picker

[Sprint 2 — MVP Core]
  └── Full A1 curriculum, 5 exercise types, audio, streak system

[Sprint 3 — Beta]
  └── Closed testing with Kurdish community, feedback loop

[v1.0 — Launch]
  └── App Store + Google Play
```
