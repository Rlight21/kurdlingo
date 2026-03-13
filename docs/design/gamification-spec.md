# Gamification Specification — Kurdlingo

> **Owner:** `frontend` agent (Task F4)
> **Status:** COMPLETE
> **Last updated:** 2026-03-13
> **Scope:** Audit of Duolingo gamification systems; recommendations for Kurdlingo MVP

---

## Context and Framing

Kurdlingo's target learner is fundamentally different from Duolingo's median user. Duolingo optimizes for a casual Spanish or French learner in a Western market — someone motivated by travel, career, or novelty. The Kurdlingo learner is a **Kurdish diaspora member** (second- or third-generation immigrant) learning a language tied to family, identity, and cultural survival. Research on heritage language anxiety (Wesleyan, 2023; MDPI 2024) consistently finds:

- Heritage learners experience **unique shame and anxiety** about not knowing their language — different from the anxiety of learning a foreign language.
- Motivation is driven by **affective obligation and identity** ("heritage passions" and "heritage convictions"), not just intrinsic curiosity.
- Feelings of inadequacy are heightened when learners compare themselves to fluent family members.
- Positive emotional associations with the language (family warmth, cultural pride) are **a learner asset** that gamification design must protect, not erode.

This means:
1. Punitive mechanics (mistakes = loss) carry **higher emotional cost** for Kurdlingo users than for Duolingo users.
2. Competitive mechanics (leagues, leaderboards) risk triggering shame rather than motivation.
3. Notification tone must be **warm and culturally resonant**, not scolding.
4. The design goal is **sustaining intrinsic motivation**, not maximizing daily active users via anxiety loops.

All recommendations below are evaluated through this lens, alongside Self-Determination Theory (SDT) — which identifies autonomy, competence, and relatedness as the three pillars of self-sustaining motivation — and Habit Formation Theory (habit loop: cue → routine → reward).

---

## System-by-System Evaluation

### 1. Hearts / Lives System

| Attribute | Duolingo (Original) | Kurdlingo Recommendation |
|---|---|---|
| Mechanic | 5 hearts per day; lose a heart per mistake; refill via ad, gems, or wait | **Drop** the hearts system entirely |
| SDT impact | Undermines **competence** — mistakes become costly rather than educational | — |
| Diaspora risk | HIGH — heritage learners already carry shame about mistakes; punishment amplifies this | — |
| Replacement | Unlimited attempts; use **mistake review** (surfacing errors as a post-lesson review queue) | See below |

**Rationale.** Duolingo itself abandoned pure hearts in 2025, replacing them with an "energy" system that de-emphasizes mistake punishment. Research confirms the problem: punishing mistakes is antithetical to language acquisition (comprehensible-input theory, Krashen) and to SDT's competence need. For a heritage learner already anxious about not knowing Kurmanji as well as a grandparent, having their session cut short by five errors would be actively harmful. The only appropriate role for a "lives" concept is rate-limiting **abusive behavior** (e.g., rapidly guessing to farm XP) — which can be handled server-side without surfacing it as a UI penalty.

**Kurdlingo version:** No hearts or energy. Unlimited attempts within any lesson. Mistakes are tracked silently and fed into the FSRS spaced-repetition scheduler (increasing review frequency for weak items). After each lesson, a "Betlêker" (review) card shows a count of mistakes with encouragement — e.g., "3 words to practice more — they'll come back soon."

---

### 2. XP (Experience Points)

| Attribute | Duolingo | Kurdlingo Recommendation |
|---|---|---|
| Mechanic | XP per exercise; daily XP goals; weekly XP totals; used in leagues | **Include with modifications** |
| SDT impact | Supports **competence** (visible progress) and can support **autonomy** (goal-setting) | — |
| Diaspora risk | LOW — XP is a private progress metric and does not involve public comparison | — |
| Dark pattern risk | MEDIUM — XP can be gamed (easy lessons for fast XP) rather than earned via genuine learning | — |

