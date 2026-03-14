# Proof-of-Concept Technical Specification

> **Owner:** `backend` agent (Task B4)
> **Status:** COMPLETE
> **Last updated:** 2026-03-13
> **Blocked by:** ADR.md (architecture locked), srs-spec.md (COMPLETE), schema.md (COMPLETE)

---

## Table of Contents

1. [PoC Scope](#1-poc-scope)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Xcode Project Structure](#3-xcode-project-structure)
4. [Swift Package Dependencies](#4-swift-package-dependencies)
5. [Dev Environment Setup](#5-dev-environment-setup)
6. [Sprint 1 Task Breakdown](#6-sprint-1-task-breakdown)
7. [Definition of Done](#7-definition-of-done)

---

## 1. PoC Scope

The PoC is the smallest runnable end-to-end slice of Kurdlingo that proves the full stack
works together. Every item listed here will be built in Sprint 1. Nothing outside this list
is in scope for Sprint 1.

### 1.1 In Scope

| # | Feature | Notes |
|---|---|---|
| 1 | Email + password registration and login | Supabase Auth; profile row auto-created via DB trigger |
| 2 | Skill tree screen: 1 unit (Unit 1: Greetings), unlocked | Static seed data; no unlock logic yet |
| 3 | Lesson session: 5 vocabulary cards, Multiple Choice (L2 → L1) | Kurdish prompt → choose English answer |
| 4 | FSRS card state updated locally in SwiftData/SQLite after each answer | Full FSRS v4 scheduling; no network needed |
| 5 | Session complete screen: score (correct / total) + XP earned | XP = 10 per correct answer, flat |
| 6 | Foreground sync: dirty FSRS cards pushed to Supabase on app resume | `AppLifecycleListener`; retry up to 5 times |
| 7 | Character picker bar on any text input screen | Inserts ê / î / û / ç / ş above system keyboard |

### 1.2 Explicitly Out of Scope for PoC

- Audio playback (deferred to Sprint 2)
- Streak tracking and last-active-date logic
- Multiple exercise types (only Multiple Choice L2 → L1)
- Leagues, leaderboards, and XP rankings (dropped permanently)
- Hearts / lives system (dropped permanently)
- Sorani / Zazaki dialects
- Push notifications
- Offline content download

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Kurdlingo iOS App (SwiftUI)                       │
│                                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────────┐  │
│  │  Auth View    │   │ Skill Tree   │   │    Lesson View         │  │
│  │  (login/reg) │   │  View        │   │  (MC exercise view)    │  │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬─────────────┘  │
│         │                  │                       │                 │
│         └──────────────────┴───────────────────────┘                │
│                            │ @Observable view models                  │
│         ┌──────────────────┴───────────────────────┐                │
│         │                                           │                │
│  ┌──────▼──────────┐                   ┌───────────▼──────────┐    │
│  │  AuthRepository │                   │  LessonRepository    │    │
│  │  (supabase-swift)│                  │  (SwiftData + FSRS)  │    │
│  └──────┬──────────┘                   └───────────┬──────────┘    │
│         │                                          │                 │
│  ┌──────▼──────────────────────────────────────────▼──────────┐    │
│  │                    SyncService                               │    │
│  │  (ScenePhase observer → flush dirty rows to Supabase)       │    │
│  └──────┬──────────────────────────────────────────┬──────────┘    │
│         │                                           │                │
│  ┌──────▼──────────┐                   ┌───────────▼──────────┐    │
│  │  supabase-swift │                   │  SwiftData            │    │
│  │  (remote calls) │                   │  (local source of    │    │
│  └──────┬──────────┘                   │   truth in-session)  │    │
│         │                              └──────────────────────┘    │
└─────────┼────────────────────────────────────────────────────────────┘
          │ HTTPS / JWT
┌─────────▼───────────────────────────────────┐
│               Supabase (cloud)               │
│                                              │
│  ┌────────────┐  ┌────────────────────────┐ │
│  │  Auth      │  │  PostgreSQL            │ │
│  │  (email +  │  │  profiles              │ │
│  │   password)│  │  vocabulary_items      │ │
│  └────────────┘  │  lesson_units          │ │
│                  │  fsrs_cards            │ │
│                  │  exercise_results      │ │
│                  │  user_progress         │ │
│                  └────────────────────────┘ │
└──────────────────────────────────────────────┘

Data flow — lesson session:
  1. App launches → SyncService.pullFsrsCards() → seeds SwiftData from Supabase
  2. LessonRepository.loadLesson(unitId) → reads 5 vocabulary rows from SwiftData
  3. User answers card → FSRSScheduler.scheduleReview() → writes card to SwiftData (is_dirty=1)
  4. App foregrounded → SyncService.pushDirty() → upserts dirty cards to Supabase
```

---

## 3. Xcode Project Structure

All source lives under `Kurdlingo/`. Tests go in `KurdlingoTests/`.

```
Kurdlingo/
├── Kurdlingo.xcodeproj
├── .env                              ← gitignored; holds SUPABASE_URL + SUPABASE_ANON_KEY
├── Resources/
│   └── seed_unit_1.json              ← 5 PoC vocabulary items + unit metadata
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql
└── Kurdlingo/
    ├── KurdlingoApp.swift             ← @main entry point; injects ModelContainer + Supabase
    │
    ├── Features/
    │   ├── Auth/
    │   │   ├── AuthView.swift                ← login / register tab view
    │   │   ├── AuthViewModel.swift           ← @Observable; calls AuthRepository
    │   │   └── AuthRepository.swift          ← wraps supabase.auth.signIn / signUp
    │   │
    │   ├── SkillTree/
    │   │   ├── SkillTreeView.swift           ← shows unit cards; taps navigate to lesson
    │   │   ├── SkillTreeViewModel.swift      ← @Observable; loads units + progress
    │   │   └── UnitCardView.swift            ← single unit tile (locked/unlocked state)
    │   │
    │   └── Lesson/
    │       ├── LessonView.swift              ← orchestrates card queue; shows progress bar
    │       ├── LessonViewModel.swift         ← @Observable; owns card queue + FSRS calls
    │       ├── LessonCompleteView.swift      ← score display + XP earned
    │       └── Exercises/
    │           └── MultipleChoice/
    │               ├── MCExerciseView.swift  ← L2 prompt + 4 answer buttons
    │               └── MCDistractors.swift   ← picks 3 wrong answers from vocab pool
    │
    ├── Services/
    │   ├── SRS/
    │   │   └── FSRS.swift                    ← FSRS v4 scheduler (from srs-spec.md §7)
    │   └── Sync/
    │       └── SyncService.swift             ← pull on launch; push dirty on foreground
    │
    ├── Data/
    │   ├── Models/                           ← SwiftData @Model definitions
    │   │   ├── FSRSCard.swift
    │   │   ├── VocabularyItem.swift
    │   │   ├── LessonUnit.swift
    │   │   └── UserProgress.swift
    │   │
    │   └── Remote/
    │       ├── SupabaseManager.swift         ← singleton Supabase client
    │       ├── VocabularyRemote.swift        ← fetchAll(), fetchByUnit()
    │       ├── FSRSCardsRemote.swift         ← upsertBatch(), fetchByUser()
    │       └── UserProgressRemote.swift      ← upsertProgress()
    │
    └── Shared/
        ├── DTOs/
        │   ├── VocabularyItemDTO.swift       ← Codable for JSON/Supabase
        │   ├── LessonUnitDTO.swift
        │   └── LessonResult.swift            ← holds score + xp for complete screen
        ├── Components/
        │   ├── CharPickerBar.swift           ← SwiftUI View; row of special-char buttons
        │   └── PrimaryButton.swift           ← reusable styled button
        └── Navigation/
            └── AppRouter.swift               ← NavigationStack + NavigationPath routing

KurdlingoTests/
    ├── FSRSTests.swift
    ├── CharPickerBarTests.swift
    └── SyncServiceTests.swift
```

**File count:** ~25 Swift source files for the PoC. Every file has a single clear responsibility.

---

## 4. Swift Package Dependencies

Managed via Swift Package Manager (SPM) in Xcode.

```swift
// Package.swift dependencies (or add via Xcode → File → Add Package Dependencies)

dependencies: [
    // Supabase iOS SDK
    .package(url: "https://github.com/supabase/supabase-swift", from: "2.0.0"),
]
```

**Built-in frameworks used (no packages needed):**
- **SwiftUI** — UI framework
- **SwiftData** — local persistence (Core Data successor)
- **Foundation** — JSON decoding via `Codable`

**Version notes:**
- `supabase-swift 2.x` includes Auth, Realtime, Storage, and PostgREST clients.
- SwiftData is included in iOS 17+ — no external dependency needed.
- No code generation step required (unlike Flutter's `build_runner`). Swift's `Codable` and `@Model` work at compile time.

---

## 5. Dev Environment Setup

### 5.1 Prerequisites

| Tool | Required version | Install |
|---|---|---|
| SwiftUI SDK | 3.22.x stable | `swift.dev/docs/get-started/install` |
| Swift SDK | >=3.3.0 (bundled with SwiftUI) | Comes with SwiftUI |
| Supabase CLI | 1.x latest | `brew install supabase/tap/supabase` or `scoop install supabase` |
| Docker Desktop | Any recent stable | Required by Supabase local dev stack |

Verify before continuing:

```bash
swift doctor          # All checks green except optional items
supabase --version      # 1.x.x
docker info             # Docker daemon running
```

### 5.2 Clone and open in Xcode

```bash
git clone https://github.com/Rlight21/kurdlingo.git
cd kurdlingo
open Kurdlingo.xcodeproj
```

Xcode automatically resolves SPM dependencies (supabase-swift). No code generation step needed.

### 5.3 Start the local Supabase stack

```bash
# From the project root (supabase/ directory must exist)
supabase start
```

This starts a local PostgreSQL instance, Auth server, and REST API on Docker.
First run downloads ~1 GB of images; subsequent starts are fast.

After `supabase start` completes, the CLI prints:

```
API URL:     http://localhost:54321
DB URL:      postgresql://postgres:postgres@localhost:54322/postgres
Studio URL:  http://localhost:54323
anon key:    eyJ...  (copy this)
service_role key: eyJ...
```

### 5.5 Apply the schema migration

```bash
supabase db reset
# This runs supabase/migrations/001_initial_schema.sql automatically.
```

To run just the migration without resetting:

```bash
supabase migration up
```

Verify in Supabase Studio (http://localhost:54323) that the following tables exist:
`profiles`, `vocabulary_items`, `lesson_units`, `fsrs_cards`, `exercise_results`, `user_progress`.

### 5.6 Seed Unit 1 vocabulary

Run the seed script (Swift command-line tool):

```bash
swift scripts/seed_unit1.swift \
  --url http://localhost:54321 \
  --service-key <service_role_key_from_supabase_start>
```

This inserts 5 Kurmanji vocabulary items (Greetings unit) and the `lesson_units` row for Unit 1.

### 5.6 Configure environment variables

In Xcode, edit the scheme (Product → Scheme → Edit Scheme → Run → Arguments → Environment Variables):

```
SUPABASE_URL = http://localhost:54321
SUPABASE_ANON_KEY = <anon_key_from_supabase_start>
```

The app reads these via `ProcessInfo.processInfo.environment` in `KurdlingoApp.swift`.

### 5.7 Run the app

Select **iPhone 15 Pro** simulator in Xcode and press **Cmd+R**.

### 5.8 Run tests

Press **Cmd+U** in Xcode (or Product → Test).

SwiftData tests use `ModelConfiguration(isStoredInMemoryOnly: true)` — no additional setup needed.

---

## 6. Sprint 1 Task Breakdown

Tasks are ordered for a single developer executing them sequentially. Complexity:
**S** = <2 h, **M** = 2–4 h, **L** = 4–8 h.

| # | Task | Complexity | Notes |
|---|---|---|---|
| 1 | Supabase project setup (local CLI) + run `001_initial_schema.sql` | S | `supabase start && supabase db reset` |
| 2 | Xcode project scaffold: create project, add `supabase-swift` via SPM, configure signing | S | |
| 3 | Copy `FSRS.swift` skeleton from `srs-spec.md §7` into `Services/SRS/FSRS.swift` | S | No changes needed; spec is production-ready |
| 4 | Write FSRS unit tests (`KurdlingoTests/FSRSTests.swift`) against checklist in `srs-spec.md Appendix B` | M | Must pass before any lesson code is written |
| 5 | Implement SwiftData @Model definitions: `FSRSCard`, `VocabularyItem`, `LessonUnit`, `UserProgress` | L | Configure `ModelContainer` in `KurdlingoApp.swift` |
| 6 | Implement `AuthRepository` + `AuthView.swift` (register + login flows) | M | Uses `supabase.auth.signUp` and `supabase.auth.signIn` |
| 7 | Implement `SupabaseManager` singleton + `VocabularyRemote` + `FSRSCardsRemote` | M | Thin wrappers around `supabase.from("table")` calls |
| 8 | Implement `SyncService`: `pullFsrsCards()` on launch + `pushDirty()` on foreground | M | Use `ScenePhase` observer; retry loop with `attempts < 5` guard |
| 9 | Write seed script (`scripts/seed_unit1.swift`) and seed Unit 1 into local Supabase | S | 5 vocabulary rows + 1 lesson_unit row |
| 10 | Implement `SkillTreeView` + `SkillTreeViewModel` (reads units + user_progress from SwiftData) | M | Single unit card, unlocked, taps go to lesson |
| 11 | Implement `LessonViewModel`: load 5 cards, card queue state machine, call FSRS after each answer | L | Core lesson loop; must write card to SwiftData immediately after rating |
| 12 | Implement `MCExerciseView` (Kurdish prompt + 4 answer buttons) + `MCDistractors` helper | M | Distractors: pick 3 random from remaining vocab pool |
| 13 | Implement `LessonView` (progress bar + card queue rendering) | M | Feeds `LessonViewModel`; no audio hooks needed |
| 14 | Implement `LessonCompleteView` (score display, XP earned, back to skill tree) | S | Reads `LessonResult` Codable struct from view model |
| 15 | Implement `CharPickerBar` SwiftUI view; wire it into `AuthView` and any future text inputs | S | Row of `Button`s; each inserts char into focused `TextField` via `@FocusState` |
| 16 | Wire `NavigationStack` + `NavigationPath`: auth guard, skill tree, lesson, lesson complete | S | `NavigationStack` with `.navigationDestination` modifiers |
| 17 | Integration smoke test: register → complete lesson → check Supabase Studio for synced cards | S | Manual; verify `fsrs_cards` rows exist in local Supabase |
| 18 | Write XCTest UI tests for `CharPickerBar` (ê/î/û/ç/ş insertion) | S | `XCUIApplication`; tap each button and verify text field content |

**Total estimated effort:** ~40–48 hours (1 developer, 1 sprint week).

---

## 7. Definition of Done

The PoC sprint is complete when all of the following are true. No item may be skipped.

### Functional checklist

- [ ] A new user can register with an email and password; a `profiles` row is automatically created in Supabase (via the `handle_new_user` trigger)
- [ ] A returning user can log in with their credentials and land on the skill tree
- [ ] The skill tree screen shows exactly 1 unit (Unit 1: Greetings) in the unlocked state
- [ ] Tapping the unit launches a lesson session with exactly 5 vocabulary cards
- [ ] Each card shows a Kurmanji word (L2) as the prompt and 4 English answer buttons (L1)
- [ ] Selecting an answer reveals whether it was correct and shows the Again / Hard / Good / Easy FSRS rating buttons
- [ ] After rating, the next card is shown; the progress bar advances
- [ ] After the 5th card, the session complete screen shows the correct-answer count and XP earned
- [ ] All 5 FSRS card states are persisted to the local SwiftData database immediately after rating (verified by re-launching the app and inspecting the DB via SwiftData DevTools or a direct SQLite query)
- [ ] On app kill + relaunch, previously scheduled cards retain their `state`, `stability`, `difficulty`, and `due_date` (FSRS state survives app restart)
- [ ] Bringing the app back to the foreground after a lesson triggers `SyncService.pushDirty()`; the updated `fsrs_cards` rows appear in Supabase Studio within 5 seconds on a healthy connection
- [ ] The character picker bar is visible whenever a text field is focused on both the login screen and any screen with a text input
- [ ] Tapping ê, î, û, ç, ş in the character picker bar inserts the correct Unicode character into the active text field
- [ ] The app compiles and runs on iOS Simulator (iPhone 15 Pro, iOS 17+) without errors

### Test checklist

- [ ] All FSRS unit tests pass (`KurdlingoTests/FSRSTests.swift`), covering the 10 cases in `srs-spec.md Appendix B`
- [ ] `CharPickerBar` UI tests pass: each of the 5 special characters is inserted correctly
- [ ] All tests pass in Xcode (Cmd+U, exit code 0)
- [ ] No compiler warnings in Xcode (Build Succeeded with 0 warnings)

### Code quality checklist

- [ ] No hardcoded Supabase URLs or keys in source files; all secrets injected via Xcode scheme environment variables
- [ ] `.env` is listed in `.gitignore`
- [ ] All @Observable view models use explicit types (no `Any`)
- [ ] SwiftData `isDirty` flag is always set to `true` before the FSRS write returns — never left in an ambiguous state
- [ ] `SyncService.pushDirty()` handles network failure gracefully (increments `attempts`; stops retrying at 5)

---

## Appendix A — Seed Data Format

`assets/content/seed_unit_1.json` (loaded by `scripts/seed_unit1.swift`):

```json
{
  "unit": {
    "level": "A1.1",
    "unit_number": 1,
    "title_kurmanji": "Silav û Nasîn",
    "title_english": "Greetings",
    "required_xp": 0
  },
  "vocabulary": [
    { "word": "Silav",   "pos": "noun",        "glosses": { "en": "Hello / Greeting" }, "tags": ["A1", "greetings"] },
    { "word": "Spas",    "pos": "noun",        "glosses": { "en": "Thank you" },        "tags": ["A1", "greetings"] },
    { "word": "Erê",     "pos": "particle",    "glosses": { "en": "Yes" },              "tags": ["A1", "greetings"] },
    { "word": "Na",      "pos": "particle",    "glosses": { "en": "No" },               "tags": ["A1", "greetings"] },
    { "word": "Xatirê te", "pos": "phrase",   "glosses": { "en": "Goodbye" },           "tags": ["A1", "greetings"] }
  ]
}
```

All `word` values use Kurmanji Latin script with special characters from the
approved set: ê (U+00EA), î (U+00EE), û (U+00FB), ç (U+00E7), ş (U+015F).
The developer (native speaker) must validate all vocabulary before seeding.

---

## Appendix B — Key Design Decisions for the Developer

These are decisions already locked in the ADR. Do not re-debate them during Sprint 1.

| Decision | Locked choice | Rationale summary |
|---|---|---|
| Local DB | SwiftData | Offline-first FSRS; native Apple persistence, iCloud-ready |
| Sync strategy | Dirty flag + foreground push | Simpler than real-time subscriptions for PoC; good enough until multi-device sync is needed |
| FSRS persistence | SwiftData is source of truth during session; Supabase is authoritative after sync | Avoids network latency on every card flip |
| Conflict resolution | Last-write-wins on `updated_at` | Acceptable for single-device PoC; multi-device reconciliation is Sprint 3+ concern |
| Auth | Supabase email+password | Simplest path; OAuth (Google/Apple) deferred |
| Exercise type | Multiple Choice L2→L1 only | Fastest to build; proves the card queue and FSRS loop work end-to-end |
| XP formula | 10 XP per correct answer, flat | No balancing needed for PoC; gamification spec (F4) will revise in Sprint 2 |
| Character input | Picker bar above keyboard | Clean UX; see CLAUDE.md |

---

## Appendix C — Supabase Column Mapping (Swift ↔ DB)

When serialising `FSRSCard` to the `fsrs_cards` Supabase table, use this mapping.
The SwiftData `@Model` uses Swift property names; Supabase uses snake_case.

| Swift property | Supabase column | Swift type | DB type |
|---|---|---|---|
| `id` | `id` | `UUID` | UUID |
| `userId` | `user_id` | `UUID` | UUID |
| `vocabularyItemId` | `vocabulary_item_id` | `UUID` | UUID |
| `stability` | `stability` | `Double` | FLOAT8 |
| `difficulty` | `difficulty` | `Double` | FLOAT8 |
| `dueDate` | `due_date` | `Date` | TIMESTAMPTZ |
| `lastReview` | `last_review` | `Date?` | TIMESTAMPTZ nullable |
| `reviewCount` | `review_count` | `Int` | INT |
| `state` | `state` | `String` | TEXT |
| `updatedAt` | `updated_at` | `Date` | TIMESTAMPTZ |
| `isDirty` | _(local only)_ | `Bool` | _(SwiftData only)_ |

`isDirty` is a SwiftData-only property. Never include it in Supabase upsert payloads. Use `CodingKeys` to exclude it from `Codable` conformance.
