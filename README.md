# Kurdlingo

> A Duolingo-inspired mobile app for learning Kurdish (Kurmanji dialect) — iOS & Android.

---

## Why Kurdlingo?

Kurdish is spoken by 30–40 million people worldwide, yet no major language learning platform offers a quality Kurdish course. Kurdlingo fills this gap with a gamified, science-backed mobile experience built by and for the Kurdish community — starting with Kurmanji, the most widely spoken dialect.

---

## Current Status

**Research Phase** — gathering literature, making architecture decisions, building documentation before any code is written.

See [`/docs/`](docs/) for all deliverables.

---

## Target Users

- **Primary:** Kurdish diaspora (heritage learners in Netherlands, Germany, Sweden, UK) wanting to reconnect with their language
- **Secondary:** Complete beginners with no prior Kurdish knowledge

---

## Planned Features (MVP)

- Skill tree with A1 → B1 Kurmanji curriculum
- Spaced repetition (FSRS v4) for vocabulary retention
- Audio for all vocabulary (KurdishTTS.com API + native speaker recordings)
- Gamification: XP, streaks, progress tracking
- Special character support (ê, î, û, ç, ş)
- Offline-capable with Supabase sync

---

## Tech Stack

| Layer | Technology |
|---|---|
| Mobile | Flutter (Dart) |
| Backend | Supabase (PostgreSQL) |
| State | Riverpod |
| SRS | FSRS v4 |
| Audio | KurdishTTS.com API |

---

## Roadmap

- [ ] **Research Phase** ← *we are here*
- [ ] Architecture & Design Decisions
- [ ] PoC: Single lesson, one exercise type, audio playback
- [ ] MVP Sprint 1: Core skill tree, 5 exercise types, user accounts
- [ ] MVP Sprint 2: Full A1 curriculum, streak system, audio complete
- [ ] Beta: Closed testing with Kurdish community

---

## Contributing

This project is in early research. Contributions welcome once the MVP phase begins — especially from native Kurdish speakers, educators, and Flutter developers.

---

## License

TBD
