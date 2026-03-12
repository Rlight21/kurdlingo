# Kurdlingo — Exercise Type Inventory

**Document type:** Design specification
**Status:** Draft v1.0
**Date:** 2026-03-12
**Audience:** Frontend developer, backend agent (data models), product owner

---

## 1. Overview

This document catalogues all candidate exercise types for Kurdlingo, a Duolingo-inspired mobile app for learning Kurmanji Kurdish (Latin script). Each type is evaluated for audio requirements, Kurmanji-specific feasibility, build complexity, and learning value. The document closes with an MVP build order and a set of Kurmanji-specific exercise ideas that have no direct equivalent in Duolingo.

**Language parameters**
- Script: Latin (LTR)
- Special characters: ê, î, û, ç, ş
- Dialect: Kurmanji (Northern Kurdish)
- Audio source: KurdishTTS.com API (bulk) + native speaker validation/recording

---

## 2. Full Exercise Type Inventory

### 2.1 Multiple Choice — Word to Meaning (L2 → L1)

**Description:** The learner sees a Kurdish word or short phrase and selects its English/target-language meaning from 3–4 options.

| Attribute | Value |
|-----------|-------|
| Audio required | Optional (play audio of the Kurdish word for listening reinforcement) |
| Kurmanji feasibility | High — purely text-based, no Kurdish-specific tooling needed |
| Build complexity | Low |
| Learning value | Medium — good for receptive vocabulary; risk of guessing without real comprehension |

**Kurdish-specific considerations:**
- Distractors should be phonologically or morphologically plausible (e.g., *av* "water" vs. *av û nan* "water and bread") to prevent trivial guessing.
- The ezafe suffix *-a/-ê* can be stripped or included depending on lesson stage; make clear whether the presented form is bare or inflected.
- Use of special characters (ê, î, û, ç, ş) must render correctly in all option buttons — test on both iOS and Android with a Kurdish-compatible font.

---

### 2.2 Multiple Choice — Meaning to Word (L1 → L2)

**Description:** The learner sees an English gloss and selects the correct Kurdish word from 3–4 options.

| Attribute | Value |
|-----------|-------|
| Audio required | Optional (play audio when the correct answer is tapped) |
| Kurmanji feasibility | High |
| Build complexity | Low |
| Learning value | Medium — builds productive recall, but options scaffold the answer |

**Kurdish-specific considerations:**
- Distractors must respect grammatical gender (Kurmanji has masculine/feminine noun classes). Mixing genders in the option set is a useful distractor strategy and also teaches gender implicitly.
- Verb distractors should match tense/person of the target form to avoid giving away the answer by morphological mismatch.

---

### 2.3 Word Bank Translation (Tap to Build a Sentence)

**Description:** The learner sees an English sentence and a shuffled bank of Kurdish word tiles. They tap tiles in order to reconstruct the Kurdish translation.

| Attribute | Value |
|-----------|-------|
| Audio required | Optional (tile tap plays pronunciation; sentence playback available) |
| Kurmanji feasibility | High — SOV word order makes sentence construction a meaningful challenge |
| Build complexity | Medium |
| Learning value | High — forces active recall of word order without requiring free typing |

**Kurdish-specific considerations:**
- Kurmanji is SOV (Subject–Object–Verb) and VSO word order also appears in questions; the word bank format is excellent for drilling this contrast.
- Clitic pronouns (e.g., *-im, -it, -e*) should be included as separate tiles or fused with their host, depending on lesson stage.
- The ezafe construction (*keça spî* "the white girl", lit. girl-EZ white) reverses English adjective-noun order — word bank tiles are ideal for drilling this.
- Include necessary special-character tiles as discrete options; do not rely on the learner knowing to type ê vs. e.

---

### 2.4 Free Typing Translation

**Description:** The learner sees a prompt (English or Kurdish) and types the full translation in a text field.

| Attribute | Value |
|-----------|-------|
| Audio required | No |
| Kurmanji feasibility | Medium — depends on keyboard availability |
| Build complexity | Medium-High |
| Learning value | High — most rigorous productive exercise; no scaffolding |

**Kurdish-specific considerations:**
- No dedicated Kurdish Kurmanji keyboard exists on stock iOS/Android. The app must provide an in-app supplementary key row for ê, î, û, ç, ş above the native keyboard.
- Answer validation must be accent-tolerant with configurable strictness: decide whether *ez dizanim* and *ez dizânîm* (spelling variants) should both be accepted.
- Typo tolerance (Levenshtein distance 1–2) is strongly recommended given the unfamiliarity of special characters for diaspora learners.
- Reserve for A2+ learners; A1 learners should not be forced into free typing until they have basic orthographic confidence.

