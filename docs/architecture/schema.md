# Supabase PostgreSQL Schema

> **Owner:** `backend` agent (Task B3)
> **Status:** COMPLETE
> **Last Updated:** 2026-03-12

---

## 1. Entity-Relationship Overview

Kurdlingo uses six tables. Three are content tables (read-only for authenticated users) and three are user-data tables (protected by Row-Level Security).

```
auth.users (Supabase built-in)
    │
    └── profiles (1:1)
            │
            ├── fsrs_cards (1:many) ──── vocabulary_items (many:many bridge)
            ├── exercise_results (1:many) ── vocabulary_items
            └── user_progress (1:many) ──── lesson_units

vocabulary_items ◄── lesson_units.vocabulary_item_ids (uuid[])
lesson_units ──► lesson_units (self-referential: prerequisite_unit_id)
```

**Content tables** (seeded from YAML/JSON at deploy time, read-only for app users):
- `vocabulary_items` — the Kurdish dictionary corpus
- `lesson_units` — skill-tree nodes defining the course structure

**User-data tables** (one set of rows per authenticated user, RLS-protected):
- `profiles` — gamification state (XP, gems, streak)
- `fsrs_cards` — per-user FSRS v4 spaced-repetition state for every card
- `exercise_results` — immutable append-only log of every exercise attempt
- `user_progress` — per-unit completion status and star rating

---

## 2. Table-by-Table Specification

### 2.1 `profiles`

Extends `auth.users` with a 1:1 row created automatically on sign-up via trigger.

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | `uuid` | PK, FK → `auth.users(id)` ON DELETE CASCADE | Matches Supabase auth UID |
| `username` | `text` | UNIQUE, NOT NULL | Chosen display handle |
| `display_name` | `text` | | Full name or nickname |
| `created_at` | `timestamptz` | DEFAULT `now()` | Account creation time |
| `streak_count` | `int` | DEFAULT 0, NOT NULL | Consecutive daily study days |
| `last_active_date` | `date` | | Date of most recent session (UTC) |
| `total_xp` | `int` | DEFAULT 0, NOT NULL | Cumulative XP across all units |
| `gems` | `int` | DEFAULT 0, NOT NULL | In-app premium currency |

**Notes:** `streak_count` and `last_active_date` are updated by a server-side function called at session start, not from the client, to prevent tampering.

---

### 2.2 `vocabulary_items`

The Kurdish dictionary. Loaded from `assets/content/vocabulary.yaml` at deploy time. Never written to by the app client.

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | `uuid` | PK, DEFAULT `gen_random_uuid()` | Stable item identifier |
| `word` | `text` | NOT NULL | Kurmanji headword (Latin script) |
| `pos` | `text` | NOT NULL | Part of speech (`noun`, `verb`, `adj`, …) |
| `glosses` | `jsonb` | NOT NULL | `{"en": "...", "de": "...", "tr": "..."}` |
| `ipa` | `text` | | IPA pronunciation string |
| `examples` | `jsonb` | | Array of `{kurmanji, translation}` objects |
| `forms` | `jsonb` | | Inflected forms: `{plural, construct_state, …}` |
| `tags` | `text[]` | | Thematic tags: `["body","A1","high-frequency"]` |
| `difficulty_rating` | `float8` | DEFAULT 0.3 | Initial FSRS difficulty hint (0–1) |
| `created_at` | `timestamptz` | DEFAULT `now()` | Seed timestamp |

---

### 2.3 `lesson_units`

Skill-tree nodes. Each unit references the vocabulary items it teaches and optionally a prerequisite unit that must be completed first.

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | `uuid` | PK, DEFAULT `gen_random_uuid()` | Unit identifier |
| `level` | `text` | NOT NULL | CEFR level string, e.g. `A1.1`, `A2.3` |
| `unit_number` | `int` | NOT NULL | Ordering within a level |
| `title_kurmanji` | `text` | NOT NULL | Unit title in Kurmanji |
| `title_english` | `text` | NOT NULL | Unit title in English |
| `required_xp` | `int` | DEFAULT 0, NOT NULL | XP needed to unlock this unit |
| `prerequisite_unit_id` | `uuid` | FK → `lesson_units(id)`, NULLABLE | Self-referential unlock dependency |
| `vocabulary_item_ids` | `uuid[]` | NOT NULL, DEFAULT `'{}'` | Ordered list of vocabulary_item IDs in this unit |
| `created_at` | `timestamptz` | DEFAULT `now()` | Seed timestamp |