**Rationale.** XP is one of the cleaner gamification mechanics because it primarily provides a visible signal of effort. Goal-Setting Theory (Locke & Latham) shows that specific, measurable goals ("earn 20 XP today") outperform vague intentions in driving follow-through. The main risk is the proxy-metric problem (Dev.to, 2025): optimizing XP ≠ optimizing learning. Mitigation: weight XP by difficulty, not by speed.

**Kurdlingo version:**
- XP is awarded per exercise completed, weighted by item difficulty (FSRS difficulty rating).
- A **Daily Goal** is user-configurable: Casual (10 XP), Regular (20 XP), Serious (50 XP). Default is Regular.
- XP does not appear on public leaderboards in MVP (see Leagues section).
- Weekly XP total is visible on the user's own profile only.
- Milestone celebrations at weekly XP thresholds (e.g., 100 XP in a week) use Kurmanji congratulations ("Aferin!" / "Baş e!") to strengthen cultural connection.

---

### 3. Streaks

| Attribute | Duolingo | Kurdlingo Recommendation |
|---|---|---|
| Mechanic | Day-count of consecutive practice days; lost if user skips a day | **Include with significant modification** |
| SDT impact | Exploits **loss aversion** (Kahneman & Tversky) — losing feels 2x worse than gaining feels good | — |
| Diaspora risk | MEDIUM — irregular diaspora schedules (family events, Newroz, Eid) cause streak breaks during culturally important times | — |
| Dark pattern risk | HIGH — encourages speed-running easy lessons to maintain streak rather than genuine engagement | — |

**Rationale.** Streaks are Duolingo's most effective retention tool — a 14% lift in day-14 retention with streak wagers (StriveCloud, 2026). But research from Dev.to (2025) identifies the mechanism clearly: streaks work via loss aversion, not intrinsic motivation. When the streak breaks, there is often nothing left — the user abandons rather than restarts. This is the "overjustification effect" applied to habit loops.

For Kurdlingo, the cultural calendar is a specific risk: a learner who misses practice during Newroz celebrations should not be punished. The notification tone that accompanies streak anxiety is also antithetical to how diaspora learners should feel about their heritage language.

**Kurdlingo version:**
- Streaks are shown positively ("You've practiced X days this month!") rather than as a countdown to loss.
- **Weekly streaks** replace daily streaks as the primary metric: completing at least 3 sessions in a week counts as a "practice week." This is more forgiving of real life.
- A **Cultural Calendar** build: Kurdish holidays (Newroz on March 21, Eid, etc.) automatically grant a streak freeze — no user action needed.
- Streak freeze is available as a free, automatic mechanic (1 per week) — not a purchasable power-up.
- The app **never sends a guilt-framed notification** about streak loss. Post-break messaging: "Welcome back! Your Kurdish is waiting for you." — not "Your streak is broken!"

---

### 4. Leagues / Leaderboards

| Attribute | Duolingo | Kurdlingo Recommendation |
|---|---|---|
| Mechanic | Weekly XP competition in Bronze → Diamond tiers; promotion/relegation | **Drop for MVP; optional opt-in later** |
| SDT impact | Mixed: can support **relatedness** for competitive learners; undermines **competence** and **autonomy** for others | — |
| Diaspora risk | HIGH — heritage learners are sensitive to public comparison with other Kurds; language shame is community-specific | — |
| Dark pattern risk | HIGH — documented cases of leagues causing anxiety and app abandonment (arXiv 2022); users report leagues "stress me out rather than motivate me" | — |

**Rationale.** The arXiv qualitative study (2022) on Duolingo gamification misuse found leagues and leaderboards are the most-cited source of anxiety and compulsive behavior. Research from Oulu University (2025) confirms that non-competitive learners experience leaderboards as "social comparison that leads to discouragement." For Kurdlingo's diaspora audience, the stakes are higher: being ranked below another Kurdish learner in a public leaderboard may activate exactly the shame and inadequacy dynamics that heritage language research identifies as barriers to engagement.

**Kurdlingo version:**
- No public leagues or leaderboards in MVP.
- Phase 2 consideration: **opt-in friend challenges** (compare XP with specific friends you invite, not anonymous strangers). This supports SDT relatedness without the competitive anxiety of global leagues.
- If leagues are ever introduced, they must be **opt-in only**, never visible by default.

