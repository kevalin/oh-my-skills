---
name: crap-design
description: Universal CRAP design rules from "The Non-Designer's Design Book" (Robin Williams) — Contrast, Repetition, Alignment, Proximity plus type and color laws, with validation checklists for any layout, typography, color, or visual design. Use whenever designing or reviewing any visual artifact (poster, flyer, card, slide, page, cover, chart).
platforms: [linux]
---

# CRAP Design Rules (from "The Non-Designer's Design Book" by Robin Williams)

Universal rules for constraining and validating any design's layout, typography, and color.
First understand the information structure, then beautify — layout is the externalization of information structure, not decoration.

## Overview

- **First step of any design: clarify the information structure** — what belongs together, who is the protagonist
- **Name it to control it**: give design elements names (alignment axis, repeating elements, contrast levels) — you can only fix what you can see
- **White space is not wasted** — it is breathing room and the primary tool for grouping (Proximity)
- The four principles work together: **Proximity groups, Alignment connects, Repetition unifies, Contrast ranks**

---

## ① Proximity — Achieve Organization

**Goal**: organize information so the reader instantly sees "what belongs together".

**How**:
- Physically group related items into one **visual unit**
- Test: scan the page and count how many groups you see — grouping should be clear and logical
- White space is the primary grouping tool (separate by distance, not by rules/lines)

**Avoid**:
- Unrelated elements too close (they get read as one group)
- All elements evenly distributed (no groups = chaos)
- **Intra-group spacing must be smaller than inter-group spacing** (otherwise grouping fails)

**Checklist**:
- [ ] Does each logical group cohere into one visual unit?
- [ ] Is inter-group spacing clearly larger than intra-group spacing?
- [ ] Are there unrelated elements wrongly grouped?

---

## ② Alignment — Unified and Ordered

**Goal**: page unity and order. Every element has a **visual connection** to another element on the page (an invisible line connects them even when physically separated).

**How**:
- Pick one clear alignment line (left axis / right axis / center axis) and hang all elements on it
- Left alignment is most common and readable; right alignment has formality
- **Center alignment is the weakest** — avoid for everyday design (reserve for formal occasions: certificates, invitations)
- Deliberate breaks of alignment must be intentional and obvious (otherwise it reads as a mistake)

**Avoid**:
- **Mixing multiple alignment styles** (center inside a left-aligned layout = the classic beginner error)
- Center alignment (unless formal)
- "Almost aligned" = not aligned

**Checklist**:
- [ ] Is there only one primary alignment axis on the page?
- [ ] Can every element find its alignment reference?
- [ ] Do baselines, margins, and decoration lines sit on the same invisible line?

---

## ③ Repetition — Unify and Strengthen

**Goal**: unify the whole page, strengthen visual effect.

**How**:
- Repeat visual elements: color, shape, texture, spatial relationship, line weight, font, size, image style
- If the page has nothing to repeat, **create a repeatable element** (a unifying symbol, palette, or line language)
- **The same logical level must use the same visual language** (all headings one style, all highlights one marker)

**Avoid**:
- **Over-repetition** (repetition serves unity, not monotony)
- Under-repetition (every element looks different — the page falls apart)

**Checklist**:
- [ ] Does the accent color/font/line language appear ≥2 times?
- [ ] Is every element at the same level (all headings / all highlights) in exactly the same style?
- [ ] Any element repeated to the point of fatigue?

---

## ④ Contrast — Attract the Eye and Organize Information

**Core rule**: **If two elements are not the same, make them very different.** Almost-the-same is not contrast, it is **Conflict** — the worst state: the reader wonders "are these the same or not?"

**Contrast dimensions**:
- Large type vs small type (easiest)
- Elegant serif vs bold sans-serif (typeface contrast)
- Thin line vs thick line (line weight)
- Cool color vs warm color (color contrast)
- Smooth vs rough (texture)
- Horizontal vs vertical (direction, e.g. a long line of text vs a tall narrow column)
- Wide spacing vs tight spacing (space)
- Small image vs large image (size)

**Avoid**:
- "Almost different" contrast (18px heading vs 16px body = a typographic accident)
- **Too much contrast** (if everything stands out, nothing stands out)
- Contrast that breaks hierarchy (secondary info more prominent than the protagonist)

**Checklist**:
- [ ] Are type sizes separated into ≥3 clear levels (e.g. 128/40/20/16)?
- [ ] Is color contrast sufficient (white on dark, dark on light)?
- [ ] Does the eye land on the protagonist first?

