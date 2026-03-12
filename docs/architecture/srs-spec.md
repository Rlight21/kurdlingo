# SRS Algorithm Specification — FSRS v4

> **Owner:** `backend` agent (Task B2)
> **Status:** COMPLETE
> **Last updated:** 2026-03-12

---

## Table of Contents

1. [Algorithm Overview](#1-algorithm-overview)
2. [Data Model](#2-data-model)
3. [Parameters — w0 through w16](#3-parameters--w0-through-w16)
4. [Core Formulas](#4-core-formulas)
5. [Rating Scale](#5-rating-scale)
6. [Integration with Kurdlingo](#6-integration-with-kurdlingo)
7. [Dart Skeleton Code](#7-dart-skeleton-code)

---

## 1. Algorithm Overview

### What is FSRS?

FSRS (Free Spaced Repetition Scheduler) v4 is an open-source spaced repetition algorithm
developed by Jarrett Ye (L-M-Sheep) and published in 2022. It is the algorithm that replaced
SM-2 as Anki's default scheduler in Anki 23.10.

FSRS is based on a **DSR model** (Difficulty, Stability, Retrievability):

- **Difficulty (D):** How inherently hard a card is to memorise. Ranges 1–10. Cards that are
  frequently forgotten gain higher difficulty. Persists across reviews.
- **Stability (S):** The number of days after which retrievability decays to 90%. A card with
  S = 10 will be at 90% recall 10 days after the last successful review. Stability grows with
  each successful review and resets (but not to zero) after a lapse.
- **Retrievability (R):** The estimated probability of recall right now, given how much time
  has passed since the last review and the current stability. Ranges 0–1.

### Why FSRS v4 over SM-2?

| Dimension | SM-2 (Anki legacy) | FSRS v4 |
|---|---|---|
| Model | Interval multiplier (EF) | Psychologically grounded DSR model |
| Forgetting curve | Assumed exponential | Power-law (empirically validated) |
| Difficulty | Single "ease factor" | Continuous difficulty + stability |
| Personalisation | None (fixed parameters) | 17 parameters optimisable per-user |
| Recall accuracy | Baseline | Measurably higher on public datasets |
| State transitions | Linear | Explicit New/Learning/Review/Relearning states |

For a language learning app like Kurdlingo, where learners encounter new vocabulary daily,
the improved recall accuracy and difficulty modelling of FSRS v4 directly translates to
fewer wasted reviews and better long-term retention.

### High-level scheduling flow

```
User sees card
     │
     ▼
Calculate R = retrievability(card, now)
     │
     ▼
User rates: Again | Hard | Good | Easy
     │
     ├── Again (lapse) ──► recalculate S'_f, increase D, move to Relearning
     │
     └── Hard/Good/Easy ──► recalculate S'_r, update D, schedule next Review
                                    │
                                    ▼
                          nextInterval = f(S', requestedRetention)
                          due = now + nextInterval
```

---

## 2. Data Model

### 2.1 CardState enum

```
New         — Card has never been reviewed
Learning    — Card is in the initial learning phase (short intervals, minutes/hours)
Review      — Card has graduated to spaced review (intervals in days)
Relearning  — Card lapsed (Again in Review state); short re-learning intervals
```

### 2.2 FSRSCard fields

| Field | Dart type | Description |
|---|---|---|
| `id` | `String` | UUID; maps to `vocabulary_item.id` in Supabase |
| `stability` | `double` | S — days until R drops to 90%; initially set by first review rating |
| `difficulty` | `double` | D — inherent card difficulty, range [1, 10] |
| `retrievability` | `double` | R — estimated recall probability at review time, range [0, 1] |
| `dueDate` | `DateTime` | When the card is next due for review (UTC) |
| `lastReview` | `DateTime?` | Timestamp of the most recent review (null for New cards) |
| `reviewCount` | `int` | Total number of reviews performed on this card |
| `lapseCount` | `int` | Number of times the card has been forgotten (Again in Review) |
| `state` | `CardState` | Current scheduling state |
| `elapsedDays` | `int` | Days since lastReview at the time of the last review (used in stability formula) |

### 2.3 SchedulingResult

The output of `scheduleReview()`. Immutable value object.

| Field | Dart type | Description |
|---|---|---|
| `card` | `FSRSCard` | Updated card with new stability, difficulty, state, dueDate |
| `reviewLog` | `ReviewLog` | Audit record for Supabase persistence |

### 2.4 ReviewLog fields

| Field | Dart type | Description |
|---|---|---|
| `cardId` | `String` | FK to vocabulary_item |
| `rating` | `Rating` | The rating given (Again/Hard/Good/Easy) |
| `state` | `CardState` | State the card was in when reviewed |
| `stability` | `double` | Stability after this review |
| `difficulty` | `double` | Difficulty after this review |
| `retrievability` | `double` | Retrievability at the moment of review |
| `scheduledDays` | `int` | Number of days until next due |
| `reviewedAt` | `DateTime` | UTC timestamp of review |

---

## 3. Parameters — w0 through w16

FSRS v4 uses 17 trainable parameters. The defaults below are the values from the published
FSRS v4 paper and are suitable for a new user before personalised optimisation.

| Index | Name (informal) | Default value | Role |
|---|---|---|---|
| w0 | initial_stability_again | 0.4072 | Initial S when first review is Again |
| w1 | initial_stability_hard | 1.1829 | Initial S when first review is Hard |
| w2 | initial_stability_good | 3.1262 | Initial S when first review is Good |
| w3 | initial_stability_easy | 7.9334 | Initial S when first review is Easy |
| w4 | initial_difficulty | 7.1949 | Baseline difficulty for difficulty formula |
| w5 | difficulty_decay | 0.5345 | Controls how quickly difficulty changes |
| w6 | difficulty_weight | 1.4604 | Weight of rating in difficulty update |
| w7 | stability_decay | 0.1030 | Stability decay multiplier for recall |
| w8 | stability_recall_factor | 1.9395 | Growth factor for stability after recall |
| w9 | stability_mean_reversion | 0.1100 | Mean reversion towards w4 in difficulty |
| w10 | hard_penalty | 0.2900 | Stability multiplier for Hard rating (< 1) |
| w11 | easy_bonus | 2.6100 | Stability multiplier for Easy rating (> 1) |
| w12 | stability_forget_factor | 0.0100 | Base stability after forgetting |
| w13 | stability_forget_decay | 0.9000 | Exponent on stability in forget formula |
| w14 | stability_forget_difficulty | 0.2000 | Difficulty influence on post-lapse stability |
| w15 | stability_forget_retrievability | 1.0000 | Retrievability influence on post-lapse stability |
| w16 | stability_forget_short_term | 1.0000 | Short-term stability factor after forgetting |

> **Note:** These defaults are taken from FSRS v4 (`fsrs-4.5` branch defaults as of 2024).
> The Supabase table `user_srs_parameters` will store per-user optimised weights after
> sufficient review history is available (typically 1 000+ reviews).

---

## 4. Core Formulas

All formulas use the variable names: **R** = retrievability, **S** = stability,
**D** = difficulty, **t** = elapsed days since last review, **r** = rating (1–4).

### 4.1 Retrievability

Estimates the probability of successful recall given elapsed time and current stability.

```
R(t, S) = (1 + t / (9 * S)) ^ (-1)
```

This is a power-law forgetting curve. When t = 0, R = 1 (perfect recall immediately
after review). When t = S, R ≈ 0.90 (stability is calibrated to the 90% retention point).

### 4.2 Stability after successful recall — S'_r

Applied when rating is Hard, Good, or Easy.

```
S'_r = S * (
    e ^ (w7)
  * (11 - D)
  * S ^ (-w8)
  * (e ^ (w9 * (1 - R)) - 1)
  * hard_penalty   [if rating == Hard,  else 1.0]
  * easy_bonus     [if rating == Easy,  else 1.0]
)
```

Where:
- `hard_penalty = w10` (default 0.29 — reduces stability growth for Hard)
- `easy_bonus = w11` (default 2.61 — boosts stability growth for Easy)
- `w7`, `w8`, `w9` shape the base growth curve

The formula encodes three intuitions: (1) harder cards grow stability more slowly,
(2) stability grows slower as stability is already high (forgetting is sublinear),
(3) being surprised by successful recall (low R) produces larger stability gains
(the "spacing effect" / "desirable difficulty").

### 4.3 Stability after forgetting — S'_f

Applied when rating is Again (lapse from Review or Relearning state).

```
S'_f = w12
     * D ^ (-w14)
     * ((S + 1) ^ w13 - 1)
     * e ^ (w15 * (1 - R))
```

The card's stability resets but is not zero. Cards that had high stability before the lapse
recover faster (the (S+1)^w13 term). Cards with lower difficulty also recover faster.

### 4.4 Difficulty update — D'

Applied on every review. Keeps difficulty from drifting too far from the population mean.

```
D'(D, r) = w5 * D_0(4) + (1 - w5) * (D - w6 * (r - 3))
```

Where:
- `D_0(4) = w4 - w6 * (4 - 3) = w4 - w6` — the "easy" baseline difficulty (mean reversion target)
- `r` = rating (1 = Again, 2 = Hard, 3 = Good, 4 = Easy)
- `w5` = mean reversion coefficient (keeps D anchored near the population mean)
- `w6` = how much each rating step shifts difficulty

After computing D', clamp to [1, 10].

### 4.5 Next interval — I

Given a target retention rate `R_d` (desired retention, default 0.9) and the new stability S':

```
I(S', R_d) = (9 * S') / (1/R_d - 1)   [derived by inverting the retrievability formula]
             rounded to nearest integer, minimum 1 day
```

For Learning/Relearning states, fixed short intervals are used instead (1 min, 10 min,
1 day) until the card graduates to Review state.

---

## 5. Rating Scale

| Value | Name | Meaning | Typical UX label |
|---|---|---|---|
| 1 | Again | Complete failure; could not recall | "Forgot" / "Again" |
| 2 | Hard | Recalled with significant difficulty | "Hard" |
| 3 | Good | Recalled correctly with moderate effort | "Good" |
| 4 | Easy | Recalled instantly with no effort | "Easy" |

### Psychological mapping for Kurdlingo

In a vocabulary drill, the four ratings map to the learner's subjective experience:

- **Again (1):** "I had no idea" or "I said the completely wrong word." The card is sent back
  to a short re-learning loop (10 minutes for the first lapse).
- **Hard (2):** "I remembered it eventually but it took effort / I almost said the wrong word."
  Interval grows less than normal.
- **Good (3):** "I remembered it correctly." Normal interval growth.
- **Easy (4):** "That was obvious / I always know this word." Interval grows significantly;
  this is the "leech" escape valve for over-scheduled cards.

The UI should present these four buttons after every card reveal in the lesson flow.

---

## 6. Integration with Kurdlingo

### 6.1 VocabularyItem → FSRSCard mapping

The Supabase `vocabulary_items` table stores linguistic data. The SRS state is stored in
a separate `user_card_states` table so it is user-specific.

```
vocabulary_items (shared, per-language-pair)
  id              UUID PK
  kurdish_word    TEXT
  english_word    TEXT
  ...

user_card_states (per user, per card)
  id              UUID PK
  user_id         UUID FK → auth.users
  vocabulary_id   UUID FK → vocabulary_items
  stability       FLOAT8
  difficulty      FLOAT8
  due_date        TIMESTAMPTZ
  last_review     TIMESTAMPTZ
  review_count    INT
  lapse_count     INT
  state           TEXT  CHECK (state IN ('new','learning','review','relearning'))
  elapsed_days    INT
  created_at      TIMESTAMPTZ DEFAULT now()
  updated_at      TIMESTAMPTZ DEFAULT now()
```

The Flutter `FSRSCard` model is constructed by joining these two tables on `vocabulary_id`.

### 6.2 Review trigger in lesson flow

```
Lesson session starts
  │
  ├── Query due cards: SELECT * FROM user_card_states
  │     WHERE user_id = $uid AND due_date <= now()
  │     ORDER BY due_date ASC LIMIT 20
  │
  ├── Interleave new cards (state = 'new') up to daily_new_limit (default: 10)
  │
  └── For each card shown:
        1. Construct FSRSCard from DB row
        2. Show Kurdish → English (or reverse) prompt
        3. User reveals answer
        4. User taps Again / Hard / Good / Easy
        5. Call FSRSScheduler.scheduleReview(card, rating)
        6. Persist SchedulingResult.card → user_card_states (upsert)
        7. Insert SchedulingResult.reviewLog → review_logs table
```

### 6.3 Supabase persistence

**Upsert card state** (called after every review):

```sql
INSERT INTO user_card_states
  (user_id, vocabulary_id, stability, difficulty, due_date,
   last_review, review_count, lapse_count, state, elapsed_days, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, now())
ON CONFLICT (user_id, vocabulary_id) DO UPDATE SET
  stability    = EXCLUDED.stability,
  difficulty   = EXCLUDED.difficulty,
  due_date     = EXCLUDED.due_date,
  last_review  = EXCLUDED.last_review,
  review_count = EXCLUDED.review_count,
  lapse_count  = EXCLUDED.lapse_count,
  state        = EXCLUDED.state,
  elapsed_days = EXCLUDED.elapsed_days,
  updated_at   = now();
```

**Insert review log** (immutable audit trail):

```sql
INSERT INTO review_logs
  (card_id, user_id, rating, state, stability, difficulty,
   retrievability, scheduled_days, reviewed_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, now());
```

### 6.4 Parameter optimisation (future)

After a user accumulates ≥ 1 000 review logs, an offline optimisation job (Python/WASM)
can minimise the log-loss between predicted R and actual recall outcomes to produce
personalised w0–w16 values. These are stored in `user_srs_parameters` and loaded at
session start. Until then, the default parameters in `FSRSParameters` are used.

---

## 7. Dart Skeleton Code

The following file should live at `lib/services/srs/fsrs.dart`.

```dart
// lib/services/srs/fsrs.dart
//
// FSRS v4 Spaced Repetition Scheduler — Dart skeleton
// Reference: https://github.com/open-spaced-repetition/fsrs4anki
//
// This file is skeleton/specification code.
// Production implementation should add: error handling, freezed codegen,
// Supabase serialisation, and unit tests.

import 'dart:math' as math;

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

enum CardState { newCard, learning, review, relearning }

enum Rating {
  again(1),
  hard(2),
  good(3),
  easy(4);

  const Rating(this.value);
  final int value;
}

// ---------------------------------------------------------------------------
// FSRSParameters — 17 trainable weights with FSRS v4 defaults
// ---------------------------------------------------------------------------

class FSRSParameters {
  const FSRSParameters({
    this.w0  = 0.4072,   // initial stability: Again
    this.w1  = 1.1829,   // initial stability: Hard
    this.w2  = 3.1262,   // initial stability: Good
    this.w3  = 7.9334,   // initial stability: Easy
    this.w4  = 7.1949,   // initial difficulty baseline
    this.w5  = 0.5345,   // difficulty mean-reversion coefficient
    this.w6  = 1.4604,   // difficulty shift per rating step
    this.w7  = 0.1030,   // stability recall: e^w7 multiplier
    this.w8  = 1.9395,   // stability recall: S^(-w8) decay
    this.w9  = 0.1100,   // stability recall: spacing effect weight
    this.w10 = 0.2900,   // hard penalty multiplier (< 1)
    this.w11 = 2.6100,   // easy bonus multiplier  (> 1)
    this.w12 = 0.0100,   // post-lapse stability base
    this.w13 = 0.9000,   // post-lapse stability: prior-S exponent
    this.w14 = 0.2000,   // post-lapse stability: difficulty factor
    this.w15 = 1.0000,   // post-lapse stability: retrievability factor
    this.w16 = 1.0000,   // post-lapse stability: short-term factor
    this.requestedRetention = 0.9, // target recall probability (R_d)
    this.maximumInterval    = 36500, // ~100 years ceiling
  });

  final double w0,  w1,  w2,  w3;
  final double w4,  w5,  w6;
  final double w7,  w8,  w9,  w10, w11;
  final double w12, w13, w14, w15, w16;
  final double requestedRetention;
  final int    maximumInterval;

  /// Initial stability for first-time reviews, indexed by Rating.value (1-4).
  double initialStability(Rating rating) {
    switch (rating) {
      case Rating.again: return w0;
      case Rating.hard:  return w1;
      case Rating.good:  return w2;
      case Rating.easy:  return w3;
    }
  }

  /// D_0(4) — the easy-baseline used as mean-reversion anchor in difficulty update.
  double get difficultyMeanReversionTarget => w4 - w6 * (4 - 3);

  FSRSParameters copyWith({
    double? w0,  double? w1,  double? w2,  double? w3,
    double? w4,  double? w5,  double? w6,
    double? w7,  double? w8,  double? w9,  double? w10, double? w11,
    double? w12, double? w13, double? w14, double? w15, double? w16,
    double? requestedRetention,
    int?    maximumInterval,
  }) {
    return FSRSParameters(
      w0:  w0  ?? this.w0,   w1:  w1  ?? this.w1,
      w2:  w2  ?? this.w2,   w3:  w3  ?? this.w3,
      w4:  w4  ?? this.w4,   w5:  w5  ?? this.w5,   w6:  w6  ?? this.w6,
      w7:  w7  ?? this.w7,   w8:  w8  ?? this.w8,   w9:  w9  ?? this.w9,
      w10: w10 ?? this.w10,  w11: w11 ?? this.w11,
      w12: w12 ?? this.w12,  w13: w13 ?? this.w13,
      w14: w14 ?? this.w14,  w15: w15 ?? this.w15,  w16: w16 ?? this.w16,
      requestedRetention: requestedRetention ?? this.requestedRetention,
      maximumInterval:    maximumInterval    ?? this.maximumInterval,
    );
  }
}

// ---------------------------------------------------------------------------
// FSRSCard — immutable value object (use copyWith to produce updated cards)
// ---------------------------------------------------------------------------

class FSRSCard {
  const FSRSCard({
    required this.id,
    this.stability    = 0.0,
    this.difficulty   = 5.0,  // mid-range default
    this.retrievability = 0.0,
    required this.dueDate,
    this.lastReview,
    this.reviewCount  = 0,
    this.lapseCount   = 0,
    this.state        = CardState.newCard,
    this.elapsedDays  = 0,
  });

  final String    id;
  final double    stability;
  final double    difficulty;
  final double    retrievability;
  final DateTime  dueDate;
  final DateTime? lastReview;
  final int       reviewCount;
  final int       lapseCount;
  final CardState state;
  final int       elapsedDays;   // days between last two reviews (used in S'_r formula)

  FSRSCard copyWith({
    double?    stability,
    double?    difficulty,
    double?    retrievability,
    DateTime?  dueDate,
    DateTime?  lastReview,
    int?       reviewCount,
    int?       lapseCount,
    CardState? state,
    int?       elapsedDays,
  }) {
    return FSRSCard(
      id:              id,
      stability:       stability       ?? this.stability,
      difficulty:      difficulty      ?? this.difficulty,
      retrievability:  retrievability  ?? this.retrievability,
      dueDate:         dueDate         ?? this.dueDate,
      lastReview:      lastReview      ?? this.lastReview,
      reviewCount:     reviewCount     ?? this.reviewCount,
      lapseCount:      lapseCount      ?? this.lapseCount,
      state:           state           ?? this.state,
      elapsedDays:     elapsedDays     ?? this.elapsedDays,
    );
  }

  /// Convenience: days elapsed since lastReview as of [now].
  int daysSinceLastReview(DateTime now) {
    if (lastReview == null) return 0;
    return now.difference(lastReview!).inDays;
  }
}

// ---------------------------------------------------------------------------
// ReviewLog — immutable audit record written to Supabase after every review
// ---------------------------------------------------------------------------

class ReviewLog {
  const ReviewLog({
    required this.cardId,
    required this.rating,
    required this.stateBefore,
    required this.stability,
    required this.difficulty,
    required this.retrievability,
    required this.scheduledDays,
    required this.reviewedAt,
  });

  final String    cardId;
  final Rating    rating;
  final CardState stateBefore;
  final double    stability;
  final double    difficulty;
  final double    retrievability;
  final int       scheduledDays;
  final DateTime  reviewedAt;

  Map<String, dynamic> toJson() => {
    'card_id':        cardId,
    'rating':         rating.value,
    'state':          stateBefore.name,
    'stability':      stability,
    'difficulty':     difficulty,
    'retrievability': retrievability,
    'scheduled_days': scheduledDays,
    'reviewed_at':    reviewedAt.toIso8601String(),
  };
}

// ---------------------------------------------------------------------------
// SchedulingResult — output of FSRSScheduler.scheduleReview()
// ---------------------------------------------------------------------------

class SchedulingResult {
  const SchedulingResult({
    required this.card,
    required this.reviewLog,
  });

  final FSRSCard  card;
  final ReviewLog reviewLog;
}

// ---------------------------------------------------------------------------
// FSRSScheduler — core algorithm
// ---------------------------------------------------------------------------

class FSRSScheduler {
  const FSRSScheduler({FSRSParameters? parameters})
      : params = parameters ?? const FSRSParameters();

  final FSRSParameters params;

  // -------------------------------------------------------------------------
  // Public API
  // -------------------------------------------------------------------------

  /// Returns R(t, S): estimated probability of recall right now.
  /// Uses the power-law forgetting curve: R = (1 + t/(9*S))^(-1)
  double calculateRetrievability(FSRSCard card, DateTime now) {
    if (card.state == CardState.newCard || card.lastReview == null) return 0.0;
    final double t = card.daysSinceLastReview(now).toDouble();
    final double s = card.stability;
    if (s <= 0) return 0.0;
    return math.pow(1.0 + t / (9.0 * s), -1.0).toDouble();
  }

  /// Core scheduling method. Returns an updated FSRSCard and a ReviewLog.
  SchedulingResult scheduleReview(FSRSCard card, Rating rating, {DateTime? now}) {
    final DateTime reviewedAt = now ?? DateTime.now().toUtc();
    final double r = calculateRetrievability(card, reviewedAt);

    FSRSCard updated;

    switch (card.state) {
      case CardState.newCard:
        updated = _scheduleNew(card, rating, reviewedAt);
        break;
      case CardState.learning:
      case CardState.relearning:
        updated = _scheduleLearning(card, rating, reviewedAt, r);
        break;
      case CardState.review:
        updated = _scheduleReview(card, rating, reviewedAt, r);
        break;
    }

    final log = ReviewLog(
      cardId:         card.id,
      rating:         rating,
      stateBefore:    card.state,
      stability:      updated.stability,
      difficulty:     updated.difficulty,
      retrievability: r,
      scheduledDays:  updated.dueDate.difference(reviewedAt).inDays,
      reviewedAt:     reviewedAt,
    );

    return SchedulingResult(card: updated, reviewLog: log);
  }

  // -------------------------------------------------------------------------
  // Private scheduling handlers
  // -------------------------------------------------------------------------

  /// First review of a brand-new card. Stability is set by initial w values.
  FSRSCard _scheduleNew(FSRSCard card, Rating rating, DateTime reviewedAt) {
    final double s = params.initialStability(rating);
    final double d = _initialDifficulty(rating);

    CardState nextState;
    DateTime  due;

    if (rating == Rating.again) {
      nextState = CardState.learning;
      due       = reviewedAt.add(const Duration(minutes: 1));
    } else if (rating == Rating.hard) {
      nextState = CardState.learning;
      due       = reviewedAt.add(const Duration(minutes: 5));
    } else if (rating == Rating.good) {
      nextState = CardState.learning;
      due       = reviewedAt.add(const Duration(minutes: 10));
    } else {
      // Easy — skip learning phase, graduate immediately
      nextState = CardState.review;
      due       = reviewedAt.add(Duration(days: _nextInterval(s)));
    }

    return card.copyWith(
      stability:      s,
      difficulty:     d,
      retrievability: 1.0,
      dueDate:        due,
      lastReview:     reviewedAt,
      reviewCount:    card.reviewCount + 1,
      state:          nextState,
      elapsedDays:    0,
    );
  }

  /// Review during Learning or Relearning phase (short fixed intervals).
  FSRSCard _scheduleLearning(
    FSRSCard card, Rating rating, DateTime reviewedAt, double r) {

    final double d = _updateDifficulty(card.difficulty, rating);
    double s = card.stability;
    CardState nextState = card.state;
    DateTime  due;

    if (rating == Rating.again) {
      // Restart learning
      due = reviewedAt.add(const Duration(minutes: 10));
    } else if (rating == Rating.hard) {
      due = reviewedAt.add(const Duration(minutes: 20));
    } else if (rating == Rating.good) {
      // Graduate to Review
      nextState = CardState.review;
      s         = math.max(s, 1.0);
      due       = reviewedAt.add(Duration(days: _nextInterval(s)));
    } else {
      // Easy — graduate with bonus
      nextState = CardState.review;
      s         = s * params.w11;
      due       = reviewedAt.add(Duration(days: _nextInterval(s)));
    }

    return card.copyWith(
      stability:      s,
      difficulty:     d,
      retrievability: r,
      dueDate:        due,
      lastReview:     reviewedAt,
      reviewCount:    card.reviewCount + 1,
      state:          nextState,
      elapsedDays:    card.daysSinceLastReview(reviewedAt),
    );
  }

  /// Review in the spaced-repetition (Review) state.
  FSRSCard _scheduleReview(
    FSRSCard card, Rating rating, DateTime reviewedAt, double r) {

    final int    t       = card.daysSinceLastReview(reviewedAt);
    final double d       = _updateDifficulty(card.difficulty, rating);
    double s;
    CardState nextState;
    DateTime  due;
    int lapseCount       = card.lapseCount;

    if (rating == Rating.again) {
      // Lapse
      s         = _stabilityAfterForgetting(card.stability, d, r);
      nextState = CardState.relearning;
      lapseCount++;
      due       = reviewedAt.add(const Duration(minutes: 10));
    } else {
      s         = _stabilityAfterRecall(card.stability, d, r, rating);
      s         = s.clamp(1.0, params.maximumInterval.toDouble());
      nextState = CardState.review;
      due       = reviewedAt.add(Duration(days: _nextInterval(s)));
    }

    return card.copyWith(
      stability:      s,
      difficulty:     d,
      retrievability: r,
      dueDate:        due,
      lastReview:     reviewedAt,
      reviewCount:    card.reviewCount + 1,
      lapseCount:     lapseCount,
      state:          nextState,
      elapsedDays:    t,
    );
  }

  // -------------------------------------------------------------------------
  // Core FSRS formulas
  // -------------------------------------------------------------------------

  /// Formula 4.2 — Stability after successful recall.
  /// S'_r = S * e^w7 * (11 - D) * S^(-w8) * (e^(w9*(1-R)) - 1) * modifier
  double _stabilityAfterRecall(
      double s, double d, double r, Rating rating) {
    final double modifier = rating == Rating.hard
        ? params.w10
        : rating == Rating.easy
            ? params.w11
            : 1.0;

    final double growth = math.exp(params.w7)
        * (11.0 - d)
        * math.pow(s, -params.w8)
        * (math.exp(params.w9 * (1.0 - r)) - 1.0)
        * modifier;

    return s * (1.0 + growth);
  }

  /// Formula 4.3 — Stability after forgetting (lapse).
  /// S'_f = w12 * D^(-w14) * ((S+1)^w13 - 1) * e^(w15*(1-R))
  double _stabilityAfterForgetting(double s, double d, double r) {
    return params.w12
        * math.pow(d, -params.w14)
        * (math.pow(s + 1.0, params.w13) - 1.0)
        * math.exp(params.w15 * (1.0 - r));
  }

  /// Formula 4.4 — Difficulty update with mean reversion.
  /// D' = w5 * D_0(4) + (1 - w5) * (D - w6*(r-3)), clamped [1,10]
  double _updateDifficulty(double d, Rating rating) {
    final double anchor = params.difficultyMeanReversionTarget;
    final double delta  = params.w6 * (rating.value - 3);
    final double next   = params.w5 * anchor + (1.0 - params.w5) * (d - delta);
    return next.clamp(1.0, 10.0);
  }

  /// Formula 4.5 — Next interval from new stability and requested retention.
  /// I = (9 * S) / (1/R_d - 1), rounded, clamped [1, maximumInterval]
  int _nextInterval(double s) {
    final double r  = params.requestedRetention;
    final double interval = (9.0 * s) / (1.0 / r - 1.0);
    return interval.round().clamp(1, params.maximumInterval);
  }

  /// Initial difficulty for a brand-new card.
  /// D_0(r) = w4 - w6 * (r - 3), clamped [1, 10]
  double _initialDifficulty(Rating rating) {
    final double d = params.w4 - params.w6 * (rating.value - 3);
    return d.clamp(1.0, 10.0);
  }
}
```

---

## Appendix A — Supabase table DDL

```sql
-- SRS state per user per card
CREATE TABLE user_card_states (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  vocabulary_id  UUID NOT NULL REFERENCES vocabulary_items(id) ON DELETE CASCADE,
  stability      FLOAT8  NOT NULL DEFAULT 0,
  difficulty     FLOAT8  NOT NULL DEFAULT 5,
  due_date       TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_review    TIMESTAMPTZ,
  review_count   INT NOT NULL DEFAULT 0,
  lapse_count    INT NOT NULL DEFAULT 0,
  state          TEXT NOT NULL DEFAULT 'new'
                   CHECK (state IN ('new','learning','review','relearning')),
  elapsed_days   INT NOT NULL DEFAULT 0,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, vocabulary_id)
);

-- Immutable review audit log
CREATE TABLE review_logs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id         UUID NOT NULL REFERENCES vocabulary_items(id),
  user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  rating          SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 4),
  state           TEXT NOT NULL,
  stability       FLOAT8 NOT NULL,
  difficulty      FLOAT8 NOT NULL,
  retrievability  FLOAT8 NOT NULL,
  scheduled_days  INT NOT NULL,
  reviewed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Per-user optimised FSRS parameters (populated after ≥1000 reviews)
CREATE TABLE user_srs_parameters (
  user_id     UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  w           FLOAT8[17] NOT NULL,  -- w0..w16
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## Appendix B — Unit test checklist

Before shipping the FSRS implementation, the following cases must pass:

- [ ] New card rated Good: state → Learning, dueDate = +10 min, S = w2 (3.1262)
- [ ] New card rated Easy: state → Review, dueDate ≈ +4 days (interval formula), S = w3
- [ ] Learning card rated Good: state → Review, S ≥ 1
- [ ] Review card rated Again: state → Relearning, lapseCount += 1, S < prior S
- [ ] Review card rated Easy: S > prior S * 1.0 (stability increases)
- [ ] Difficulty clamp: D never < 1 or > 10 regardless of rating sequence
- [ ] Retrievability = 1.0 immediately after review (t=0)
- [ ] Retrievability ≈ 0.9 at t = S days (definition of stability)
- [ ] nextInterval respects maximumInterval ceiling
- [ ] ReviewLog.toJson() produces keys matching Supabase column names
