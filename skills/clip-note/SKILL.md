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

### 0. Normalize URL → Dedup (MANDATORY — before any content fetch)

**0a. Normalize the URL first.** Dedup needs the **canonical URL**, not the link you were sent. Resolving the canonical URL is a lightweight step (seconds) — it is NOT article parsing:

- **Direct article/X URLs** (`x.com/.../status/123`, blog posts) — already canonical, skip to 0b
- **t.co / short / wrapper links** — resolve the canonical URL first: follow redirects (`curl -sIL`), or `web_search` for the canonical (e.g. `stripe.dev/blog/...`); only ask the user if search fails. **Never dedup against the wrapper URL** — the vault stores canonical `source:` values, so a wrapper search always misses
- **Slax Reader X shares** (`r.slax.com/b/<id>`) — extract the canonical X URL from the Source link first
- **r.jina.ai / reader wrappers** — strip the wrapper prefix, use the inner URL as canonical

**0b. Dedup against the canonical URL.** Check if the source/canonical URL already exists in the vault. Search frontmatter `source:` values. If found → report filename, stop. Do NOT fetch, translate, or download anything until the dedup check passes.

**Duplicate re-send response format** (learned 2026-08-02, adrianpunk115 + free_ai_guides re-sent twice): when the user re-sends a link that's already clipped, reply `Filename.md ✅（已存在）` — no re-processing, no explanation. Confirm the file still exists (`ls` it) so the reply names a real file, then stop. Do not re-run any pipeline step on a duplicate.

**Exception — re-sent URL of an OLD-STYLE note = re-polish, not ✅（已存在）** (learned 2026-08-13, incentivising "How to Get Maximum Results" re-sent): when the existing note's Chinese side predates the 2026-08-13 style mandate (English straight quotes `"..."` instead of 「」, AI-isms, stiff phrasing), the user's re-send is a re-polish request in disguise. Check the note's style first: `grep -c '"' <note>` on the CN side or scan for mandate violations (对举, 大词, template phrasing). If old-style → run the Re-Polish workflow below instead of replying ✅. If already mandate-compliant → ✅（已存在）.

```bash
rg -l --fixed-strings "<canonical-url>" <vault>   # or: python scripts/clip.py --dedup-only <canonical-url>
```

### 1. Fetch Content

