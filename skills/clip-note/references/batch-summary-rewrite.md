# Batch Summary Rewrite — Programmatic Frontmatter Update

When the summary standard changes (or existing notes need frontmatter updates
across the board), use a Python script to parse, rewrite, and re-dump YAML
frontmatter for multiple vault files at once.

**Current standard (2026-08-08): summary = 导读 (teaser), ≤120 stripped chars,
NOT a 总结. Anatomy: 钩子/最独特的点 + 一句方法或价值 + 可选评价收尾 (值得读).
Full rules in SKILL.md §5. The 2026-08-04 <200-char RIA standard below is
superseded for the char limit (120) and intent (sell, not summarize).**

**Full-vault run status: COMPLETE (2026-08-08, 429 files → 429/429 compliant).**
10 dispatch rounds, 28 groups (27×15 + 1×20); final all-vault scan (yaml.safe_load
per file) reported 0 issues: all ≤120 stripped chars (min 61 / max 120), no ——,
no protected terms, single-line OK. The one miss (group25, 15 files untouched by a
self-reporting subagent) was caught ONLY by the closing full-vault scan, re-dispatched
with read-back asserts, and re-verified clean — including after a race where the
original fan-out returned late and both subagents wrote the same 15 files
(last-writer-wins, both compliant).

## When to use

- Retroactive summary rewrites when the style guide changes (e.g. new ≤120 char limit, 导读-not-总结 rule).
- Batch frontmatter field updates across many existing notes.
- Any task that touches the `summary` (or other YAML field) of 3+ existing vault files.

## The script pattern

```python
import yaml, re, os

BASE = '/home/win98/Documents/obsidian/Interpreter'

summaries = {
    'filename1.md': "new summary text...",
    'filename2.md': "new summary text...",
}

for filename, new_summary in summaries.items():
    fpath = os.path.join(BASE, filename)
    t = open(fpath, encoding='utf-8').read()
    m = re.search(r'^---\n(.*?)\n---\n', t, re.S)
    fm = yaml.safe_load(m.group(1))
    fm['summary'] = new_summary
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False,
                            default_flow_style=False).strip()

    # --- MANDATORY post-dump fixes (see below) ---
    new_fm = re.sub(r"type: 'clipper'", 'type: clipper', new_fm)
    new_fm = re.sub(r"published: '(\d{4}-\d{2}-\d{2})'", r'published: \1', new_fm)
    new_fm = re.sub(r"created: '([^']+)'", r'created: "\1"', new_fm)
    new_fm = re.sub(r"source: '([^']+)'", r'source: "\1"', new_fm)

    t = re.sub(r'^---\n.*?\n---\n', f'---\n{new_fm}\n---\n', t, count=1, flags=re.S)
    open(fpath, 'w', encoding='utf-8').write(t)
```

## yaml.safe_dump quoting fixes (MANDATORY)

`yaml.safe_dump` with `allow_unicode=True` quotes scalars that PyYAML thinks
need quoting. These fixes are the known set — apply ALL of them after every
`safe_dump` of clip-note frontmatter:

| Field | safe_dump output | Required fix |
|-------|-----------------|--------------|
| `type` | `type: 'clipper'` | `type: clipper` |
| `published` | `published: '2026-07-31'` | `published: 2026-07-31` |
| `created` | `created: '2026-07-31T15:00:00+08:00'` | `created: "2026-07-31T15:00:00+08:00"` |
| `source` | `source: 'https://...'` | `source: "https://..."` |

The `sort_keys=False` flag preserves field order (otherwise safe_dump
alphabetizes, which reorders frontmatter and diff-checks fail).
`default_flow_style=False` keeps block-style YAML (no inline lists).

## Verification script (run after all rewrites)

`scripts/verify_summary_chars.py` — scans vault `.md` files, checks each summary for:
**≤120 stripped chars (2026-08-08 导读 standard; the script was updated 2026-08-08
to 120 and the paragraph-break requirement was REMOVED — single-line summaries are
normal at ≤120)**, no `——`, no protected terms (智能体|提示词|资源), no fixed openings
(读完最值得记住的一句|一句话理解|想落地就做三件事), no paradigm labels
(**核心**|**拆解**|**行动**|**R**|**I**|**A**). Uses `yaml.safe_load` for accurate
multi-line extraction (fixed 2026-08-04 — old regex missed `\n\n` breaks).
Pass `--file "glob"` to narrow scope.