---

### 2.5 Listening Comprehension — Audio to Meaning

**Description:** The learner hears a Kurdish word, phrase, or sentence (no text shown) and selects its meaning from multiple-choice options, or types/taps the translation.

| Attribute | Value |
|-----------|-------|
| Audio required | Yes — mandatory |
| Kurmanji feasibility | High — TTS + native recordings available |
| Build complexity | Medium |
| Learning value | High — develops aural discrimination; critical for a spoken heritage language |

**Kurdish-specific considerations:**
- The distinction between short and long vowels (a/ê, i/î, u/û) is phonemically contrastive in Kurmanji (*bir* "take" vs. *bîr* "well/memory"). Audio exercises are one of the best tools to teach this.
- TTS quality for Kurmanji is limited; native speaker recordings should be prioritized for all A1 vocabulary.
- Offer a "replay audio" button — do not penalize for replays at A1/A2.
- Slow-playback option (0.75x) is highly valuable for beginner learners.

---

### 2.6 Speaking Exercise (Mic — Speech Recognition)

**Description:** The learner is prompted to say a word or phrase aloud; the app uses speech recognition to evaluate pronunciation.

| Attribute | Value |
|-----------|-------|
| Audio required | Yes — reference audio for feedback |
| Kurmanji feasibility | Low — no production-quality ASR model exists for Kurmanji Kurdish as of early 2026 |
| Build complexity | High |
| Learning value | High in theory; impractical without reliable ASR |

**Kurdish-specific considerations:**
- No major ASR provider (Google, Apple, Azure, Whisper fine-tunes) offers a reliable, production-ready Kurmanji speech recognition model. Using a generic Arabic or Persian model will produce incorrect results.
- A workaround is phoneme-level waveform comparison (compare learner recording to reference recording visually/aurally) without transcription-based scoring — but this is non-standard and hard to implement well.
- **Recommendation: Exclude from MVP entirely.** Flag as a post-MVP feature, contingent on ASR model availability or a community-contributed Whisper fine-tune.

---

### 2.7 Matching Pairs

**Description:** The learner sees two columns — Kurdish words on one side, English meanings on the other — and draws lines or taps to match them.

| Attribute | Value |
|-----------|-------|
| Audio required | Optional (tap a Kurdish word to hear it) |
| Kurmanji feasibility | High |
| Build complexity | Low-Medium |
| Learning value | Medium — efficient for vocabulary review; less effective for grammar |

**Kurdish-specific considerations:**
- Limit to 5–6 pairs per screen on mobile to avoid scroll and visual clutter.
- Pairs should be thematically grouped (e.g., all family terms, all color adjectives) so the distractor set is meaningful.
- Can be adapted for grammatical matching: bare noun ↔ ezafe form (*keç / keça*), infinitive ↔ past stem (*çûn / çû*).

---

### 2.8 Fill in the Blank

**Description:** A sentence is shown with one or more blanks. The learner types or selects (from a small dropdown/word bank) the missing word.

| Attribute | Value |
|-----------|-------|
| Audio required | Optional |
| Kurmanji feasibility | High |
| Build complexity | Low (word bank variant) / Medium (typed variant) |
| Learning value | High — contextual grammar and vocabulary in a sentence frame |

**Kurdish-specific considerations:**
- Especially valuable for teaching:
  - Ezafe agreement (*keça spî* vs. *kurrê spî* — feminine vs. masculine ezafe)
  - Verb conjugation endings (*ez diçim / tu diçî / ew diçe*)
  - Postpositions (*di ... de*, *li ... de*, *ji ... re*)
- The cloze position matters: blanking the verb final position reinforces SOV structure.
- Word bank variant is preferred for A1; typed variant for A2+.

---

### 2.9 Ordering / Arrange Words (Sentence Scramble)

**Description:** All words of a sentence are presented as shuffled tiles; the learner drags or taps them into the correct order.

| Attribute | Value |
|-----------|-------|
| Audio required | Optional |
| Kurmanji feasibility | High |
| Build complexity | Medium |
| Learning value | High — directly teaches word order, which differs significantly from English |

