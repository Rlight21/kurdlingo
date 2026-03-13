# Proof-of-Concept Technical Specification

> **Owner:** `backend` agent (Task B4)
> **Status:** COMPLETE
> **Last updated:** 2026-03-13
> **Blocked by:** ADR.md (architecture locked), srs-spec.md (COMPLETE), schema.md (COMPLETE)

---

## Table of Contents

1. [PoC Scope](#1-poc-scope)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Flutter Project Structure](#3-flutter-project-structure)
4. [Flutter Dependencies](#4-flutter-dependencies)
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
| 4 | FSRS card state updated locally in Drift/SQLite after each answer | Full FSRS v4 scheduling; no network needed |
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
│                         Flutter App (Dart)                           │
│                                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────────┐  │
│  │  Auth Screen  │   │ Skill Tree   │   │    Lesson Screen       │  │
│  │  (login/reg) │   │  Screen      │   │  (MC exercise widget)  │  │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬─────────────┘  │
│         │                  │                       │                 │
│         └──────────────────┴───────────────────────┘                │
│                            │ Riverpod providers                      │
│         ┌──────────────────┴───────────────────────┐                │
│         │                                           │                │
│  ┌──────▼──────────┐                   ┌───────────▼──────────┐    │
│  │  AuthRepository │                   │  LessonRepository    │    │
│  │  (Supabase SDK) │                   │  (Drift + FSRS)      │    │
│  └──────┬──────────┘                   └───────────┬──────────┘    │
│         │                                          │                 │
│  ┌──────▼──────────────────────────────────────────▼──────────┐    │
│  │                    SyncService                               │    │
│  │  (AppLifecycleListener → flush dirty rows to Supabase)      │    │
│  └──────┬──────────────────────────────────────────┬──────────┘    │
│         │                                           │                │
│  ┌──────▼──────────┐                   ┌───────────▼──────────┐    │
│  │  Supabase SDK   │                   │  Drift / SQLite      │    │
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
  1. App launches → SyncService.pullFsrsCards() → seeds Drift from Supabase
  2. LessonRepository.loadLesson(unitId) → reads 5 vocabulary rows from Drift
  3. User answers card → FSRSScheduler.scheduleReview() → writes card to Drift (is_dirty=1)
  4. App foregrounded → SyncService.pushDirty() → upserts dirty cards to Supabase
```

---

## 3. Flutter Project Structure

All source lives under `lib/`. Test files mirror this tree under `test/`.

```
kurdlingo/
├── pubspec.yaml
├── pubspec.lock
├── analysis_options.yaml
├── .env                          ← gitignored; holds SUPABASE_URL + SUPABASE_ANON_KEY
├── assets/
│   └── content/
│       └── seed_unit_1.json      ← 5 PoC vocabulary items + unit metadata
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql
└── lib/
    ├── main.dart                 ← entry point; initialises Supabase + Drift; runs app
    ├── app.dart                  ← MaterialApp.router with GoRouter; ProviderScope wrapper
    │
    ├── features/
    │   ├── auth/
    │   │   ├── auth_screen.dart           ← login / register tab view
    │   │   ├── auth_controller.dart       ← Riverpod AsyncNotifier; calls AuthRepository
    │   │   └── auth_repository.dart       ← wraps supabase.auth.signIn / signUp
    │   │
    │   ├── skill_tree/
    │   │   ├── skill_tree_screen.dart     ← shows unit cards; taps navigate to lesson
    │   │   ├── skill_tree_controller.dart ← Riverpod provider; loads units + progress
    │   │   └── unit_card_widget.dart      ← single unit tile (locked/unlocked state)
    │   │
    │   └── lesson/
    │       ├── lesson_screen.dart         ← orchestrates card queue; shows progress bar
    │       ├── lesson_controller.dart     ← AsyncNotifier; owns card queue + FSRS calls
    │       ├── lesson_complete_screen.dart← score display + XP earned
    │       └── exercises/
    │           └── multiple_choice/
    │               ├── mc_exercise_widget.dart    ← L2 prompt + 4 answer buttons
    │               └── mc_distractors.dart        ← picks 3 wrong answers from vocab pool
    │
    ├── services/
    │   ├── srs/
    │   │   └── fsrs.dart                 ← FSRS v4 scheduler (from srs-spec.md §7)
    │   └── sync/
    │       └── sync_service.dart         ← pull on launch; push dirty on foreground
    │
    ├── data/
    │   ├── local/
    │   │   ├── app_database.dart         ← Drift database class (tables + DAOs)
    │   │   ├── tables/
    │   │   │   ├── fsrs_cards_table.dart ← Drift table definition
    │   │   │   ├── vocabulary_table.dart ← local cache of vocabulary_items
    │   │   │   ├── lesson_units_table.dart
    │   │   │   └── user_progress_table.dart
    │   │   └── daos/
    │   │       ├── fsrs_cards_dao.dart   ← getDirty(), upsert(), markClean()
    │   │       ├── vocabulary_dao.dart
    │   │       ├── lesson_units_dao.dart
    │   │       └── user_progress_dao.dart
    │   │
    │   └── remote/
    │       ├── supabase_client.dart      ← singleton Supabase client provider
    │       ├── vocabulary_remote.dart    ← fetchAll(), fetchByUnit()
    │       ├── fsrs_cards_remote.dart    ← upsertBatch(), fetchByUser()
    │       └── user_progress_remote.dart ← upsertProgress()
    │
    └── shared/
        ├── models/
        │   ├── vocabulary_item.dart      ← freezed value object
        │   ├── lesson_unit.dart          ← freezed value object
        │   └── lesson_result.dart        ← freezed; holds score + xp for complete screen
        ├── providers/
        │   └── app_providers.dart        ← top-level Riverpod providers (db, supabase)
        └── widgets/
            ├── char_picker_bar/
            │   ├── char_picker_bar.dart  ← StatelessWidget; row of special-char buttons
            │   └── char_picker_bar_test.dart  ← (in test/ mirror)
            └── primary_button.dart       ← reusable styled button
```

**File count:** ~30 Dart source files for the PoC. Every file has a single clear responsibility.

---

## 4. Flutter Dependencies

Add to `pubspec.yaml`. Versions are the latest stable as of early 2026.

```yaml
name: kurdlingo
description: Duolingo-inspired Kurdish learning app — PoC
publish_to: 'none'
version: 0.1.0+1

environment:
  sdk: '>=3.3.0 <4.0.0'
  flutter: '>=3.22.0'

dependencies:
  flutter:
    sdk: flutter

  # --- State management ---
  flutter_riverpod: ^2.5.1
  riverpod_annotation: ^2.3.5

  # --- Navigation ---
  go_router: ^14.2.0

  # --- Supabase ---
  supabase_flutter: ^2.5.3

  # --- Local database (Drift / SQLite) ---
  drift: ^2.20.0
  drift_flutter: ^0.2.1          # bundles sqlite3 for Flutter
  sqlite3_flutter_libs: ^0.5.24  # native SQLite3 for iOS + Android

  # --- Code generation helpers ---
  freezed_annotation: ^2.4.4
  json_annotation: ^4.9.0

  # --- Path provider (Drift DB location) ---
  path_provider: ^2.1.3
  path: ^1.9.0

dev_dependencies:
  flutter_test:
    sdk: flutter

  # --- Code generation ---
  build_runner: ^2.4.9
  riverpod_generator: ^2.4.3
  freezed: ^2.5.2
  json_serializable: ^6.8.0
  drift_dev: ^2.20.0

  # --- Linting ---
  flutter_lints: ^4.0.0
```

**Version notes:**
- `supabase_flutter ^2.5.3` ships the GoTrue auth client and Realtime; no separate package needed.
- `drift_flutter ^0.2.1` replaces the old `moor_flutter`; bundles the correct native SQLite for each platform without manual linking.
- `sqlite3_flutter_libs` is required on Android (no system SQLite guarantee); on iOS the system SQLite is used but the package is still listed for parity.
- Do not add `riverpod` directly — `flutter_riverpod` re-exports it.

---

## 5. Dev Environment Setup

### 5.1 Prerequisites

| Tool | Required version | Install |
|---|---|---|
| Flutter SDK | 3.22.x stable | `flutter.dev/docs/get-started/install` |
| Dart SDK | >=3.3.0 (bundled with Flutter) | Comes with Flutter |
| Supabase CLI | 1.x latest | `brew install supabase/tap/supabase` or `scoop install supabase` |
| Docker Desktop | Any recent stable | Required by Supabase local dev stack |

Verify before continuing:

```bash
flutter doctor          # All checks green except optional items
supabase --version      # 1.x.x
docker info             # Docker daemon running
```

### 5.2 Clone and install Flutter dependencies

```bash
git clone https://github.com/<org>/kurdlingo.git
cd kurdlingo
flutter pub get
```

### 5.3 Run code generation

The project uses `build_runner` for Drift, Freezed, Riverpod, and json_serializable.
Run this once after initial checkout and again after editing any annotated file:

```bash
dart run build_runner build --delete-conflicting-outputs
```

To watch for changes during development:

```bash
dart run build_runner watch --delete-conflicting-outputs
```

### 5.4 Start the local Supabase stack

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

Run the seed script (written in Dart, lives at `scripts/seed_unit1.dart`):

```bash
dart run scripts/seed_unit1.dart \
  --url http://localhost:54321 \
  --service-key <service_role_key_from_supabase_start>
```

This inserts 5 Kurmanji vocabulary items (Greetings unit) and the `lesson_units` row for Unit 1.

### 5.7 Configure environment variables

Create `.env` in the project root (this file is gitignored):

```
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=<anon_key_from_supabase_start>
```

The app reads these at runtime via `--dart-define`. The `main.dart` entry point calls:

```dart
const supabaseUrl = String.fromEnvironment('SUPABASE_URL');
const supabaseAnonKey = String.fromEnvironment('SUPABASE_ANON_KEY');
```

### 5.8 Run the app

**iOS Simulator:**
```bash
flutter run \
  --dart-define=SUPABASE_URL=http://localhost:54321 \
  --dart-define=SUPABASE_ANON_KEY=<anon_key> \
  -d "iPhone 15 Pro"
```

**Android Emulator:**
```bash
# Android cannot reach localhost; use the host machine address
flutter run \
  --dart-define=SUPABASE_URL=http://10.0.2.2:54321 \
  --dart-define=SUPABASE_ANON_KEY=<anon_key> \
  -d emulator-5554
```

**Convenience:** create a `Makefile` or `.vscode/launch.json` that bakes in the
`--dart-define` flags so you don't paste them every run.

### 5.9 Run tests

```bash
flutter test
```

Tests requiring a Drift in-memory DB use `NativeDatabase.memory()` — no additional
setup needed.

---

## 6. Sprint 1 Task Breakdown

Tasks are ordered for a single developer executing them sequentially. Complexity:
**S** = <2 h, **M** = 2–4 h, **L** = 4–8 h.

| # | Task | Complexity | Notes |
|---|---|---|---|
| 1 | Supabase project setup (local CLI) + run `001_initial_schema.sql` | S | `supabase start && supabase db reset` |
| 2 | Flutter project scaffold: `flutter create`, add all `pubspec.yaml` deps, run `flutter pub get` | S | |
| 3 | Copy `fsrs.dart` skeleton from `srs-spec.md §7` into `lib/services/srs/fsrs.dart` | S | No changes needed; spec is production-ready |
| 4 | Write FSRS unit tests (`test/services/srs/fsrs_test.dart`) against checklist in `srs-spec.md Appendix B` | M | Must pass before any lesson code is written |
| 5 | Implement Drift local database: all 4 tables + DAOs (`app_database.dart`, tables/, daos/) | L | Run `build_runner` after writing table definitions |
| 6 | Implement `AuthRepository` + `auth_screen.dart` (register + login flows) | M | Uses `supabase.auth.signUpWithPassword` and `signInWithPassword` |
| 7 | Implement `SupabaseClient` provider + `VocabularyRemote` + `FsrsCardsRemote` | M | Thin wrappers around `supabase.from('table')` calls |
| 8 | Implement `SyncService`: `pullFsrsCards()` on launch + `pushDirty()` on foreground | M | Use `AppLifecycleListener`; retry loop with `attempts < 5` guard |
| 9 | Write seed script (`scripts/seed_unit1.dart`) and seed Unit 1 into local Supabase | S | 5 vocabulary rows + 1 lesson_unit row |
| 10 | Implement `SkillTreeScreen` + `SkillTreeController` (reads units + user_progress from Drift) | M | Single unit card, unlocked, taps go to lesson |
| 11 | Implement `LessonController`: load 5 cards, card queue state machine, call FSRS after each answer | L | Core lesson loop; must write card to Drift immediately after rating |
| 12 | Implement `McExerciseWidget` (Kurdish prompt + 4 answer buttons) + `McDistractors` helper | M | Distractors: pick 3 random from remaining vocab pool |
| 13 | Implement `LessonScreen` (progress bar + card queue rendering) | M | Feeds `LessonController`; no audio hooks needed |
| 14 | Implement `LessonCompleteScreen` (score display, XP earned, back to skill tree) | S | Reads `LessonResult` freezed object from controller |
| 15 | Implement `CharPickerBar` widget; wire it into `AuthScreen` and any future text inputs | S | Row of `TextButton`s; each calls `TextEditingController.text += char` |
| 16 | Wire GoRouter: `/login`, `/skill-tree`, `/lesson/:unitId`, `/lesson-complete` | S | `GoRouter` redirect guard: unauthenticated → `/login` |
| 17 | Integration smoke test: register → complete lesson → check Supabase Studio for synced cards | S | Manual; verify `fsrs_cards` rows exist in local Supabase |
| 18 | Write widget tests for `CharPickerBar` (ê/î/û/ç/ş insertion on iOS + Android target) | S | `flutter_test`; use `tester.tap()` on each button |

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
- [ ] All 5 FSRS card states are persisted to the local Drift database immediately after rating (verified by re-launching the app and inspecting the DB via Drift DevTools or a direct SQLite query)
- [ ] On app kill + relaunch, previously scheduled cards retain their `state`, `stability`, `difficulty`, and `due_date` (FSRS state survives app restart)
- [ ] Bringing the app back to the foreground after a lesson triggers `SyncService.pushDirty()`; the updated `fsrs_cards` rows appear in Supabase Studio within 5 seconds on a healthy connection
- [ ] The character picker bar is visible whenever a text field is focused on both the login screen and any screen with a text input
- [ ] Tapping ê, î, û, ç, ş in the character picker bar inserts the correct Unicode character into the active text field on both iOS Simulator and Android Emulator
- [ ] The app compiles and runs on iOS (Simulator, iPhone 15 Pro, iOS 17) without errors
- [ ] The app compiles and runs on Android (Emulator, Pixel 8, API 34) without errors

### Test checklist

- [ ] All FSRS unit tests pass (`test/services/srs/fsrs_test.dart`), covering the 10 cases in `srs-spec.md Appendix B`
- [ ] `CharPickerBar` widget tests pass: each of the 5 special characters is inserted correctly
- [ ] `flutter test` exits with code 0 (no failing tests)
- [ ] `flutter analyze` exits with code 0 (no lint errors)

### Code quality checklist

- [ ] No hardcoded Supabase URLs or keys in source files; all secrets injected via `--dart-define`
- [ ] `.env` is listed in `.gitignore`
- [ ] All Riverpod providers are typed (no `dynamic` providers)
- [ ] Drift `is_dirty` flag is always set to `1` before the FSRS write returns — never left in an ambiguous state
- [ ] `SyncService.pushDirty()` handles network failure gracefully (increments `attempts`; stops retrying at 5)

---

## Appendix A — Seed Data Format

`assets/content/seed_unit_1.json` (loaded by `scripts/seed_unit1.dart`):

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
| Local DB | Drift / SQLite | Offline-first FSRS; type-safe Dart DSL |
| Sync strategy | Dirty flag + foreground push | Simpler than real-time subscriptions for PoC; good enough until multi-device sync is needed |
| FSRS persistence | Drift is source of truth during session; Supabase is authoritative after sync | Avoids network latency on every card flip |
| Conflict resolution | Last-write-wins on `updated_at` | Acceptable for single-device PoC; multi-device reconciliation is Sprint 3+ concern |
| Auth | Supabase email+password | Simplest path; OAuth (Google/Apple) deferred |
| Exercise type | Multiple Choice L2→L1 only | Fastest to build; proves the card queue and FSRS loop work end-to-end |
| XP formula | 10 XP per correct answer, flat | No balancing needed for PoC; gamification spec (F4) will revise in Sprint 2 |
| Character input | Picker bar above keyboard (not long-press) | Long-press is unreliable on Android; see CLAUDE.md |

---

## Appendix C — Supabase Column Mapping (Dart ↔ DB)

When serialising `FSRSCard` to the `fsrs_cards` Supabase table, use this mapping.
The Drift local table uses identical column names.

| Dart field | Supabase column | Drift column | Type |
|---|---|---|---|
| `id` | `id` | `id` | UUID / TEXT |
| `userId` | `user_id` | `user_id` | UUID / TEXT |
| `vocabularyItemId` | `vocabulary_item_id` | `vocabulary_item_id` | UUID / TEXT |
| `stability` | `stability` | `stability` | FLOAT8 / REAL |
| `difficulty` | `difficulty` | `difficulty` | FLOAT8 / REAL |
| `dueDate` | `due_date` | `due_date` | TIMESTAMPTZ / INTEGER (Unix ms) |
| `lastReview` | `last_review` | `last_review` | TIMESTAMPTZ / INTEGER nullable |
| `reviewCount` | `review_count` | `review_count` | INT |
| `state` | `state` | `state` | TEXT |
| `updatedAt` | `updated_at` | `updated_at` | TIMESTAMPTZ / INTEGER |
| _(local only)_ | _(not in Supabase)_ | `is_dirty` | INTEGER (0/1) |

`is_dirty` is a Drift-only column. Never include it in Supabase upsert payloads.
