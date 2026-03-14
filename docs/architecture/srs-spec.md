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
7. [Swift Skeleton Code](#7-swift-skeleton-code)

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

| Field | Swift type | Description |
|---|---|---|
| `id` | `String` | UUID; maps to `vocabulary_item.id` in Supabase |
| `stability` | `Double` | S — days until R drops to 90%; initially set by first review rating |
| `difficulty` | `Double` | D — inherent card difficulty, range [1, 10] |
| `retrievability` | `Double` | R — estimated recall probability at review time, range [0, 1] |
| `dueDate` | `Date` | When the card is next due for review (UTC) |
| `lastReview` | `Date?` | Timestamp of the most recent review (nil for New cards) |
| `reviewCount` | `Int` | Total number of reviews performed on this card |
| `lapseCount` | `Int` | Number of times the card has been forgotten (Again in Review) |
| `state` | `CardState` | Current scheduling state |
| `elapsedDays` | `Int` | Days since lastReview at the time of the last review (used in stability formula) |

### 2.3 SchedulingResult

The output of `scheduleReview()`. Immutable value type.

| Field | Swift type | Description |
|---|---|---|
| `card` | `FSRSCard` | Updated card with new stability, difficulty, state, dueDate |
| `reviewLog` | `ReviewLog` | Audit record for Supabase persistence |

### 2.4 ReviewLog fields

| Field | Swift type | Description |
|---|---|---|
| `cardId` | `String` | FK to vocabulary_item |
| `rating` | `Rating` | The rating given (Again/Hard/Good/Easy) |
| `state` | `CardState` | State the card was in when reviewed |
| `stability` | `Double` | Stability after this review |
| `difficulty` | `Double` | Difficulty after this review |
| `retrievability` | `Double` | Retrievability at the moment of review |
| `scheduledDays` | `Int` | Number of days until next due |
| `reviewedAt` | `Date` | UTC timestamp of review |

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

The SwiftUI `FSRSCard` model is constructed by joining these two tables on `vocabulary_id`.

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

## 7. Swift Skeleton Code

The following file should live at `Sources/Services/SRS/FSRS.swift`.

```swift
// Sources/Services/SRS/FSRS.swift
//
// FSRS v4 Spaced Repetition Scheduler — Swift skeleton
// Reference: https://github.com/open-spaced-repetition/fsrs4anki
//
// This file is skeleton/specification code.
// Production implementation should add: error handling, Codable extensions,
// Supabase serialisation, and unit tests.

import Foundation

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

enum CardState: String, Codable {
    case newCard     = "new"
    case learning    = "learning"
    case review      = "review"
    case relearning  = "relearning"
}

enum Rating: Int, Codable {
    case again = 1
    case hard  = 2
    case good  = 3
    case easy  = 4
}

// ---------------------------------------------------------------------------
// FSRSParameters — 17 trainable weights with FSRS v4 defaults
// ---------------------------------------------------------------------------

struct FSRSParameters: Codable {
    var w0:  Double = 0.4072   // initial stability: Again
    var w1:  Double = 1.1829   // initial stability: Hard
    var w2:  Double = 3.1262   // initial stability: Good
    var w3:  Double = 7.9334   // initial stability: Easy
    var w4:  Double = 7.1949   // initial difficulty baseline
    var w5:  Double = 0.5345   // difficulty mean-reversion coefficient
    var w6:  Double = 1.4604   // difficulty shift per rating step
    var w7:  Double = 0.1030   // stability recall: e^w7 multiplier
    var w8:  Double = 1.9395   // stability recall: S^(-w8) decay
    var w9:  Double = 0.1100   // stability recall: spacing effect weight
    var w10: Double = 0.2900   // hard penalty multiplier (< 1)
    var w11: Double = 2.6100   // easy bonus multiplier  (> 1)
    var w12: Double = 0.0100   // post-lapse stability base
    var w13: Double = 0.9000   // post-lapse stability: prior-S exponent
    var w14: Double = 0.2000   // post-lapse stability: difficulty factor
    var w15: Double = 1.0000   // post-lapse stability: retrievability factor
    var w16: Double = 1.0000   // post-lapse stability: short-term factor
    var requestedRetention: Double = 0.9   // target recall probability (R_d)
    var maximumInterval:    Int    = 36500 // ~100 years ceiling

    /// Initial stability for first-time reviews, indexed by Rating.rawValue (1-4).
    func initialStability(_ rating: Rating) -> Double {
        switch rating {
        case .again: return w0
        case .hard:  return w1
        case .good:  return w2
        case .easy:  return w3
        }
    }

    /// D_0(4) — the easy-baseline used as mean-reversion anchor in difficulty update.
    var difficultyMeanReversionTarget: Double {
        w4 - w6 * Double(4 - 3)
    }
}

// ---------------------------------------------------------------------------
// FSRSCard — value type (mutate via copyWith to produce updated cards)
// ---------------------------------------------------------------------------

struct FSRSCard: Codable {
    let id:              String
    var stability:       Double    = 0.0
    var difficulty:      Double    = 5.0   // mid-range default
    var retrievability:  Double    = 0.0
    var dueDate:         Date
    var lastReview:      Date?     = nil
    var reviewCount:     Int       = 0
    var lapseCount:      Int       = 0
    var state:           CardState = .newCard
    var elapsedDays:     Int       = 0     // days between last two reviews (used in S'_r formula)

    func copyWith(
        stability:      Double?    = nil,
        difficulty:     Double?    = nil,
        retrievability: Double?    = nil,
        dueDate:        Date?      = nil,
        lastReview:     Date?      = nil,
        reviewCount:    Int?       = nil,
        lapseCount:     Int?       = nil,
        state:          CardState? = nil,
        elapsedDays:    Int?       = nil
    ) -> FSRSCard {
        var copy = self
        if let v = stability      { copy.stability      = v }
        if let v = difficulty     { copy.difficulty      = v }
        if let v = retrievability { copy.retrievability  = v }
        if let v = dueDate        { copy.dueDate         = v }
        if let v = lastReview     { copy.lastReview      = v }
        if let v = reviewCount    { copy.reviewCount     = v }
        if let v = lapseCount     { copy.lapseCount      = v }
        if let v = state          { copy.state           = v }
        if let v = elapsedDays    { copy.elapsedDays     = v }
        return copy
    }

    /// Convenience: days elapsed since lastReview as of `now`.
    func daysSinceLastReview(_ now: Date) -> Int {
        guard let lastReview = lastReview else { return 0 }
        return Calendar.current.dateComponents([.day], from: lastReview, to: now).day ?? 0
    }
}

// ---------------------------------------------------------------------------
// ReviewLog — immutable audit record written to Supabase after every review
// ---------------------------------------------------------------------------

struct ReviewLog: Codable {
    let cardId:         String
    let rating:         Rating
    let stateBefore:    CardState
    let stability:      Double
    let difficulty:     Double
    let retrievability: Double
    let scheduledDays:  Int
    let reviewedAt:     Date

    func toJson() -> [String: Any] {
        let formatter = ISO8601DateFormatter()
        return [
            "card_id":        cardId,
            "rating":         rating.rawValue,
            "state":          stateBefore.rawValue,
            "stability":      stability,
            "difficulty":     difficulty,
            "retrievability": retrievability,
            "scheduled_days": scheduledDays,
            "reviewed_at":    formatter.string(from: reviewedAt),
        ]
    }
}

// ---------------------------------------------------------------------------
// SchedulingResult — output of FSRSScheduler.scheduleReview()
// ---------------------------------------------------------------------------

struct SchedulingResult {
    let card:      FSRSCard
    let reviewLog: ReviewLog
}

// ---------------------------------------------------------------------------
// FSRSScheduler — core algorithm
// ---------------------------------------------------------------------------

final class FSRSScheduler {
    let params: FSRSParameters

    init(parameters: FSRSParameters = FSRSParameters()) {
        self.params = parameters
    }

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    /// Returns R(t, S): estimated probability of recall right now.
    /// Uses the power-law forgetting curve: R = (1 + t/(9*S))^(-1)
    func calculateRetrievability(_ card: FSRSCard, now: Date) -> Double {
        if card.state == .newCard || card.lastReview == nil { return 0.0 }
        let t = Double(card.daysSinceLastReview(now))
        let s = card.stability
        if s <= 0 { return 0.0 }
        return pow(1.0 + t / (9.0 * s), -1.0)
    }

    /// Core scheduling method. Returns an updated FSRSCard and a ReviewLog.
    func scheduleReview(_ card: FSRSCard, rating: Rating, now: Date? = nil) -> SchedulingResult {
        let reviewedAt = now ?? Date()
        let r = calculateRetrievability(card, now: reviewedAt)

        let updated: FSRSCard

        switch card.state {
        case .newCard:
            updated = scheduleNew(card, rating: rating, reviewedAt: reviewedAt)
        case .learning, .relearning:
            updated = scheduleLearning(card, rating: rating, reviewedAt: reviewedAt, r: r)
        case .review:
            updated = scheduleReviewState(card, rating: rating, reviewedAt: reviewedAt, r: r)
        }

        let scheduledDays = Calendar.current.dateComponents(
            [.day], from: reviewedAt, to: updated.dueDate
        ).day ?? 0

        let log = ReviewLog(
            cardId:         card.id,
            rating:         rating,
            stateBefore:    card.state,
            stability:      updated.stability,
            difficulty:     updated.difficulty,
            retrievability: r,
            scheduledDays:  scheduledDays,
            reviewedAt:     reviewedAt
        )

        return SchedulingResult(card: updated, reviewLog: log)
    }

    // -------------------------------------------------------------------------
    // Private scheduling handlers
    // -------------------------------------------------------------------------

    /// First review of a brand-new card. Stability is set by initial w values.
    private func scheduleNew(_ card: FSRSCard, rating: Rating, reviewedAt: Date) -> FSRSCard {
        let s = params.initialStability(rating)
        let d = initialDifficulty(rating)

        let nextState: CardState
        let due: Date

        switch rating {
        case .again:
            nextState = .learning
            due       = reviewedAt.addingTimeInterval(1 * 60)       // +1 min
        case .hard:
            nextState = .learning
            due       = reviewedAt.addingTimeInterval(5 * 60)       // +5 min
        case .good:
            nextState = .learning
            due       = reviewedAt.addingTimeInterval(10 * 60)      // +10 min
        case .easy:
            // Easy — skip learning phase, graduate immediately
            nextState = .review
            due       = reviewedAt.addingTimeInterval(Double(nextInterval(s)) * 86400)
        }

        return card.copyWith(
            stability:      s,
            difficulty:     d,
            retrievability: 1.0,
            dueDate:        due,
            lastReview:     reviewedAt,
            reviewCount:    card.reviewCount + 1,
            state:          nextState,
            elapsedDays:    0
        )
    }

    /// Review during Learning or Relearning phase (short fixed intervals).
    private func scheduleLearning(
        _ card: FSRSCard, rating: Rating, reviewedAt: Date, r: Double
    ) -> FSRSCard {
        let d = updateDifficulty(card.difficulty, rating: rating)
        var s = card.stability
        var nextState = card.state
        let due: Date

        switch rating {
        case .again:
            // Restart learning
            due = reviewedAt.addingTimeInterval(10 * 60)            // +10 min
        case .hard:
            due = reviewedAt.addingTimeInterval(20 * 60)            // +20 min
        case .good:
            // Graduate to Review
            nextState = .review
            s         = max(s, 1.0)
            due       = reviewedAt.addingTimeInterval(Double(nextInterval(s)) * 86400)
        case .easy:
            // Easy — graduate with bonus
            nextState = .review
            s         = s * params.w11
            due       = reviewedAt.addingTimeInterval(Double(nextInterval(s)) * 86400)
        }

        return card.copyWith(
            stability:      s,
            difficulty:     d,
            retrievability: r,
            dueDate:        due,
            lastReview:     reviewedAt,
            reviewCount:    card.reviewCount + 1,
            state:          nextState,
            elapsedDays:    card.daysSinceLastReview(reviewedAt)
        )
    }

    /// Review in the spaced-repetition (Review) state.
    private func scheduleReviewState(
        _ card: FSRSCard, rating: Rating, reviewedAt: Date, r: Double
    ) -> FSRSCard {
        let t = card.daysSinceLastReview(reviewedAt)
        let d = updateDifficulty(card.difficulty, rating: rating)
        var s: Double
        let nextState: CardState
        let due: Date
        var lapseCount = card.lapseCount

        if rating == .again {
            // Lapse
            s         = stabilityAfterForgetting(card.stability, d: d, r: r)
            nextState = .relearning
            lapseCount += 1
            due       = reviewedAt.addingTimeInterval(10 * 60)      // +10 min
        } else {
            s         = stabilityAfterRecall(card.stability, d: d, r: r, rating: rating)
            s         = min(max(s, 1.0), Double(params.maximumInterval))
            nextState = .review
            due       = reviewedAt.addingTimeInterval(Double(nextInterval(s)) * 86400)
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
            elapsedDays:    t
        )
    }

    // -------------------------------------------------------------------------
    // Core FSRS formulas
    // -------------------------------------------------------------------------

    /// Formula 4.2 — Stability after successful recall.
    /// S'_r = S * e^w7 * (11 - D) * S^(-w8) * (e^(w9*(1-R)) - 1) * modifier
    private func stabilityAfterRecall(
        _ s: Double, d: Double, r: Double, rating: Rating
    ) -> Double {
        let modifier: Double = {
            switch rating {
            case .hard: return params.w10
            case .easy: return params.w11
            default:    return 1.0
            }
        }()

        let growth = exp(params.w7)
            * (11.0 - d)
            * pow(s, -params.w8)
            * (exp(params.w9 * (1.0 - r)) - 1.0)
            * modifier

        return s * (1.0 + growth)
    }

    /// Formula 4.3 — Stability after forgetting (lapse).
    /// S'_f = w12 * D^(-w14) * ((S+1)^w13 - 1) * e^(w15*(1-R))
    private func stabilityAfterForgetting(_ s: Double, d: Double, r: Double) -> Double {
        return params.w12
            * pow(d, -params.w14)
            * (pow(s + 1.0, params.w13) - 1.0)
            * exp(params.w15 * (1.0 - r))
    }

    /// Formula 4.4 — Difficulty update with mean reversion.
    /// D' = w5 * D_0(4) + (1 - w5) * (D - w6*(r-3)), clamped [1,10]
    private func updateDifficulty(_ d: Double, rating: Rating) -> Double {
        let anchor = params.difficultyMeanReversionTarget
        let delta  = params.w6 * (Double(rating.rawValue) - 3.0)
        let next   = params.w5 * anchor + (1.0 - params.w5) * (d - delta)
        return min(max(next, 1.0), 10.0)
    }

    /// Formula 4.5 — Next interval from new stability and requested retention.
    /// I = (9 * S) / (1/R_d - 1), rounded, clamped [1, maximumInterval]
    private func nextInterval(_ s: Double) -> Int {
        let r = params.requestedRetention
        let interval = (9.0 * s) / (1.0 / r - 1.0)
        return min(max(Int(interval.rounded()), 1), params.maximumInterval)
    }

    /// Initial difficulty for a brand-new card.
    /// D_0(r) = w4 - w6 * (r - 3), clamped [1, 10]
    private func initialDifficulty(_ rating: Rating) -> Double {
        let d = params.w4 - params.w6 * (Double(rating.rawValue) - 3.0)
        return min(max(d, 1.0), 10.0)
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
- [ ] All model types conform to Codable for supabase-swift serialisation
