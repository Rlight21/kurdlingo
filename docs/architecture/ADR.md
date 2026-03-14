# Architecture Decision Record (ADR)

> **Project:** Kurdlingo — Duolingo-inspired Kurmanji Kurdish Learning App
> **Owner:** Backend Architect Agent (Task B1)
> **Status:** LOCKED — Core decisions confirmed. ADR-011 supersedes ADR-001 and ADR-003 (iOS native pivot).
> **Last Updated:** 2026-03-12
> **Reviewers:** Staff Manager, Lead Engineer

---

## Table of Contents

1. [ADR-001: Mobile Framework — Flutter](#adr-001-mobile-framework--flutter)
2. [ADR-002: Backend — Supabase](#adr-002-backend--supabase)
3. [ADR-003: State Management — Riverpod](#adr-003-state-management--riverpod)
4. [ADR-004: SRS Algorithm — FSRS v4](#adr-004-srs-algorithm--fsrs-v4)
5. [ADR-005: Audio Strategy — Hybrid Native + KurdishTTS.com](#adr-005-audio-strategy--hybrid-native--kurdishttscoms)
6. [ADR-006: Content Format — JSON/YAML in Repository](#adr-006-content-format--jsonyaml-in-repository)
7. [ADR-007: Character Input — Picker Bar](#adr-007-character-input--picker-bar)
8. [ADR-008: Offline-First Architecture for SRS Engine](#adr-008-offline-first-architecture-for-srs-engine)
9. [ADR-009: Kurmanji-Specific Technical Considerations](#adr-009-kurmanji-specific-technical-considerations)
10. [ADR-010: CI/CD Pipeline](#adr-010-cicd-pipeline)
11. [ADR-011: iOS Native Pivot — SwiftUI](#adr-011-ios-native-pivot--swiftui) *(supersedes ADR-001, ADR-003)*

---

## ADR-001: Mobile Framework — Flutter

**Status:** SUPERSEDED by ADR-011
**Decision Date:** 2026-03-12

### Context

Kurdlingo requires a polished, performant mobile application deployable on both iOS and Android from a single codebase. The app is animation-heavy (lesson transitions, streak animations, XP counters), requires custom UI widgets (character picker bar, card flip animations), and must handle Unicode text rendering for Kurmanji Latin characters reliably across both platforms. The team is small and cannot afford to maintain two separate native codebases.

### Decision

**Flutter (Dart)** is the chosen mobile framework.

### Rationale

- **Performance:** Dart compiles to native ARM code via AOT (Ahead-of-Time) compilation. The Flutter rendering engine (Impeller on iOS, Skia/Impeller on Android) renders at a consistent 60–120fps directly to a canvas, bypassing platform UI widgets entirely. This guarantees smooth card-flip and streak animations without JavaScript bridge overhead.
- **Single codebase:** One Dart codebase targets iOS, Android, and (if needed later) web/desktop. This is critical for a small team — no duplicated feature work.
- **Widget library:** Flutter's Material and Cupertino widget sets, plus the pub.dev ecosystem, provide all UI primitives needed: `AnimatedContainer`, `Hero` transitions, `CustomPainter` for progress rings, etc.
- **Internationalization (i18n):** Flutter's `intl` package and `flutter_localizations` support multiple locales out of the box. Kurmanji Latin (left-to-right) is straightforward.
- **Unicode and font rendering:** Flutter uses the HarfBuzz text shaping engine, which correctly renders all Kurmanji Latin special characters (ê, î, û, ç, ş) without custom shaping code.
- **Strong typing:** Dart's sound null safety reduces runtime crashes — important for a production app with complex SRS state logic.
- **Hot reload:** Development velocity benefit — UI changes reflect in under a second without losing app state.

### Consequences

- **Positive:** High-fidelity UI, fast iteration, single codebase, excellent Unicode support.
- **Negative:** App binary size is larger than native apps (~10–15 MB compressed). Dart is a less common language — hiring is slightly harder than React Native (JavaScript). Platform-specific plugin gaps can occasionally require writing native Kotlin/Swift code.
- **Neutral:** The team must learn Dart if coming from a JavaScript/TypeScript background. Dart is syntactically similar to Java/Kotlin, so the learning curve is low.

### Alternatives Considered

| Option | Reason Rejected |
|---|---|
| **React Native** | JavaScript bridge introduces frame-drop risk on animation-heavy screens. JSI (new architecture) mitigates this but is still not as deterministic as AOT Dart. Expo ecosystem adds abstractions that complicate low-level audio control. |
| **Native iOS (Swift) + Android (Kotlin)** | Two separate codebases, two release pipelines, two QA matrices. Not feasible for a small team. |
| **Capacitor / Ionic** | Web-based rendering is insufficient for 60fps card animations. Poor offline SQLite integration. |
| **Kotlin Multiplatform Mobile (KMM)** | Shares only business logic, not UI — still requires writing native UI for both platforms separately. |

---

## ADR-002: Backend — Supabase

**Status:** LOCKED
**Decision Date:** 2026-03-12

### Context

Kurdlingo needs a backend that provides: user authentication (email/password, social OAuth), persistent storage for user progress (FSRS card states, lesson completions, XP, streaks), real-time features (optional: leaderboard updates), file/audio storage, and Row-Level Security so users can only read their own data. The team has no dedicated backend engineer — the backend must be largely managed infrastructure.

### Decision

**Supabase** (PostgreSQL + Auth + Realtime + Storage) is the chosen backend platform.

### Rationale

- **PostgreSQL foundation:** FSRS review data is relational by nature (users → decks → cards → review_logs). PostgreSQL's JSONB columns can store FSRS algorithm state (stability, difficulty, retrievability) efficiently alongside structured foreign keys.
- **Row-Level Security (RLS):** Supabase's built-in RLS policies enforce data isolation at the database layer — a user can never query another user's card states even with a leaked JWT. This is the correct security layer for a consumer app.
- **Supabase Auth:** Handles email/password, magic link, Google OAuth, and Apple Sign-In out of the box. Flutter integration via `supabase_flutter` package is mature and actively maintained.
- **Realtime:** PostgreSQL logical replication subscriptions enable live XP/streak updates and (future) social features without a separate WebSocket server.
- **Storage:** Audio files for native recordings (see ADR-005) are served from Supabase Storage (S3-compatible) with CDN, avoiding the need to configure a separate object store.
- **Managed infrastructure:** No servers to provision. Free tier supports MVP; Pro tier ($25/month) supports production. Automatic backups, connection pooling (PgBouncer), and SSL are included.
- **Supabase Edge Functions:** Deno-based serverless functions available for backend logic that must not run on client (e.g., validating lesson completion server-side, rate-limiting TTS API calls).
- **Flutter SDK:** The `supabase_flutter` package provides typed query builders, auth state streams, and Realtime subscriptions that integrate cleanly with Riverpod's `StreamProvider`.

### Consequences

- **Positive:** Rapid development, no DevOps overhead, excellent Flutter SDK, strong security model via RLS.
- **Negative:** Vendor lock-in — migrating away from Supabase is non-trivial. Free tier has connection limits (60 connections); production apps must use connection pooling carefully. Edge Functions are Deno-based (not Node.js), which may surprise contributors.
- **Neutral:** PostgreSQL schema migrations must be managed via Supabase CLI (`supabase migration new`). Schema version control is tracked in `supabase/migrations/`.

### Alternatives Considered

| Option | Reason Rejected |
|---|---|
| **Firebase (Firestore)** | NoSQL document model is a poor fit for relational FSRS data. Querying "all cards due before date X across all decks for user Y" is expensive and awkward in Firestore. Pricing scales badly with read-heavy SRS apps. |
| **PocketBase** | Self-hosted only — requires managing servers. No managed tier. Not suitable for a small team wanting zero ops. |
| **Custom Node.js + PostgreSQL on Railway/Render** | Requires writing and maintaining the entire auth, storage, and real-time layers from scratch. Too much custom backend work for MVP. |
| **AWS Amplify** | Significantly more complex configuration. DynamoDB has the same NoSQL mismatch issue. Overkill for MVP. |
| **Hasura** | GraphQL overhead for a mobile app is unnecessary complexity. Hasura requires a separate PostgreSQL instance and more DevOps. |

---

## ADR-003: State Management — Riverpod

**Status:** SUPERSEDED by ADR-011
**Decision Date:** 2026-03-12

### Context

Kurdlingo's Flutter app has complex, interconnected state: the current lesson session (card queue, FSRS states, timer), user profile (XP, streak, settings), audio playback state, connectivity status (for offline-first sync), and UI state (selected tab, animation progress). State must be accessible across deeply nested widget trees without prop drilling, and async data (Supabase queries, local SQLite reads) must be handled safely with loading/error states.

### Decision

**Riverpod** (specifically `flutter_riverpod` with code generation via `riverpod_generator`) is the chosen state management solution.

### Rationale

- **Compile-time safety:** Riverpod providers are resolved at compile time — accessing an undefined provider is a compile error, not a runtime exception. This is critical for a codebase where FSRS state mutations must be provably correct.
- **Provider types match use cases:** `FutureProvider` for Supabase async queries, `StreamProvider` for Realtime subscriptions and connectivity streams, `StateNotifierProvider` (or `NotifierProvider` in Riverpod 2.x) for mutable lesson session state, and `Provider` for pure dependency injection (repository instances, FSRS algorithm object).
- **No `BuildContext` dependency:** Providers are read via `ref`, not `context`. This means business logic (repositories, sync services) can be tested without a Flutter widget tree.
- **Testability:** Riverpod's `ProviderContainer` and `ProviderScope` overrides enable unit and integration tests to swap out Supabase clients for mocks without any dependency injection framework.
- **Auto-dispose:** Providers can be configured to dispose when no longer observed (e.g., a lesson session provider disposes when the user leaves the lesson screen), preventing memory leaks.
- **Offline-first synergy:** A `connectivityProvider` (wrapping the `connectivity_plus` package) can be watched by the sync service provider, automatically triggering sync when connectivity is restored — all within Riverpod's reactive graph.

### Consequences

- **Positive:** Type-safe, testable, scales well as the app grows. Excellent interop with Supabase's stream-based APIs.
- **Negative:** Steeper learning curve than `setState` or `Provider`. Requires understanding of provider scoping and `ref.watch` vs `ref.read` semantics. Code generation (`build_runner`) adds a build step.
- **Neutral:** Riverpod 2.x with `@riverpod` annotation syntax is the preferred style — all new code should use the generator. Legacy `StateNotifierProvider` patterns should be avoided in new code.

### Alternatives Considered

| Option | Reason Rejected |
|---|---|
| **BLoC / Cubit** | More boilerplate than Riverpod for equivalent functionality. Event-driven model adds indirection that is unnecessary for read-heavy SRS state. |
| **Provider (package)** | Predecessor to Riverpod. Riverpod fixes its core design flaws (context dependency, global state issues). No reason to use the older package. |
| **GetX** | Anti-pattern for clean architecture. Couples UI to business logic via static globals. Poor testability. |
| **MobX** | Observable/reaction model is powerful but adds code generation complexity without meaningful advantage over Riverpod for this use case. |
| **setState + InheritedWidget** | Does not scale beyond simple screens. Managing FSRS session state and sync state with `setState` would lead to unmaintainable widget trees. |

---

## ADR-004: SRS Algorithm — FSRS v4

**Status:** LOCKED
**Decision Date:** 2026-03-12

### Context

Kurdlingo's core learning mechanic requires a spaced repetition system (SRS) that schedules card reviews to maximize long-term retention with minimum review time. The algorithm must run entirely on-device (offline-first, no round-trip to server), be deterministic for conflict resolution, and be well-documented enough for the team to implement correctly in Dart.

### Decision

**FSRS v4** (Free Spaced Repetition Scheduler, version 4) is the chosen SRS algorithm.

### Rationale

- **State-of-the-art retention model:** FSRS is based on the DSR (Difficulty, Stability, Retrievability) memory model, derived from Ebbinghaus forgetting curve research. It outperforms SM-2 (used by Anki) in retention efficiency by approximately 20% in controlled studies.
- **Parametric and personalizable:** FSRS v4 has 17 learnable parameters (w0–w16) that can be optimized per-user via gradient descent on review history. MVP ships with default parameters; personalization is a V2 feature.
- **Fully local computation:** The scheduling algorithm is pure mathematics — given current card state (stability `S`, difficulty `D`) and rating (Again/Hard/Good/Easy), the next review interval is computed deterministically. No network call required.
- **Determinism for conflict resolution:** Because FSRS is deterministic given the same inputs, last-write-wins conflict resolution (see ADR-008) is safe — replaying review events always produces the same card state.
- **Open specification:** The FSRS v4 algorithm is fully documented and has reference implementations in Python, JavaScript, and Rust. A Dart port can be written and unit-tested against the reference implementation's test vectors.
- **Active community:** FSRS is maintained by the open-source Anki community. Version updates are well-communicated. v5 is planned but v4 is stable for production use.

### Consequences

- **Positive:** Best-in-class retention efficiency, fully offline, deterministic, well-documented.
- **Negative:** More complex to implement than SM-2. The 17-parameter model requires careful floating-point handling — must use identical precision (64-bit double) across all platforms to avoid drift. User-facing explanations ("why is this card due in 14 days?") are harder to communicate than simpler algorithms.
- **Neutral:** FSRS v4 Dart implementation must be unit-tested against the official Python reference (open_spaced_repetition/fsrs4anki). Floating-point rounding must be consistent between local computation and any server-side validation.

### Alternatives Considered

| Option | Reason Rejected |
|---|---|
| **SM-2 (SuperMemo 2)** | Older algorithm, lower retention efficiency than FSRS. Used by classic Anki but being replaced by FSRS. |
| **SM-18 (SuperMemo 18)** | Proprietary, extremely complex, not open-source. No feasible Dart implementation. |
| **Leitner Box System** | Too simplistic for a modern app. Fixed intervals, no adaptive scheduling. Poor retention outcomes. |
| **Custom algorithm** | Would require significant research and validation effort. No justification when FSRS v4 is open-source and well-validated. |

---

## ADR-005: Audio Strategy — Hybrid Native + KurdishTTS.com

**Status:** LOCKED
**Decision Date:** 2026-03-12

### Context

Kurmanji Kurdish is a low-resource language — high-quality TTS engines (Google Cloud TTS, Amazon Polly, Azure Cognitive Services) do not support Kurmanji as of 2026. Audio pronunciation is essential for a language-learning app. The team must balance audio quality (critical for correct pronunciation learning) against scalability and cost.

### Decision

**Hybrid audio strategy:**
1. **Native recordings** (professionally recorded MP3/OGG files) for A1 core vocabulary.
2. **KurdishTTS.com API** for dynamically generated audio for sentences, phrases, and content beyond the core vocabulary set.

### Rationale

- **Native recordings for core vocabulary:** A1 Kurmanji has approximately 300–500 core words. Recording these professionally is a one-time cost that produces the highest possible audio quality. Native speaker recordings are the gold standard for phoneme accuracy, especially for Kurmanji-specific sounds that TTS engines may mispronounce.
- **KurdishTTS.com for dynamic content:** The kurdishtts.com API supports both Kurmanji (Badini and Kurmanji dialects) and Sorani, making it the only known API with native Kurmanji support. It is suitable for sentence-level audio where recording every combination is infeasible.
- **Supabase Storage for audio CDN:** Native recordings are stored in Supabase Storage (S3-compatible) and served via CDN. Flutter's `just_audio` package handles playback with caching.
- **Offline pre-caching:** A1 core vocabulary audio files (the native recordings) are bundled with the app or downloaded on first launch and cached locally. This ensures offline lesson functionality.
- **API call rate limiting:** KurdishTTS.com API calls are proxied through a Supabase Edge Function to enforce rate limiting and cache responses, preventing redundant API calls for the same phrase.

### Consequences

- **Positive:** Highest quality audio for core vocabulary. Scalable TTS for extended content. Kurmanji language coverage not available from major cloud providers.
- **Negative:** Native recording quality is time and budget dependent. KurdishTTS.com is a third-party service with no SLA — app must degrade gracefully if the API is unavailable (show text only, no audio). API response latency adds delay to sentence audio playback.
- **Neutral:** KurdishTTS.com API key must be stored as a Supabase Edge Function environment variable — never embedded in the Flutter app binary. Audio caching strategy must be implemented in the app to avoid repeated API calls.

### Alternatives Considered

| Option | Reason Rejected |
|---|---|
| **Google Cloud TTS** | No Kurmanji support. Kurdish is not in Google Cloud TTS language list. |
| **Amazon Polly** | No Kurmanji support. Same issue. |
| **Azure Cognitive Services TTS** | No Kurmanji support. |
| **ElevenLabs custom voice** | High cost for a minority language. Would require training data collection. No existing Kurmanji model. |
| **Native recordings only** | Does not scale beyond core vocabulary. Recording every sentence combination is not feasible. |
| **No audio** | Unacceptable for a language learning app. Pronunciation is a primary learning objective. |

---

## ADR-006: Content Format — JSON/YAML in Repository

**Status:** LOCKED
**Decision Date:** 2026-03-12

### Context

Kurdlingo's lesson content (vocabulary, exercises, sentences, grammar rules, lesson metadata) must be authored, reviewed, and version-controlled. For MVP, a content management system (CMS) adds unnecessary complexity. The team needs a format that is human-readable (for language experts to review and edit), version-controllable (for diff/review in pull requests), and parseable by Flutter at runtime.

### Decision

**JSON/YAML files committed directly to the Git repository** for all MVP lesson content.

### Rationale

- **Version control as CMS:** Every content change is a Git commit with a diff, author, and timestamp. Content errors can be reverted with `git revert`. This is the simplest possible content management system.
- **Human-readable authoring:** YAML is preferred for authoring (cleaner syntax, supports comments for translator notes) and converted to JSON for bundling. JSON is used for runtime consumption — no YAML parser needed in the Flutter app.
- **Flutter asset bundling:** JSON files are declared in `pubspec.yaml` under `flutter.assets` and bundled into the app binary. `rootBundle.loadString()` loads them at runtime with zero network dependency.
- **Schema validation in CI:** A JSON Schema is defined for each content type (lesson, card, exercise). GitHub Actions runs `ajv-cli` validation on every PR that modifies content files, preventing malformed content from reaching production.
- **Low barrier for contributors:** Language experts and community contributors can submit content corrections via pull requests without needing access to a CMS dashboard or database credentials.
- **Migration path to CMS:** When content volume outgrows the repo (V2+), content can be migrated to a headless CMS (Contentful, Sanity) or directly to Supabase tables with minimal app-side changes — the Flutter data layer abstracts the source behind a `ContentRepository` interface.

### Content Directory Structure

```
assets/
  content/
    units/
      unit_01_greetings.yaml     # YAML source (for authoring)
    generated/
      unit_01_greetings.json     # JSON output (bundled in app)
    schema/
      lesson.schema.json
      card.schema.json
scripts/
  convert_yaml_to_json.py        # Build script: YAML → JSON
```

### Consequences

- **Positive:** Zero infrastructure cost for MVP. Full version history. PR-based content review. No external dependencies for content loading.
- **Negative:** Does not scale beyond ~50 units without impacting app binary size. No non-technical contributor interface. Content updates require an app release (for bundled content). Large JSON blobs in PRs are hard to review.
- **Neutral:** A Supabase table for remote content delivery (without an app update) is a natural V2 upgrade. The `ContentRepository` abstraction in the app makes this migration transparent to the UI layer.

### Alternatives Considered

| Option | Reason Rejected |
|---|---|
| **Contentful (Headless CMS)** | Overkill for MVP. Adds cost, API dependency, and content modelling complexity. |
| **Supabase tables for all content** | Content changes require SQL migrations or admin dashboard access, not PR-friendly. No offline bundling without explicit caching logic. |
| **Google Sheets + API** | Unreliable schema enforcement. No version history per cell. API rate limits. |
| **Hardcoded Dart classes** | Not editable by language experts. Every content change requires a code review and app release. |

---

## ADR-007: Character Input — Picker Bar

**Status:** LOCKED
**Decision Date:** 2026-03-12

### Context

Kurmanji Kurdish Latin script uses five characters not present on standard iOS/Android QWERTY keyboards: **ê** (U+00EA), **î** (U+00EE), **û** (U+00FB), **ç** (U+00E7), **ş** (U+015F). Learners completing typing exercises must be able to input these characters without switching keyboard languages or using long-press accents (which are slow and inconsistent across devices).

### Decision

A **character picker bar** (a horizontal scrollable row of tappable character buttons) is displayed above the system keyboard whenever a Kurmanji text input field is focused.

### Rationale

- **Duolingo-proven UX pattern:** Duolingo uses this exact pattern for accent characters in Spanish, French, German, etc. Users familiar with language learning apps will recognize it immediately.
- **No keyboard switch required:** Users do not need to install a Kurmanji keyboard or switch input method — the picker bar injects characters directly into the focused `TextEditingController`.
- **Platform-independent:** A Flutter `Row` of `TextButton` widgets above the keyboard works identically on iOS and Android. No platform channel needed.
- **Five-character scope:** The small, fixed set of special characters (ê, î, û, ç, ş) means the picker bar can display all characters simultaneously without scrolling on standard screen widths.
- **Implementation:** A `KeyboardAttachedWidget` using Flutter's `MediaQuery.of(context).viewInsets.bottom` positions the bar directly above the system keyboard. Character insertion uses `TextEditingController.value.copyWith()` to insert at cursor position.

### Consequences

- **Positive:** Frictionless special character input, consistent with established language app conventions, simple Flutter implementation.
- **Negative:** Picker bar occupies ~44px of vertical screen space when keyboard is visible. On small screens (iPhone SE), this reduces the visible exercise area.
- **Neutral:** The picker bar is only shown when `hasFocus` is true on a Kurmanji input field — it does not appear on English-input screens (username, password, etc.).

### Alternatives Considered

| Option | Reason Rejected |
|---|---|
| **Long-press accent popup** | Too slow for typing exercises. Inconsistent behavior between iOS and Android. |
| **Suggest a Kurmanji keyboard app** | Poor UX — redirects user to App Store mid-lesson. Many users will not bother. |
| **Transliteration (x-notation)** | Using `ex`, `ix`, `ux` as substitutes is not standard Kurmanji and teaches incorrect spelling. |
| **On-screen full custom keyboard** | Massive implementation complexity. Replaces the system keyboard, losing autocorrect and swipe-type features. Overkill for 5 characters. |

---

## ADR-008: Offline-First Architecture for SRS Engine

**Status:** LOCKED
**Decision Date:** 2026-03-12

### Context

A spaced repetition app that requires internet connectivity to record a card review is fundamentally broken for its core use case — users study on commutes, planes, and in areas with poor connectivity. FSRS card reviews must be recordable offline with full fidelity, and sync to Supabase when connectivity is restored. This requires a local-first data store, a sync queue, and a conflict resolution strategy.

This section incorporates architectural analysis provided by Qwen3-Coder-480B (consulted 2026-03-12), which validated the approach and identified key failure modes.

### Decision

**Local SQLite database via the Drift package** is the primary data store for all card state and review logs. Supabase is treated as a remote replica. Sync is triggered on connectivity restoration with **optimistic updates** and **last-write-wins per card** conflict resolution.

### Data Layer Architecture

```
┌─────────────────────────────────────────┐
│              Flutter App                │
│                                         │
│  ┌─────────────┐    ┌─────────────────┐ │
│  │  Riverpod   │    │  StudySession   │ │
│  │  Providers  │◄───│  Notifier       │ │
│  └──────┬──────┘    └────────┬────────┘ │
│         │                   │           │
│  ┌──────▼──────────────────▼──────────┐ │
│  │         CardRepository             │ │
│  │   (offline-first abstraction)      │ │
│  └──────┬──────────────────┬──────────┘ │
│         │                  │            │
│  ┌──────▼──────┐   ┌───────▼────────┐  │
│  │ Drift/SQLite│   │  SyncService   │  │
│  │ (local DB)  │   │  + SyncQueue   │  │
│  └─────────────┘   └───────┬────────┘  │
└──────────────────────────── │ ─────────┘
                               │ (when online)
                    ┌──────────▼──────────┐
                    │   Supabase          │
                    │   PostgreSQL        │
                    └─────────────────────┘
```

### Local Database: Drift (SQLite)

**Drift** (formerly Moor) is chosen as the local SQLite ORM for Flutter because:
- Strongly typed queries generated at compile time — no raw SQL string errors.
- `DriftDatabase` integrates cleanly with Riverpod via a `Provider<AppDatabase>`.
- Supports complex queries (e.g., "SELECT all cards WHERE next_review_date <= NOW() ORDER BY due_priority") that are impractical with key-value stores.
- Drift's `watchSingleOrNull` / `watch` return `Stream<T>` — these streams are directly consumed by Riverpod `StreamProvider`, giving the UI live updates when card states change.

**Local Schema (key tables):**

```
cards              — card_id, deck_id, front, back, audio_url, created_at
fsrs_states        — card_id, stability, difficulty, last_review, next_review,
                     review_count, updated_at, is_dirty (pending sync flag)
review_logs        — log_id, card_id, rating, reviewed_at, elapsed_days,
                     scheduled_days, synced_at (null = pending)
sync_operations    — op_id, operation_type, entity_id, payload_json,
                     created_at, retry_count, last_error
```

### Sync Strategy: Optimistic Updates

1. **On card review:** The FSRS algorithm computes the new card state locally. `fsrs_states` is updated immediately (optimistic update). The UI reflects the change instantly. A `sync_operations` record is inserted with `operation_type = 'upsert_review'`.
2. **On connectivity restoration:** The `SyncService` (a Riverpod `Provider` watching `connectivityProvider`) processes the `sync_operations` queue in FIFO order, batching up to 50 operations per Supabase RPC call.
3. **On success:** The `sync_operations` record is deleted and `review_logs.synced_at` is set.
4. **On failure:** Exponential backoff (2^attempt seconds, max 5 retries). The operation remains in the queue. A background retry is scheduled.

### Conflict Resolution: Last-Write-Wins Per Card

FSRS states are resolved with **last-write-wins (LWW) keyed on `updated_at` timestamp**:

- Each `fsrs_states` row carries an `updated_at` (ISO 8601, UTC, millisecond precision).
- During sync, the server compares `updated_at` of the incoming record against the stored record.
- The record with the **later `updated_at`** wins — no merge of individual fields.
- This is safe for FSRS because:
  - A card can only be reviewed on one device at a time in practice.
  - Even if two devices review the same card offline, the most recent review reflects the user's actual current memory state better than the earlier one.
  - Review logs are **append-only** — both review events are preserved regardless of which state "wins", enabling future parameter optimization.

**Why not merge?** Field-level merging of FSRS state (e.g., taking max `stability`) produces mathematically invalid states — the FSRS DSR model assumes states are computed from a contiguous review history. Merging produces values that were never output by the algorithm.

**Why not vector clocks?** Vector clocks add implementation complexity with no meaningful benefit for a single-user SRS app. LWW is correct and simple for this use case.

### Failure Modes and Mitigations

The following failure modes were identified during architectural review (Qwen3-Coder-480B analysis, 2026-03-12):

| Failure Mode | Mitigation |
|---|---|
| **Network failure during sync batch** | Atomic batch operations — full batch succeeds or rolls back. Retry queue preserves all pending operations. |
| **Duplicate review submission** | `review_logs` has a unique constraint on `(card_id, reviewed_at)`. Duplicate upserts are idempotent via `ON CONFLICT DO NOTHING`. |
| **Clock skew between devices** | `updated_at` is set by the client. The server records a `server_received_at` timestamp. Supabase RLS policies are based on user_id, not timestamps, so clock skew only affects LWW ordering (acceptable). |
| **Storage exhaustion on device** | `review_logs` older than 180 days are archived (soft-deleted locally, retained on server). `StorageManager` checks available space before bulk import. |
| **Corrupted FSRS state** | A `DataIntegrityChecker` runs on app startup to validate that all `fsrs_states` values are within FSRS v4 valid ranges. Corrupted records are flagged and reset to new-card defaults with a logged event. |
| **Supabase outage** | All learning functionality works fully offline. Sync simply queues. User is shown an unobtrusive "Sync pending" indicator — no blocking UI. |
| **App killed during sync** | `sync_operations` queue is persisted in SQLite. On next launch, incomplete operations are detected (no `synced_at`) and retried. |
| **User logs in on new device** | Full deck state is downloaded from Supabase on first launch. Local SQLite is populated from server. Normal sync resumes. |

### Riverpod Integration for Sync

```
connectivityProvider (StreamProvider)
    └── syncServiceProvider (Provider, watches connectivity)
            └── triggers processSyncQueue() on reconnection
                    └── cardRepositoryProvider.markSynced(ops)
                            └── driftDatabaseProvider (local write)
                            └── supabaseClientProvider (remote upsert)
```

The `StudySessionNotifier` calls `cardRepository.recordReview(card, rating)` which:
1. Runs FSRS algorithm synchronously (pure Dart, no async).
2. Writes updated `fsrs_states` to Drift (async, awaited).
3. Inserts `review_log` and `sync_operation` to Drift (async, awaited).
4. Updates Riverpod state with the new card (triggers UI rebuild).

The sync service operates entirely in the background — it does not block the study session.

---

## ADR-009: Kurmanji-Specific Technical Considerations

**Status:** LOCKED
**Decision Date:** 2026-03-12

### Context

Kurdlingo teaches Kurmanji Kurdish, a language with specific linguistic and technical characteristics that affect rendering, input, font selection, and audio. These considerations must be documented to prevent common incorrect assumptions (e.g., "Kurdish must use RTL layout") from being built into the app.

### Unicode and Character Encoding

**Kurmanji Kurdish uses the Latin script** — the same Unicode block as English and most Western European languages. There is no requirement for custom Unicode processing, bidirectional text handling, or complex text shaping beyond what Flutter's HarfBuzz engine provides by default.

Special characters and their Unicode code points:

| Character | Unicode | Name |
|---|---|---|
| **ê** | U+00EA | Latin Small Letter E with Circumflex |
| **î** | U+00EE | Latin Small Letter I with Circumflex |
| **û** | U+00FB | Latin Small Letter U with Circumflex |
| **ç** | U+00E7 | Latin Small Letter C with Cedilla |
| **ş** | U+015F | Latin Small Letter S with Cedilla |

All five characters are in the **Latin Extended-A** and **Latin-1 Supplement** Unicode blocks, which are universally supported in all modern fonts and operating systems. No custom font is required for correct rendering.

**Uppercase equivalents** (for display only — Kurmanji lessons focus on lowercase input):

| Lower | Upper | Unicode Upper |
|---|---|---|
| ê | Ê | U+00CA |
| î | Î | U+00CE |
| û | Û | U+00DB |
| ç | Ç | U+00C7 |
| ş | Ş | U+015E |

### Font Selection: Noto Sans

**Recommended font: Noto Sans** (Google Fonts, open-source).

Rationale:
- Noto Sans has complete coverage of Latin Extended-A, ensuring all Kurmanji characters render identically on iOS, Android, and any future web/desktop target.
- On iOS, the default system font (San Francisco) supports all Kurmanji characters natively — no custom font is strictly required. However, using Noto Sans ensures visual consistency across platforms.
- On Android, the default Roboto font supports all required characters, but Roboto's glyph shapes for ş and ê differ subtly from Noto Sans — using Noto Sans provides pixel-level consistency.
- Noto Sans is available via the `google_fonts` Flutter package: `GoogleFonts.notoSans()`.
- No RTL font variants are needed.

**Implementation:** Set `GoogleFonts.notoSansTextTheme()` as the app's `ThemeData.textTheme`. All text throughout the app inherits this font automatically.

### Text Direction: Left-to-Right

**Kurmanji Kurdish (Latin script) is written LEFT-TO-RIGHT.** There is no RTL layout requirement.

Important note: Sorani Kurdish uses the Arabic script and IS right-to-left. Kurdlingo targets Kurmanji (Latin script) only in MVP. If Sorani support is added in a future version, a full RTL layout audit would be required. The Flutter `Directionality` widget would need to be set to `TextDirection.rtl` for Sorani content.

For MVP: all `Directionality` widgets use `TextDirection.ltr` (the Flutter default). No RTL-specific layout code is required.

### Character Input: Picker Bar (see ADR-007)

The five special characters above are handled by the character picker bar. Input fields for Kurmanji content should:
1. Use `TextInputType.text` (not `emailAddress` or other constrained types).
2. Register a `FocusNode` listener to show/hide the picker bar.
3. Use `TextEditingController` for character insertion at cursor position.

### Audio Considerations

- **Dialect:** Kurdlingo targets **Kurmanji** (also called Northern Kurdish, Badini dialect for Iraqi Kurmanji). The KurdishTTS.com API offers both Kurmanji and Sorani — the Kurmanji voice must be explicitly selected in API requests.
- **Phoneme coverage:** Native recordings for A1 vocabulary must cover all phonemes including ê, î, û, ç, ş in both initial and final positions to model correct pronunciation.
- **Audio file naming convention:** Audio files for native recordings use the canonical Kurmanji spelling as the filename: `xweş.mp3`, `çêj.mp3`. File names are stored as-is in Supabase Storage — no ASCII transliteration in filenames.
- **Normalization:** All Kurmanji text stored in the database must be Unicode NFC normalized. Dart: `String normalized = text.normalize(NormalizationForm.NFC)` using the `unorm2` package. This prevents duplicate card entries caused by different Unicode representations of the same character (e.g., composed vs. decomposed ê).

### Locale Configuration

The Flutter app's locale for Kurmanji content:
- **BCP-47 language tag:** `ku` (Kurdish) or `ku-Latn` (Kurdish, Latin script) — use `ku-Latn` where precision is needed.
- **No locale-specific number formatting** is needed for MVP — lesson progress uses standard Arabic numerals.
- **Sort order:** Kurmanji Latin alphabetical order follows standard Latin Unicode code point order for most characters. Dictionary-mode sort (for future vocabulary browser) requires a custom `Collator` that treats ê after e, î after i, û after u, ç after c, ş after s.

---

## ADR-010: CI/CD Pipeline

**Status:** LOCKED
**Decision Date:** 2026-03-12

### Context

Kurdlingo requires a reliable, automated build and deployment pipeline that enforces code quality, runs tests on every change, and delivers tested builds to testers and stores. The pipeline must support the Flutter codebase, Supabase schema migrations, and content validation. Two environments are needed: staging (for testing) and production (for users).

### Decision

**GitHub Actions** for CI (linting, testing, content validation, schema migration checks) combined with **EAS Build** (Expo Application Services from Expo/Meta, also available for non-Expo Flutter) — specifically the **Fastlane** + **GitHub Actions** combination for Flutter app delivery — to build and distribute iOS and Android binaries.

More precisely: **GitHub Actions** for all CI steps, and **EAS Build** (via `eas-cli`) for cloud-based iOS and Android builds that do not require local macOS (for iOS signing).

### Branch Strategy

```
main (protected)
 │
 ├── feature/lesson-unit-01
 ├── feature/fsrs-sync-service
 ├── fix/picker-bar-cursor-position
 └── content/add-greetings-unit-audio
```

**Rules:**
- `main` is protected: no direct pushes. All changes via Pull Request.
- PRs require: 1 approving review + all CI checks green.
- Feature branches are named `feature/`, `fix/`, `content/`, `chore/` for clarity.
- Branch is deleted after merge.
- Release tags follow SemVer: `v1.0.0`, `v1.1.0`, etc.

### Environments

| Aspect | Staging | Production |
|---|---|---|
| Supabase project | `kurdlingo-staging` | `kurdlingo-prod` |
| Supabase URL | Staging project URL | Production project URL |
| App bundle ID (iOS) | `com.kurdlingo.app.staging` | `com.kurdlingo.app` |
| App ID (Android) | `com.kurdlingo.app.staging` | `com.kurdlingo.app` |
| KurdishTTS API key | Staging key (rate-limited) | Production key |
| EAS profile | `preview` | `production` |

Environment-specific configuration is injected via **Dart environment variables** (`--dart-define=SUPABASE_URL=...`) at build time. These are set as GitHub Actions secrets and referenced in the EAS `eas.json` build profiles. The Flutter app reads them via `const String.fromEnvironment('SUPABASE_URL')`. No secrets are committed to the repository.

### CI/CD Pipeline Stages

```
PR opened / commit pushed to feature branch
        │
        ▼
┌─────────────────────────────────────────────┐
│  Stage 1: Lint & Format (GitHub Actions)    │
│  - dart format --check                      │
│  - dart analyze (zero warnings policy)      │
│  - flutter test (unit tests)                │
│  - JSON Schema validation (content files)   │
│  Duration: ~3 minutes                       │
└────────────────────┬────────────────────────┘
                     │ (on PR merge to main)
                     ▼
┌─────────────────────────────────────────────┐
│  Stage 2: Integration Tests (GitHub Actions)│
│  - flutter test integration_test/           │
│  - Supabase migration dry-run               │
│    (supabase db push --dry-run)             │
│  Duration: ~8 minutes                       │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  Stage 3: Staging Deploy (GitHub Actions)   │
│  - supabase db push (staging project)       │
│  - eas build --platform all --profile       │
│    preview (EAS cloud build)                │
│  - eas submit to TestFlight (iOS)           │
│  - eas submit to Firebase App Distribution  │
│    (Android)                                │
│  Duration: ~15 minutes (EAS cloud)          │
└────────────────────┬────────────────────────┘
                     │ (on release tag push)
                     ▼
┌─────────────────────────────────────────────┐
│  Stage 4: Production Release                │
│  - supabase db push (production project)    │
│  - eas build --platform all --profile       │
│    production                               │
│  - eas submit to App Store Connect          │
│  - eas submit to Google Play (internal →    │
│    production track, manual promotion)      │
│  Duration: ~20 minutes                      │
└─────────────────────────────────────────────┘
```

### Key GitHub Actions Workflows

**`.github/workflows/ci.yml`** — Runs on every PR and push to `main`:
- Flutter SDK setup (`subosito/flutter-action@v2`)
- Dependency install (`flutter pub get`)
- Code generation (`flutter pub run build_runner build --delete-conflicting-outputs`)
- Format check, analysis, unit tests
- Content schema validation (`npx ajv-cli validate`)

**`.github/workflows/staging.yml`** — Runs on merge to `main`:
- Supabase CLI migration (staging)
- EAS build (preview profile)
- Distribution to TestFlight / Firebase App Distribution

**`.github/workflows/release.yml`** — Runs on `v*` tag push:
- Supabase CLI migration (production) — manual approval gate via GitHub Environments
- EAS build (production profile)
- Store submission

### Supabase Schema Migration Workflow

All database schema changes follow this process:
1. `supabase migration new <name>` creates a timestamped SQL file in `supabase/migrations/`.
2. The migration is tested locally with `supabase db reset`.
3. CI runs `supabase db push --dry-run` against staging to validate syntax.
4. On merge, CI applies the migration to the staging Supabase project.
5. Production migration is applied only on release, behind a GitHub Environment manual approval gate.

This ensures production schema is never modified by an automated process without explicit human sign-off.

### Zero-Downtime Migration Policy

FSRS state schema changes must be backwards-compatible for at least one app version (to support users who haven't updated). This means:
- **Additive changes only** (new columns, new tables) are deployed freely.
- **Breaking changes** (column renames, type changes) require a multi-step migration with a compatibility shim.
- Column removals are deferred to the subsequent release after the old app version is no longer supported.

### Consequences

- **Positive:** Fully automated quality gates. No manual build steps for testers or store submission. Staging/production isolation. Schema migration version history in Git.
- **Negative:** EAS Build has a free-tier build queue limit (30 builds/month) — paid plan may be needed for active development periods. iOS builds require Apple Developer Program membership ($99/year) and certificate management in EAS Secrets.
- **Neutral:** All secrets (Supabase keys, EAS token, Apple certificates, Google Play JSON key) are stored as GitHub Actions secrets and EAS secrets. A secrets audit should be performed before any open-source release of the repository.

---

## Summary Table

| ADR | Decision | Status |
|---|---|---|
| ADR-001 | Flutter (Dart) for mobile | LOCKED |
| ADR-002 | Supabase for backend | LOCKED |
| ADR-003 | Riverpod for state management | LOCKED |
| ADR-004 | FSRS v4 for SRS algorithm | LOCKED |
| ADR-005 | Hybrid audio: native recordings + KurdishTTS.com | LOCKED |
| ADR-006 | JSON/YAML in repository for content | LOCKED |
| ADR-007 | Character picker bar for ê î û ç ş | LOCKED |
| ADR-008 | Offline-first SRS with Drift/SQLite + Supabase sync | LOCKED |
| ADR-009 | Kurmanji-specific: LTR, Noto Sans, Unicode NFC | LOCKED |
| ADR-010 | GitHub Actions + EAS Build CI/CD | LOCKED |

---

## ADR-011: iOS Native Pivot — SwiftUI

**Status:** LOCKED
**Decision Date:** 2026-03-14
**Supersedes:** ADR-001 (Flutter), ADR-003 (Riverpod)

### Context

After completing the research phase, the project owner decided to target **iOS only** for the MVP, dropping the cross-platform requirement. The Kurdish diaspora audience skews heavily toward iPhone users in Western Europe and North America. A native iOS app delivers better performance, tighter Apple ecosystem integration (Sign in with Apple, StoreKit, AVSpeechSynthesizer), and simpler deployment via Xcode + TestFlight. The small team size argument that favored Flutter is offset by the fact that maintaining one native platform is simpler than one cross-platform framework with platform-specific workarounds.

### Decision

**SwiftUI (Swift)** replaces Flutter (Dart) as the mobile framework. **@Observable / SwiftData** replaces Riverpod as the state management approach.

### New Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| UI framework | **SwiftUI** | Declarative, native iOS, first-class Apple support |
| Language | **Swift 5.9+** | Modern concurrency (async/await, actors), strong typing |
| State management | **@Observable + SwiftData** | Native to SwiftUI, no third-party dependencies |
| Local persistence | **SwiftData** (Core Data successor) | Offline-first SRS card storage, iCloud sync possible |
| Backend | **Supabase** (unchanged) | PostgreSQL + Auth + Storage — `supabase-swift` SDK |
| SRS algorithm | **FSRS v4** (unchanged) | Rewritten in Swift (was Dart skeleton) |
| Audio | **AVFoundation + KurdishTTS.com API** (unchanged) | Native audio playback, background audio support |
| Content format | **JSON in repo** (unchanged) | Decoded via Swift `Codable` |

### Consequences

- **Positive:** Native performance, smaller binary size (~5MB vs ~15MB), first-class accessibility (VoiceOver), StoreKit for subscriptions, WidgetKit for streak widgets, no JavaScript/Dart bridge overhead.
- **Negative:** No Android support in MVP. Android users must wait for a future phase (could use KMP for shared logic later).
- **Migration impact:** SRS Dart skeleton → Swift rewrite. poc-spec.md Sprint 1 tasks updated for Xcode/SwiftUI. Frontend agent reconfigured for SwiftUI.

### Alternatives Reconsidered

| Option | Status |
|---|---|
| Flutter (Dart) | Dropped — cross-platform not needed for iOS-only MVP |
| React Native | Same rationale as ADR-001 rejection, plus iOS-native is now preferred |
| Kotlin Multiplatform | Deferred — may be used later for shared business logic if Android is added |

---

The following questions are deferred to V2 design and must not block MVP development:

1. **FSRS parameter personalization:** When should the app begin collecting enough review history to optimize the 17 FSRS parameters per user? What is the minimum review count threshold? (Suggested: 100 reviews per card type.)
2. **Sorani support:** If Sorani Kurdish (Arabic script, RTL) is added, what is the full scope of RTL layout changes required across the app?
3. **Content CMS migration:** At what content volume (number of units) does the JSON/YAML-in-repo approach break down, and what headless CMS should replace it?
4. **Leaderboard real-time:** When Supabase Realtime is enabled for leaderboard features, what are the connection cost implications at scale?
5. **FSRS v5 migration:** When FSRS v5 becomes stable, what is the migration path for existing user card states computed under v4 parameters?

---

*This document is the authoritative record of all architectural decisions for Kurdlingo. Changes to any LOCKED decision require a new ADR entry superseding the relevant section, approved by the Staff Manager and Lead Engineer.*