---

### 5. Gems / Lingots (In-App Currency)

| Attribute | Duolingo | Kurdlingo Recommendation |
|---|---|---|
| Mechanic | Earned from lessons and achievements; spent on streak freezes, bonus content, cosmetics | **Simplify — consider dropping or deferring** |
| SDT impact | Introduces an **extrinsic reward layer** that can crowd out intrinsic motivation (overjustification effect) | — |
| Diaspora risk | LOW — currency mechanics are culturally neutral | — |
| Dark pattern risk | MEDIUM — currency obfuscates the real cost of purchases; creates compulsion loops around saving/spending | — |

**Rationale.** A virtual currency layer adds UX complexity that is not justified for an MVP. Gems serve primarily as (a) a monetization vector and (b) a way to make purchases feel less like real money. For a free, community-minded heritage language app, this is low-priority and risks feeling out of place. The SDT risk of external rewards crowding out intrinsic motivation is real — if learners start "farming" for gems, the game-within-a-game eclipses the actual language.

**Kurdlingo version:**
- No gems/currency in MVP.
- Achievements (see below) are used for unlocking cosmetics and bonus content — no currency transaction layer.
- Revisit in Phase 2 if monetization requires it; if introduced, prefer a simple "coin" metaphor rather than a named currency.

---

### 6. Streak Freeze

| Attribute | Duolingo | Kurdlingo Recommendation |
|---|---|---|
| Mechanic | Purchasable item (with gems) that prevents streak loss for one missed day | **Include as free automatic mechanic** |
| SDT impact | Reduces streak anxiety — positive; but requiring purchase is a dark pattern | — |
| Diaspora risk | MEDIUM — diaspora learners are more likely to miss days due to family/cultural obligations | — |
| Dark pattern risk | HIGH in Duolingo's implementation: the need to purchase a freeze manufactures anxiety it then sells a solution to | — |

**Rationale.** The streak freeze concept is sound — life happens, and a grace mechanism makes the streak system humane. The dark pattern is that Duolingo monetizes it. For Kurdlingo, streak freezes should be a standard feature with no purchase required.

**Kurdlingo version:**
- 1 automatic streak freeze per week, applied without user action.
- Additional freezes for identified Kurdish holidays (see Streaks section).
- No "purchase more freezes" mechanic in MVP.

---

### 7. Super Duolingo (Paid Tier)

| Attribute | Duolingo | Kurdlingo Recommendation |
|---|---|---|
| Mechanic | Removes hearts; offline mode; no ads; exclusive features | **Defer — MVP is free** |
| SDT impact | Positive in principle (removes punitive mechanics for paying users) but creates a two-tier experience | — |
| Diaspora risk | MEDIUM — Kurdish diaspora communities include significant socioeconomic diversity; paywalling core learning is exclusionary | — |

**Rationale.** Duolingo's paid tier essentially removes the dark patterns from the free tier — you pay to escape the anxiety loops. This is structurally problematic: it means the free tier is deliberately worse. For Kurdlingo, the mission is diaspora access, and paywalling core features contradicts that.

**Kurdlingo version:**
- MVP is fully free with no ad interruptions.
- Phase 2 "Supporter" tier can exist for users who want to financially back the project — unlocks cosmetics, name in credits, etc. — but **never gates learning functionality**.

---

## Dark Patterns Audit

The following Duolingo mechanics are identified as manipulative rather than genuinely motivating, and should be explicitly avoided in Kurdlingo:

| Dark Pattern | Duolingo Manifestation | Why It Matters for Kurdlingo |
|---|---|---|
| **Shame notifications** | Guilt-framing ("You forgot about me!"), melting owl icon | Heritage learners already carry language shame; external shame amplifies barriers to re-engagement |
| **Manufactured urgency** | League relegation countdowns; streak-save prompts | Anxiety-driven engagement is fragile — it collapses when the streak breaks, leaving no intrinsic motivation |
| **Paywalled relief** | Selling streak freezes; selling heart refills | Manufactures the problem it then monetizes; antithetical to an equity-focused app |
| **Compulsive league design** | Leagues structured so even users who hit daily goals can be relegated | Documented cause of anxiety and app abandonment; especially harmful for non-competitive learners |
| **XP inflation for easy content** | Equal XP for hard and easy exercises encourages easy-lesson farming | Disconnects the metric from the learning; trains users to optimize the game, not the language |
| **Notification overload** | Multiple daily notifications across streak, league, XP goals | Notification fatigue leads to disengagement; diaspora learners may resent feeling nagged about their heritage language |