| Source | Method |
|--------|--------|
| **X/Twitter Articles** | `curl https://api.fxtwitter.com/status/<ID>` → parse `tweet.article.content.blocks`. **Detect by `tweet.article` presence, NOT by `is_note_tweet`** (verified 2026-08-08, Dickie Bush article tweet): `is_note_tweet: False` + empty `tweet.text` can STILL carry a full article (`tweet.article.title` + 90+ `content.blocks`). When `text` is empty and `lang` is null, check `tweet.article` before concluding it's a plain tweet — an Article tweet with no visible text preview dumps its whole body in `article.content.blocks` |
| **X plain tweet (no article)** | fxtwitter returns `article: null` — check `tweet.media.photos[]`. If the content lives in screenshots (common for interview/story threads), download the photos via proxy, OCR them (`tesseract <img> stdout -l eng`), and build the bilingual note from OCR text with the images embedded locally. See "Plain tweets (no article)" below |
| **X plain tweet linking to a blog article** (learned 2026-08-04, Replit "AI adoption starts with truth"): tweet text is a short pitch + blog URL; the real content is the linked post. Treat as a WEB article: `web_extract` the blog URL for the body, set `source:` to the TWEET URL (what the user sent), add a `blog: <url>` frontmatter field for the canonical post, download the tweet's attached photo(s) via proxy as the note's image(s), and gate with `--source-text` (web mode) — no `--json`. Author = blog authors; publish date = post date |
| **X with "Copy as Markdown"** | User-pasted Markdown — preferred, avoids fxtwitter risk |
| **Slax Reader X shares** | `https://r.slax.com/b/<id>` — read-only mirror, extract canonical X URL from Source link, then fxtwitter |
| **Web articles** | Jina Reader (`https://r.jina.ai/<url>`) → clean markdown. **No publish date on the page? Find it in the blog index or RSS, not the raw HTML** (learned 2026-08-10, promptless.ai "Writing code was hard, actually"): the article page showed only "Copyright © 2026", but the blog listing page (`/blog`) carried the date in its HTML (`collection-feed-date` → `Feb 24, 2026`). Grep the raw article HTML for date patterns at your peril — analytics config values match too (a PostHog init `defaults: '2026-01-30'` looked like a publish date). Reliable order: article page meta → blog index near the article's title link → RSS `<pubDate>` |
| **Web (Jina blocked)** | `web_extract` or browser |
| **Substack/paywalled** | RSS feed `content:encoded` (proxy unset: `env -u http_proxy -u https_proxy curl -4 -L --http1.1`), otherwise ask user |
| **Medium (Cloudflare)** | Jina Reader fallback, localize `miro.medium.com` images |
| **JS-rendered dev blogs (stripe.dev, etc.)** | `web_extract` returns only metadata — the article body renders client-side. Use browser navigation + `document.querySelector('article')?.innerText` (or the page's "Copy for LLM" button). Many such pages expose the full text via `innerText` on the article element |
| **Talk/slide-deck pages** | Parse `article.talk` / `.talk-segment` with paired images, exclude nav/social-card chrome |
| **Event pages (Goldcast, etc.)** | Parse `window.uberdata`, archive durable content only (title, abstract, speakers, bullets), strip registration chrome |
| **PDF papers/reports** | Test text layer first (`pdftotext`, `web_extract`); if image-only → `pdftoppm` + `tesseract` OCR. Prefer canonical arXiv URL as `source`. For long surveys, create research-note archive (metadata, abstract, claims, taxonomy, key tables, limitations) rather than verbatim dump |
| **t.co / wrapper links** | Already canonicalized in step 0a — fetch the canonical URL directly |

**Fxtwitter retry pattern:** `curl` may fail with TLS EOF under proxy. Retry chain:
1. `curl -sL --max-time 30 -x http://127.0.0.1:7890 "https://api.fxtwitter.com/status/<ID>"` → `/tmp/x_<ID>.json`
2. If TLS EOF: retry with Python `requests` + explicit `http`/`https` proxies + `verify=False`
3. **Persistent exit 35 → retry with `--http1.1`** (learned 2026-08-13, coreyganim "Codex built me a fully functioning business"): h2 TLS handshake through the proxy can fail repeatedly (`error:0A000126:SSL routines::unexpected eof`) while HTTP/1.1 succeeds — `curl -sL --http1.1 -x http://127.0.0.1:7890 "https://api.fxtwitter.com/status/<ID>"` returned the full 35KB JSON after 3 plain retries failed. Do NOT encode the transient failure as a permanent constraint.
4. **The fxtwitter API itself is reachable WITHOUT the proxy** (learned 2026-08-05, agupta Palette link): unlike `pbs.twimg.com` media, `api.fxtwitter.com` resolves fine directly — when the proxy throws TLS EOF (curl exit 35), try dropping `-x` for this host before falling back to requests: `curl -s --max-time 30 "https://api.fxtwitter.com/status/<ID>"` → exit 0 / 200. Proxy flakiness is per-host, not global.
5. **Host-wide flake → go straight to web_extract** (learned 2026-08-09, thedankoe "Life is a mind game" 169-block article): when the proxy TLS-EOFs AND direct curl AND requests all fail (curl exit 35 / `SSLEOFError` on both proxy and direct), `api.fxtwitter.com` itself is flaky at that moment — don't burn more retries, jump to `web_extract(["https://api.fxtwitter.com/status/<ID>"])`. It routes through a different network path and succeeds when curl/requests cannot. The full JSON lands in the Hermes cache (`~/.hermes/cache/web/api.fxtwitter.com-*.md`) with Markdown escapes. Recover with the unescape-then-load pattern (verified working end-to-end):
   ```python
   import json, re
   raw = open("<cached .md path>").read()
   data = json.loads(re.sub(r'\\([_*\\[\\]#`])', r'\\1', raw))  # undo \_ \* \[ \] \# \` escapes
   json.dump(data, open('/tmp/x_<ID>.json', 'w'), ensure_ascii=False)
   ```
   fxtwitter JSON only carries the `\_`-style escape classes in practice; extend the regex class if a future payload shows others.
6. If all fail: browser extraction as last resort
7. **vxtwitter is NOT a full-article fallback** (learned 2026-08-13, coreyganim): `api.vxtwitter.com/status/<ID>` returns only `article.preview_text` + title + cover — no blocks/entityMap. Use it to confirm the article exists/type only; for the full article, retry fxtwitter with `--http1.1`.

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
#    - Add type: clipper, summary (Chinese, <250 chars, RIA 干货结构 — see §5)
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
- **Never draft a native note as bilingual first** (learned 2026-08-05, xiangxiang103 "手把手把 DeepSeek V4 Flash 接进 Codex" 167 blocks): writing EN=CN duplicated `<br>` lines for a Chinese original trips EVERY bilingual structural check (markers after `<br>`, H1 lacks `<br>`, coverage at 0.85-0.91 from paraphrased/truncated CN-side duplication) AND the native gate rejects `<br>` presence entirely. Correct path for hand-building a native note: **extract every block VERBATIM from the fxtwitter JSON** — `header-one/two` → `## `, `blockquote` → `> `, list items → plain lines, skip CTA tail blocks — no translation, no condensation, no `<br>` anywhere. A dump script that walks `tweet.article.content.blocks[]` and emits text per type (see `references/native-note-rebuild.md`) is the reliable generator; hand-transcription truncates and fails coverage. For 100+ block Chinese tutorials, run `save-x-article.py` and fix up, or dump+assemble — do not hand-write.
- **Native summary limit is <250 chars RAW (whitespace included), not <200 stripped** (same article): gate.py's native check is `len(m.group(1).strip()) >= 250` on the raw summary string — unlike the bilingual <200-stripped rule. A 527-char (570 raw) summary FAILS even after `\s` removal math. Trim to <250 raw chars (CJK-heavy summaries are denser — drop example lists, keep RIA structure tight). **Exact boundary (verified 2026-08-05, same article): `>= 250` means 250 raw chars STILL FAILS — 251 FAIL, 250 FAIL, 248 PASS. Target ≤249.** Compress in ONE command that prints the raw len (mirror the gate regex `^summary:\s*["']?(.*?)["']?\s*$` + `.strip()`) and rewrites the field — do not hand-iterate scripts, each pass costs a full gate cycle. **(re-verified 2026-08-08, Russell Palantir FDE native note):** the gate measures `len(summary.strip())` — raw chars INCLUDING internal spaces (CJK summaries have few, but count them); a stripped-only assert (`len(re.sub(r'\s','',s))`) under-reports the true length. Compress to ≤230 in ONE write (≈15% margin) — creeping down 5-10 chars per gate cycle wastes 5+ runs (tool-loop detector fires on the repeated FAIL) and every pass is a full gate run.
- **Protected-term check fires on native SUMMARY too, and the source-JSON exemption does NOT cover the summary** (same article): summary contained `提示词` → FAIL, even though the term exists in the source blocks (body exemption applied, summary didn't). Keep summary free of 智能体/提示词/资源 entirely; rephrase (提示词 → 系统提示/skills 说明) rather than rely on exemption.
- **`related` frontmatter key is required in native mode too** (same article): rebuilding frontmatter without it → `missing frontmatter keys: related`. Set `related: []` when no connections. (Existing bilingual pitfall, but easy to drop when regenerating native frontmatter from scratch.)
- **gate.py `strip_md` asymmetry: blocks containing `*` / `[` `]` can never match coverage** (same article, block 60 `[profiles.*]`): the gate strips the NOTE side with `strip_md` (removes `*`, link brackets) but compares source blocks with `collapse()` (whitespace only) — so a source block whose text contains markdown-significant chars like `[profiles.*]` (Codex multi-provider section) fails `s not in vis` at 0.64 no matter how verbatim the note is, because the note side got stripped and the source side didn't. Workarounds: (a) if the block is short, inline the exact chars in a way that survives strip (`[profiles.*]` — strip turns it into `profiles.`; can't recover) → use `--skip-cta-regex` for that block's distinctive text — **confirmed working in production (2026-08-05, xiangxiang103 block 60 `[profiles.*]`: added `据 CC Switch 的发布说明` to the skip regex and the block cleared the next run)**, or (b) report the gate bug: `collapse()` should apply the same punctuation strip as `strip_md` on the comparison. Don't burn cycles re-transcribing a block that is byte-exact in the file.

**Plain tweets (no article JSON)** — content often lives in attached screenshots:

1. fxtwitter JSON has `tweet.article == null`; check `tweet.media` / `tweet.media.photos[]` for image URLs (`pbs.twimg.com` — always download via proxy)
2. Download each photo (`requests` + proxies + `verify=False` if curl exits 35), save to `/tmp/x_<ID>-<n>.jpg`
3. OCR with `tesseract <img> stdout -l eng` (eng langdata ships with tesseract; no chi_sim needed for EN tweets)
4. Build the bilingual note from OCR'd text — **OCR is lossy**: fix obvious OCR artifacts (spacing, `l`/`1`, missing punctuation) on the EN side, and note in the frontmatter that the source was a screenshot tweet
5. Embed the original screenshots locally in the body (`assets/x_<ID>-<n>.jpg`) — they are the source of truth; the OCR text is for readability/search
6. **Gate with structural mode only** — there is no article JSON, so no `--json`, no source coverage: `gate.py --file note.md --expect-images <n>`
7. `--expect-images` = number of embedded local images (photos), NOT the count of `![` lines if you also embed a cover

Learned 2026-08-01 (coolcoder56 OpenAI SWE interview tweet): plain-tweet workflow ≠ X Article workflow; do not try to run `--json` source coverage on a note built from OCR.

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

**Atomic blocks are NOT always images — detect code-block atomics BEFORE counting media** (learned 2026-08-10, knoxtwts "how to master AI marketing in 30 days" 91 blocks): the article had 11 `atomic` blocks that looked like inline media but were actually fenced CODE blocks. Detection signals: (a) `media_entities` list is EMPTY while `entityMap` entries carry `data.markdown` (the atomic block's `entityRanges[].key` resolves to a markdown-carrying entity — sometimes typed `LINK` with a `markdown` payload, not `MARKDOWN`), and (b) atomic block `text` is blank (`' '`). When confirmed: extract each code block with `emap = {e['key']: e['value']['data'].get('markdown','') for e in entityMap}`, render verbatim as fenced blocks at the atomic position (single-language, no `<br>` partner, no translation), and gate with `--expect-images 0` — blank-text atomics are skipped by source coverage (`text_blocks` filters on non-empty text), so no EN-side coverage obligation and no image count. Never download anything for these. If atomic blocks exist but you haven't resolved their entityMap keys, you can't tell images from code — resolve first, count media_entities second.

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
- No Chinese em-dashes (`——`) ANYWHERE in bilingual X notes — **gate.py's x_mode check is unconditional**: `if x_mode and ("——" in text ...)` fires on the mere presence of `——`, even when the EN side legitimately has `—`/`–`/` - ` (e.g. list items `1. Reference signal (the goal) – ...<br>参考信号（目标）——...` still FAIL). The skill's old "unless EN has a dash" rule is aspirational, not what the gate enforces. Practical substitutions: explanatory → `：` or `，`; contrast → `，` or `。`; quote attributions (`——Naval`) → single `—Naval` (a lone `—` doesn't trip the `——` literal check). Check with `grep -c '——' note.md` before gating — must be 0. **The check scans the WHOLE file**, so `——` inside the frontmatter `summary` FAILs too (thedankoe 2026-08 — summary line was the last remaining hit). **One line can carry two `——`** and a targeted `replace()` fixes only the matched substring — after any em-dash pass, iterate `grep -c '——'` until it returns 0 (hit twice on one line in ridark_eth 2026-08: `你保留判断——…机器承担数量——…`).
- Escape bare `$` → `\$` outside code blocks — **mode-specific: only web mode (`--source-text`) and `--audit` enforce this; the X-bilingual main gate SKIPS the bare-`$` check** (verified 2026-08-09, thedankoe block 148 `$100m` kept verbatim → gate PASS). In X-bilingual (`--json`) runs, keeping `$` verbatim is the coverage-safe choice (EN side byte-exact, no escape noise in the note). If the note must also survive future vault-wide `--audit` scans, `\$` is equally coverage-safe: the word-overlap tokenizer treats `\$100m` and `$100m` as the same `$100m` token, so escaping costs nothing but a rendered escape sequence.
- "代理公司/代理服务" = business agency, keep in Chinese. All other 代理 in AI context → `agent`
- **"Resources:" heading → translate as 资料/参考, NOT 资源** (learned 2026-08-01, free_ai_guides article): `资源` is in `PROTECTED_TERM_RE` (compact list `智能体|提示词|资源`), so a perfectly correct translation of the common "Resources:" section heading trips `possible protected AI term translated into Chinese` on bilingual notes. Same for narrative "resources" → use 资料/支持/参考 depending on context (e.g. `engineering resources` → 工程力量, `best resourced` → 投入最大). Reserve 资源 for cases where no synonym reads naturally. **This also fires on the frontmatter title**: translating "43 Free Resources Inside" as `43 个免费资源` in the `<br>` title tripped it too (undefinedki 2026-08) — use 免费资料/免费参考 in titles and summaries as well. **Body-translation hits where the EN term is on the keep-English terminology list revert to English, not a synonym** (learned 2026-08-02, posthog "as resources and slash commands"): when the flagged word is a protocol/technical term (`resource`/MCP resources, `prompt`, `tool`), the cleanest fix is restoring the English original (`作为 resources 和斜杠命令`), which is both accurate and gate-clean — the terminology list in §4 explicitly keeps these words in English. This beats hunting a Chinese synonym that reads wrong. **Resource synonyms in non-protocol contexts (2026-08-09, incentivising + thedankoe notes): `the rare resource` → 稀缺品, `raw resources` (France 1940, military matériel) → 原始物资. When a body hit is NOT protocol-speak, pick a contextual synonym first (资料/参考/条件/物资/稀缺品); only revert to English when the term is genuinely on the keep-English list.**
- **"AI 公司" 语义区分**: when the source says "AI company" but actually means application-layer companies → translate as `AI 应用型公司`. Only use `大模型公司` / `基础模型公司` when explicitly referring to OpenAI/Anthropic-style foundation-model companies. Never use the vague catch-all `AI 公司`.

**CTA/UI stripping — remove from output:**
- "Follow me @handle", "Sign up for newsletter", "hope this was useful"
- "Want to publish your own Article?", "Upgrade to Premium"
- Like/repost/view/bookmark counts and metrics
- "Trending now", footer links, copyright notices
- Author bio, follower stats
- "Install/try/buy this product today"

**CTA handling in gates**: gate.py accepts `--skip-cta-regex "pat1|pat2"` to exclude CTA blocks from source-coverage accounting (e.g. `"bootcamp|Eden|MyMind|Kortex"` for a self-promo block, or the transition sentence `"Skip to the rest|allergic to self-promotion"` that introduces a stripped promo section — it's part of the promo unit, so stripping the promo without skipping its lead-in line fails coverage). Simpler than building a `_nocta.json`; prefer it when the CTA blocks are few and identifiable by regex. Learned 2026-08-01 (thedankoe article): article-length product pitches (Kortex/Eden/MyMind) need their own skip patterns — don't try to keep them in the note just to satisfy coverage. **Full advertorials (e.g. "Thanks Higgsfield for sponsoring this article", AnatoliKopadze 2026-07) are different**: the sponsored content IS the article body and often the value (18 copy-paste prompts) — keep the body, translate it, and skip only the explicit sponsor line (`--skip-cta-regex "sponsor|Higgsfield|Supercomputer"`). Distinguish "promo section inside an article" (strip) from "article that is a promo" (keep body, skip the sponsor disclosure). **CTA tail AFTER the author signoff = strip as one unit** (learned 2026-08-09, thedankoe "The Art Of Strategic Thinking" 239 blocks): everything after a closing `– Dan` / `— Author` / "Talk soon" signoff is almost always a product push (Eden promo blocks 236-238: `try out Eden here|you can use Eden to research|ultimate advantage so standing out`) — strip it all and cover the tail's lead-ins with ONE `--skip-cta-regex`. Contrast with promo sentences EMBEDDED in substantive blocks (block 132's "I made a little bot… free here" inside a vision-example paragraph): those blocks stay WHOLE and get translated, because coverage requires the full block (see tail-trim pitfall). The signoff is the boundary: before it = article (keep whole), after it = promo tail (strip as a unit).

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
- `summary` always Chinese-only, **≤120 stripped chars** (count with `len(re.sub(r'\\s','',s))` — punctuation and Latin tokens count toward the limit). **The bilingual gate does NOT enforce this cap — gate PASS at 157 stripped chars is real** (learned 2026-08-10, knoxtwts note: gate's only summary check lives in native mode, `>= 250` raw; bilingual mode never inspects summary length). The ≤120 limit is user convention — verify with `scripts/verify_summary_chars.py` (or the one-line `len(re.sub(r'\\s','',s))` check) BEFORE gating, and compress to ≤120 in ONE pass; do not treat gate PASS as summary approval. **User-mandated 2026-08-08: summary is 导读 (a teaser that decides whether to open the note), NOT a 总结 — it must NOT try to convey 80% of the content; it only needs to sell the note. User re-emphasized the distinction the same day ("我再次强调是导读，不是总结"). Hard cap ≤120 chars stripped (user tightened 150→120: "导读设置为120字以内"). 导读 anatomy (verified 2026-08-08 on 4 notes, 61-92 chars natural range): 钩子/最独特的点 (数据库里没有一家公司 / 视频模型零记忆) + 一句方法或价值 (Ontology+FDE 把隐性知识显式化 / 角色卡+密封 prompt 保一致) + 可选目标读者或评价性收尾 (想做 FDE 或 AI 进企业，这篇值得读). Evaluation-style closers (值得读/值得关注) are LEGAL in 导读 — they are the point of a teaser, unlike in 总结. Cut background/process-description first (40 亿、三层结构、创始人背景); keep the single most distinctive claim; noun-evidence only if space allows.**
- **Summary structure — RIA 干货式 + 去 AI 味 smooth 表达 (user-mandated 2026-08-02; refined 2026-08-04: "<200字, 去掉'读完最值得记住的一句'开头, 增加结构化格式, 不要一坨"; refined same day: "格式化的范式不用增加这些词汇(核心/拆解/行动等标签), 在内容上区分并合适的换行即可")**: structure stays RIA (a structured knowledge card, NOT a narrative/dense paragraph), but the WORDS must read like a person wrote them — no AI-isms. **Format**: NO paradigm label words (no `**核心**`/`**拆解**`/`**行动**`/`R`/`I`/`A` tags — user explicitly rejected label words 2026-08-04); instead distinguish parts BY CONTENT and separate them with appropriate line breaks (2-4 short paragraphs inside the YAML summary field using `\n\n`, OR a single line at ≤120 chars — single-line accepted 2026-08-08, Palantir FDE 112-char and Grok 104-char both passed as one line; paragraph breaks are optional when the whole summary fits 120). First paragraph = the core conclusion (one sentence, most valuable point up front, not chronological retelling); middle paragraphs = 2-3 concrete points (concepts, tool cards, root causes, concrete scenarios); last paragraph = concrete "接下来怎么做" action. **视觉打点**: keep bold ONLY for key terms worth emphasizing (optional), never for paradigm labels. **去 AI 味 rules**: no fixed opening phrase like 「读完最值得记住的一句」(user explicitly rejected 2026-08-04); no AI-isms (值得注意的是/总而言之/赋能/抓手/沉淀/闭环/在这个快速发展的时代); read the summary aloud in Chinese — if it sounds like a template, rewrite it. Gate compatibility: no `——`, no protected terms (智能体/提示词/资源) inside the summary; line breaks inside the YAML field are fine (gate counts whitespace-stripped chars) — the **≤120** limit applies to stripped chars (2026-08-08 mandate supersedes the earlier <200). Apply to BOTH bilingual and native notes. **Script match**: 繁体中文 source notes get traditional-Chinese summaries — match the note's script, never default to simplified (learned 2026-08-04, 給 Agent 開發者的 Harness + Loop Engineering 系列). **Canonical worked example (accepted 2026-08-04, "Don't be a meat proxy" article): 4 short paragraphs, no labels — `别把 AI 输出原样转发，对方自己能聊，还更快、更能控上下文。` / `AI 回复啰嗦、常带貌似合理的胡话、术语密集；读懂、验证、用自己的话重写，才是你加的价值。` / `代码评审最典型：复制粘贴 ticket 和 reviewer 反馈，实现者其实是 reviewer + Claude Code，你只是肉代理。` / `该用 AI 就用，但回复前先过自己的脑子和手。` — 157 stripped chars.**
- `description` single line only — collapse whitespace
- Empty values → omit property entirely
- `type: clipper` always present (no quotes)
- `published` always date-only (not datetime)
- `image` — optional cover-art field, local `assets/...` path only (e.g. `assets/x-<post_id>-cover.jpg`). Vault convention: X Articles with a cover carry this field (15+ notes); web articles usually omit it.
- **Batch-rewriting summaries across existing vault files**: when the summary standard changes (or retroactively updating old notes), use the programmatic yaml.safe_dump pattern in `references/batch-summary-rewrite.md` — it documents the mandatory quoting-fix chain (`type: 'clipper'` → `type: clipper`, etc.) that PyYAML introduces on every re-dump, plus a validation script and the iteration strategy for trimming dense articles to ≤120 stripped chars. **Verified production batches (2026-08-08, ≤120 导读 standard): 4 dense notes compressed in one pass — Palantir FDE 232→92, Grok Imagine 505→76, Base Power 413→61, Palette 371→66 — all gate PASS, all accepted by user as 导读 (NOT 总结). The intermediate 112/104/118/112-char versions were REJECTED as 总结-style — see `references/summary-ria-deai.md` for accepted vs rejected examples. Even a 505-char tutorial fits 120 by applying the four-step cut.**

### 6. Images

Download ALL images to `~/Documents/obsidian/Interpreter/assets/` with deterministic names — **actual production convention (2026-08): underscore after `x`, long numeric media_id, not index**:
- `x_<tweet_id>-cover.<ext>` for cover (e.g. `x_2087519404976156987-cover.jpg`)
- `x_<tweet_id>-<media_id>.<ext>` for inline, media_id = `media_entities[].media_id` (e.g. `x_2087519404976156987-2087509863211384832.jpg`)

(Older skill text said `x-<post_id>-<index>.<ext>` with hyphens/index — stale; the vault has used the underscore+media_id form across 20+ notes. When adding images to an existing note, follow the file's existing naming, don't mix schemes.)

Rewrite all markdown image refs to local `assets/...` paths. No `pbs.twimg.com` or remote URLs should remain.

For X images: **must use proxy** (`curl -x http://127.0.0.1:7890`). Direct downloads from `pbs.twimg.com` time out.

If `curl` exits 35 (TLS EOF under proxy) for an image: retry with Python `requests` + explicit proxies + `verify=False` (same fallback as the fxtwitter JSON fetch).

**Video media entities — top-level `original_img_url` is null, but the preview thumbnail IS downloadable** (corrected 2026-08-02, ashpreetbedi RAI article — old guidance said "skip videos" and was wrong): `media_entities[]` entries whose `media_info.__typename` is `ApiVideo` have NO top-level `original_img_url`, BUT `media_info.preview_image.original_img_url` carries a real thumbnail (`https://pbs.twimg.com/amplify_video_thumb/<media_id>/img/....jpg`). The body renders `[IMAGE:<media_id>]` placeholders for videos too, so a video-heavy article has MORE image markers than image-type entities. Correct handling: for every video entity referenced in the body, download `preview_image.original_img_url` as `x-<tweet_id>-<media_id>.jpg`, localize the placeholder, and COUNT it toward `--expect-images` (body image refs = image entities + video thumbs). Do NOT skip them — screen-recorded demo clips carry the article's visual content, and dropping them fails the count if the source dump emitted the marker. To find the thumb URL when it's missing: recurse `media_info.preview_image` for any `original_img_url` key (it lives one level deeper than image entities).

**ApiGif media entities carry a downloadable mp4 variant, not a thumbnail** (learned 2026-08-15, alexeixbt "Neuroplasticity"): `__typename == "ApiGif"` → `media_info.preview_image` is empty/None and the usable URL lives in `media_info.variants[]` (`[{bit_rate: 0, content_type: "video/mp4", url: "https://video.twimg.com/tweet_video/<short>.mp4"}]`). Download the mp4 via proxy (`curl -x http://127.0.0.1:7890`) into assets as `x-<tweet_id>-<media_id>.mp4` and embed it as a normal image line (`![image](assets/x_...mp4)`); Obsidian renders local mp4 inline. It COUNTS toward `--expect-images` like any other body media. The entity still renders as an `[IMAGE:<media_id>]` body placeholder, so localization + counting works identically to the ApiVideo case — the only difference is the URL source (variants vs preview_image) and file extension.

**`--expect-images` counts BODY image refs only — the frontmatter `image:` cover does NOT count in bilingual mode** (learned 2026-08-02, ashpreetbedi: passed `--expect-images 7` for 6 body media + cover → gate FAIL `image count 6 != expected 7`; 6 → PASS). This is the mirror image of the native-mode pitfall below, where `save-x-article.py` DOES emit `![Cover image]` in the body and cover counts. In bilingual hand-written notes the cover lives only in frontmatter `image:`, so `--expect-images` = number of `![...]` lines in the body (image entities + video thumbs) — never add +1 for cover. When in doubt, count actual `![` occurrences in the file body.

**Body URLs use SHORT media filenames — `media_id` ≠ URL filename segment** (learned 2026-08-02, formulasearch 16-image native article): `media_entities[].media_id` is the long numeric ID (`2083770699102187520`), but the URLs embedded in article body blocks are `https://pbs.twimg.com/media/HOsKaRlacAAbo7Q.jpg` — the filename segment (`HOsKaRlacAAbo7Q`) is a short ID unrelated to `media_id`. If you download images using `media_id`-based names (`x-<tweet_id>-<media_id>.jpg`) and then try to localize body URLs by matching on `media_id`, EVERY replacement misses (`!! 未映射: <url>` for all of them). Correct localization mapping: iterate `media_entities`, split each `media_info.original_img_url` on `/` to get `(short_filename, ext)`, build a `short_filename → (media_id, ext)` reverse map, then for each body URL extract its filename, look up the media_id, and replace with `assets/x-<tweet_id>-<media_id>.<ext>`. Cover is a separate single entry (`cover_media.media_info.original_img_url`) — match it by full-URL equality before the filename lookup. Verify with `grep -c 'pbs.twimg.com' note.md` (must be 0) after the pass.

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

□ A1. YAML complete: title, source, author, published/created, description, summary, tags, type: clipper. summary is Chinese-only, **≤120 stripped chars**, single line or `\n\n`-separated paragraphs.
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

**De-AI pass (2026-08-18):** run the CN side through the `deai-ify` skill (load with skill_view before translating/rewriting). Its five rules + 补充规则 (禁对举、禁升华结尾、禁三连排比、标点克制、叙事先人后事、术语保留英文) ARE the operational checklist for the style mandate below — check B1–B10 first for term fidelity, then run the deai-ify 自查 7 步 on the finished CN side (朗读 → 扫大词 → 扫句式 → 扫段落 → 看结尾 → 看标点 → 再读). If the Chinese side reads like an AI wrote it, rewrite.

**Translation style mandate (user-mandated 2026-08-13 — applies to ALL 中文翻译 sides, every note):** translate like an experienced, opinionated person naturally explaining things — concrete, continuous, detailed, rhythmic. NO template feel, NO big words, NO elevation. If the Chinese side reads like an AI wrote it, rewrite.

□ B1. AI agent terms stay English: agent, subagent, MCP, tool, resource, prompt, host, client, server. Not translated to 智能体/代理/工具/资源/提示.
□ B2. Exact original forms: match source spelling, hyphenation, capitalization, pluralization. sub-agents ≠ subagent ≠ subagents.
□ B3. Untranslatable terms kept: brand names, product names, proper nouns, framework names. No forced translations.
□ B4. "代理公司/代理服务" = business agency → keep in Chinese. All other 代理 in AI context → `agent`.
□ B5. Contextual fluency: reads like natural written Chinese, not word-for-word. Sentence structure adjusted for Chinese reading flow.
□ B6. No AI-isms: no 值得注意的是, 总而言之, 让我们, 众所周知, 在这个快速发展的时代; no 赋能/打造/助力/开启/深度/全方位/系统性/重塑/沉淀/闭环/抓手/提升.
□ B6a. No forced 对举 (不是……而是……) constructions to manufacture contrast/conclusion effect.
□ B6b. No grand-narrative endings (时代/文明/结构/人类命运) unless the source itself goes there.
□ B6c. Paragraphs: natural prose — several full sentences per paragraph, continuous narrative/logic. Short sentences only for rhythm, pause, humor, turn, or emphasis. NEVER one-sentence-per-paragraph fragmentation for literary effect (the #1 failure mode in recent translations).
□ B6d. Punctuation: minimize —— / quotes / ; / : in Chinese. Full-width punctuation only — no half-width punctuation inside Chinese text.
□ B6e. Endings: no mechanical elevation, no rhetorical-question strings, no triple parallelism, no 「这就是我们这个时代……」 closers. End light — on a person, a detail, an action, or one lingering judgment.
□ B6f. Narrative first: people and scenes before definitions or abstract judgment; concrete detail before concept. No open-with-definition/classification/theory.
□ B6g. Oral-source material: keep the speaker's voice and meaning, drop filler words, adjust breaks and rhythm — do not force oral speech into standard-essay prose.
□ B7. No em-dash drift: `——` only when EN source has `—`, `–`, or ` - ` as a pause.
□ B8. `$` escaped: bare `$` → `\$` outside code blocks (web mode / `--audit` only — X-bilingual gate skips it; see §4).
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
- **English titles ending in a period produce a double-dot filename** (`...Run Them All at Once.` → `...Once..md`) — the trim-trailing-dot rule is easy to miss mid-pipeline. When the English side of the title ends in `.` (common with imperative titles like "Run them all at once."), explicitly strip it before appending `.md`, and remember the vault copy is what matters — the `/tmp` draft filename doesn't need renaming.
- Pure-Chinese titles (Chinese-source articles) keep the Chinese title as-is
- Cap at 120 chars, cut at a word boundary

After renaming: batch-update `[[wikilink]]` references vault-wide, and never reuse a name that already exists (merge duplicates first).

For retrofitting the whole vault (mass rename, duplicate merge, wikilink chaining, verification) see `references/vault-maintenance.md` — the exact procedure used on the 390-file vault in 2026-07. Reuse it whenever the filename rule changes or legacy names are discovered.

**Response discipline**: Reply with `Filename.md ✅` only. Do NOT paste validation logs, image counts, gate output, or process summaries unless the user asks or there was a blocker.

## Operational Patterns

### Re-Polish an Existing Note (中文翻译要重新润色)

When the user sends `[K L] <exact note title>` with **NO URL** (e.g. `[K L] A Good Loop Ends With Proof` + `中文翻译要重新润色`), they want the existing vault note's Chinese side re-polished under the current translation style mandate (Part B, 2026-08-13) — NOT a fresh fetch, NOT a duplicate check. Learned 2026-08-13 (3 notes re-polished in one session).

1. **Locate the note**: `rg -l -i "<title>" <vault>` — several notes may contain the phrase; pick the exact-title match (e.g. `A Good Loop Ends With Proof.md` vs `AI循环：...md`; `How to Become AI Native.md` vs `How to become AI-Native.md` — case/hyphen distinguish them). Read the full note before touching it.
2. **Scope of the rewrite**: ONLY the Chinese side (after `<br>`), plus a tightening pass on the CN side of the title and the frontmatter `summary` if they violate the mandate (对举句式, mechanical enumeration, stiff phrasing: `一个好的循环以证据收尾` → `好的循环以证据收尾`). Keep the English side **byte-exact** (coverage depends on it), keep structure, assets, image lines, frontmatter fields. Fix typos found along the way (烘培→烘焙). **Byte-exact includes parenthetical placement** (learned 2026-08-13, "How to Fix Your Entire Life in 1 Day"): do not move annotation parentheticals like `(conditioning)` or `(learning)` between list items while re-polishing — the EN side must match the source block text exactly, including which item carries which annotation. Also **localize remote images during re-polish**: old notes embed `![Cover](https://pbs.twimg.com/media/...jpg)` and `![...](https://...)` remote URLs — download them into `assets/` (`x_<tweet_id>-cover.jpg`, `x_<tweet_id>-<media_id>.jpg` or descriptive names like `-loop.jpg`) and rewrite the refs to local paths; add `image:` frontmatter for the cover. Remote images still pass structural gates but violate the vault's local-assets convention.
3. **Legacy frontmatter trap** (learned 2026-08-13, "A Good Loop Ends With Proof"): pre-2026-07-migration notes carry `url:`/`date:`/`source: X (Twitter) - Article` and lack `type: clipper`, `created:`, and the Internal Links / Link Candidates sections → the structural gate FAILs with `missing frontmatter keys: type, created`, `YAML source is missing or non-HTTPS`, `missing Internal Links or Link Candidates section`. Normalize while re-polishing: add `source: <https url>` (legacy `url:`/`date:` can stay), `created: "YYYY-MM-DDTHH:MM:SS+08:00"`, `type: clipper`, and BOTH relationship sections (bare headings suffice; Link Candidates items bilingual `<br>` lines). Preserve `xhs_post_*` fields.
4. **Gate with structural mode** — no `--json` needed (EN side unchanged, so source coverage is unaffected): `python ~/.hermes/skills/content/interpreter-content-pipeline/scripts/gate.py --file <note>`. Accept the `possible UI/CTA residue: Like` narrative false positive (e.g. "Like how a thermostat...").
5. Reply `Filename.md ✅` per Response discipline.

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
- **For batch subagent work (summary rewrites, mass renames), a subagent can self-report "全部完成" while writing ZERO files** (observed 2026-08-08, 421-file 导读 batch: one 15-file group untouched at old lengths). Per-batch spot-checks missed it; only the closing full-vault scan (all files, `yaml.safe_load` summary extraction) surfaced the miss. Close EVERY multi-file subagent batch with a full-vault scan — see `references/batch-summary-rewrite.md` → "Dispatch mechanics" for the race/verify rules.

### Ultra-Long Articles (>100 blocks)

For X Articles with 100+ blocks or web articles over 20k chars:

1. **Phase 1 — Parse & dump**: Save full source dump to `/tmp/<slug>_source.md` with `<!-- BLOCK N -->` markers
2. **Phase 2 — Fragment translation**: Split into contiguous ranges (e.g., 0–160, 160–320, 320–end). Delegate each fragment to write ONLY `/tmp/<slug>_translated_part_<start>_<end>.md`. Include block markers for reassembly.
3. **Phase 3 — Parent assembly**: Assemble fragments in order, add frontmatter, localize images, add relationship layer, strip CTA
4. **Phase 4 — Parent gates**: Run all applicable gates. Never confirm from a subagent.

**Parent-side fast path for all-text articles** (learned 2026-08-09, thedankoe 169 blocks, "Life is a mind game. Here's how you win."): when the article has ZERO media_entities (no atomic MEDIA placeholders to localize, no cover-in-body), skip delegation entirely — write the bilingual note directly in 2-3 `write_file` parts (`/tmp/<slug>_partN.md`), then `cat part1 part2 part3 > "$VAULT/<Title>.md"`. Parent-side assembly avoids subagent drift (paraphrase, truncation, frontmatter bugs) AND the mandatory re-verification cycle; the 169-block article passed gate on the FIRST run this way, same as the 69-block eptwts article written in one shot. Reserve delegation for articles heavy in media/entity localization, where parallel work actually saves time.

**Fast path holds with media too** (re-verified 2026-08-09, thedankoe "The Art Of Strategic Thinking" 239 blocks, 1 atomic MEDIA + cover): a single body image doesn't force delegation — localize the one `![image](assets/...)` at the atomic block's position, count it (`--expect-images 1`; cover stays uncounted in bilingual), write 3 parts (≈20KB each), and gate. It passed on the first gate run after 3 protected-term fixes (see §4 资源 synonyms). Block count alone is not the delegation trigger; media/entity density is.

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

- **Quick Start must lead with the mandatory first step** (learned 2026-08-01, user: "应该先检查重复，再做其他的"): the pipeline table had Step 0 Dedup, but the Quick Start one-liner said only "fetches, detects language, translates…" — an agent reading the summary skips the mandatory check and fetches/translates first. When a step is MANDATORY-before-anything, the Quick Start line and setup-guide's test walkthrough must mention it too, not just the numbered pipeline. Now: "checks for duplicates first, then fetches…".

- **Agent term replacement**: Never use 智能体 or 代理 for AI agent. Match exact source form (sub-agents ≠ subagent ≠ subagents).
- **English side purity**: No Wikilinks, no Markdown styling (`**`, `*`, `[]`, etc.), no paraphrasing. Source coverage compares byte-for-byte. Strip all `**` from English side of `<br>` lines before gates — bold/emphasis only on Chinese side.
- **Images are single-language**: Never add a Chinese partner image line (`![]()` has no `<br>`). The gate counts markdown image lines — a bilingual duplicate causes `image count mismatch: 2 != 1`. One image, one line.
- **Multi-part assembly drops images — verify embed count BEFORE gating** (learned 2026-08-13, andreysuperior \"There Are Only 4 Ways to Make Money\" 106 blocks, 5 media): writing a note in 2-3 `write_file` parts and `cat`-merging is the fast path, but the `![image](assets/...)` lines for atomics that land at part boundaries get silently skipped — this note embedded only 3 of 5 (gate FAIL `image count 3 != expected 5`); the missing two were the FIRST atomic (block 4, right after the intro) and the LAST one (block 92, near the close), exactly the spots a fragment writer trims. Before gating any multi-part note: `grep -o 'assets/x_<tweet_id>' <note> | sort -u | wc -l` and compare to `--expect-images`; then re-check each atomic block's entityMap key against the note (walk `entityRanges[].key` → MEDIA id → position). Fix by inserting the `![image](...)` line at the correct position with `patch`, not by appending — the image must sit where the atomic block was (order matters for the reader).
- **`related` required even if empty**: `gate.py` requires `related` in frontmatter. Set `related: []` for articles with no known connections.
- **Internal Links / Link Candidates always required — BOTH, not either** (verified 2026-08-08, Dickie Bush "Grow An 𝕏 Audience" article): gate.py L154 is a double negation — `if "## Internal Links" not in text or "## Link Candidates" not in text: FAIL` — so despite the error message's "or" wording, a note with only ONE of the two sections FAILS (`missing Internal Links or Link Candidates section`). Add BOTH `## Internal Links` and `## Link Candidates` headings (bare heading text matches the substring check, `<br>` on the heading is optional). Link Candidates list items must be bilingual `<br>` lines (`- EN title<br>中文说明`) — a plain `- EN (中文注释)` line trips `missing <br>` from the orphan check. Internal Links wikilink bullets (`- [[...]]`) are exempt from the orphan check (they start with `- `).
- **Numbered headings**: Chinese side drops the number. `## 1. Title<br>标题`, not `## 1. Title<br>1. 标题`. If you write `<br>1. 中文`, gate.py FAILs with `Chinese side starts with an ordered-list marker after <br>`. Bulk fix: `re.sub(r'(<br>)\\d+\\.\\s+', r'\\1', text)` — applies to ALL `<br>N. ` patterns including chapter headings (seen in marfinxx Master Agent Architecture 2026-07). **The gate's marker check does NOT require CJK after the number** — it fires on any `<br>N. `, so the fix regex must be unconditional. **Counter-case: `N - ` (number-space-hyphen) headings do NOT trip this check** — `# 1 - Why vibe coding stops working<br>1 - 为什么 vibe coding 会失效` passed gate unchanged with the number kept on the Chinese side (0xJeyx Stop Vibe Coding, 2026-08-01). The check matches `\d+\.` only, not `\d+ - `. Canonical form is still number-dropped, but if a `N - ` heading slips through with the number retained, it is NOT a gate failure — don't chase it. A conditional variant `(<br>)\\d+\\.\\s*[\\u4e00-\\u9fff]` silently misses cases where the Chinese side starts with Latin text (e.g. `<br>18. Graph engineering：互相检查的 agents`, AnatoliKopadze 2026-07). If the unconditional regex would wrongly strip a legitimate number (e.g. a literal "version 2." in the Chinese side), do a targeted `replace()` for just that line instead.
- **List-marker strip must handle Latin/digit-starting Chinese too** (learned 2026-08-01, AnatoliKopadze + ridark_eth batches): the same "Chinese side repeats the marker" bug occurs when the CN side starts with digits/Latin — `<br>- 8 GB 显存跑...`, `<br>2. Claude 帮你写...`, `<br>3. Provider：ollama`. The `[\u4e00-\u9fff]`-anchored conditional regex misses ALL of these. Use TWO unconditional passes in order: `re.sub(r'<br>\\s*\\d+\\.\\s+', '<br>', t)` then `re.sub(r'<br>\\s*[-*]\\s+', '<br>', t)`. Verify with a scan for `re.search(r'<br>\\s*(\\d+\\.|[-*])\\s+\\S', line)` — the trailing `\S` catches any next char (CJK, digit, or Latin).
- **Headings repeat the `#` marker after `<br>`** (learned 2026-08-01, undefinedki AI Engineer guide): `# What the data says<br># 数据怎么说`, `## Materials<br>## 资料` trip the check `Chinese side repeats a heading marker after <br>`. The Chinese side of a heading keeps the text but drops `#` (the English side keeps the real heading level). Add a THIRD unconditional pass alongside the list-marker strips: `re.sub(r'<br>\s*#+\s+', '<br>', t)`. Run `#+` first, then `\d+\.`, then `[-*]` — all three before gating. Blanket is safe because a `<br>` never legitimately follows `#` on the EN side. (Note: `# 1 - Why vibe coding...` number-space-hyphen headings do NOT trip it — see numbered-heading pitfall.)
- **Web-mode H1 must match the SOURCE byte-for-byte — not the frontmatter title** (learned 2026-08-02, jakub.kr "Details That Make Interfaces Feel Better"): `check_web_coverage` does `strip_md(raw) not in saved_norm`, a case-sensitive line-membership check against the cleaned source dump. The source's first line is `# Details that make interfaces feel better` (sentence case), so a Title-Case H1 (`# Details That Make Interfaces Feel Better<br>...`) fails with `source coverage missing 1 lines; first examples: ['# Details that...']`. The frontmatter `title` may keep Title Case (display convention), but the H1 English side MUST reproduce the source's exact casing — draft the H1 from the source text, not from the title. Applies to any line ≥25 chars in the source dump, so keep casing identical on every transcribed paragraph too (web mode has no per-block source list to catch the rest).
- **Web-mode source dump must match heading LEVEL and list NUMBERING, not just text** (learned 2026-08-04, Replit "AI adoption starts with truth"): `strip_md` does NOT strip `#` markers and does not normalize `N.` list numbers, so `check_web_coverage` compares them verbatim. Three failures hit in one note: (1) source dump used `### Section` while the note's bilingual H2 was `## Section<br>中文` → `source coverage missing 10 lines` listing the `###` lines — fix by rewriting the source dump's headings to the SAME level the note uses (`sed -i 's/^### /## /' source.md`); (2) source had `2.`/`3.`/`4.` ordered items while the note (per the `<br>` marker rules) wrote `1.` for every item → coverage FAIL — normalize source numbers to `1.`; (3) a source line truncated when hand-transcribing the dump (`...deliberate and inspectable.` vs note's longer `...deliberate and inspectable, which is the property you want most...`) → FAIL — the source dump must carry the FULL line text that appears on the note's English side. Iterate: run gate, read the `source coverage missing` lines, align the dump, re-run — each round usually fixes a class of mismatch.
- **Standalone inline-code command lines trip `missing <br>` in web mode** (same article): an install command on its own paragraph — `` `npx skills add org/repo` `` — is NOT exempt like `/`-commands are, and the bilingual structural check flags the paragraph as missing `<br>`. Fix: pair the command with itself on both sides of `<br>` (`` `cmd`<br>`cmd` ``). Same for any bare command/code-only paragraph in web articles. Prose-wrapping the command inline (`` use `npx skills add …` to ``) avoids the issue entirely. Web articles (jakub.kr, Vercel-blob-hosted) may carry `.avif` images behind `/_next/image?url=…` wrappers — unwrap to the blob.vercel-storage.com URL and download with the usual requests+proxy pattern; name them `web_<slug>-<n>.<ext>` since there's no tweet ID.
- **Web-mode markdown tables: every row line needs `<br>`, and the full EN row must stay contiguous** (learned 2026-08-13, aihero.dev "A Complete Guide To AGENTS.md"): a bilingual markdown table written as two separate tables (EN table block, then CN table block) trips `missing <br>` on EVERY row line in web mode — the structural check wants `<br>` on each content line, and table rows are content. The split-cell format (`| EN cell<br>CN cell |` inside each cell) satisfies `<br>` but BREAKS source coverage: `strip_md` splits at the first `<br>`, so the EN blob line becomes just `| Small, focused AGENTS.md |` — the tail cells (`. | More tokens...`) detach and the full EN source row no longer appears. Correct format: one line per row, `| Full EN row |<br>| 完整中文行 |`, with the EN row byte-exact from the source dump (header row too: `| Scenario | Impact |<br>| 场景 | 影响 |`). The `<br>` lives BETWEEN the two table rows, not inside cells. Same applies to any non-paragraph block (code fences are exempt; tables are not).\n- **Web-mode byte-exactness extends to Unicode punctuation and markdown emphasis markers — never \"clean\" them** (learned 2026-08-15, sosams Substack \"How To Fix Your Confidence\"): the Jina source dump preserves curly apostrophes (U+2019: `you’ll`, `don’t`, `it’s`) and emphasis markers (`_“Can I remember … won?”_`, `**Now you’re ready …**`), and the gate does NOT normalize these — a hand-transcribed EN side that \"fixed\" them to ASCII (`you'll`) or dropped the `_…_`/`**…**` wrappers FAILS `source coverage missing N lines`, listing exactly those lines even though the visible text looks identical. Fix: copy the offending source lines VERBATIM onto the EN side — curly apostrophes stay curly, emphasis markers stay. When a web-mode coverage FAIL lists lines that appear byte-identical, diff them against `/tmp/<slug>_source.md` for Unicode drift (’ vs ', “ ” vs " ") and dropped `_`/`**` wrappers before rewriting any content. Applies to short hand-written web notes as much as long ones; Jina output is the ground truth for character-level fidelity.
- **Ellipsis is the same mismatch class — and the fix may go on the SOURCE-DUMP side, not the note** (learned 2026-08-15, theunintuitive "50 Observations on Living Well"): the web_extract source dump used ASCII `...` while the hand-written EN side used U+2026 `…` in 6 lines → `source coverage missing 6 lines` even though the text reads identically. Because the gate compares `strip_md(source_line) in strip_md(note)`, aligning EITHER side works. When the note EN side is mostly clean, normalize the SOURCE DUMP instead of touching the note: `src.replace('\u2019',"'").replace('\u2018',"'").replace('\u201c','"').replace('\u201d','"')` (curly→straight), **but do NOT blanket-convert `…`↔`...` in the source before checking which form the note actually used** — pick the direction per-line. This session: source had ASCII `...` everywhere, note had a mix (9 ASCII / 6 `…`) → normalized only the note's 6 EN-side `…` → `...` (CN side keeps `……`). Also strip Substack source-dump leftovers the gate's skip list does NOT catch: the `[Share](…)` link line (>25 chars, no subscribe/signup keyword) and `*BIG thanks to everyone…*` promo lines both FAIL coverage — delete from `/tmp/<slug>_source.md` before gating (`re.sub(r'\[Share\]\([^)]*\)', '', s)` + `re.sub(r'\*BIG thanks[^*]*\*', '', s)`).
- **Substack custom-domain images: download via Python urllib + proxy, NOT shell curl** (learned 2026-08-15, theunintuitive.com): `substackcdn.com/image/fetch/...` URLs contain literal `$` (price tokens in the fetch params) and `&` — shell curl mangles them (`&` backgrounds the command / `$` expands), yielding 9-byte garbage files silently. Use `urllib.request.build_opener(urllib.request.ProxyHandler({'http':'http://127.0.0.1:7890','https':'http://127.0.0.1:7890'}))` + `addheaders User-Agent`, or quote args with `shlex.quote`. Detect corrupt downloads immediately: `stat -c%s` any result <1KB is a failed fetch, not an image. Publish date for Substack: grep the raw article HTML for `"datePublished":"..."` (present in the JSON-LD even when Jina/web_extract omit it). When r.jina.ai TLS-fails (exit 35) for a Substack URL, `web_extract` on the custom domain works — and the full text is cached at `~/.hermes/cache/web/<domain>-<hash>.md` (read the cache file to recover middle sections web_extract truncates).\n- **Promo blocks living INSIDE the source dump: strip them from the source file, don't fight `--skip-cta-regex`** (learned 2026-08-13, aihero.dev): the Jina dump carried a link-formatted promo block (`[AI Hero · Skill System ### A great AGENTS.md is step one ... See the skill set](...)`) that was one long multi-line link — regex-skipping it was fragile because the `---`-style markdown inside made it look like multiple lines to the coverage check. Fix: remove the promo block from `/tmp/aihero_source.md` itself before gating (`re.sub(r'\[AI Hero · Skill System.*?See the skill set\]\([^)]*\)', '', s, flags=re.S)` + collapse `\n{3,}` → `\n\n`), then gate against the cleaned dump. `--skip-cta-regex` remains the right tool for CTA blocks that ARE in the source as normal text; for markdown-link promo blobs, editing the source dump is more reliable.
- **Materials/link-list coverage is byte-exact on the trailing annotation** (learned 2026-08-01, undefinedki guide): gate.py's `material source coverage` check matches the full block text, not just the URL. A link line like `- https://surgehq.ai/careers/... -$250k, apply with a take-home.` fails coverage if the note writes `- $250k, apply...` (space inserted between `-` and `$250k`) — the check compares the annotation after the URL byte-for-byte (`-$250k` vs `- $250k`). Same for `-40+ curated first issues` (source has no space: `contribute -40+`, note must not write `- 40+`). When transcribing Materials lines, copy the annotation verbatim including dash-spacing; the failure message prints the exact missing blocks (`material source coverage missing N block(s): <score> <block-text>`).
- **Materials URL lines get the same `<br>- ` strip** (learned 2026-08-01, undefinedki guide): in Materials/resource sections, the Chinese partner of a URL bullet is `https://... - 中文注释` — the gate sees `<br>- https://` and flags `Chinese side starts with a bullet marker after <br>`. This is the same Latin-starting case as the numbered/bullet strip above, so the unconditional `[-*]` pass handles it — no CJK-anchored regex. Note this happens even though the Chinese side starts with the URL itself (not a translation), because the `- ` list marker is what's flagged.
- **Bullet/numbered lists**: No repeated markers after `<br>`. `- EN<br>CN`, not `- EN<br>- CN`.
- **Code blocks**: Preserved as-is, single-language, no `<br>` partner. Do not add translated code fence.
- **`$` escaping**: Bare `$` → `\$` on both sides outside backticks — enforced by web mode and `--audit` only; the X-bilingual main gate skips the check (see §4).
- **Internal newlines**: Collapse embedded `\n` in fxtwitter text blocks before `<br>`.
- **Description**: Single line. Collapse `preview_text` newlines before writing.
- **CTA stripping**: Do not reinsert promotional copy just to satisfy source coverage. Build a `_nocta.json` and gate against that instead.
- **Duplicate key**: Exact canonical URL. Same author ≠ duplicate. Different status ID ≠ duplicate.
- **Parent verification**: After subagent batches, re-inspect first 20 lines for frontmatter drift (authors vs author, unquoted datetimes, type: "clipper" vs type: clipper, source mismatch).
- **Contraction drift**: When composing bilingual text from fxtwitter blocks, it's easy to write `you'll` when the source has `you`, or add a possessive `'s` that isn't there. The source coverage gate compares `block.text` byte-for-byte — always copy the exact text field for the English side. Never paraphrase, expand contractions, or "fix" grammar.
- **Truncating an English block's tail sentences fails material coverage — even when the tail looks like CTA** (learned 2026-08-04, nicholasdulait "Reddit SEO in 2026"): the X-Article material check scores per-block WORD OVERLAP (`sum(w in eblob) / len(words)`, min 0.92), not byte equality — so a block whose tail you trimmed (e.g. dropped `Search Engine Land reported in December 2025 that ranking for fan-out queries raised AI Overview citation odds by 161%.` or a `That's the part ChatSEO runs for me: ...` product sentence) still FAILS at 0.88/0.78/0.54 because the missing words drag the ratio under threshold. Two correct moves: (a) keep the FULL English block and translate the tail too (even a promo sentence — coverage requires it), or (b) if the WHOLE block is CTA, exclude it via `--skip-cta-regex`. What does NOT work: dropping just the tail. The `material source coverage missing N block(s): <score> <block-text>` message prints the score — use it to gauge how much of the block is missing. Also note an X Article with zero real media (only empty `atomic` separators) gates cleanly with `--expect-images 0`.
- **fxtwitter drops spaces at LINK-entity boundaries — merged tokens fail coverage even on faithful notes** (learned 2026-08-13, ericzakariasson "Grok 4.6 – A field guide" block 40): the raw JSON block text merges the words around an inline link into one token (`to work from.I asked ... gave itthe docs` — the space before/after the linked span is consumed). Re-spacing naturally on the EN side (`gave it the docs`) leaves the merged tokens (`itthe`) absent from the note → coverage 18/20 = 0.89 < 0.92 FAIL, and duplicating/rephrasing the EN sentence doesn't fix it either. Correct fix: reproduce the offending block's raw text VERBATIM on the EN side (`to work from.I asked ... gave itthe docs`) — `normalized in eblob` then matches and the block passes outright. Matching even one merged token verbatim suffices (19/20 = 0.95). Never lower `--min-word-coverage` for this. Longer blocks with the same artifact pass anyway (72-word block, 2 merged tokens = 0.97), so only short link-heavy blocks surface it. Full case: `interpreter-content-pipeline/references/fxtwitter-link-boundary-merged-tokens.md`.
- **SKIPPING whole blocks fails coverage even when they read as redundant** (learned 2026-08-05, beamnxw "Context vs. Memory Engineering" 105 blocks): I omitted the intro bullet list (blocks 6/7/8/9/10: "This article covers… / What context engineering involves…") as TLDR-ish summary, plus a lead-in sentence ("A MemoryEntry schema that encodes these concerns directly…") — all FAILED at 0.56-0.89. Every non-CTA block must appear: intro lists, transition sentences, blockquote lead-ins, even blocks that merely restate the TLDR. The `0.81`/`0.69` scores were whole-block omission, not tail-trim — the fix was inserting the verbatim block text at the right position, not touching the existing paraphrase. When repairing, grep the note for a distinctive phrase from the reported block to confirm it's truly absent (not just reworded) before editing.\n- **Mass-paraphrasing the English side of X Articles is the biggest repair time-sink** (learned 2026-08-04, a16z "Base Power" 94 blocks): condensing/smoothing the EN side of many blocks at once → 12-14 blocks fail coverage at 0.72-0.89, each needing a repair pass. Transcribe the EN side VERBATIM from the JSON block text; condense/smooth only on the CN side. See `references/gate-fail-recovery.md` for the 5 failure classes (markers after `<br>`, unconditional `——`, `===` divider blocks, truncated tails, mass paraphrase) and the head-char-match repair script that pulls original text from JSON and replaces condensed lines in bulk.\n- **Bare `===` divider blocks in X Articles must be included verbatim** (learned 2026-08-04, Alfred Lin "Speed Above All Else"): a source block that is just `===` fails coverage at 0.00 if skipped — include it as `===<br>===`.
- **Image-caption / label / beat-marker lines are coverage blocks too** (learned 2026-08-05, tetsuo "Grok Imagine" 141 blocks): visual tutorials interleave bare label lines between `atomic` image blocks — `OTIS:`, `ROMAN FORUM:`, `Beat 1.`, `Post Processing.` — and skipping them fails ~20 blocks at once (0.00-0.89). Every non-CTA block must appear, even pure labels (`OTIS:<br>OTIS：`). **URLs must stay on the EN side of `<br>`** — appending a URL after `<br>` (on the CN side) fails coverage because the EN side lacks it. Insertion-repair pattern (anchor-line EN-prefix match) and the label-class fix: `references/gate-fail-recovery.md` failure class 6.
- **Marker-cleanup regexes destroy the anchors you need for later insert-repair** (learned 2026-08-08, tetsuo "Grok Imagine" 141-block repair): running the `re.sub(r'<br>\s*#+\s+', '<br>', t)` / `\d+\.` / `[-*]` cleanup passes BEFORE inserting missing label/caption blocks strips the `## `/`1. `/`- ` prefix from the CHINESE side of every heading/list line — so a full-line anchor like `## Step 2: …<br>## 第二步` no longer exists and every insertion misses (`✗ no anchor` for all 20). Anchor insertions on the ENGLISH side prefix only: `en_part = line.split('<br>')[0]`, match `en_part.startswith(anchor_en)`, insert after the first match. Related: `--skip-cta-regex` patterns must match the failing CTA block's OPENING text — a pattern matching only a later substring (`AI newsletter` for a block starting `Every Wednesday, …`) leaves the block failing at 0.62 (Miles Deutscher 2026-08-08); add the block's distinctive lead-in (`Every Wednesday`) to the alternation.
- **References/works-cited tails with zero-width chars can never match coverage — skip the whole section** (learned 2026-08-05, Cerebras "How we built our knowledge base"): research articles end with a `References` heading followed by citation blocks (`Malkov and Yashunin, …`, `Anthropic, …`) whose text is interleaved with zero-width chars (U+200B/U+200C/U+200D/U+FEFF) that fxtwitter preserves — the source blocks literally cannot appear in the note no matter how verbatim you transcribe, and they pollute grep output with invisible garbage. Don't try to reproduce them; skip the whole references section with one `--skip-cta-regex` covering the citation lead-ins: `--skip-cta-regex "is hiring|Malkov|Anthropic|Cormack|Li et al|Liu et al|Salesforce|Improving Agents|Cursor,"`. Beware `Anthropic` also appears as a brand name in the body — keep the pattern anchored to citation forms so body coverage isn't affected. Related: the Authors block (block 0) of these posts often carries TWO lines — `Authors: @a, @b, @c` plus a `note: the interactive version of full technical blog available: <url>` line — transcribe both, not just the author handles.
- **Inline style formula corruption**: fxtwitter `inlineStyleRanges` can mark substrings inside formulas as italic/bold, turning `=A2*B2, =A3*B3` into broken `=A2*B2*, =*A3*B3`. After applying styles, compare source blocks against saved file for exact text preservation; remove stray emphasis markers inside formulas/code before confirming.
- **Bold markers causing mass coverage failures**: applying `**` from `inlineStyleRanges` to the English side breaks source coverage because the raw block text doesn't have them. Fix: strip all `**` from English side of `<br>` lines before gates. Apply bold/emphasis only on Chinese side.
- **Cross-language contamination**: After drafting translations manually or via fragments, scan for non-English/non-Chinese stray scripts (e.g., Cyrillic `посвящ`) indicating accidental language drift. Source coverage gates won't catch these.
- **Retroactive fixes**: When translation rules change (e.g., new forbidden-translation term), check whether existing files need retroactive patching. Use `gate.py --audit <vault>` for `<br>` format audits, and Python sed for terminology sweeps.
- **Design-constraint sweeps must grep code, not just prose** (learned 2026-08-01 during the fixed EN→ZH sweep): removing a parameter framework leaves residuals in three places prose-greps miss: (1) README/skill-table cells ("bilingual (EN/CN) or native-language Obsidian note" survived 3 doc revisions), (2) code identifiers (`--native-lang`, `DEFAULT_NATIVE_LANG`, `native_language` JSON key), (3) **half-migrated files** where the docstring was updated but the code wasn't (clip.py said `--lang` in its docstring while still exposing `--native-lang`). Sweep the literal identifier forms (`native-lang`, `native_lang`, `NATIVE_LANG`, `--lang`, old skill name) across ALL file types (.md AND .py/.sh) until zero hits. After the sweep, remaining `native` usages are CORRECT (Chinese-original note mode, gate.py detects `"<br>" not in text`) — do not re-clean them.
- **gate.py check ownership — never re-mix modes** (learned 2026-07 during 5→1 consolidation; each check belongs to specific modes and applying it elsewhere causes false positives):
  - X modes (bilingual X + native) own: UI/metric residue via `UI_RE`, Chinese em-dash drift, `published`/`created` format checks, source coverage vs fxtwitter JSON.
  - Web mode (`--source-text`) owns: word-level `Like`/`Sign up` residue via `UI_RESIDUE`, unescaped `$` check.
  - Native mode owns: local-only image validation (`assets/...`, no remote CDN), exact `source` URL match via `--source-url`, `summary` <250 chars.
  - `PROTECTED_TERM_RE` must stay the compact `智能体|提示词|资源` — adding `工具`/`代理`/`提示` breaks real notes because `tool` legitimately translates to 工具 and 提示 commonly means "remind".
- **Ghost script references (doc drift)**: This skill once cited 3 scripts that never existed (`manual-br-final-gate.py`, `fxtwitter-parse-script.py`, `audit-fix-bilingual-format.py`) — referencing a script by name does not create it. When a SKILL.md mentions a helper, verify the file actually exists in the pipeline skill's `scripts/`; when deleting a script, sweep SKILL.md for dangling references. Before claiming a referenced script is missing, grep the whole `~/.hermes` tree — it may live under a different skill.
- **Package drift after rename**: the skill was renamed `interpreter` → `clip-note` (2026-07, commit `3a07e5e`). Old names may still appear in: README tables, setup-guide paths, `related_skills` of other skills (e.g. `interpreter-content-pipeline`), and repo directory names. A rename is incomplete until a full-tree `grep -rn "oldname"` comes back clean (excluding the umbrella `interpreter-content-pipeline` and `interpreter-weekly-report` which legitimately keep their names).

## Scripts

- `scripts/clip.py` — dedup first (always) + fetch + language detection + image download + raw save; `--dedup-only` stops after the duplicate check (no fetch/save, exit 1 = exists / 0 = safe)
- `scripts/dedup.sh` — quick vault duplicate scan
- `scripts/verify_summary_chars.py` — batch-verify summary fields across the vault: **≤120 stripped chars (2026-08-08 导读 standard)**, no em-dash, no protected terms, no fixed openings, no paradigm labels (paragraph-break check removed 2026-08-08 — single-line summaries are normal at ≤120). Uses `yaml.safe_load` for accurate multi-line summary extraction. Use after any batch summary edit.
- `scripts/dump-native-body.py` — parameterized VERBATIM block dumper for Chinese-original X Articles: `python dump-native-body.py /tmp/x_<id>.json /tmp/cn_body.txt` (atomic blocks skipped; headers get `## `/`# `, blockquote `> `, list items plain — list numbers NOT required by the native gate). Note body must reproduce its output byte-for-byte to pass native coverage. Replaces the one-off hardcoded dump script that silently dumped the WRONG article when reused.
- Gate scripts (in `interpreter-content-pipeline`): `gate.py` (unified; auto-detects X-bilingual / web / native / structural modes), `save-x-article.py` (Chinese-original X save helper)
- `interpreter-content-pipeline/scripts/fxtwitter-parse.py` — full fxtwitter block dump + image resolution
- `interpreter-content-pipeline/scripts/gate.py --audit <vault>` — audit/fix `<br>` format across vault
- `references/gate-py-modes.md` — mode-detection table, per-mode check ownership, and the false-positive history behind each boundary (read before editing gate.py)
- `references/batch-summary-rewrite.md` — programmatic frontmatter update across many existing vault files: the yaml.safe_dump + quoting-fix script pattern, the validation checklist, the delegate_task fan-out pattern (3×15-16 files/round, pilot-first), and the iteration strategy for hitting ≤120 chars on dense articles (2026-08-08 导读 standard; <200-era notes kept as history)
- `references/gate-fail-recovery.md` — the 5 gate-fail classes for bilingual X Articles (markers after `<br>`, unconditional `——`, `===` dividers, truncated tails, mass paraphrase) + the head-char-match bulk repair script for already-condensed blocks
- `references/native-note-rebuild.md` — Chinese-original X Article rebuild: verbatim block-dump script pattern, native-mode gate rules (summary <250 RAW chars, protected-term check on summary, `related` required, `strip_md` asymmetry bug), and the native gate invocation

## Credits

By K L (@kevalin). Production-tested on 390+ articles. MIT license.
Distributed via [kevalin/oh-my-skills](https://github.com/kevalin/oh-my-skills) — publish new skills to `skills/<name>/` there.

**Portability status (2026-07-31)**: repo contains SKILL.md (agent-agnostic) + clip.py + dedup.sh + fxtwitter-parse.py + gate.py (unified) + save-x-article.py + setup-guide.md. A fresh user with any coding agent can run the full pipeline including Validate. External references (all optional): `humanizer` (open-source blader/humanizer). `proofreader` checklist is fully inlined in section 8. (renhua belongs to the Xiaohongshu pipeline, not Clip-note — removed 2026-07-31.) Script consolidation done 2026-07-31: 5 gate/audit scripts merged into one `gate.py`; `verify-chinese-x-article.py` → native mode; `audit-bilingual-format.py` → `--audit` mode; `save-x-article-from-fxtwitter.py` → `save-x-article.py`. 小而美.