```bash
python3 ~/.hermes/skills/content/clip-note/scripts/verify_summary_chars.py --file "The*"
```

## Iteration strategy for hitting the char limit

First drafts of dense articles often run 250-350 stripped chars. Key lessons
from the 2026-08-04 batch rewrite of 9 notes (limits then <200; the tactics
carry over to the ≤120 导读 standard — scale the targets down):

1. **Aim ~90-110 stripped chars on the FIRST draft** — the ≤120 budget is tight;
   writing 200+ char drafts and iteratively trimming wastes 3-4 rounds.
2. **One line or 2-3 short clauses only** — 钩子 + 一句方法/价值 + 可选评价收尾;
   paragraph breaks optional at ≤120.
3. **Read all files first** (batch `read_file` calls) before writing any —
   context across all notes helps write tighter summaries.
4. **Common over-budget patterns**: listing every detail (resist — pick the
   single most distinctive claim), restating the title (redundant), keeping
   background/process description (40 亿、三层结构、创始人背景 — cut first).
5. Re-run the char counter after each pass. Target ≤115 to leave headroom.

Do NOT cut the core claim or the 钩子 — those ARE the 导读.

## Large-batch delegate_task pattern (100+ files)

When updating summaries across the entire vault (100+ files), use
`delegate_task` with 3 parallel leaf subagents. Each subagent reads
the full article text, writes a new summary, and updates frontmatter
programmatically.

### Splitting strategy (corrected 2026-08-04 — earlier "27 is sweet spot" advice was WRONG)

- **9-16 files per subagent is the safe range.** Evidence from the 413-file
  full-vault rewrite (2026-08-04): 9 files/batch → ~4 min, clean; 16 files/batch
  → ~9 min, clean; **31 files/batch → TIMED OUT at the 600s cap twice**
  (2 of 3 such tasks), with **ZERO files written** before the timeout — a
  timed-out subagent leaves no partial work to salvage.
- When a batch times out: re-dispatch the FULL file list — do not check for
  partial completion. Verify by scanning disk state, not by trusting subagent
  self-reports (a task can report "全部完成" while another sibling in the same
  fan-out wrote nothing).
- 3 subagents × 15-16 = ~48 files per round. For 400+ files, budget ~8-10
  rounds; each round's completion arrives as an async notification.
- **Dispatch pattern (verified 2026-08-08, 421-file 导读 batch):** write each
  group's filenames to `/tmp/group<N>.txt` (one filename per line, Python
  `glob` + `os.path.getmtime` sort, oldest-first), exclude already-updated
  files via a `done` set BEFORE slicing, then `delegate_task` with 3 parallel
  leaf subagents — each reads its `/tmp/group<N>.txt`, reads each file's BODY,
  writes the 导读 summary, and re-dumps frontmatter with the quoting fixes
  below. 15 files/task runs ~9 min; if a group 503s repeatedly, drop to 10.
- **Pilot-first rule (2026-08-08):** dispatch ONE 3×15 batch (~45 files) as a
  quality pilot, spot-check the actual on-disk summaries (not subagent
  self-reports) for 导读 structure + ≤120 chars, THEN fan out the rest. A
  full-vault fan-out on an unverified standard wastes rounds.
- **Subagent context must include (2026-08-08 导读 batch):** the 导读 anatomy
  (钩子/最独特的点 + 一句方法或价值 + 可选评价收尾), the ≤120 stripped-char rule,
  the banned list (——, 智能体/提示词/资源 in SUMMARY even if exempt in body,
  fixed openings, paradigm labels, AI-isms), the yaml.safe_dump quoting fixes,
  and the report format (per file: 字数 | ✓/✗问题). Give 1-2 approved example
  summaries (Palantir 92-char, Base Power 61-char) as style anchors.
- Print the file list to `/tmp/<group>.json` first, then split into
  chunks in Python before dispatching. Exclude files already updated this
  session (track them in a set) to avoid double-processing.

### Context to pass each subagent

