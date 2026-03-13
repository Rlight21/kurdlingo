# Kurdlingo

> A Duolingo-inspired mobile app for learning Kurdish (Kurmanji dialect) — iOS & Android.
> Built by a native Kurmanji speaker. Designed for the Kurdish diaspora.

---

## Why Kurdlingo?

Kurdish is spoken by 30–40 million people worldwide. The Kurmanji dialect alone has ~15 million speakers — yet no major language platform (Duolingo, Babbel, Pimsleur) offers a Kurmanji course. Existing Kurdish apps are either limited in scope or plagued by technical bugs.

Kurdlingo fills this gap with:
- A **science-backed SRS engine** (FSRS v4) for vocabulary retention
- A **structured curriculum** from A1 to B1, including Kurmanji verb morphology and ezafe
- **Diaspora-first design** — gamification engineered for heritage learners, not tourist phrasebooks
- **Native speaker authority** — all linguistic content validated by a fluent Kurmanji speaker

---

## Current Status

**Research Phase complete → entering coding phase.**

All architecture decisions are locked and documented. Sprint 1 (PoC) is ready to begin.

| Document | Status |
|---|---|
| [`docs/architecture/ADR.md`](docs/architecture/ADR.md) | ✓ Complete — 10 architecture decisions |
| [`docs/architecture/srs-spec.md`](docs/architecture/srs-spec.md) | ✓ Complete — FSRS v4 spec + Dart skeleton |
| [`docs/architecture/schema.md`](docs/architecture/schema.md) | ✓ Complete — Supabase PostgreSQL schema |
| [`docs/architecture/poc-spec.md`](docs/architecture/poc-spec.md) | ✓ Complete — Sprint 1 coding handoff |
| [`docs/design/exercise-types.md`](docs/design/exercise-types.md) | ✓ Complete — 13 exercise types, MVP build order |
| [`docs/design/ui-spec.md`](docs/design/ui-spec.md) | ✓ Complete — char picker + skill tree wireframes |
| [`docs/design/gamification-spec.md`](docs/design/gamification-spec.md) | ✓ Complete — diaspora-aware gamification |
| [`docs/content/curriculum-v0.md`](docs/content/curriculum-v0.md) | ✓ Draft — 200 A1 words, native speaker review needed |
| [`docs/content/linguistic-spec.md`](docs/content/linguistic-spec.md) | ⏳ Awaiting native speaker (user) |
| [`docs/research/competitive-analysis.md`](docs/research/competitive-analysis.md) | ✓ Complete |

---

## Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Mobile | **Flutter** (Dart) | AOT performance, single codebase, HarfBuzz Unicode |
| Backend | **Supabase** (PostgreSQL) | Relational SRS schema, RLS, predictable pricing |
| State | **Riverpod** | Compile-time safe, testable providers |
| SRS | **FSRS v4** | Outperforms SM-2; no training data needed |
| Audio | **KurdishTTS.com** + native recordings | API for bulk; native speaker validates accent |
| Content | **JSON/YAML in repo** (MVP) | Version-controlled, Qwen-generatable |

---

## Kurmanji Language Notes

- **Script:** Latin-based, left-to-right
- **Special characters:** ê (U+00EA), î (U+00EE), û (U+00FB), ç (U+00E7), ş (U+015F)
- **Input:** Character picker bar above keyboard (not long-press — unreliable on Android)
- **Grammar highlights:** ezafe construction, verb root system (present/past stems), SOV word order
- **Future:** Sorani (Arabic script, RTL) and Zazaki may be added — architecture is extensible

---

## Roadmap

- [x] **Research Phase** — literature, architecture decisions, design specs
- [ ] **PoC** ← *starting now* — 1 lesson, 5 MC cards, FSRS sync, auth, char picker
- [ ] **MVP Sprint 1** — core skill tree, 5 exercise types, user accounts, A1.1 content
- [ ] **MVP Sprint 2** — full A1 curriculum, audio complete, streak system
- [ ] **Beta** — closed testing with Kurdish diaspora community
- [ ] **v1.0** — public launch, App Store + Google Play

---

## Docs Structure

```
docs/
  architecture/
    ADR.md              ← All 10 architecture decisions
    srs-spec.md         ← FSRS v4 spec + Dart skeleton
    schema.md           ← Supabase PostgreSQL schema + SQL migration
    poc-spec.md         ← PoC coding handoff (Sprint 1)
  content/
    linguistic-spec.md  ← Kurmanji alphabet, phonology, grammar (USER writes)
    curriculum-v0.md    ← A1 skill tree skeleton + 200 vocabulary words
  design/
    exercise-types.md   ← 13 exercise types + MVP build order
    ui-spec.md          ← Screen wireframes, char picker, skill tree
    gamification-spec.md← XP, streaks, diaspora-aware design decisions
  research/
    competitive-analysis.md ← App comparison, user personas, market gaps
```

---

## Contributing

Contributions welcome — especially from:
- **Native Kurdish speakers** (linguistic validation, content review)
- **Kurdish community members** (user research, feedback)
- **Flutter developers** (once Sprint 1 begins)

All linguistic content must be validated by a native Kurmanji speaker before entering the app.

---

## License

TBD