---

### 2.4 `fsrs_cards`

The core spaced-repetition state. One row per (user, vocabulary_item) pair. Created lazily when a user first encounters a card. Synced bidirectionally with the local Drift/SQLite database (see Section 5).

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | `uuid` | PK, DEFAULT `gen_random_uuid()` | Card row identifier |
| `user_id` | `uuid` | NOT NULL, FK → `profiles(id)` ON DELETE CASCADE | Owning user |
| `vocabulary_item_id` | `uuid` | NOT NULL, FK → `vocabulary_items(id)` ON DELETE CASCADE | Which word |
| `stability` | `float8` | DEFAULT 0.0 | FSRS S parameter (days) |
| `difficulty` | `float8` | DEFAULT 0.3 | FSRS D parameter (0–1) |
| `due_date` | `timestamptz` | NOT NULL, DEFAULT `now()` | When card is next due for review |
| `last_review` | `timestamptz` | | Timestamp of most recent rating |
| `review_count` | `int` | DEFAULT 0, NOT NULL | Total number of reviews |
| `state` | `text` | NOT NULL, CHECK IN (`new`,`learning`,`review`,`relearning`) | FSRS card state |
| `created_at` | `timestamptz` | DEFAULT `now()` | First encounter |
| `updated_at` | `timestamptz` | DEFAULT `now()` | Auto-updated by trigger |

**Unique constraint:** `(user_id, vocabulary_item_id)` — one card per user per word.

---

### 2.5 `exercise_results`

Append-only audit log of every exercise attempt. Never updated or deleted by the client. Drives analytics and streaks.

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | `uuid` | PK, DEFAULT `gen_random_uuid()` | Attempt identifier |
| `user_id` | `uuid` | NOT NULL, FK → `profiles(id)` ON DELETE CASCADE | Owning user |
| `vocabulary_item_id` | `uuid` | NOT NULL, FK → `vocabulary_items(id)` | Which word was exercised |
| `exercise_type` | `text` | NOT NULL | `multiple_choice`, `fill_blank`, `listening`, `flashcard` |
| `was_correct` | `bool` | NOT NULL | Whether the user answered correctly |
| `response_time_ms` | `int` | | Milliseconds to answer |
| `rating` | `int` | CHECK (`rating` BETWEEN 1 AND 4) | FSRS rating: 1=Again 2=Hard 3=Good 4=Easy |
| `created_at` | `timestamptz` | DEFAULT `now()`, NOT NULL | Attempt timestamp (immutable) |

---

### 2.6 `user_progress`

One row per (user, lesson_unit) pair, tracking completion state and stars earned.

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | `uuid` | PK, DEFAULT `gen_random_uuid()` | Progress row identifier |
| `user_id` | `uuid` | NOT NULL, FK → `profiles(id)` ON DELETE CASCADE | Owning user |
| `lesson_unit_id` | `uuid` | NOT NULL, FK → `lesson_units(id)` ON DELETE CASCADE | Which unit |
| `status` | `text` | NOT NULL, CHECK IN (`locked`,`unlocked`,`in_progress`,`completed`) | Unlock/completion state |
| `lessons_completed` | `int` | DEFAULT 0, NOT NULL | Number of lessons finished within the unit |
| `xp_earned` | `int` | DEFAULT 0, NOT NULL | XP gained from this unit so far |
| `stars` | `int` | DEFAULT 0, CHECK (`stars` BETWEEN 0 AND 3) | Performance rating 0–3 |
| `completed_at` | `timestamptz` | | When unit reached `completed` status |

**Unique constraint:** `(user_id, lesson_unit_id)` — one progress row per user per unit.

---

## 3. RLS Policy Summary

| Table | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|
| `profiles` | Own row only (`id = auth.uid()`) | Service role only (via trigger) | Own row only | Prohibited |
| `vocabulary_items` | All authenticated users | Service role only | Service role only | Service role only |
| `lesson_units` | All authenticated users | Service role only | Service role only | Service role only |
| `fsrs_cards` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Prohibited |
| `exercise_results` | `user_id = auth.uid()` | `user_id = auth.uid()` | Prohibited (append-only) | Prohibited |
| `user_progress` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Prohibited |

