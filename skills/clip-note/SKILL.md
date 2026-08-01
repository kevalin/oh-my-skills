---
name: clip-note
description: "Clip any web article or X/Twitter post into an Obsidian note. Fixed EN→ZH pipeline: English articles translate to Chinese, Chinese articles save as-is. Produces bilingual EN/CN notes with YAML frontmatter, local images, duplicate detection, and validation gates."
version: 2.1.0
platforms: [linux, macos]
metadata:
  hermes:
    related_skills: [proofreader, humanizer, interpreter-content-pipeline]
---

# Clip-note

Turn URLs into polished Obsidian notes — in your language. The production workflow that powers a 390+ note knowledge base.

> **Design constraints (user-mandated, 2026-07):** 小而美 — do NOT generalize. Fixed language pair **EN→ZH** only (no language-parameter framework, no polyglot/multi-language abstractions). One URL in, one bilingual note out. Keep the package small: consolidation of the gate scripts into fewer entry points is an approved direction; expansion/generalization is not.

## Quick Start

```
clip https://example.com/article
```

That's it. Hermes checks for duplicates first, then fetches, detects language, translates if needed, downloads images, and saves.

First-time setup: tell Hermes your Obsidian vault path once.

## The Full Pipeline

When the user sends a URL or says `clip <url>`:

### 0. Dedup (MANDATORY — do this first, before any fetch)

Before ANY work, check if the source/canonical URL already exists in the vault. Search frontmatter `source:` values. If found → report filename, stop. Do not fetch, translate, or download anything until the dedup check passes.

```bash
rg -l --fixed-strings "<url>" <vault>   # or: python scripts/clip.py --dedup-only <url>
```

### 1. Fetch Content