**Kurdish-specific considerations:**
- This is among the highest-value exercise types for Kurmanji specifically due to SOV order and the verb-final constraint in subordinate clauses.
- Ideal for drilling: verb-final placement, clitic climbing, and question particle *ma* position.
- Drag-and-drop on mobile requires careful UX: tiles must be large enough to tap (minimum 44pt), and reordering must be smooth. Consider a tap-to-place model (like Duolingo) over drag for reliability.

---

### 2.10 Image Association

**Description:** An image is shown and the learner selects or types the Kurdish word it represents.

| Attribute | Value |
|-----------|-------|
| Audio required | Optional (audio plays on correct selection) |
| Kurmanji feasibility | Medium — requires sourcing culturally appropriate images |
| Build complexity | Medium (image asset pipeline is the main cost) |
| Learning value | Medium — excellent for concrete nouns; not applicable for abstract vocabulary or grammar |

**Kurdish-specific considerations:**
- Image selection should reflect Kurdish cultural context where possible (e.g., traditional foods, clothing, landscapes of Kurdistan) rather than generic stock photos, to resonate with diaspora learners.
- Avoid culturally ambiguous images (e.g., a "house" image may not match *mal* if it shows an apartment).
- Not suitable for A2+ grammar-focused lessons.

---

### 2.11 Reading Comprehension

**Description:** The learner reads a short Kurdish text (2–6 sentences) and answers comprehension questions in English or Kurdish.

| Attribute | Value |
|-----------|-------|
| Audio required | Optional (audio narration of the passage) |
| Kurmanji feasibility | High — text generation is feasible |
| Build complexity | High (passage authoring + question design is content-intensive) |
| Learning value | High — integrates vocabulary, grammar, and cultural content |

**Kurdish-specific considerations:**
- Suitable from A2 upward; A1 passages should be limited to 1–2 sentences with controlled vocabulary.
- Passages can introduce Kurdish proverbs (*gotinên pêşiyan*), folk tales, or historical context — high relevance for diaspora learners motivated by cultural connection.
- Requires native speaker review of all passages; TTS cannot be used as the sole authoring tool.
- Post-MVP feature due to high content-authoring cost.

---

### 2.12 Pronunciation / Phoneme Discrimination

**Description:** The learner hears two similar sounds or minimal-pair words and must identify which one they heard, or which pronunciation is correct.

| Attribute | Value |
|-----------|-------|
| Audio required | Yes — mandatory |
| Kurmanji feasibility | High (audio is available) |
| Build complexity | Low-Medium |
| Learning value | High — Kurmanji phonology has several pairs that are difficult for English speakers and diaspora learners |

**Kurdish-specific considerations:**
- Minimal pairs to drill: *xwarin* (to eat) vs. *xwarin* (food) — same form, tonal/contextual disambiguation; *b/p*, *d/t*, *g/k* aspiration contrasts; long vs. short vowel pairs (*bir* vs. *bîr*, *çu* vs. *çû*).
- This exercise type has no direct Duolingo equivalent and is especially valuable for Kurmanji.

---

### 2.13 Dialogue Completion

**Description:** A short scripted dialogue is shown with one speaker's turn blank. The learner selects or types the appropriate response.

| Attribute | Value |
|-----------|-------|
| Audio required | Optional (audio for both speakers) |
| Kurmanji feasibility | High |
| Build complexity | Medium |
| Learning value | High — situational, pragmatic language use |

**Kurdish-specific considerations:**
- Greetings and politeness formulae in Kurmanji differ significantly from English (e.g., *spas/sipas* for thanks, *xatirê te* for goodbye, formality registers). Dialogue exercises are the natural vehicle for this.
- Post-MVP; content-authoring cost is moderate.

---

## 3. MVP Build Order

The following 5 exercise types are recommended for the Kurdlingo MVP, in priority order.