**Design principle:** Every Kurdlingo gamification mechanic must pass the test — "Does this help the learner feel more capable, more autonomous, and more connected to Kurdish culture?" If a mechanic primarily works by creating anxiety about losing something, it should be dropped or redesigned.

---

## Notification Strategy

### Guiding Principles

1. **Warm, not guilt-tripping.** Duo's "owl guilt" marketing works for Gen Z irony consumers; it is inappropriate for diaspora learners with language anxiety.
2. **Low frequency by default.** One notification per day maximum; user-configurable to "weekly digest" or "off."
3. **Culturally grounded.** Use Kurmanji in notifications where possible. Reference cultural moments (approaching Newroz, a new vocabulary category unlocked).
4. **Timing respects the user's chosen schedule.** If user sets a practice reminder for 8pm, the notification fires at 8pm — not also at 9pm and 10pm.

### Recommended Notification Types

| Type | Trigger | Tone | Example |
|---|---|---|---|
| **Practice reminder** | User's chosen daily time | Warm invite | "Silavê! A 5-minute lesson is ready for you." |
| **Streak milestone** | Completing a 7-day or 30-day practice week | Celebratory | "7 practice days this month — Aferin!" |
| **New content** | New lesson or skill unlocked | Curious | "New lesson: Colors — 8 new words, including the Kurdish word for 'emerald'." |
| **Long absence** | 14+ days inactive | Gentle, non-shaming | "Your Kurdish is waiting — no pressure, come back whenever you're ready." |
| **Holiday greeting** | Kurdish cultural holidays | Cultural connection | "Newroz Piroz Be! Take a moment to learn how to say 'Happy New Year' in Kurmanji." |

### What to Never Do

- Never send multiple notifications in one day.
- Never use loss language ("You're about to lose your streak!", "Don't let Duo down!").
- Never send notifications after 9pm or before 8am in the user's timezone.
- Never use the crying/melting mascot concept as an emotional manipulation tool.

---

## Onboarding Flow — First 3 Minutes

### Duolingo's Onboarding: What Works and What Doesn't

**Works well:**
- Zero account required to start — users are in a lesson within 10 taps.
- Goal-setting at the start (daily commitment) activates behavioral commitment theory.
- Placement test option respects prior knowledge.
- Immediate positive reinforcement during the first exercise.

**Fails for Kurdlingo's audience:**
- Duolingo's opening asks "Why are you learning [language]?" with generic options (Travel, Education, Career). None of these capture "I want to connect with my family's heritage" — the primary Kurdlingo motivation.
- The first lesson presents Kurdish as just another foreign language, missing the emotional resonance opportunity.
- No acknowledgment of prior cultural knowledge (e.g., a learner may know Kurdish greetings from family but have no reading ability).

### Kurdlingo Onboarding — Recommended Flow

**Screens 1–2: Emotional anchoring (30 seconds)**
- Screen 1: Full-screen image evocative of Kurdish culture (mountains, textile pattern, or a warm family scene — user-tested). Tagline in English and Kurmanji: "Kurdê te li benda te ye" (Your Kurdish is waiting for you).
- Screen 2: Single question — "What brings you here?" with options:
  - "I want to connect with my family's heritage"
  - "I have Kurdish roots and want to learn"
  - "I'm learning Kurdish culture and language"
  - "Other"
  - (This data personalizes encouragement messages, not the curriculum — which is the same for all.)

**Screen 3: Skill self-assessment (30 seconds)**
- "How much Kurmanji do you already know?"
  - I know a few words from family
  - I can understand some but can't speak
  - I'm starting from zero
  - I can already hold basic conversations
