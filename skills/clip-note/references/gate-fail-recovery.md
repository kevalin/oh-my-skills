# Gate-Fail Recovery for Bilingual X Articles

Five distinct failure classes hit repeatedly in the 2026-08-04 batch of X Articles
(Reddit SEO, Speed Above All Else, Base Power, Hermes Content Engine, Context vs Memory).
Each has a specific fix. The general loop: **run gate → read the `FAIL` lines → fix one
class → re-run** — each round usually clears one class; never re-run blind.

## Failure class 1: Markers after `<br>` on the Chinese side

`Chinese side starts with a bullet/ordered-list marker after <br>` /
`Chinese side repeats a heading marker after <br>`.

Fix (three unconditional passes, in this order, before gating):

```python
import re
t = re.sub(r'<br>\s*#+\s+', '<br>', t)      # headings:  ## 中文 → 中文
t = re.sub(r'<br>\s*\d+\.\s+', '<br>', t)    # ordered:  1. 中文 → 中文
t = re.sub(r'<br>\s*[-*]\s+', '<br>', t)     # bullets:  - 中文 → 中文
```

The Chinese side of a list item/heading keeps the text, drops the marker
(`## EN<br>CN`, `1. EN<br>CN`, `- EN<br>CN`). Blanket passes are safe: a `<br>`
never legitimately follows a marker on the EN side.

## Failure class 2: Chinese em-dash `——`

`Chinese em dash found` is **unconditional** — fires on mere presence anywhere in
the file (body AND frontmatter summary), even when the EN side has `—`/`–`/` - `.
Fix: replace every `——` with `：` (explanation), `，`/`。` (contrast/clause), or
single `—` (attribution). Iterate `grep -c '——' note.md` until 0 — one line can
carry two hits and a single replace() fixes only the matched substring.

## Failure class 3: `===` separator blocks (coverage 0.00)

Some X Articles contain a bare `===` divider block (Alfred Lin "Speed Above All
Else": block[1] = `===`). If you skip it, gate reports `0.00 <block>` in material
coverage. Fix: include it verbatim with a Chinese partner:
`===<br>===`.

## Failure class 4: Truncated English block tail

The material check scores per-block WORD OVERLAP (min 0.92), not byte equality.
Dropping a block's tail sentences (even CTA-looking ones like
`Search Engine Land reported in December 2025...` or a product sentence
`That's the part ChatSEO runs for me: ...`) drags the ratio to 0.54-0.88 → FAIL.
Two correct moves:
(a) keep the FULL English block and translate the tail too (even promo), or
(b) if the WHOLE block is CTA, exclude via `--skip-cta-regex`.
What never works: dropping just the tail.

## Failure class 5: Mass paraphrase of the English side

The biggest time-sink of the batch (a16z Base Power, 94 blocks): paraphrasing/
condensing the EN side of MANY blocks at once → 12-14 blocks fail coverage at
0.72-0.89. Word-overlap scoring punishes condensation everywhere, not just tails.

**The rule: for X Articles, transcribe the EN side VERBATIM from the JSON block
text — do not condense, smooth, or merge sentences.** Translation happens only on
the CN side. Condensing saves drafting time but costs a repair pass over every
condensed block.

## The systematic repair script (for class 4/5, when blocks are already condensed)

Don't hand-fix 14 blocks. Build a script that pulls original text from the JSON
and replaces the note's condensed lines by head-char matching:

```python
# -*- coding: utf-8 -*-
import json

d = json.load(open('/tmp/x_<ID>.json'))
blocks = d['tweet']['article']['content']['blocks']
def txt(i):
    return blocks[i].get('text', '').strip()

fixes = {
  10: txt(10) + "<br>" + "中文翻译…",   # block index → full original + translation
  14: txt(14) + "<br>" + "中文翻译…",
}

t = open(note_path, encoding='utf-8').read()
for i, new in fixes.items():
    head = txt(i)[:45].replace('"', '')          # first ~45 chars of original
    for line in t.split('\n'):
        if head[:40] in line.replace('"', ''):
            t = t.replace(line, new)             # replace whole note line
            break
    else:
        print(f"!! not found block {i}: {head[:40]}")   # inspect & patch manually
open(note_path, 'w', encoding='utf-8').write(t)
```