**Key decisions:**
- `profiles` INSERT is handled by a `SECURITY DEFINER` trigger on `auth.users`, not from the client, preventing users from creating profiles for other UIDs.
- `exercise_results` has no UPDATE policy — the log is immutable. Corrections are made by inserting a compensating row.
- DELETE is prohibited on all user-data tables; soft-delete or account deletion is handled via `auth.users` cascade.

---

## 4. Index Rationale

| Index | Columns | Type | Rationale |
|---|---|---|---|
| `idx_fsrs_cards_user_due` | `(user_id, due_date)` | BTREE | Primary query pattern: fetch all cards due for a user sorted by due date. Covers the daily review queue load. |
| `idx_fsrs_cards_user_state` | `(user_id, state)` | BTREE | Filters cards by state (e.g. fetch only `learning` cards). Used during lesson session assembly. |
| `idx_exercise_results_user_created` | `(user_id, created_at DESC)` | BTREE | Powers the activity history feed and streak calculation, which reads recent rows per user. |
| `idx_user_progress_user_unit` | `(user_id, lesson_unit_id)` | BTREE | Also backed by a UNIQUE constraint; the index satisfies both uniqueness enforcement and the common lookup `WHERE user_id = ? AND lesson_unit_id = ?`. |
| `idx_vocabulary_items_tags` | `tags` | GIN | Enables fast filtering by tag array (e.g. `WHERE tags @> ARRAY['A1']`) for content seeding scripts and admin tooling. |
| `idx_lesson_units_level` | `level` | BTREE | Supports ordered skill-tree queries grouped by CEFR level. |

---

## 5. Sync Architecture (Drift ↔ Supabase)

### 5.1 Why offline-first

FSRS card scheduling must work without a network connection. The Flutter client uses **Drift** (SQLite) as the source of truth for card state during a session. Changes are queued and flushed to Supabase when connectivity is restored.

### 5.2 Local Drift schema (mirrored tables)

The Drift database mirrors two Supabase tables with identical column names and types (mapped to Dart types):

**`fsrs_cards` (local)**
```
id TEXT PK, user_id TEXT, vocabulary_item_id TEXT,
stability REAL, difficulty REAL, due_date INTEGER (Unix ms),
last_review INTEGER, review_count INTEGER, state TEXT,
created_at INTEGER, updated_at INTEGER,
is_dirty INTEGER DEFAULT 1   -- 1 = needs sync
```

**`exercise_results` (local)**
```
id TEXT PK, user_id TEXT, vocabulary_item_id TEXT,
exercise_type TEXT, was_correct INTEGER, response_time_ms INTEGER,
rating INTEGER, created_at INTEGER,
is_synced INTEGER DEFAULT 0   -- 0 = pending upload
```

**`sync_operations` (local only — not in Supabase)**
```
id INTEGER PK AUTOINCREMENT,
table_name TEXT NOT NULL,        -- 'fsrs_cards' | 'exercise_results'
row_id TEXT NOT NULL,            -- UUID of the affected row
operation TEXT NOT NULL,         -- 'upsert' | 'insert'
payload TEXT NOT NULL,           -- JSON snapshot of the row
created_at INTEGER NOT NULL,
attempts INTEGER DEFAULT 0,
last_error TEXT
```

### 5.3 Sync flow

```
[User completes exercise]
        │
        ▼
1. FSRS algorithm runs locally (Dart)
2. fsrs_cards updated in Drift (is_dirty = 1)
3. exercise_results row inserted in Drift (is_synced = 0)
4. sync_operations rows enqueued for both rows
        │
        ▼ (background, when online)
5. SyncService reads sync_operations WHERE attempts < 5
6. Upserts fsrs_cards to Supabase (ON CONFLICT (user_id, vocabulary_item_id) DO UPDATE)
7. Inserts exercise_results to Supabase
8. On success: sets is_dirty=0 / is_synced=1, deletes sync_operations row
9. On conflict (another device edited same card): last_write-wins on updated_at
```