---

## ⑤ Typography Rules

**Three states of type**:
| State | Definition | Effect |
|---|---|---|
| Concord | One typeface (or one family) | Safe, calm, monotonous |
| **Conflict** | Two typefaces but almost the same | ❌ Worst state |
| Contrast | Two typefaces clearly different | ✅ Goal |

**Six type rules**:
1. **≤2 typefaces per page** (or one family in different weights)
2. **Consistency**: the same kind of content uses the same typeface/size/weight
3. **Contrast strongly**: if two typefaces, differentiate them clearly (size / serif-vs-sans / weight)
4. **No over-decoration**: few italics, few underlines, few ornaments
5. **Watch kerning and leading**: too-tight or too-loose hurts readability; leading ≥1.2× type size
6. **Consistent personality**: typeface personality must match content (don't use playful fonts for serious content)

**Checklist**:
- [ ] ≤2 typefaces?
- [ ] Same level entirely consistent?
- [ ] Two typefaces "clearly different"?
- [ ] Typeface personality matches content?
- [ ] Leading ≥1.2× type size?

---

## ⑥ Color Rules

**Color wheel relationships**:
| Relationship | Composition | Effect |
|---|---|---|
| Complementary | 180° opposite | Strongest contrast, vivid; accent complementary = pop |
| Triadic | Equilateral triangle | Balanced, rich |
| Analogous | Adjacent | Harmonious, safe, low contrast |
| Monochromatic | One hue in lightness/saturation variations | Clean, unified, elegant |

**Four contrast dimensions (more important than hue contrast)**:
1. **Value/lightness contrast (most important)** — dark-light contrast determines readability; white on dark, dark on light
2. Hue contrast
3. Saturation contrast (high saturation pops on muted backgrounds)
4. Warm-cool contrast (**warm advances, cool recedes** — warm grabs attention, cool recedes to background)

**Rules**:
- ≤3 main colors (excluding neutral black/white/gray)
- Same function, same color (consistency)
- **Set value/lightness first, hue second** (wrong value = unreadable)
- **Neutral colors get tinted by the dominant hue**: in a red/yellow/black-only composition, gray appears bluish — watch for "off-tint" neutrals

**Checklist**:
- [ ] ≤3 colors?
- [ ] Sufficient value contrast between text and background?
- [ ] Accent color consistent globally?
- [ ] Warm protagonist / cool background?
- [ ] No abnormal tint on neutrals?

---

## Design Process

```
1. Understand the information: structure? who groups with whom? who is the protagonist?
2. Establish the alignment axis: one primary alignment, unified across the page
3. Establish the repetition language: the color/type/line repetition system
4. Pull contrast: separate heading/body/emphasis type sizes, weights, and colors
5. Finish with white space: complete grouping with spacing, let the page breathe
6. Validate: run every checklist above
```

**Review workflow**: take any design (yours or someone else's) → check every item ①-⑥ → name violations (cite the principle + the "avoid" item) + give fix direction → re-check after fixing. Report format: `Violation (principle + checklist item) → problem description → fix suggestion`.

### Example violations and fixes (generic scenarios)

**Case 1: Proximity — annotation wrongly grouped**
- Violation: an annotation line (explaining the headline) placed closer to the footer contact block than to the headline — physical distance inverted the logical relationship
- Fix: move the annotation into the headline group (spacing 30–44px)
- Lesson: **inter-group spacing must follow logical relationships, not convenience**; ambiguous distances (~70–100px) are an error state

**Case 2: Contrast — type sizes "almost the same"**
- Violation: kicker 16px / subtitle 17px / footer 15px — three different levels with nearly identical sizes = the book's "Conflict" case
- Fix: separate to 20 / 16 / 14 (adjacent gap ≥4px or ≥1.25×)
- Lesson: **levels must be separated by type size, not only color/letter-spacing** — color blurs in thumbnails, size difference does not

**Case 3: Alignment — mixed axes**
- Violation: top label centered + body left-aligned + footer centered = center axis mixed with left axis
- Fix: unify on one axis (e.g. all-centered symmetric composition)
- Lesson: **one page, one primary alignment axis** — even if every local region "looks aligned", mixing axes across regions is a violation

## License

MIT — usable by any agent (Claude Code, Codex, OpenCode, Gemini CLI, Hermes Agent, etc.) with no platform-specific runtime.
