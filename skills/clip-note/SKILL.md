---
name: clip-note
description: "Clip any web article or X/Twitter post into an Obsidian note in your native language. Detects source language — translates only when needed. Produces bilingual EN/CN notes with YAML frontmatter, local images, duplicate detection, and validation gates."
version: 3.0.0
platforms: [linux, macos]
license: MIT
---

# Interpreter

Turn URLs into polished Obsidian notes — in your language. A production workflow that powers a 390+ note knowledge base. **Agent-agnostic**: works with any coding agent (Claude Code, Codex, OpenCode, Gemini CLI, Hermes, etc.) — no platform-specific tools required beyond a shell, Python 3.10+, and whatever fetch capability your agent has.

## Quick Start

```
clip https://example.com/article
```

That's it. Fetch, detect language, translate if needed, download images, save.

First-time setup: tell the agent your native language and Obsidian vault path once (or pass them each time).

## Repository Layout

```
clip-note/
├── SKILL.md                  # this file — the agent runbook
├── scripts/
│   ├── clip.py               # fetch + dedup + language detection + image download + raw save
│   ├── dedup.sh              # quick vault duplicate scan (requires ripgrep)
│   ├── fxtwitter-parse.py    # dump fxtwitter X Article JSON → markdown source + media manifest
│   ├── batch-x-article-final-gate.py       # gate: X Article structure/terminology/coverage
│   ├── manual-web-article-final-gate.py    # gate: web article <br> format/YAML/UI residue
│   ├── manual-bilingual-final-check.py     # gate: bilingual structure/images/terminology drift
│   ├── verify-chinese-x-article.py         # gate: Chinese-original X Articles (monolingual)
│   ├── save-x-article-from-fxtwitter.py    # helper: Chinese-original X Article direct save
│   └── audit-bilingual-format.py           # audit/fix <br> format across a vault
└── references/
    └── setup-guide.md        # first-time setup for a new user
```

All scripts are pure Python/shell with no agent-specific dependencies. The gates are **deterministic** — the same input always produces the same verdict, so any agent can run them and get identical results.

## The Full Pipeline

When the user sends a URL or says `clip <url>`:

### 0. Dedup