| Priority | Exercise Type | Rationale |
|----------|--------------|-----------|
| 1 | **Multiple Choice (L2 → L1)** | Lowest build complexity, immediately usable, good for first-session engagement. Establishes the core exercise scaffolding (question + options + feedback) that all MC variants share. |
| 2 | **Multiple Choice (L1 → L2)** | Reuses ~90% of the MC component built in Priority 1; adds productive recall direction. Small incremental cost, high coverage. |
| 3 | **Word Bank Translation** | Highest learning value for grammar (SOV order, ezafe) without requiring a Kurdish keyboard. This is Kurdlingo's signature exercise for sentence-level learning. Medium build cost is justified. |
| 4 | **Listening Comprehension (Audio → MC)** | Audio infrastructure (TTS API + native recordings) must be built for the app regardless; this exercise reuses it directly. Kurmanji's phonemic vowel length distinctions make listening exercises uniquely valuable and non-replicable through text alone. |
| 5 | **Fill in the Blank (Word Bank variant)** | Bridges vocabulary exercises into grammar without introducing free typing complexity. Ezafe, verb conjugation, and postposition drills are all naturally expressed here. |

**Excluded from MVP with reasons:**
- Speaking exercise: No viable ASR for Kurmanji.
- Reading comprehension: High content-authoring cost; better suited post-MVP when a content library exists.
- Free typing: Keyboard complexity (special characters) makes this a poor first-session experience; introduce at A2.
- Image association: Image pipeline cost; lower priority than grammar-focused types.

---

## 4. Exercise Type to CEFR Level Mapping

| Exercise Type | A1 | A2 | B1 |
|---------------|----|----|-----|
| Multiple Choice (L2 → L1) | Primary | Review | Review |
| Multiple Choice (L1 → L2) | Primary | Review | — |
| Word Bank Translation | Secondary | Primary | Review |
| Listening Comprehension (MC) | Primary | Primary | Primary |
| Fill in the Blank (word bank) | Secondary | Primary | — |
| Fill in the Blank (typed) | — | Secondary | Primary |
| Matching Pairs | Primary | Review | — |
| Ordering / Arrange Words | Secondary | Primary | Primary |
| Free Typing Translation | — | Secondary | Primary |
| Image Association | Primary | Secondary | — |
| Phoneme Discrimination | Primary | Primary | — |
| Dialogue Completion | — | Secondary | Primary |
| Reading Comprehension | — | Secondary | Primary |
| Speaking Exercise | — | — | Post-MVP |

**Key:**
- **Primary** — exercise type is well-suited and heavily used at this level
- **Secondary** — exercise type is used occasionally at this level, often for consolidation
- **Review** — used only as revision/warm-up, not for introducing new material
- **—** — not appropriate or not recommended at this level

---

## 5. Kurmanji-Specific Exercise Ideas

The following exercise types are tailored to features of Kurmanji that have no direct Duolingo equivalent. They represent differentiated value for Kurdlingo and a connection to Kurdish linguistic identity.

---

### 5.1 Ezafe Construction Drill

**What it tests:** The Kurmanji ezafe (*tewandin*) is a linking particle (*-a* for feminine, *-ê* for masculine) that connects a noun to a modifier (adjective, genitive, relative clause). It is one of the most distinctive and challenging features of Kurmanji grammar.

**Exercise format:** The learner is shown a Kurdish noun phrase with the ezafe particle missing and must select or type the correct form.

**Example:**
> *keç + spî* → ___
> Options: *keça spî* / *keçê spî* / *keçin spî*
> Correct: *keça spî* (girl-EZ.F white, "the white girl")

**Why this is unique:** Duolingo's generic grammar exercises cannot model this construction well. It deserves its own dedicated drill type because it appears in nearly every Kurdish sentence with a modified noun.

---

### 5.2 Verb Root Identification

**What it tests:** Kurmanji verbs have two stems: the present stem (used for present tense, subjunctive, imperative) and the past stem (used for past tense forms). Learners must recognise that *diçim* (I go, present) and *çûm* (I went, past) share the root *ç-*.

**Exercise format:** A conjugated verb is shown; the learner taps or types the verb root/infinitive it derives from.

**Example:**
> *dikim* → What is the infinitive?
> Options: *kirin* / *birin* / *xwarin*
> Correct: *kirin* (to do/make)

**Why this is unique:** Verb stem alternation is one of the hardest aspects of Kurmanji morphology. No existing app drills this explicitly.

---

### 5.3 Kurdish Proverbs (Gotinên Pêşiyan)

**What it tests:** Cultural literacy + advanced vocabulary + inferential comprehension.

**Exercise format:** A Kurdish proverb is shown in Kurdish. The learner selects the English proverb or idea that best matches its meaning (not a literal translation).

**Example:**
> *Dûr e, dilê min e.* ("It is far, but it is in my heart.")
> What does this proverb express?
> Options: (a) Longing for a distant homeland / (b) Directions to a place / (c) A warning about travel

