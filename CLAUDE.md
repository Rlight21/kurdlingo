# Kurdlingo — Project CLAUDE.md

## What Is This Project
Kurdlingo is a Duolingo-inspired mobile app for learning Kurdish, starting with the Kurmanji dialect. **iOS-native** (SwiftUI). The developer is a **native Kurmanji speaker** who validates all linguistic content.

---

## AI Staff

| Agent | Model | Tools | Responsibility |
|---|---|---|---|
| Claude (Staff Manager) | Opus 4.6 | All | Orchestrate, delegate, review deliverables |
| `researcher` | Haiku (fast) | Tavily + NotebookLM | Literature search, NotebookLM population, Briefing Docs |
| `frontend` | DeepSeek V3.2 | DeepSeek MCP + Read/Write/Bash | SwiftUI UI/UX, wireframes, character input design |
| `backend` | Qwen 3 coder 480b | Qwen MCP + Read/Write/Bash | Supabase schema, FSRS algorithm, PoC spec |

**Sub-agent files:** `.claude/agents/` (project-local, not global)

**When to delegate:**
- Research / literature → `researcher`
- UI/UX / SwiftUI component design → `frontend`
- Schema / algorithm / data pipeline → `backend`

---

## Tech Stack (Decided)

| Layer | Choice | Rationale |
|---|---|---|
| Mobile framework | **SwiftUI (Swift)** | iOS-native performance; first-class Apple ecosystem |
| Backend | **Supabase** | Relational schema for SRS; predictable pricing |
| State management | **SwiftUI @Observable + SwiftData** | Native Apple state management |
| SRS algorithm | **FSRS v4** | Outperforms SM-2; no training data needed |
| Audio | **KurdishTTS.com API** + native recordings | API for bulk; native speaker validates Kurmanji accent |
| Content format | **JSON/YAML in repo** (MVP) | Simple, version-controlled, Qwen-generatable |

---

## Content Pipeline

1. **Vocabulary source:** Kaikki.org Kurmanji JSONL dumps (March 2026, Wiktionary-extracted)
2. **Audio:** KurdishTTS.com API for bulk generation → native speaker (user) validates accent
3. **Curriculum structure:** `docs/content/curriculum-v0.md` (user-authored)
4. **Linguistic authority:** Developer is native Kurmanji speaker — all language content must be validated by them

---

## Kurmanji Language Notes

- **Script:** Latin-based, LTR
- **Special characters:** ê (U+00EA), î (U+00EE), û (U+00FB), ç (U+00E7), ş (U+015F)
- **Keyboard:** Character picker bar above keyboard for typing exercises
- **Future dialects:** Sorani (Arabic script, RTL) and Zazaki may be added later — architect for extensibility
- **Grammar features:** ezafe construction, verb root system (present/past stems), SOV word order

---

## Project Phase

**Currently: Research Phase** — no coding yet.

See `/docs/` for all deliverables. Coding begins when `docs/architecture/poc-spec.md` is complete.

---

## GitHub

- Repo: `kurdlingo`
- GitHub MCP: `@modelcontextprotocol/server-github` (PAT required — provide to enable milestone/issue automation)
- Issue templates: `.github/ISSUE_TEMPLATE/`
- Milestones: Research Phase → MVP Sprint 1 → MVP Sprint 2

---

## Docs Structure

```
docs/
  architecture/
    ADR.md              ← All architecture decisions (backend agent B1)
    srs-spec.md         ← FSRS v4 spec + Swift skeleton (backend B2)
    schema.md           ← Supabase PostgreSQL schema (backend B3)
    poc-spec.md         ← PoC coding handoff doc (backend B4)
  content/
    linguistic-spec.md  ← Kurmanji alphabet, phonology, grammar (USER writes)
    curriculum-v0.md    ← Skill tree skeleton + top-200 vocab (USER writes)
  design/
    exercise-types.md   ← Exercise inventory + MVP build order (frontend F1)
    ui-spec.md          ← Screen wireframes, char input, skill tree (frontend F2+F3)
    gamification-spec.md← XP, streaks, hearts audit (frontend F4)
  research/
    competitive-analysis.md ← App comparison, user persona (from Notebook 4)
```

---

## Conventions

- Always ask: which staff member should handle this?
- Do not start coding until `poc-spec.md` is complete and user-approved
- All linguistic content must be validated by the native speaker (user)
- Commit messages: conventional commits (`feat:`, `docs:`, `chore:`, etc.)
- Kurdish text in code/docs uses Unicode codepoints explicitly when relevant