| Source | Method |
|--------|--------|
| **X/Twitter Articles** | `curl https://api.fxtwitter.com/status/<ID>` → parse `tweet.article.content.blocks` |
| **X with "Copy as Markdown"** | User-pasted Markdown — preferred, avoids fxtwitter risk |
| **Slax Reader X shares** | `https://r.slax.com/b/<id>` — read-only mirror, extract canonical X URL from Source link, then fxtwitter |
| **Web articles** | Jina Reader (`https://r.jina.ai/<url>`) → clean markdown |
| **Web (Jina blocked)** | `web_extract` or browser |
| **Substack/paywalled** | RSS feed `content:encoded` (proxy unset: `env -u http_proxy -u https_proxy curl -4 -L --http1.1`), otherwise ask user |
| **Medium (Cloudflare)** | Jina Reader fallback, localize `miro.medium.com` images |
| **JS-rendered dev blogs (stripe.dev, etc.)** | `web_extract` returns only metadata — the article body renders client-side. Use browser navigation + `document.querySelector('article')?.innerText` (or the page's "Copy for LLM" button). Many such pages expose the full text via `innerText` on the article element |
| **Talk/slide-deck pages** | Parse `article.talk` / `.talk-segment` with paired images, exclude nav/social-card chrome |
| **Event pages (Goldcast, etc.)** | Parse `window.uberdata`, archive durable content only (title, abstract, speakers, bullets), strip registration chrome |
| **PDF papers/reports** | Test text layer first (`pdftotext`, `web_extract`); if image-only → `pdftoppm` + `tesseract` OCR. Prefer canonical arXiv URL as `source`. For long surveys, create research-note archive (metadata, abstract, claims, taxonomy, key tables, limitations) rather than verbatim dump |
| **t.co / wrapper links** | Try web_search for the canonical URL first (e.g. `stripe.dev/blog/...`); only ask the user if search fails — do not bypass redirect security |

**Fxtwitter retry pattern:** `curl` may fail with TLS EOF under proxy. Retry chain:
1. `curl -sL --max-time 30 -x http://127.0.0.1:7890 "https://api.fxtwitter.com/status/<ID>"` → `/tmp/x_<ID>.json`
2. If TLS EOF: retry with Python `requests` + explicit `http`/`https` proxies + `verify=False`
3. If still fails: `web_extract(["https://api.fxtwitter.com/status/<ID>"])` → read cached file, undo Markdown escapes in JSON, write to `/tmp/x_<ID>.json`
4. If all fail: browser extraction as last resort

Use `scripts/fxtwitter-parse.py` (see `interpreter-content-pipeline/scripts/`) for any X Article: dump blocks, resolve images, extract metadata in one pass.

For all X/Twitter image downloads, use proxy: `curl -x http://127.0.0.1:7890`. Direct downloads from `pbs.twimg.com` time out.

### 2. Detect Language

Sample first 2000 chars. CJK >30% → Chinese (`zh`), else English (`en`).

- **source == zh** → save directly, no translation needed
- **source == en** → proceed with bilingual translation

**Chinese-original X Articles (source=zh):**

When source is already Chinese, use a different save path — no translation, no `<br>` format:

```bash
# 1. Fetch fxtwitter JSON as usual
curl -sL --max-time 30 -x http://127.0.0.1:7890 "https://api.fxtwitter.com/status/<ID>" -o /tmp/x_<ID>.json

# 2. Save directly with the Chinese-first helper
python ~/.hermes/skills/content/interpreter-content-pipeline/scripts/save-x-article.py \
  --json /tmp/x_<ID>.json --source-url "https://x.com/user/status/<ID>" --tags "topic,tag"

# 3. Post-save cleanup (always inspect before confirming):
#    - YAML published must be real year (not 0000-*)
#    - Add type: clipper, summary (Chinese, <250 chars)
#    - Localize remote cover URL → assets/
#    - Add frontmatter related + Internal Links + Link Candidates
#    - Strip CTA blocks (感谢看到这里, 欢迎关注, etc.)
#    - Wrap bare code-like blocks in fenced fences
#    - Remove <!-- [image not available] --> placeholders
#    - For MARKDOWN atomics: extract value.data.markdown, insert as fenced block

# 4. Verify (auto-detects Chinese-original native mode)
python ~/.hermes/skills/content/interpreter-content-pipeline/scripts/gate.py \
  --file path/to/note.md --json /tmp/x_<id>.json \
  --source-url https://x.com/<user>/status/<id>
```

Chinese-original notes are monolingual — no `<br>` anywhere. The bilingual gate will produce expected false positives on these.

**Native post-processing pitfalls (2026-07, Graph engineering 中文教程 case):**
- **NEVER regex-edit the save-x-article.py frontmatter.** Its `description:` is multi-line (preview_text contains embedded `\n` inside the YAML quotes), so a greedy `re.S` match on `^description: "(.*)"$` swallows every following YAML key (tags/platform/summary/related/image) into one line. Correct path: split off the frontmatter, `yaml.safe_load` it, mutate the dict (flatten description with `re.sub(r'\s+', ' ', ...)`, add summary/related, localize image), rebuild keys in canonical order, dump. Never reorder with regex `pick()`-style field popping — list sub-keys (`  - "..."`) get orphaned from their parents.
- **Relationship layer must be monolingual on native notes** (see step 7). gate.py detects native mode as `"<br>" not in text` — a single `<br>` in Internal Links/Link Candidates flips the whole note into bilingual mode and fails every structural check (H1 lacks `<br>`, orphan lines, missing `<br>` everywhere). Pure-Chinese relationship sections only.
- **Cover image counts as a markdown image**: save-x-article.py emits `![Cover image](...)` in the body, so `--expect-images` = media_entities count + 1 (cover), or count actual `![` occurrences.
- After a yaml re-dump, unquote scalar fields before gating: `type: "clipper"` → `type: clipper`, `published: "2026-07-31"` → `published: 2026-07-31`.
- `possible protected AI term translated into Chinese` WILL fire on native notes — the Chinese author's own words (智能体 etc.) are not translation drift. Accept when the term exists in the source JSON blocks.

### 3. Parse Content

For X Articles from fxtwitter JSON:
- `tweet.article.content.blocks[]` — ordered block stream (unstyled, header-one/two, unordered-list-item, ordered-list-item, atomic)
- `tweet.article.content.entityMap[]` — list of `{key, value: {type, data}}`
- `tweet.article.media_entities[]` — `{media_id, media_info: {original_img_url}}`
- Cover: `tweet.article.cover_media.media_info.original_img_url`

EntityMap resolution:
- **MEDIA**: `entityMap[key].data.mediaItems[0].mediaId` → match `media_entities` → `original_img_url`
- **MARKDOWN**: `entityMap[key].data.markdown` → fenced code block (preserve as-is, no translation)
- **LINK**: `entityMap[key].data.url` → use on Chinese side; keep English raw for coverage
- **DIVIDER**: `---` if substantive, strip if decorative
- **TWEET**: embed as `Embedded tweet: <url><br>嵌入 tweet：<url>`

### 4. Translate

**Format rule — every content block uses `<br>` on one line:**

```
## English Heading<br>中文标题

English paragraph text.<br>中文翻译。

1. English list item<br>中文列表项
- English bullet<br>中文子弹

> English quote<br>中文引用
```

**Exact forms with no translation:**
- Code blocks (``` fences), inline code (`backticks`), command lines starting with `/`
- Images (`![alt](url)`)
- Attribution lines starting with `@`
- Audio/video references

**Terminology — these words stay in English:**
`agent`, `agents`, `sub-agent`, `subagent`, `subagents`, `MCP`, `host`, `client`, `server`, `tool`, `tools`, `resource`, `prompt`, `spec`, `SDD`, `API`, `CLI`, `SDK`, `loop`, `harness`

Match the **exact original form** from the English source — hyphenation, capitalization, pluralization. Never normalize.

**Translation quality:**
- Before translating, load the `humanizer` skill (`creative/humanizer`) — strip AI-isms at a global level, not just individual words.
- Contextual, not word-for-word. Read like natural Chinese.
- Strip AI-isms: no "值得注意的是", "总而言之", "让我们", "众所周知", "在这个快速发展的时代".
- No Chinese em-dashes (`——`) unless the English source has `—`, `–`, or ` - ` as a pause
- Escape bare `$` → `\$` outside code blocks
- "代理公司/代理服务" = business agency, keep in Chinese. All other 代理 in AI context → `agent`
- **"AI 公司" 语义区分**: when the source says "AI company" but actually means application-layer companies → translate as `AI 应用型公司`. Only use `大模型公司` / `基础模型公司` when explicitly referring to OpenAI/Anthropic-style foundation-model companies. Never use the vague catch-all `AI 公司`.

**CTA/UI stripping — remove from output:**
- "Follow me @handle", "Sign up for newsletter", "hope this was useful"
- "Want to publish your own Article?", "Upgrade to Premium"
- Like/repost/view/bookmark counts and metrics
- "Trending now", footer links, copyright notices
- Author bio, follower stats
- "Install/try/buy this product today"

### 5. YAML Frontmatter

```yaml
---
title: "English Title<br>中文标题"
source: "https://original.url"
author:
  - "[[Author Handle]]"
published: 2026-07-31
created: "2026-07-31T15:00:00+08:00"
description: "English summary. Single line, no newlines."
summary: "中文总结，不超过250字，单行。"
tags:
  - ai
  - clipper
  - topic-tag
related:
  - "[[Related Note]]"
  # use related: [] for articles with no connections
type: clipper
---
```

Rules:
- Strings double-quoted; dates unquoted; datetimes quoted
- `summary` always Chinese-only, <250 chars, single line
- `description` single line only — collapse whitespace
- Empty values → omit property entirely
- `type: clipper` always present (no quotes)
- `published` always date-only (not datetime)
- `image` — optional cover-art field, local `assets/...` path only (e.g. `assets/x-<post_id>-cover.jpg`). Vault convention: X Articles with a cover carry this field (15+ notes); web articles usually omit it.

### 6. Images

Download ALL images to `~/Documents/obsidian/Interpreter/assets/` with deterministic names:
- `x-<post_id>-cover.<ext>` for cover
- `x-<post_id>-<index>.<ext>` for inline (zero-padded)

Rewrite all markdown image refs to local `assets/...` paths. No `pbs.twimg.com` or remote URLs should remain.

For X images: **must use proxy** (`curl -x http://127.0.0.1:7890`). Direct downloads from `pbs.twimg.com` time out.

If `curl` exits 35 (TLS EOF under proxy) for an image: retry with Python `requests` + explicit proxies + `verify=False` (same fallback as the fxtwitter JSON fetch).

**Video media entities are not images**: `media_entities[]` entries whose `media_info.__typename` is `ApiVideo` (or any video type) have `original_img_url: null` — they render as `[IMAGE:...]` placeholders in the block dump but cannot be downloaded as images. Skip them: count them as 0 for `--expect-images`, do not localize, and do not add an image line. A note that says "the article contains a video" on the Chinese side is optional; there is no file to save.

If all download methods fail (corporate CDN block): keep remote URLs, note failure with ⚠️.

### 7. Relationship Layer

**Always required** — add these sections after the body in every saved note:

```markdown
---

## Internal Links<br>内部链接

## Link Candidates<br>链接候选

- [Author on X](https://x.com/author)<br>[作者的 X 主页](https://x.com/author)
```

For concept-rich articles, populate with actual links. For simple articles, leave headings with Link Candidates containing at least the source URL. The unified `gate.py` checks for these sections — missing = FAIL.

**Native (Chinese-original) notes**: relationship sections must be **monolingual Chinese, no `<br>`** (`## Internal Links` / `## Link Candidates` with plain `- [[...]]` / `- [text](url)` lines). A bilingual `<br>` relationship layer flips gate.py's native-mode detection (`"<br>" not in text`) into bilingual mode and fails every structural check.

### 8. Proofread

Load the `proofreader` skill (`editorial/proofreader`) and execute its methodology against these project-specific standards:

**Part A — Structural (格式合规)**

□ A1. YAML complete: title, source, author, published/created, description, summary, tags, type: clipper. summary is Chinese-only, <250 chars, single line.
□ A2. Heading format: h1 uses `<br>` for bilingual. h1 matches frontmatter title.
□ A3. Paragraph format: EN and CN on SAME line separated by `<br>`. No split-line pairs.
□ A4. Sub-headings: `### EN<br>CN` on one line.
□ A5. Ordered lists: `1. EN<br>CN` on one line, Chinese side drops the number.
□ A6. Unordered lists: `- EN<br>CN` on one line. Not `- EN` then `- CN` on separate lines.
□ A7. X engagement stripped: no likes, reposts, bookmarks, view counts.
□ A8. UI text stripped: no "Want to publish your own Article?", "Upgrade to Premium", "Follow me", "Sign up", "Log in".
□ A9. CTAs stripped: no author bios, follower stats, "hope this was useful", product promos.
□ A10. Images preserved: all original images embedded at correct positions.
□ A11. Relationship layer: frontmatter `related`, Chinese-side Wikilinks, Internal Links, Link Candidates present for concept-rich articles. No Wikilinks/Markdown styling on English source side.

**Part B — Content Quality (翻译质量)**

□ B1. AI agent terms stay English: agent, subagent, MCP, tool, resource, prompt, host, client, server. Not translated to 智能体/代理/工具/资源/提示.
□ B2. Exact original forms: match source spelling, hyphenation, capitalization, pluralization. sub-agents ≠ subagent ≠ subagents.
□ B3. Untranslatable terms kept: brand names, product names, proper nouns, framework names. No forced translations.
□ B4. "代理公司/代理服务" = business agency → keep in Chinese. All other 代理 in AI context → `agent`.
□ B5. Contextual fluency: reads like natural written Chinese, not word-for-word. Sentence structure adjusted for Chinese reading flow.
□ B6. No AI-isms: no 值得注意的是, 总而言之, 让我们, 众所周知, 在这个快速发展的时代.
□ B7. No em-dash drift: `——` only when EN source has `—`, `–`, or ` - ` as a pause.
□ B8. `$` escaped: bare `$` → `\$` outside code blocks.
□ B9. Source-Chinese articles: saved as monolingual MD, not bilingual. No `<br>` anywhere.
□ B10. "AI 公司" distinction: 大模型公司 for foundation-model companies (OpenAI/Anthropic), AI 应用型公司 for application-layer companies. No vague 笼统 "AI 公司".

### 9. Validate

After proofreading passes, run the unified gate (mode auto-detected):

```bash
GATE=~/.hermes/skills/content/interpreter-content-pipeline/scripts/gate.py

# Bilingual X Article (source coverage vs fxtwitter JSON)
python $GATE --file path/to/note.md --json /tmp/x_<id>.json --expect-images <n>

# Bilingual web article (source coverage vs cleaned text dump)
python $GATE --file path/to/note.md --source-text /tmp/source.md --expect-images <n>

# Chinese-original X Article (no <br> body, local-only images)
python $GATE --file path/to/note.md --json /tmp/x_<id>.json \
  --source-url https://x.com/<user>/status/<id> --expect-images <n>

# Structural-only quick check (any note)
python $GATE --file path/to/note.md
```

**Known false positives (accept, don't fix):**
- `possible UI/CTA residue: Like` — the word "Like" in narrative text
- `possible Chinese em-dash drift` — when EN side has ` - ` (space-hyphen-space) pause
- `possible protected AI-term translation drift` — "tools"/"resources" in non-MCP context
- `possible AI-term translation drift: 提示` — when 提示 means "remind" (verb), not "prompt" (noun)
- `possible protected AI term translated into Chinese` on **native** notes — the Chinese author's own words (智能体 etc.), not translation drift; accept when the term is in the source JSON blocks

If ONLY these remain → PASS.

### 10. Save and Confirm

Save as a **flat file** (no per-note subdirectory) at `~/Documents/obsidian/Interpreter/<Title>.md`.

**Filename rule — `title.md`:** the filename is the English side of the frontmatter `title` (`<br>`-separated or ` - `-separated), slugged:

- Strip the Chinese side entirely: `How LLMs Actually Work - LLM 工作原理详解` → `How LLMs Actually Work.md`
- Replace `: \ / * ? " < > |` with spaces, collapse whitespace, trim trailing `.`/space
- Pure-Chinese titles (Chinese-source articles) keep the Chinese title as-is
- Cap at 120 chars, cut at a word boundary

After renaming: batch-update `[[wikilink]]` references vault-wide, and never reuse a name that already exists (merge duplicates first).

For retrofitting the whole vault (mass rename, duplicate merge, wikilink chaining, verification) see `references/vault-maintenance.md` — the exact procedure used on the 390-file vault in 2026-07. Reuse it whenever the filename rule changes or legacy names are discovered.

**Response discipline**: Reply with `Filename.md ✅` only. Do NOT paste validation logs, image counts, gate output, or process summaries unless the user asks or there was a blocker.

## Operational Patterns

### Interrupted-Turn Recovery

If a session is cut off mid-translation, inspect `/tmp` for artifacts (`x_<ID>.json`, `*_source.md`, `*_translated_part_*.md`). Check if a partial `.md` already exists in vault before re-delegating.

**Resume decision tree:**
- `/tmp/x_<ID>.json` exists but no vault file → build from JSON (parent or subagent)
- `*_source.md` exists → read it, don't re-fetch
- `*_translated_part_*.md` fragments exist → parent assembles and gates
- Nothing in `/tmp` → start fresh

When a new URL arrives while a previous one is still in progress: process both as one batch. Do the duplicate check first, then translate both independently, and report all filenames together.

### Parallel / Batch URL Handling

When user sends multiple URLs or a new URL mid-processing:

1. **Dedup all URLs first** — separate read-only checks from side-effectful writes
2. **Fetch/parse in parallel** — independent fxtwitter/Jina calls
3. **Translate each independently** — use `delegate_task` for >70-block articles, parent for shorter ones
4. **Parent verification for ALL** — subagents complete translation but parent must re-inspect frontmatter, run gates, and strip CTA before confirming
5. **Report together** — list all filenames with ✅, one per line

**Parent verification after subagents** (mandatory):
- Read first 20 lines of each saved file
- Fix common subagent drift: `authors:` → `author:`, `type: "clipper"` → `type: clipper`, unquoted `created` datetime, `published` as datetime → date-only, source URL casing mismatch
- Run all applicable gates per file
- Only confirm after all gates pass

### Ultra-Long Articles (>100 blocks)

For X Articles with 100+ blocks or web articles over 20k chars:

1. **Phase 1 — Parse & dump**: Save full source dump to `/tmp/<slug>_source.md` with `<!-- BLOCK N -->` markers
2. **Phase 2 — Fragment translation**: Split into contiguous ranges (e.g., 0–160, 160–320, 320–end). Delegate each fragment to write ONLY `/tmp/<slug>_translated_part_<start>_<end>.md`. Include block markers for reassembly.
3. **Phase 3 — Parent assembly**: Assemble fragments in order, add frontmatter, localize images, add relationship layer, strip CTA
4. **Phase 4 — Parent gates**: Run all applicable gates. Never confirm from a subagent.

For atomic blocks in fragments:
- MARKDOWN → original fenced block, no Chinese partner
- MEDIA → placeholder for parent localization  
- DIVIDER → `---` only if substantive
- TWEET → bilingual embedded-tweet URL line

## Configuration

| Setting | Default | Override |
|---------|---------|----------|
| Vault | `~/Documents/obsidian/Interpreter` | `--vault /path` |
| Force re-clip | false | `--force` |
| Dedup-only | false | `--dedup-only` |

## Pitfalls

- **Agent term replacement**: Never use 智能体 or 代理 for AI agent. Match exact source form (sub-agents ≠ subagent ≠ subagents).
- **English side purity**: No Wikilinks, no Markdown styling (`**`, `*`, `[]`, etc.), no paraphrasing. Source coverage compares byte-for-byte. Strip all `**` from English side of `<br>` lines before gates — bold/emphasis only on Chinese side.
- **Images are single-language**: Never add a Chinese partner image line (`![]()` has no `<br>`). The gate counts markdown image lines — a bilingual duplicate causes `image count mismatch: 2 != 1`. One image, one line.
- **`related` required even if empty**: `gate.py` requires `related` in frontmatter. Set `related: []` for articles with no known connections.
- **Internal Links / Link Candidates always required**: Both sections must exist in every saved note (even if empty with just the headings). Gate 2 checks for their presence.
- **Numbered headings**: Chinese side drops the number. `## 1. Title<br>标题`, not `## 1. Title<br>1. 标题`. If you write `<br>1. 中文`, gate.py FAILs with `Chinese side starts with an ordered-list marker after <br>`. Bulk fix: `re.sub(r'(<br>)\d+\.\s+', r'\1', text)` — applies to ALL `<br>N. ` patterns including chapter headings (seen in marfinxx Master Agent Architecture 2026-07).
- **Bullet/numbered lists**: No repeated markers after `<br>`. `- EN<br>CN`, not `- EN<br>- CN`.
- **Code blocks**: Preserved as-is, single-language, no `<br>` partner. Do not add translated code fence.
- **`$` escaping**: Bare `$` → `\$` on both sides outside backticks.
- **Internal newlines**: Collapse embedded `\n` in fxtwitter text blocks before `<br>`.
- **Description**: Single line. Collapse `preview_text` newlines before writing.
- **CTA stripping**: Do not reinsert promotional copy just to satisfy source coverage. Build a `_nocta.json` and gate against that instead.
- **Duplicate key**: Exact canonical URL. Same author ≠ duplicate. Different status ID ≠ duplicate.
- **Parent verification**: After subagent batches, re-inspect first 20 lines for frontmatter drift (authors vs author, unquoted datetimes, type: "clipper" vs type: clipper, source mismatch).
- **Contraction drift**: When composing bilingual text from fxtwitter blocks, it's easy to write `you'll` when the source has `you`, or add a possessive `'s` that isn't there. The source coverage gate compares `block.text` byte-for-byte — always copy the exact text field for the English side. Never paraphrase, expand contractions, or "fix" grammar.
- **Inline style formula corruption**: fxtwitter `inlineStyleRanges` can mark substrings inside formulas as italic/bold, turning `=A2*B2, =A3*B3` into broken `=A2*B2*, =*A3*B3`. After applying styles, compare source blocks against saved file for exact text preservation; remove stray emphasis markers inside formulas/code before confirming.
- **Bold markers causing mass coverage failures**: applying `**` from `inlineStyleRanges` to the English side breaks source coverage because the raw block text doesn't have them. Fix: strip all `**` from English side of `<br>` lines before gates. Apply bold/emphasis only on Chinese side.
- **Cross-language contamination**: After drafting translations manually or via fragments, scan for non-English/non-Chinese stray scripts (e.g., Cyrillic `посвящ`) indicating accidental language drift. Source coverage gates won't catch these.
- **Retroactive fixes**: When translation rules change (e.g., new forbidden-translation term), check whether existing files need retroactive patching. Use `gate.py --audit <vault>` for `<br>` format audits, and Python sed for terminology sweeps.
- **gate.py check ownership — never re-mix modes** (learned 2026-07 during 5→1 consolidation; each check belongs to specific modes and applying it elsewhere causes false positives):
  - X modes (bilingual X + native) own: UI/metric residue via `UI_RE`, Chinese em-dash drift, `published`/`created` format checks, source coverage vs fxtwitter JSON.
  - Web mode (`--source-text`) owns: word-level `Like`/`Sign up` residue via `UI_RESIDUE`, unescaped `$` check.
  - Native mode owns: local-only image validation (`assets/...`, no remote CDN), exact `source` URL match via `--source-url`, `summary` <250 chars.
  - `PROTECTED_TERM_RE` must stay the compact `智能体|提示词|资源` — adding `工具`/`代理`/`提示` breaks real notes because `tool` legitimately translates to 工具 and 提示 commonly means "remind".
- **Ghost script references (doc drift)**: This skill once cited 3 scripts that never existed (`manual-br-final-gate.py`, `fxtwitter-parse-script.py`, `audit-fix-bilingual-format.py`) — referencing a script by name does not create it. When a SKILL.md mentions a helper, verify the file actually exists in the pipeline skill's `scripts/`; when deleting a script, sweep SKILL.md for dangling references. Before claiming a referenced script is missing, grep the whole `~/.hermes` tree — it may live under a different skill.
- **Package drift after rename**: the skill was renamed `interpreter` → `clip-note` (2026-07, commit `3a07e5e`). Old names may still appear in: README tables, setup-guide paths, `related_skills` of other skills (e.g. `interpreter-content-pipeline`), and repo directory names. A rename is incomplete until a full-tree `grep -rn "oldname"` comes back clean (excluding the umbrella `interpreter-content-pipeline` and `interpreter-weekly-report` which legitimately keep their names).

## Scripts

- `scripts/clip.py` — dedup first (always) + fetch + language detection + image download + raw save; `--dedup-only` stops after the duplicate check
- `scripts/dedup.sh` — quick vault duplicate scan
- Gate scripts (in `interpreter-content-pipeline`): `gate.py` (unified; auto-detects X-bilingual / web / native / structural modes), `save-x-article.py` (Chinese-original X save helper)
- `interpreter-content-pipeline/scripts/fxtwitter-parse.py` — full fxtwitter block dump + image resolution
- `interpreter-content-pipeline/scripts/gate.py --audit <vault>` — audit/fix `<br>` format across vault
- `references/gate-py-modes.md` — mode-detection table, per-mode check ownership, and the false-positive history behind each boundary (read before editing gate.py)

## Credits

By K L (@kevalin). Production-tested on 390+ articles. MIT license.
Distributed via [kevalin/oh-my-skills](https://github.com/kevalin/oh-my-skills) — publish new skills to `skills/<name>/` there.

**Portability status (2026-07-31)**: repo contains SKILL.md (agent-agnostic) + clip.py + dedup.sh + fxtwitter-parse.py + gate.py (unified) + save-x-article.py + setup-guide.md. A fresh user with any coding agent can run the full pipeline including Validate. External references (all optional): `humanizer` (open-source blader/humanizer). `proofreader` checklist is fully inlined in section 8. (renhua belongs to the Xiaohongshu pipeline, not Clip-note — removed 2026-07-31.) Script consolidation done 2026-07-31: 5 gate/audit scripts merged into one `gate.py`; `verify-chinese-x-article.py` → native mode; `audit-bilingual-format.py` → `--audit` mode; `save-x-article-from-fxtwitter.py` → `save-x-article.py`. 小而美.