### 5.4 Conflict resolution

- **fsrs_cards:** last-write-wins using `updated_at`. The Supabase upsert uses `ON CONFLICT DO UPDATE SET ... WHERE excluded.updated_at > fsrs_cards.updated_at`.
- **exercise_results:** insert-only; UUID primary keys prevent duplicates. Duplicate inserts on retry are silently ignored via `ON CONFLICT DO NOTHING`.
- **user_progress:** synced similarly to `fsrs_cards` with `updated_at` guard; local Drift mirrors the same columns plus `is_dirty`.

---

## 6. SQL Migration

```sql
-- =============================================================
-- Kurdlingo — Supabase PostgreSQL Migration
-- Version: 001_initial_schema
-- Date: 2026-03-12
-- =============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "moddatetime";

-- =============================================================
-- FUNCTION: updated_at trigger
-- =============================================================
CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================
-- TABLE: profiles
-- =============================================================
CREATE TABLE IF NOT EXISTS public.profiles (
  id               uuid        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username         text        UNIQUE NOT NULL,
  display_name     text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  streak_count     int         NOT NULL DEFAULT 0,
  last_active_date date,
  total_xp         int         NOT NULL DEFAULT 0,
  gems             int         NOT NULL DEFAULT 0
);

-- Auto-create profile on new auth user
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, username, display_name)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
    COALESCE(NEW.raw_user_meta_data->>'display_name', '')
  );
  RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own"
  ON public.profiles FOR SELECT
  TO authenticated
  USING (id = auth.uid());

CREATE POLICY "profiles_update_own"
  ON public.profiles FOR UPDATE
  TO authenticated
  USING (id = auth.uid())
  WITH CHECK (id = auth.uid());

-- =============================================================
-- TABLE: vocabulary_items
-- =============================================================
CREATE TABLE IF NOT EXISTS public.vocabulary_items (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  word             text        NOT NULL,
  pos              text        NOT NULL,
  glosses          jsonb       NOT NULL DEFAULT '{}',
  ipa              text,
  examples         jsonb       DEFAULT '[]',
  forms            jsonb       DEFAULT '{}',
  tags             text[]      DEFAULT '{}',
  difficulty_rating float8     NOT NULL DEFAULT 0.3,
  created_at       timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.vocabulary_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "vocabulary_items_select_authenticated"
  ON public.vocabulary_items FOR SELECT
  TO authenticated
  USING (true);

CREATE INDEX idx_vocabulary_items_tags
  ON public.vocabulary_items USING GIN (tags);

CREATE INDEX idx_vocabulary_items_pos
  ON public.vocabulary_items (pos);

-- =============================================================
-- TABLE: lesson_units
-- =============================================================
CREATE TABLE IF NOT EXISTS public.lesson_units (
  id                    uuid  PRIMARY KEY DEFAULT gen_random_uuid(),
  level                 text  NOT NULL,
  unit_number           int   NOT NULL,
  title_kurmanji        text  NOT NULL,
  title_english         text  NOT NULL,
  required_xp           int   NOT NULL DEFAULT 0,
  prerequisite_unit_id  uuid  REFERENCES public.lesson_units(id) ON DELETE SET NULL,
  vocabulary_item_ids   uuid[] NOT NULL DEFAULT '{}',
  created_at            timestamptz NOT NULL DEFAULT now(),
  UNIQUE (level, unit_number)
);

ALTER TABLE public.lesson_units ENABLE ROW LEVEL SECURITY;

CREATE POLICY "lesson_units_select_authenticated"
  ON public.lesson_units FOR SELECT
  TO authenticated
  USING (true);

CREATE INDEX idx_lesson_units_level
  ON public.lesson_units (level);

-- =============================================================
-- TABLE: fsrs_cards
-- =============================================================
CREATE TABLE IF NOT EXISTS public.fsrs_cards (
  id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  vocabulary_item_id  uuid        NOT NULL REFERENCES public.vocabulary_items(id) ON DELETE CASCADE,
  stability           float8      NOT NULL DEFAULT 0.0,
  difficulty          float8      NOT NULL DEFAULT 0.3,
  due_date            timestamptz NOT NULL DEFAULT now(),
  last_review         timestamptz,
  review_count        int         NOT NULL DEFAULT 0,
  state               text        NOT NULL DEFAULT 'new'
                        CHECK (state IN ('new', 'learning', 'review', 'relearning')),
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, vocabulary_item_id)
);

CREATE TRIGGER fsrs_cards_updated_at
  BEFORE UPDATE ON public.fsrs_cards
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE public.fsrs_cards ENABLE ROW LEVEL SECURITY;

CREATE POLICY "fsrs_cards_select_own"
  ON public.fsrs_cards FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "fsrs_cards_insert_own"
  ON public.fsrs_cards FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "fsrs_cards_update_own"
  ON public.fsrs_cards FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE INDEX idx_fsrs_cards_user_due
  ON public.fsrs_cards (user_id, due_date);

CREATE INDEX idx_fsrs_cards_user_state
  ON public.fsrs_cards (user_id, state);

-- =============================================================
-- TABLE: exercise_results
-- =============================================================
CREATE TABLE IF NOT EXISTS public.exercise_results (
  id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  vocabulary_item_id  uuid        NOT NULL REFERENCES public.vocabulary_items(id) ON DELETE CASCADE,
  exercise_type       text        NOT NULL,
  was_correct         boolean     NOT NULL,
  response_time_ms    int,
  rating              int         CHECK (rating BETWEEN 1 AND 4),
  created_at          timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.exercise_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "exercise_results_select_own"
  ON public.exercise_results FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "exercise_results_insert_own"
  ON public.exercise_results FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

-- No UPDATE policy: exercise_results is append-only

CREATE INDEX idx_exercise_results_user_created
  ON public.exercise_results (user_id, created_at DESC);

-- =============================================================
-- TABLE: user_progress
-- =============================================================
CREATE TABLE IF NOT EXISTS public.user_progress (
  id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  lesson_unit_id      uuid        NOT NULL REFERENCES public.lesson_units(id) ON DELETE CASCADE,
  status              text        NOT NULL DEFAULT 'locked'
                        CHECK (status IN ('locked', 'unlocked', 'in_progress', 'completed')),
  lessons_completed   int         NOT NULL DEFAULT 0,
  xp_earned           int         NOT NULL DEFAULT 0,
  stars               int         NOT NULL DEFAULT 0
                        CHECK (stars BETWEEN 0 AND 3),
  completed_at        timestamptz,
  updated_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, lesson_unit_id)
);

CREATE TRIGGER user_progress_updated_at
  BEFORE UPDATE ON public.user_progress
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE public.user_progress ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_progress_select_own"
  ON public.user_progress FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "user_progress_insert_own"
  ON public.user_progress FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "user_progress_update_own"
  ON public.user_progress FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE INDEX idx_user_progress_user_unit
  ON public.user_progress (user_id, lesson_unit_id);

-- =============================================================
-- GRANT service_role full access for seeding scripts
-- =============================================================
GRANT ALL ON public.vocabulary_items TO service_role;
GRANT ALL ON public.lesson_units TO service_role;
GRANT ALL ON public.profiles TO service_role;
GRANT ALL ON public.fsrs_cards TO service_role;
GRANT ALL ON public.exercise_results TO service_role;
GRANT ALL ON public.user_progress TO service_role;
```

---

## 7. Notes and Open Questions

- **`vocabulary_item_ids uuid[]` in `lesson_units`:** An array column is used instead of a join table to keep lesson ordering explicit and avoid an extra query. If the vocabulary corpus grows beyond ~10,000 items and lesson queries become a bottleneck, a `lesson_unit_vocabulary` join table should be considered.
- **`exercise_type` as free text:** Currently unconstrained. A CHECK constraint or enum should be added once all exercise types are finalised (tracked in ADR).
- **Streak calculation:** `streak_count` is not computed from `exercise_results` on every read. It is updated by a Supabase Edge Function called at session start, comparing `last_active_date` to `current_date`.
- **Leaderboard:** A future `leaderboard_weekly` materialised view (refreshed daily) can be derived from `profiles.total_xp` without schema changes.
- **FSRS `retrievability`:** Not stored as a column because it is a derived value (`R = e^(ln(0.9) * elapsed / stability)`), computed in Dart at runtime.