Before any work, check if the source/canonical URL already exists in the vault. Search frontmatter `source:` values. If found → report filename, stop.

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
| **Web (Jina blocked)** | Your agent's web-extract tool, or a headless browser |
| **Substack/paywalled** | RSS feed `content:encoded` (proxy unset: `env -u http_proxy -u https_proxy curl -4 -L --http1.1`), otherwise ask user |
| **Medium (Cloudflare)** | Jina Reader fallback, localize `miro.medium.com` images |
| **JS-rendered dev blogs (stripe.dev, etc.)** | Plain extraction returns only metadata — the article body renders client-side. Use a headless browser and read `document.querySelector('article')?.innerText` (or the page's "Copy for LLM" button) |
| **Talk/slide-deck pages** | Parse `article.talk` / `.talk-segment` with paired images, exclude nav/social-card chrome |
| **Event pages (Goldcast, etc.)** | Parse `window.uberdata`, archive durable content only (title, abstract, speakers, bullets), strip registration chrome |
| **PDF papers/reports** | Test text layer first (`pdftotext`, your extract tool); if image-only → `pdftoppm` + `tesseract` OCR. Prefer canonical arXiv URL as `source`. For long surveys, create research-note archive (metadata, abstract, claims, taxonomy, key tables, limitations) rather than verbatim dump |
| **t.co / wrapper links** | Try a web search for the canonical URL first; only ask the user if search fails — do not bypass redirect security |

**Fxtwitter retry pattern:** `curl` may fail with TLS EOF under a proxy. Retry chain:
1. `curl -sL --max-time 30 <proxy-flag> "https://api.fxtwitter.com/status/<ID>"` → `/tmp/x_<ID>.json`
2. If TLS EOF: retry with Python `requests` + explicit `http`/`https` proxies + `verify=False`
3. If still fails: fetch the API URL through your agent's web-extract tool → read the cached file, undo Markdown escapes in JSON, write to `/tmp/x_<ID>.json`
4. If all fail: headless browser as last resort

Use `scripts/fxtwitter-parse.py` for any X Article: dump blocks, resolve images, extract metadata in one pass:

```bash
python scripts/fxtwitter-parse.py /tmp/x_<ID>.json --images
# writes /tmp/x_<ID>_source.md (block-by-block source) and prints the media manifest
```

> **Proxy note:** If your environment needs a proxy for outbound requests (common in CN networks), export it or pass it via curl `-x`. The examples use `http://127.0.0.1:7890` as a placeholder — replace with your actual proxy. Image downloads from `pbs.twimg.com` typically require the proxy.

### 2. Detect Language

Sample first 2000 chars. CJK >30% → Chinese (`zh`), else English (`en`).

- **source == native** → save directly, no translation needed
- **source ≠ native** → proceed with bilingual translation

**Chinese-original X Articles (source=zh):**

When source is already Chinese, use a different save path — no translation, no `<br>` format:

```bash
# 1. Fetch fxtwitter JSON as usual
curl -sL --max-time 30 <proxy-flag> "https://api.fxtwitter.com/status/<ID>" -o /tmp/x_<ID>.json

# 2. Save directly with the Chinese-first helper
python scripts/save-x-article-from-fxtwitter.py \
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

# 4. Verify with Chinese-specific gate (NOT bilingual gate)
python scripts/verify-chinese-x-article.py \
  --file path/to/note.md --json /tmp/x_<ID>.json
```

Chinese-original notes are monolingual — no `<br>` anywhere. The bilingual gate will produce expected false positives on these.

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

### 6. Images

Download ALL images to `<vault>/assets/` with deterministic names:
- `x-<post_id>-cover.<ext>` for cover
- `x-<post_id>-<index>.<ext>` for inline (zero-padded)

Rewrite all markdown image refs to local `assets/...` paths. No `pbs.twimg.com` or remote URLs should remain.

For X images: **must use proxy** (e.g. `curl -x http://127.0.0.1:7890`). Direct downloads from `pbs.twimg.com` time out without one.

If all download methods fail (corporate CDN block): keep remote URLs, note failure with ⚠️.

### 7. Relationship Layer

**Always required** — add these sections after the body in every saved note:

```markdown
---

## Internal Links<br>内部链接

## Link Candidates<br>链接候选

- [Author on X](https://x.com/author)<br>[作者的 X 主页](https://x.com/author)
```

For concept-rich articles, populate with actual links. For simple articles, leave headings with Link Candidates containing at least the source URL. The `manual-web-article-final-gate.py` checks for these sections — missing = FAIL.

### 8. Proofread

Run this structural + content checklist against the note before gates:

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

After proofreading passes, run the gates (all paths relative to this skill's `scripts/`):

```bash
# Gate 1: X Article structure, terminology, source coverage
python scripts/batch-x-article-final-gate.py \
  --pair /tmp/x_<id>.json=path/to/note.md

# Gate 2: <br> format, YAML, orphans, UI residue (web articles)
python scripts/manual-web-article-final-gate.py \
  --file path/to/note.md --source-text /tmp/source.md

# Gate 3: Bilingual structure, code fences, images, terminology drift
python scripts/manual-bilingual-final-check.py \
  --file path/to/note.md --expect-images <n>

# Chinese-original X Articles: use Chinese-specific gate instead
python scripts/verify-chinese-x-article.py \
  --file path/to/note.md --json /tmp/x_<id>.json
```

**Known false positives (accept, don't fix):**
- `possible UI/CTA residue: Like` — the word "Like" in narrative text
- `possible Chinese em-dash drift` — when EN side has ` - ` (space-hyphen-space) pause
- `possible protected AI-term translation drift` — "tools"/"resources" in non-MCP context
- `possible AI-term translation drift: 提示` — when 提示 means "remind" (verb), not "prompt" (noun)

If ONLY these remain → PASS.

### 10. Save and Confirm

Save as a **flat file** (no per-note subdirectory) at `<vault>/<Title>.md`.

**Filename rule — `title.md`:** the filename is the English side of the frontmatter `title` (`<br>`-separated or ` - `-separated), slugged:

- Strip the Chinese side entirely: `How LLMs Actually Work - LLM 工作原理详解` → `How LLMs Actually Work.md`
- Replace `: \ / * ? " < > |` with spaces, collapse whitespace, trim trailing `.`/space
- Pure-Chinese titles (Chinese-source articles) keep the Chinese title as-is
- Cap at 120 chars, cut at a word boundary

After renaming: batch-update `[[wikilink]]` references vault-wide, and never reuse a name that already exists (merge duplicates first).

**Response discipline**: Reply with `Filename.md ✅` only. Do NOT paste validation logs, image counts, gate output, or process summaries unless the user asks or there was a blocker.

## Operational Patterns

### Parallel / Batch URL Handling

When user sends multiple URLs or a new URL mid-processing:

1. **Dedup all URLs first** — separate read-only checks from side-effectful writes
2. **Fetch/parse in parallel** — independent fxtwitter/Jina calls
3. **Translate each independently** — delegate to subagents if your runtime supports them (for >70-block articles), or translate sequentially
4. **Parent verification for ALL** — subagents complete translation but the parent must re-inspect frontmatter, run gates, and strip CTA before confirming
5. **Report together** — list all filenames with ✅, one per line

**Parent verification after subagents** (mandatory):
- Read first 20 lines of each saved file
- Fix common subagent drift: `authors:` → `author:`, `type: "clipper"` → `type: clipper`, unquoted `created` datetime, `published` as datetime → date-only, source URL casing mismatch
- Run all applicable gates per file
- Only confirm after all gates pass

### Ultra-Long Articles (>100 blocks)

For X Articles with 100+ blocks or web articles over 20k chars:

1. **Phase 1 — Parse & dump**: Save full source dump to `/tmp/<slug>_source.md` with `<!-- BLOCK N -->` markers (use `scripts/fxtwitter-parse.py`)
2. **Phase 2 — Fragment translation**: Split into contiguous ranges (e.g., 0–160, 160–320, 320–end). Delegate each fragment to write ONLY `/tmp/<slug>_translated_part_<start>_<end>.md`. Include block markers for reassembly.
3. **Phase 3 — Parent assembly**: Assemble fragments in order, add frontmatter, localize images, add relationship layer, strip CTA
4. **Phase 4 — Parent gates**: Run all applicable gates. Never confirm from a subagent.

For atomic blocks in fragments:
- MARKDOWN → original fenced block, no Chinese partner
- MEDIA → placeholder for parent localization
- DIVIDER → `---` only if substantive
- TWEET → bilingual embedded-tweet URL line

### Interrupted-Turn Recovery

If a session is cut off mid-translation, inspect `/tmp` for artifacts (`x_<ID>.json`, `*_source.md`, `*_translated_part_*.md`). Check if a partial `.md` already exists in vault before re-delegating.

**Resume decision tree:**
- `/tmp/x_<ID>.json` exists but no vault file → build from JSON
- `*_source.md` exists → read it, don't re-fetch
- `*_translated_part_*.md` fragments exist → parent assembles and gates
- Nothing in `/tmp` → start fresh

When a new URL arrives while a previous one is still in progress: process both as one batch. Do the duplicate check first, then translate both independently, and report all filenames together.

## Configuration

| Setting | Default | Override |
|---------|---------|----------|
| Vault | `~/Documents/obsidian/Interpreter` | `--vault /path` |
| Native language | `zh` | `--native-lang en` |
| Force re-clip | false | `--force` |
| Proxy | unset | `HTTP_PROXY`/`HTTPS_PROXY` env, or curl `-x` |

## Pitfalls

- **Agent term replacement**: Never use 智能体 or 代理 for AI agent. Match exact source form (sub-agents ≠ subagent ≠ subagents).
- **English side purity**: No Wikilinks, no Markdown styling (`**`, `*`, `[]`, etc.), no paraphrasing. Source coverage compares byte-for-byte. Strip all `**` from English side of `<br>` lines before gates — bold/emphasis only on Chinese side.
- **Images are single-language**: Never add a Chinese partner image line (`![]()` has no `<br>`). The gate counts markdown image lines — a bilingual duplicate causes `image count mismatch: 2 != 1`. One image, one line.
- **`related` required even if empty**: `manual-web-article-final-gate.py` requires `related` in frontmatter. Set `related: []` for articles with no known connections.
- **Internal Links / Link Candidates always required**: Both sections must exist in every saved note (even if empty with just the headings). Gate 2 checks for their presence.
- **Numbered headings**: Chinese side drops the number. `## 1. Title<br>标题`, not `## 1. Title<br>1. 标题`.
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
- **Retroactive fixes**: When translation rules change (e.g., new forbidden-translation term), check whether existing files need retroactive patching. Use `scripts/audit-bilingual-format.py` for `<br>` format audits, and Python sed for terminology sweeps.

## Optional Enhancements

- **Humanizer** ([github.com/blader/humanizer](https://github.com/blader/humanizer)): strip AI-isms from the Chinese side at a global level. Load before translating if available.
- **Proofreader pass**: the full checklist is inlined in section 8 above, so no external skill is required.

## Credits

By K L (@kevalin). Production-tested on 390+ articles. MIT license.
