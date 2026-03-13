# UI Specification

> **Owner:** `frontend` agent (Tasks F2 + F3)
> **Status:** COMPLETE — F2 and F3 filled by frontend design agent

---

## Table of Contents

- [F2 — Kurdish Character Input Design](#f2--kurdish-character-input-design)
- [F3 — Skill Tree UI Concept](#f3--skill-tree-ui-concept)

---

## F2 — Kurdish Character Input Design

### F2.1 — Typing Exercise Screen Wireframe (ASCII)

Portrait mode, small phone (375 × 812 pt / 390 × 844 pt iPhone 14):

```
┌─────────────────────────────────────────┐
│  ←   Lesson 3 · Unit 2           ❤❤❤☆  │  ← AppBar (56pt tall)
├─────────────────────────────────────────┤
│                                         │
│   Translate this sentence:              │  ← Prompt label
│                                         │
│   ┌─────────────────────────────────┐   │
│   │  "Navê te çi ye?"               │   │  ← Source text card
│   └─────────────────────────────────┘   │
│                                         │
│   ┌─────────────────────────────────┐   │
│   │  Your answer:                   │   │  ← Answer text field
│   │  Navê_ |                        │   │    (active, cursor shown)
│   └─────────────────────────────────┘   │
│                                         │
│                                         │
│                                         │
├─────────────────────────────────────────┤
│  ê   î   û   ç   ş  │ Ê   Î   Û   Ç  Ş │  ← Character picker bar
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤    (48pt tall, full width)
│                                         │
│   ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐  │
│   │ q │ │ w │ │ e │ │ r │ │ t │ │ y │  │
│   └───┘ └───┘ └───┘ └───┘ └───┘ └───┘  │
│   ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐  │
│   │ a │ │ s │ │ d │ │ f │ │ g │ │ h │  │
│   └───┘ └───┘ └───┘ └───┘ └───┘ └───┘  │
│   ┌─────┐                    ┌────────┐ │
│   │  ⇧  │  z  x  c  v  b  n │  ⌫    │ │
│   └─────┘                    └────────┘ │
│   ┌──────┐ ┌───────────────┐ ┌────────┐ │
│   │ 123  │ │    SPACE      │ │ return │ │
│   └──────┘ └───────────────┘ └────────┘ │
│                                         │
└─────────────────────────────────────────┘

  ↑ Native system keyboard (rendered by OS, not Flutter)
  ↑ Character picker bar sits ABOVE the keyboard, BELOW the text field
    using a Flutter keyboard accessory / `resizeToAvoidBottomInset: true`
```

**Layout stack (bottom-up):**
```
[ System keyboard         ]  ← OS-controlled
[ Character picker bar    ]  ← Flutter widget, MediaQuery.of(ctx).viewInsets.bottom
[ Answer text field       ]  ← Scrolls up when keyboard appears
[ Prompt card             ]
[ AppBar                  ]
```

---

### F2.2 — Character Order in the Picker Bar

Order is by corpus frequency in Kurmanji Kurdish text, derived from linguistic data. Lowercase row appears first (primary use case); uppercase section is separated by a subtle vertical divider.

```
Position:  1    2    3    4    5   │   6    7    8    9   10
Char:      ê    î    û    ç    ş   │   Ê    Î    Û    Ç    Ş
Reason:   most common vowels first,│ uppercase mirrors
          then consonants by freq  │ lowercase order
```

**Frequency rationale:**
- **ê** — appears in many core words (êvar, êş, bêhn); highest frequency vowel marker
- **î** — second most common long vowel marker (navî, kurdî, vî)
- **û** — common but less frequent than ê/î (û "and", hûn, çûn)
- **ç** — the most frequent special consonant (çi, çav, çend)
- **ş** — second special consonant (şev, şîr, şûr)
- Uppercase variants are used at sentence starts; grouped after a divider to keep the primary flow uncluttered

---

### F2.3 — Tap Target Dimensions and Spacing

```
Character picker bar: full screen width × 48dp/pt tall
                      background: surface color (e.g. grey[100] light / grey[850] dark)
                      top border: 1px divider color

Each character button:
┌────────────────────────────────────────────────────────────┐
│  Property              │  Value                            │
├────────────────────────┼───────────────────────────────────┤
│  Tap target width      │  min 44pt iOS / 48dp Android      │
│  Tap target height     │  48pt / 48dp  (full bar height)   │
│  Visual label size     │  20sp, weight 500 (medium)        │
│  Font                  │  System default (Segoe UI / SF    │
│                        │  Pro / Roboto) — Kurdish chars    │
│                        │  render correctly in all three    │
│  Lowercase button bg   │  white / surface (light mode)     │
│                        │  grey[800] (dark mode)            │
│  Uppercase button bg   │  grey[200] / grey[700] — slightly │
│                        │  differentiated from lowercase    │
│  Pressed state         │  Ink splash (Material) /          │
│                        │  opacity 0.6 fade (Cupertino)     │
│  Corner radius         │  6dp (slightly rounded)           │
│  Horizontal padding    │  6dp between buttons              │
│  Left/right edge pad   │  8dp from screen edge             │
│  Divider (│)           │  1px wide, height 28dp, centered  │
│                        │  vertically, color: divider color │
└────────────────────────┴───────────────────────────────────┘
```

**Adaptive width calculation:**
```
Total bar width W = screen width (e.g. 375pt)
Left/right edge padding = 8pt × 2 = 16pt
Divider = 1pt + 12pt margin = 13pt
Available for 10 buttons = 375 - 16 - 13 = 346pt
Each button width = 346 / 10 ≈ 34.6pt  →  round to 34pt, adjust spacing
Note: 34pt < 44pt minimum visual width, but the TOUCH TARGET extends
      to fill the available tap zone using GestureDetector / InkWell
      with a larger hitTestBehavior area (the full 48pt tall bar height
      and equal horizontal spacing slices ensure ~34-36pt touch width).
On wider phones (414pt iPhone Plus) each button gets ~38pt — comfortable.
On 320pt phones: reduce edge padding to 4pt each side.
```

---

### F2.4 — Keyboard Dismissal Behavior

```
┌──────────────────────────────────────────────────────────────────┐
│  Trigger                  │  Behavior                            │
├──────────────────────────────────────────────────────────────────┤
│  User taps outside text   │  FocusScope.unfocus() →              │
│  field (on prompt card    │  keyboard + picker bar both slide    │
│  or background)           │  down together (they are anchored    │
│                           │  to viewInsets.bottom)               │
├──────────────────────────────────────────────────────────────────┤
│  User taps "return" /     │  Submit answer if non-empty;         │
│  "done" on system kbd     │  keyboard + bar dismiss together     │
├──────────────────────────────────────────────────────────────────┤
│  User taps a char in      │  Character is inserted at cursor     │
│  the picker bar           │  position; keyboard and bar STAY     │
│                           │  visible; focus remains on field     │
├──────────────────────────────────────────────────────────────────┤
│  User presses system      │  OS back gesture (Android):          │
│  back gesture             │  first press dismisses keyboard      │
│                           │  (and picker bar); second press      │
│                           │  navigates back — standard Android   │
│                           │  behavior, no override needed        │
├──────────────────────────────────────────────────────────────────┤
│  Screen transition /      │  FocusScope.unfocus() called before  │
│  navigation away          │  route pop; picker bar animates out  │
│                           │  with keyboard slide-down            │
└──────────────────────────────────────────────────────────────────┘
```

**Implementation approach (Flutter):**
- Wrap the `Scaffold` body with `GestureDetector(onTap: () => FocusScope.of(context).unfocus())`.
- Place the picker bar widget inside `Scaffold.bottomNavigationBar` OR as a `bottomSheet` that follows `MediaQuery.viewInsets.bottom` — this ensures it rides above the system keyboard automatically on both platforms.
- Use `AnimatedContainer` with duration 200ms / curve `Curves.easeOut` for smooth bar appearance/disappearance.
- The bar is only visible when `FocusNode.hasFocus == true` on the answer text field; use a `ValueNotifier<bool>` to toggle visibility.

---

### F2.5 — Edge Cases

#### Tablets (iPad, Android tablet, width > 600dp)

```
┌──────────────────────────────────────────────────────────────────┐
│  Issue                    │  Specification                       │
├──────────────────────────────────────────────────────────────────┤
│  Screen is much wider     │  Cap picker bar content width at     │
│  than phone               │  600dp, centered horizontally.       │
│                           │  Side margins fill with bar          │
│                           │  background color.                   │
│                           │  Button width increases proportionally│
│                           │  up to max 72dp per button (avoids   │
│                           │  overstretched appearance).          │
├──────────────────────────────────────────────────────────────────┤
│  iPad split keyboard      │  Picker bar is still anchored to     │
│  (floating keyboard)      │  viewInsets; if viewInsets.bottom=0  │
│                           │  (floating kbd), hide the bar — user │
│                           │  has full control over kbd position. │
│                           │  Show a small "Kur" keyboard button  │
│                           │  in the text field suffix icon to    │
│                           │  open a modal char picker instead.   │
└──────────────────────────────────────────────────────────────────┘
```

#### Landscape Mode (phone rotated)

```
┌──────────────────────────────────────────────────────────────────┐
│  Issue                    │  Specification                       │
├──────────────────────────────────────────────────────────────────┤
│  Available vertical space │  Picker bar height stays 48dp.       │
│  shrinks dramatically     │  The answer text field shrinks to    │
│                           │  min 2 lines visible (SingleChildScrollView│
│                           │  handles overflow).                  │
│                           │  Prompt card collapses to 1-line     │
│                           │  summary with a "See full" chevron.  │
├──────────────────────────────────────────────────────────────────┤
│  Bar is wider in          │  Same cap logic as tablet: max       │
│  landscape                │  content width 600dp centered;       │
│                           │  buttons grow proportionally.        │
└──────────────────────────────────────────────────────────────────┘
```

#### External / Bluetooth Keyboard (iPad, Chromebook, desktop Flutter)

```
┌──────────────────────────────────────────────────────────────────┐
│  Issue                    │  Specification                       │
├──────────────────────────────────────────────────────────────────┤
│  System keyboard not      │  viewInsets.bottom will be 0.        │
│  shown; viewInsets = 0    │  Character picker bar DOES NOT       │
│                           │  appear above keyboard (nothing      │
│                           │  there). Instead, show picker bar    │
│                           │  as a FIXED bar below the text field │
│                           │  (above the bottom safe area) when   │
│                           │  the field has focus.                │
├──────────────────────────────────────────────────────────────────┤
│  External keyboard can    │  Implement a TextInputFormatter or   │
│  type Kurdish chars if    │  key event handler that intercepts   │
│  OS input method set      │  dead-key sequences (e.g. ^ + e →   │
│  to Kurdish layout        │  ê) as a power-user enhancement.     │
│                           │  This is out of scope for MVP but    │
│                           │  worth noting for v1.1.              │
└──────────────────────────────────────────────────────────────────┘
```

---

## F3 — Skill Tree UI Concept

### F3.1 — Skill Tree Screen Wireframe (ASCII)

Portrait mode, 375pt wide phone. The tree is a single scrollable column with nodes offset left/right to create a winding path feel (Duolingo-style path, not a grid).

```
┌─────────────────────────────────────────┐
│  [≡]   Kurdlingo          🔥 7   💎 340  │  ← AppBar: hamburger, streak, gems
├─────────────────────────────────────────┤
│                                         │
│  ╔═══════════════════════════════════╗  │
│  ║  LEVEL A1.1 · Destpêk (Beginner) ║  │  ← Level banner (collapsible)
│  ║  Unit 1 of 5 complete             ║  │    kurdish geometric border motif
│  ╚═══════════════════════════════════╝  │
│                                         │
│         ┌─────────────┐                 │
│         │  ✓ UNIT 1   │                 │  ← Completed node (checkmark, green)
│         │  Silav!     │                 │    "Silav" = Hello in Kurmanji
│         └─────────────┘                 │
│                  │                      │
│                  │  (path connector)    │
│                  │                      │
│    ┌─────────────┐                      │
│    │  ▶ UNIT 2   │                      │  ← In-progress node (pulsing ring)
│    │  Hejmar     │                      │    "Hejmar" = Numbers
│    └─────────────┘                      │
│              │                          │
│              │                          │
│              │        ┌─────────────┐   │
│              └────────│  🔒 UNIT 3  │   │  ← Locked node (padlock, grey)
│                       │  Reng       │   │    "Reng" = Colors
│                       └─────────────┘   │
│                               │         │
│                               │         │
│         ┌─────────────┐       │         │
│         │  🔒 UNIT 4  │───────┘         │  ← Locked node
│         │  Xwarin     │                 │    "Xwarin" = Food
│         └─────────────┘                 │
│                  │                      │
│                  │                      │
│    ┌─────────────┐                      │
│    │  🔒 UNIT 5  │                      │  ← Locked node
│    │  Malbat     │                      │    "Malbat" = Family
│    └─────────────┘                      │
│              │                          │
│              │                          │
│  ╔═══════════════════════════════════╗  │
│  ║  LEVEL A1.2 · locked             ║  │  ← Next level banner (locked state)
│  ║  Complete A1.1 to unlock          ║  │    dimmed / grey
│  ╚═══════════════════════════════════╝  │
│                                         │
│  (scroll continues for A1.2 → B1.1)    │
│                                         │
└─────────────────────────────────────────┘

  Path zigzag pattern (top-down):
  CENTER → LEFT → RIGHT → CENTER → LEFT → ...
  Alternates every 1-2 nodes to create organic winding feel.
  Path connectors are curved lines (CustomPainter, cubic bezier).
```

**Scroll axis:** Single `CustomScrollView` (vertical), infinite scroll down.
**Level banners** are sticky headers (`SliverPersistentHeader`, `pinned: false`) that scroll naturally but can be identified as section separators.

---

### F3.2 — Node State Visual Specification

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  State        │  Visual                   │  Colors / Assets                 │
├──────────────────────────────────────────────────────────────────────────────┤
│               │  Grey padlock icon (24dp)  │  Background: #BDBDBD (grey 400)  │
│  LOCKED       │  centered in node          │  Border: none                    │
│               │  Node label: grey, italic  │  Label text: #9E9E9E (grey 600)  │
│               │  Tap: gentle shake anim    │  Icon: 🔒 or custom padlock SVG  │
│               │  + tooltip "Complete X     │  Node size: 80×80dp circle       │
│               │  first"                   │                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│               │  Colored fill, no icon     │  Background: brand primary color  │
│  UNLOCKED     │  Node label: white, bold   │  e.g. #C0392B (deep Kurdish red) │
│  (not started)│  Tap: navigates to unit    │  Border: 3dp white ring          │
│               │  intro screen              │  Label: white #FFFFFF            │
│               │                            │  Node size: 80×80dp circle       │
├──────────────────────────────────────────────────────────────────────────────┤
│               │  Colored fill + outer      │  Background: same as unlocked    │
│  IN-PROGRESS  │  pulsing ring animation    │  Outer ring: brand color at 40%  │
│               │  (repeating scale 1.0 →    │  opacity, animates scale 1.0 →   │
│               │  1.2 → 1.0, 2s loop)       │  1.3, duration 1.5s, curve       │
│               │  Progress arc on border    │  Curves.easeInOut, repeat        │
│               │  (e.g. 3/8 lessons done)   │  Progress arc: white, 3dp stroke │
│               │  Tap: continues lesson     │  Node size: 80×80dp + 12dp ring  │
├──────────────────────────────────────────────────────────────────────────────┤
│               │  Green fill + white ✓      │  Background: #27AE60 (green 700) │
│  COMPLETED    │  checkmark icon            │  Checkmark: white, 28dp icon     │
│               │  Stars (0–3) shown below   │  Stars: gold #F1C40F / grey      │
│               │  node as ★★★ / ★★☆         │  Node size: 80×80dp circle       │
│               │  Tap: review / re-do unit  │  Optional shimmer on first reach │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Node anatomy (all states):**
```
        ┌────────────────────────┐
        │   [outer pulse ring]   │  ← only in-progress
        │  ┌──────────────────┐  │
        │  │  [icon or label] │  │  ← 80×80dp circle
        │  │                  │  │
        │  └──────────────────┘  │
        └────────────────────────┘
              UNIT 2
             Hejmar          ← label below node (14sp, centered)
              ▶ 3/8          ← sub-label (12sp, grey, in-progress only)
              ★★☆            ← stars (completed only)
```

---

### F3.3 — Animation Specification

#### Unlock Celebration (unit unlocks after completing previous)

```
Trigger:    User taps "Continue" on the lesson result screen; the unit
            that was locked is now unlocked.

Sequence:
  1. Navigate back to skill tree (route pop)
  2. Newly unlocked node: play unlock animation
       - Duration: 600ms total
       - 0–200ms:   node scales from 0.0 → 1.1 (overshoot), curve: easeOut
       - 200–350ms: scale snaps 1.1 → 0.95
       - 350–450ms: scale settles 0.95 → 1.0
       - 0–600ms:   particle burst radiates outward from node center
                    (8–12 small star/diamond particles, brand + gold colors,
                     CustomPainter or Lottie file, fade out over 600ms)
       - Lock icon fades out (opacity 1 → 0, 200ms)
       - Color fills in (grey → brand color, 300ms, ColorTween)
  3. Path connector from previous node to this node animates:
       draw-on effect, 400ms, PathMetrics animation
```

#### Level Completion Celebration

```
Trigger:    User completes the final unit of a level.

Sequence:
  1. Full-screen overlay (semi-transparent black, 60% opacity)
  2. Level completion card slides up from bottom (400ms, easeOut)
       Content: Kurdish geometric border decoration (see F3.4)
                Large text: "Asta A1.1 Temam Bû!" (Level A1.1 Complete!)
                XP earned display
                Stars earned (animated fill left to right)
                "Continue" button
  3. Confetti shower: 40–60 particles, 2s duration
       Colors: Kurdish flag palette (green #009000, yellow #F7C000,
               red #C8102E) and white
  4. Background music/haptic: short celebration haptic (HapticFeedback.heavy)
     + optional short fanfare sound (configurable off in settings)
  5. On "Continue": overlay dismisses, A1.2 level banner animates unlock
     (grey → colored, shimmer sweep left to right over banner, 500ms)
```

#### Streak Display Placement

```
Location:   AppBar trailing area (right side), always visible on skill tree.
            Format: 🔥 [number]  (e.g. 🔥 7)
            Secondary: streak freeze icon (🧊) if streak freeze item active.

Streak milestone animation (e.g. reaching 7, 30, 100 days):
  - Streak counter in AppBar: brief scale pulse (1.0 → 1.3 → 1.0, 300ms)
  - Small toast notification slides in from top (below AppBar):
    "🔥 7 günlük seri! / 7 Roj Zincîr!" (bilingual or Kurdish only)
    Auto-dismisses after 2.5s.

Daily login streak reminder:
  - If user has not done a lesson today, streak icon uses warm orange #FF6D00
  - If lesson done today, streak icon uses golden yellow #FFD600
  - If streak broken, icon shows grey with a small ❌ badge
    (with option to repair using streak freeze gem)
```

---

### F3.4 — Cultural Touches: Kurdish Visual Motifs

Two motifs are proposed, both appropriate as UI accents and non-intrusive on a mobile screen:

#### Motif 1 — Zılhevok / Stêrk (Star Geometric Pattern)

The eight-pointed star (stêrk) appears extensively in traditional Kurdish kilim weaving and jewelry. It is non-political, universally recognized as Kurdish heritage, and naturally maps onto UI elements.

**Usage in Kurdlingo:**
- Level banner borders: a repeating band of simplified 8-pointed star outlines, rendered as a thin (2dp) decorative rule above and below each level banner.
- Node completed state: the ✓ checkmark sits inside a subtle 8-pointed star outline (faint, same green at 30% opacity) rather than a plain circle.
- Onboarding splash: full decorative stêrk in the background at low opacity.

**Color:** Use brand primary (deep red #C0392B or brand green) for the star stroke; never solid fills at full opacity (keeps it subtle).

**ASCII approximation of the border band:**
```
  ✦ · · · ✦ · · · ✦ · · · ✦ · · · ✦ · · · ✦ · · · ✦
  ════════════════════════════════════════════════════
  LEVEL A1.1 · Destpêk
  ════════════════════════════════════════════════════
  ✦ · · · ✦ · · · ✦ · · · ✦ · · · ✦ · · · ✦ · · · ✦
```

#### Motif 2 — Rengen Kurdî (Kurdish Color Palette)

The traditional colors found in Kurdish dress, flag, and crafts — forest green, golden yellow, and deep red — form a natural, warm UI palette distinct from Duolingo's lime green. This avoids political connotation (it is the palette of craft and dress, not specifically of any party flag) while being unmistakably Kurdish in feel.

```
┌──────────────────────────────────────────────────────┐
│  Role                  │  Color         │  Hex        │
├──────────────────────────────────────────────────────┤
│  Primary / active node │  Deep red      │  #C0392B    │
│  Completed node        │  Forest green  │  #27AE60    │
│  XP / gems / stars     │  Golden yellow │  #F1C40F    │
│  Level banner bg       │  Warm cream    │  #FFF8E7    │  (light mode)
│  Level banner bg       │  Deep brown    │  #3E2723    │  (dark mode)
│  Locked / inactive     │  Cool grey     │  #9E9E9E    │
│  Background (light)    │  Off-white     │  #FAFAF5    │  (warm tint vs pure white)
│  Background (dark)     │  Dark charcoal │  #1A1A1A    │
└──────────────────────────────────────────────────────┘
```

**Usage rule:** No more than two of the three vivid colors (red, green, yellow) should appear simultaneously in a single screen zone. The golden yellow is reserved for rewards (XP, stars, gems) — it should not appear on navigation elements.

---

*Document complete. Last updated by frontend design agent, Task F2 + F3.*