**Why this is unique:** Proverbs are central to Kurdish oral tradition and deeply meaningful to diaspora learners who grew up hearing them. This exercise type builds cultural identity alongside language skill.

---

### 5.4 Dialect Awareness: Kurmanji vs. Sorani

**What it tests:** Awareness of the difference between Kurmanji and Sorani Kurdish, which are mutually unintelligible dialects often conflated by outsiders.

**Exercise format:** Two words or phrases are shown — one Kurmanji, one Sorani. The learner identifies which is Kurmanji.

**Example:**
> Which word means "bread" in Kurmanji?
> Options: *nan* (Kurmanji) / *nên* (Sorani)

**Why this is unique:** Diaspora learners are frequently confused about which Kurdish variety they speak. This exercise builds metalinguistic awareness while teaching vocabulary.

---

### 5.5 Gender Assignment Drill

**What it tests:** Kurmanji nouns are grammatically masculine or feminine, and this affects ezafe form, adjective agreement, and verb agreement in past-tense ergative constructions. Gender is not reliably predictable from form.

**Exercise format:** A Kurdish noun is shown (with optional image). The learner selects *nêr* (masculine) or *mê* (feminine).

**Example:**
> *dar* (tree) — nêr or mê?
> Correct: mê (feminine)

**Special consideration:** Include a "I don't know — show me" option that immediately reveals the gender with a memorable mnemonic or image cue, to reduce frustration.

---

### 5.6 Postposition Slot Fill

**What it tests:** Kurmanji uses postpositions and circumpositions (*di ... de*, *li ... de*, *ji ... re*, *bi ... re*) rather than English prepositions. The correct particle depends on the verb and semantic relationship.

**Exercise format:** A sentence with a blank for the postposition complex. The learner selects the correct postposition from 3–4 options.

**Example:**
> *Ew ___ malê ___ ye.* ("She is in the house.")
> Options: *di ... de* / *ji ... re* / *li ... ve* / *bi ... re*
> Correct: *di malê de*

---

### 5.7 Script / Special Character Recognition

**What it tests:** Correct identification of Kurmanji-specific letters that look similar to standard Latin letters (ê vs. e, î vs. i, û vs. u, ş vs. s, ç vs. c).

**Exercise format:** Two or more minimally different spellings are shown; the learner identifies which is the correctly spelled Kurdish word based on audio or meaning.

**Example:**
> Hear: [audio of *çû*]
> Options: *cu* / *çu* / *çû*
> Correct: *çû*

**Why this matters:** Diaspora learners who grew up reading Kurdish informally often use unaccented Latin substitutes. This drill habit-breaks incorrect orthography.

---

## 6. Data Model Notes for Backend Agent

The following summary is provided to guide data model design:

| Exercise Type | Key Fields Needed |
|--------------|-------------------|
| Multiple Choice | `prompt` (text/audio), `options[]` (text), `correct_index`, `explanation` |
| Word Bank Translation | `prompt_text` (L1), `target_sentence` (L2), `word_tiles[]`, `distractor_tiles[]` |
| Listening Comprehension | `audio_url`, `options[]`, `correct_index`, `transcript` (hidden) |
| Fill in the Blank | `sentence_template` (with `__blank__` markers), `options[]` or `accept_typed: bool`, `correct_answers[]` |
| Ordering/Arrange | `words[]` (correct order), `shuffled_words[]` |
| Matching Pairs | `pairs[]` ({`left`, `right`}) |
| Image Association | `image_url`, `options[]`, `correct_index` |
| Phoneme Discrimination | `audio_urls[]`, `correct_index`, `minimal_pair_note` |
| Ezafe Drill | `noun`, `modifier`, `correct_ezafe_form`, `gender` |
| Verb Root Drill | `conjugated_form`, `correct_infinitive`, `tense`, `person` |
| Proverb | `kurdish_text`, `meaning_options[]`, `correct_index`, `literal_translation` |
| Gender Assignment | `word`, `gender` (`m`/`f`), `mnemonic` |
| Postposition Fill | `sentence_template`, `correct_postposition`, `options[]` |

All exercise types should share a common base schema with: `exercise_id`, `exercise_type` (enum), `lesson_id`, `cefr_level`, `audio_url` (nullable), `created_at`, `updated_at`.

---

*End of document. This file is the authoritative exercise type specification for Kurdlingo MVP and post-MVP planning.*