- This sets the placement level and signals to the learner that prior heritage knowledge is **valued**, not ignored.

**Screens 4–6: First lesson — immediate value delivery (90 seconds)**
- Drop straight into a 5-exercise lesson on greetings: Silav, Spas, Erê/Na (Yes/No), Navê min... (My name is...).
- These are words the learner may already know from family — the "aha moment" of recognition is the emotional hook.
- Audio plays automatically for each word (KurdishTTS API). Native speaker pronunciation is the reward in itself.
- Completion screen: "Lesson complete! You just said hello in Kurmanji." + streak day 1 display + one gentle prompt to set a reminder time.

**Screen 7: Commitment (30 seconds)**
- Daily goal selector (Casual / Regular / Serious) with estimated time per day.
- Optional: "Set a reminder time" — framed as a helpful tool, not a commitment device.
- Account creation at this point (or skip — guest mode available). Do not gate the first lesson behind account creation.

**Design principles:**
- Total time to first lesson completion: under 3 minutes.
- No account required to begin.
- Heritage knowledge is acknowledged as an asset, not an absence.
- The emotional connection to Kurdish identity is established before any grammar instruction.

---

## Achievements and Badges

Not in the original audit scope, but required for completeness:

- Achievements replace the currency/store mechanic as the primary reward for milestones.
- Badge names and descriptions use Kurmanji where possible (e.g., "Zana" — the wise one, for completing 10 lessons).
- Badges are visible on user profile but not ranked against other users.
- Categories: Consistency (practice weeks), Vocabulary (word milestones), Skill completion, Cultural (holiday lessons).

---

## MVP Gamification Stack

The following mechanics are recommended for Sprint 1 (MVP build). Everything else is deferred.

| # | Mechanic | Priority | Notes |
|---|---|---|---|
| 1 | **XP per exercise** (difficulty-weighted) | P0 | Core progress signal; feeds daily goal |
| 2 | **Daily goal** (user-configurable: 10/20/50 XP) | P0 | Supports SDT autonomy; drives habit loop cue |
| 3 | **Weekly streak** (3+ sessions = practice week) | P0 | Forgiving cadence; cultural calendar auto-freeze |
| 4 | **Automatic streak freeze** (1/week, holidays) | P0 | Removes punitive streak mechanics |
| 5 | **Lesson completion celebration** (Kurmanji copy) | P0 | Immediate reward; cultural reinforcement |
| 6 | **Mistake review card** (post-lesson, non-punitive) | P0 | Feeds FSRS; reframes errors as learning data |
| 7 | **Practice reminder notification** (1/day, user-timed) | P1 | Habit cue; warm tone required |
| 8 | **Milestone badges** (Zana, etc.) | P1 | Replaces currency layer; profile cosmetic |
| 9 | **Weekly XP summary** (private, profile only) | P1 | Progress visibility without competition |

### Explicitly OUT of MVP

| Mechanic | Reason |
|---|---|
| Hearts / energy system | Punitive; actively harmful for diaspora learners |
| Leagues / leaderboards | Anxiety risk; not appropriate for heritage language context |
| Gems / currency | UX complexity without MVP value |
| Paid tier | Defer; MVP is fully free |
| Friend challenges | Phase 2 after core loop is validated |
| Daily streak (replaces weekly) | Too punitive; weekly streak is the MVP default |

---

## Open Questions for Native Speaker Review

The following gamification copy decisions require validation from the native Kurmanji speaker (project owner):

1. Is "Aferin!" (used for success celebrations) the right register for a diaspora learner? Or is "Erê, baş e!" more natural?
2. What Kurmanji word should be used for the app's encouragement mascot, if one exists? (Kurdish equivalents of "owl" or a culturally resonant animal?)
3. Are there Kurdish cultural calendar dates beyond Newroz that should be treated as automatic streak-freeze days?
4. Does the phrase "Kurdê te li benda te ye" read naturally to a diaspora Kurmanji speaker, or does it carry an unintended tone?
5. What tone of address is appropriate — formal (hûn) or informal (tu) — for a second/third-generation diaspora learner?

---

*End of Gamification Specification — Task F4*