1. The vault path (`/home/win98/Documents/obsidian/Interpreter/`)
2. The exact list of filenames (one per line, via `/tmp/group<N>.txt` — read it
   with Python, never hand-type filenames with CJK/smart-quote chars)
3. **Read the BODY (frontmatter-stripped) of each file, not just the old
   summary** — the 导读 must come from the article's actual core claim; the old
   summary is only a starting hint. For long notes, read past the truncation
   point (tail carries the conclusion).
4. The summary format standard: 导读 ≤120 stripped chars (copy the full rule
   from SKILL.md §5), single-line OK, banned list, 1-2 approved examples
5. The Python frontmatter update code pattern (from this file)
6. The mandatory yaml.safe_dump quoting fixes
7. Instruction to report: per-file char count (stripped), em-dash presence,
   protected terms, fixed openings, label words — and to NOT touch body text
   or other frontmatter fields (title/author/description stay unchanged)

### Dispatch mechanics (hard platform limits, verified 2026-08-08, 421-file batch)

- **`delegate_task` accepts AT MOST 3 tasks per call** — a 4-task batch errors
  immediately: `Too many tasks: 4 provided, but max_concurrent_children is 3`
  (no partial dispatch). For a 4th group, make a SEPARATE `delegate_task`
  call right after (it queues as its own fan-out). Plan groups in multiples
  of 3; the leftover (e.g. 20 files) gets its own single-task call.
- **Completion order ≠ dispatch order.** In the 421-file batch, group28
  (dispatched LAST, 20 files) returned in 103s while group25 (dispatched
  earlier, 15 files) took 289s. Async notifications arrive per fan-out, not
  per dispatch sequence — never assume the first-returned batch covers the
  first-dispatched group.
- **Race hazard: re-dispatching a group whose fan-out is still in flight.**
  A full-vault scan run while group25's fan-out was still running showed the
  group's files untouched → the group was re-dispatched → the ORIGINAL fan-out
  then returned "completed" for the same 15 files. Two subagents raced on
  identical filenames (last-writer-wins; both wrote compliant summaries so no
  corruption, but it's wasteful and format-drift between the two writes is a
  real risk). Before re-dispatching a "missing" group, confirm NO fan-out
  covering it is still pending — if its batch notification hasn't arrived,
  WAIT for it, then re-scan. Only re-dispatch on a confirmed miss.
- **Read-back assert in subagent instructions** (used in the group25 redo,
  worked): require each subagent to RE-OPEN the file after writing and
  `assert '\n' not in summary` + `assert len(stripped) <= 120` inside the
  script — a subagent that self-reports "完成" without writing (observed
  once in this batch: 15 files untouched, old 177-181-char summaries intact)
  cannot pass a read-back assert. Disk state is truth; the banner is a rumor.
- **Close the loop with a FINAL all-vault scan, not just per-batch checks.**
  Per-batch disk verification passed 9/10 batches; the 15-file miss surfaced
  ONLY in the closing full-vault sweep (429 files: 414 OK, 15 issues, all
  one group). Run the parent verification snippet below over `glob('*.md')`
  as the last step of every full-vault rewrite — it is the authoritative
  completion check.

### Parent verification after batch

After each batch returns, run a validation sweep:

```python
import yaml, re, glob
for f in sorted(glob.glob("*.md")):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'^---\n(.*?)\n---\n', t, re.S)
    fm = yaml.safe_load(m.group(1)) if m else {}
    s = fm.get('summary', '')
    sc = re.sub(r'\s', '', s)
    issues = []
    if len(sc) > 120: issues.append(f"over120({len(sc)})")   # 2026-08-08: 120, was 200
    if '——' in s: issues.append("em")
    if re.search(r'智能体|提示词|资源', s): issues.append("protected")
    if re.search(r'读完最值得记住|一句话理解|想落地就做', s): issues.append("oldopen")
    if re.search(r'\*\*核心\*\*|\*\*拆解\*\*|\*\*行动\*\*', s): issues.append("labels")
    # NOTE: no singleline check — at ≤120 chars single-line summaries are normal (2026-08-08)
    if issues: print(f"  ✗ {f[:50]}: {issues}")
```

Also run the verification script for a full sweep:

```bash
python3 ~/.hermes/skills/content/clip-note/scripts/verify_summary_chars.py
```

### Smart-quote filenames in search_files (2026-08-04 batch, 31 files)

When looking for files whose titles contain curly/smart punctuation
(non-ASCII apostrophes like `’`, curly quotes `""`), `search_files` with
a glob pattern will miss them. These are different characters:

- `'` (U+2019 RIGHT SINGLE QUOTATION MARK) ≠ `'` (U+0027 apostrophe)
- `"` (U+201C) / `"` (U+201D) ≠ `"` (U+0022)

Example: a file named `Your Personal Brand is Better Than a Resume. Here's How
to Build One.md` uses U+2019, while searching for `*Personal*` with ASCII
content patterns returns 0 hits. `search_files` with glob `*Personal*`
(found = 2) works because glob matching is byte-level, but content regex
patterns that include the literal `Personal Brand` may not match if the
distance between the smart-quote and the search term is miscalculated.

Fix: use glob patterns (`target='files'`) rather than content patterns
when the exact filename is uncertain due to smart quotes. `read_file` will
also fail if you pass the wrong quote character — resolve the actual
filename via `search_files` first.

### Also: Chinese punctuation in filenames

Files with Chinese titles containing fullwidth quotation marks (`""`,
not curly) also need glob-based file search. Example: `公众号贴图，
正在制造新一批"闷声赚钱"的人.md` has fullwidth `""` (U+FF02 is NOT
used — it's U+201C/U+201D in Chinese text). Searching by partial Chinese
text with `search_files` content mode works, but passing the full title
to `read_file` must match exactly byte-for-byte.

### Pitfalls observed during 2026-08-04 batches (413 files + 31-file batch)

- **Subagents produce single-line summaries** despite instructions to use
  `\n\n` — the YAML safe_dump wraps the newlines into its own indentation,
  but they parse back correctly. Verify with `'\n' in s` after safe_load,
  not by reading the raw file.
- **Dense articles (Eval Engineering, What nobody tells you)** need 3-4
  trim rounds to hit <200. Pass the iteration strategy (above) to subagents
  and tell them to aim ≤180 on first draft.
- **GPT-5.6 提示词大师课** legitimately has 「提示词」in the source —
  subagents should keep it (native term in original) not replace it.
- **Files today's session already updated** must be excluded from the
  batch list to avoid double-processing.
- **mtime-based progress check** during long batches: count files modified
  in the last 10 min to estimate subagent progress without polling.
- **HTTP 503 "Service is too busy" — subagents report `completed` while
  writing ZERO or FEWER files than claimed** (observed 6+ times, 2026-08-04
  full-vault batch): a task's result can say `status=completed` while its
  body reads `API call failed after 4 retries: HTTP 503: Service is too
  busy`. Two sub-modes, both require disk re-scan, not banner trust:
  (a) ZERO files touched (most common), (b) **PARTIAL writes — the API
  died mid-batch and some files were written before the failure** (observed:
  a 15-file group 503'd with 12 files already saved; the report still said
  `completed`). For 503 always re-scan disk state
  (`'summary' not in yaml.safe_load(...)`) for the exact file list and
  re-dispatch ONLY the files still missing — do NOT redo the partials.
  Contrast with TIMEOUT (600s cap): a timed-out subagent leaves zero
  partial work, so there you re-dispatch the FULL list. A repeated 503 on
  the same group is NOT a content problem — reduce batch size for the
  retry: 15 files/task failed repeatedly, 10 files/task went through
  cleanly on the same group. Do not burn rounds re-dispatching large
  batches into a throttled API; drop to 10 and accept more rounds.
- **Protected-term exemption must be verified against the BODY, not the
  summary alone** (2026-08-04 final sweep, 7 hits): a summary containing
  智能体/提示词/资源 is acceptable when the SOURCE ARTICLE legitimately
  uses the term. Verify programmatically by counting occurrences in the
  body with the frontmatter stripped:
  `body = re.sub(r'^---\n.*?\n---\n', '', t, flags=re.S); body.count(w) > 0`
  → exempt. All 7 hits in the 413-file sweep passed this check (titles like
  「少即是多（中）：让 AI 精分的提示词」 obviously contain the word).
- **Bare 核心/重点 in prose is FINE — only bolded label forms are banned**
  (2026-08-04 final sweep, 44 hits): a naive scan for the bare words
  核心/重点 flags legitimate natural prose (「抓重点」「核心卖点」「核心
  是修流程」) — 44 such hits across the 413-file vault, all acceptable.
  The user's no-label rule bans the PARADIGM TAG FORMAT `**核心**`/
  `**拆解**`/`**行动**` (bolded), not the ordinary words in flowing text.
  When triaging scan output, distinguish `**核心**` (must fix) from 核心
  as a normal adjective/noun (leave it). Same logic applies to 重点,
  拆解, 行动 used conversationally.
- **Traditional-Chinese source notes get traditional-Chinese summaries**
  (2026-08-04, 給 Agent 開發者的 Harness + Loop Engineering 系列): match
  the note's script, not the agent's default simplified. A simplified
  summary on a traditional-Chinese note reads as machine-generated to the
  reader. Mention script-matching in subagent context when the file list
  contains 繁体 notes.
- **verify_summary_chars.py regex bug (fixed 2026-08-04)**: the old
  `re.search(r'^summary:\s*(?:"|\'|)(.*?)(?:"|\'|)\s*$', ...)` regex
  failed to capture multi-line summaries written as `\n\n` paragraph
  breaks inside the YAML field. When `yaml.safe_dump` writes
  `summary: "line1\n\nline2\n\nline3"`, the regex matches only the first
  line and reports a truncated char count. Fixed by switching to
  `yaml.safe_load` for extraction when PyYAML is available (it handles
  both block scalars `|` and double-quoted `"\n"` forms correctly).
  The script now has both paths: yaml-safe_load for accuracy, regex as
  fallback when PyYAML is missing.
- **Ad-hoc vault scans MUST use yaml.safe_load, not a summary regex —
  single-quoted multi-line summaries misreport as MISSING, not truncated**
  (2026-08-08, 421-file 导读 batch): a throwaway scan
  `re.search(r'^summary:\s*"(.*?)"\s*$', t, re.M)` reported "无 summary: 414"
  because most legacy summaries are single-quoted multi-line YAML blocks
  (`summary: 'line1\n\nline2'`) that match neither the double-quoted nor
  the `$`-anchored forms. Consequence if trusted: the agent wrongly
  concludes 414 notes lack summaries and may re-add duplicate fields.
  Always extract via `yaml.safe_load(frontmatter_block)['summary']` for
  status scans; regex only for single-line diagnostics.
- **ing inline Python via terminal triggers security scan**: when running
  Python code inline via `terminal` (as `python3 -c "..."`), the security
  scanner may flag confusable Unicode characters if the inline string
  contains CJK text. Fix: write the script to a `.py` file with
  `write_file` first, then run it via `terminal`. Never use inline
  `-c` for batch text processing involving Chinese characters.
- **f-strings cannot contain backslashes in Python <3.12** (hit 3+ times
  in 2026-08-04 batches): `f"...{len(re.sub(r'\s','',s))}字..."` is a
  SyntaxError (`f-string expression part cannot include a backslash`).
  Fix: precompute the value into a variable BEFORE the f-string
  (`n = len(re.sub(r'\s', '', s)); print(f"...{n}字...")`). Same for any
  `re.sub`/escape inside f-string braces. This bites subagents repeatedly
  when they inline char-counting into report strings — put the pattern in
  the context you pass them.
- **Terminal tool name**: the tool is called `terminal`, not `bash`
  (attempting to call `bash` fails). This is environment-specific but
  worth noting for batch scripts that reference the tool by name.
- **Iteration for character limit on dense articles**: some articles resist
  trimming even after 2-3 rounds. Tactics that work:
  (a) drop a paragraph entirely (pick the 2 most concrete points, not 3),
  (b) shorten the conclusion to a bare clause (not a full sentence),
  (c) replace verbose connector phrases with a colon or nothing,
  (d) drop articles and pronouns where the meaning holds without them,
  (e) remember that punctuation characters (。，、) count toward the
  limit — every comma saved is ~1 char (but don't sacrifice readability).
  The harness engineering 101 article took 5 rounds to hit exactly 200.