Notes:
- Match on the first 40-45 chars of the ORIGINAL block — but curly quotes
  (`You're` U+2019 vs `You're` U+0027) differ between JSON and your draft, so
  normalize quotes on both sides (`replace('"', '')` at minimum; add `'`/`'` if needed).
- For blocks whose opening line you merged into a neighbor, match that neighbor's
  opening instead, then append the new block after it (patch by context anchor).
- After replacing, re-run gate: coverage scores improve per class, not all at once.

## Failure class 6: Skipped label/caption lines (image captions, beat markers, section lead-ins)

Learned 2026-08-05 (tetsuo "Grok Imagine short film", 141 blocks): visual tutorials
interleave bare label lines between `atomic` image blocks — `OTIS:`, `ROMAN FORUM:`,
`MEDIEVAL MARKET:`, `BEDROOM:`, `THE RED SCARF:`, `Beat 1.`, `Beat 2.`,
`Post Processing.`, plus lead-ins like `Prompt for grok.com to get the grok imagine
prompt you will need for Vera.` and `Here is the full sheet prompt for vera.`
Skipping them as "just captions" fails coverage for ~20 blocks at once (0.00-0.89).
Every non-CTA block must appear — including ones that are only a label.

Two sub-rules:
- **Pure label lines** (`OTIS:`, `ROMAN FORUM:`) still need a Chinese partner:
  `OTIS:<br>OTIS：`. Don't omit them from the bilingual body.
- **URLs must live on the EN side of `<br>`** (same article): appending a
  skill-link/`https://` URL to the Chinese side
  (`...生成。<br>…可直接生成。 https://grok.com/…`) FAILS coverage at 0.89 because
  the EN side lacks the URL. Put the URL at the END of the EN sentence:
  `...ready to generate. https://grok.com/…<br>…可直接生成。` URLs after `<br>`
  count as CN-side content and don't satisfy the EN coverage check.

## The insertion repair script (for class 6 and any omitted-block repair)

Head-char replace (above) handles condensed lines. For blocks that were SKIPPED
entirely, insert them after an anchor line by matching the anchor's EN-side prefix:

```python
# -*- coding: utf-8 -*-
import re, json
d = json.load(open('/tmp/x_<ID>.json'))
blocks = d['tweet']['article']['content']['blocks']
def txt(i):
    return blocks[i].get('text', '').strip()

# block id → anchor line whose EN side this block belongs after
anchors = {70: '### Locations', 73: 'ROMAN FORUM:', 106: '### Beats',
           114: 'For each beat we are going to use the /imagine-prompt-creator',
           136: 'Beat 9.'}
ZH = {70: '罗马广场：', 106: '现在到 beats。…', 114: 'Beat 1。'}

t = open(note_path, encoding='utf-8').read()
lines = t.split('\n')
for bid, anchor in anchors.items():
    full = txt(bid)
    if full in t:
        continue
    for li, line in enumerate(lines):
        en_part = line.split('<br>')[0].strip() if '<br>' in line else line
        if en_part.startswith(anchor):
            lines.insert(li + 1, '')
            lines.insert(li + 2, full + '<br>' + ZH.get(bid, ''))
            break
open(note_path, 'w', encoding='utf-8').write('\n'.join(lines))
```

Notes:
- **Run the three marker-strip passes (class 1) BEFORE anchor insertion** — the
  heading pass rewrites `## Step 2...<br>## 第二步` → `## Step 2...<br>第二步`, so
  anchors must match the post-strip form. Match anchors on the EN side prefix only
  (never the CN side, which changed under the strip).
- Sequential labels in source (`Beat 1.`, `Beat 2.`, …) share the same prefix —
  order the anchor dict so each inserts after its predecessor (118 after 115, etc.),
  or the second insert lands before the first.
- Anchor `startswith` matching is robust when the note's EN side is already verbatim;
  for labels the CN partner is optional (`ZH.get(bid, '')` yields `LABEL:<br>`).

## Order of operations that worked (Base Power, 4 repair rounds → PASS)

1. Script-replace the 10 blocks whose openings matched (head-char match)
2. `patch` in the 4 blocks whose openings were merged/omitted (locate via grep)
3. Strip `<br>## ` heading repeats
4. Iterate `——` replacements until grep -c == 0
5. Re-gate → PASS
