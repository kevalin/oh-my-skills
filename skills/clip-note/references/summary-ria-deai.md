# Summary style — 导读 (≤120 chars) + RIA 干货式 + 去 AI 味

User mandate history: summaries are **导读** (a teaser that decides whether to open the note),
NOT a replacement for reading the article. Length standard tightened twice in one day (2026-08-08):
**<200 → ≤120 stripped chars** (user: "导读设置为120字以内"). The four-step compression
methodology below is the user's own framework (provided 2026-08-08) and produces the ≤120 cap
reliably — even 505-char tutorials compress to ~104.

## The acceptance criteria (user's accumulated words)

1. **导读定位 (2026-08-08)**: summary sells the note — reader decides in 3 seconds whether to open it. Not a condensed version of the article; missing detail is FINE as long as the core claim lands.
2. **≤120 字 (2026-08-08)** — count with `len(re.sub(r'\s','',s))`; punctuation AND Latin tokens count (nvidia-smi = 10 chars). Hard cap; the old gate <250 / <200 limits are superseded by this writing standard.
3. 结构式思维和表达 — a knowledge card, not a dense paragraph (2026-08-02).
4. **去掉「读完最值得记住的一句」开头** (2026-08-04) — no fixed opening phrase.
5. **格式化的范式不用增加这些词汇（核心/拆解/行动等标签）在内容上区分并合适的换行即可** (2026-08-04) — NO paradigm label words; distinguish parts by content + line breaks only.

## Four-step compression methodology (user's, 2026-08-08)

1. **抓主旨 (Main Idea)** — one sentence: "这篇文章最想告诉我什么？" Decide this BEFORE writing; it sets the direction.
2. **提骨架 (Key Points)** — the 2-3 points that support the thesis (≤4 max). Test: delete the point → does the thesis still stand? If not, it's key.
3. **筛血肉 (Evidence & Detail)** — keep only data/examples/comparisons that matter; drop background, repeated argument, emotional filler.
4. **重组表达 (Rewrite)** — re-organize in your own words, not stitched source sentences. Structure: **结论 → 关键支撑 → （可选）影响/评价**.

At ≤120 chars the budget fits: **主旨 + 2 骨架点 + 1 句证据或判断**. Cut order when space is tight:
- FIRST cut background / process-description (e.g. "OpenAI 砸 40 亿", "三层结构：接数据→翻译→进工作流") — the thesis survives without them
- Keep the article's **most distinctive claim** (e.g. Palantir 的「最难建模的是动词」) over generic context
- Prefer **noun-evidence** (医院/水厂案例 — 8 chars) over raw numbers (83%/20%/$30万) — names carry more signal per char
- If it STILL can't fit 120 without losing the core claim: keep the core claim, drop the evidence — 导读 only needs to sell the note

## Canonical worked examples (FINAL accepted 导读 versions, 2026-08-08)

**NOTE — 导读 vs 总结 trap:** an earlier pass produced 112/104/118/112-char versions (below, marked REJECTED) that were structurally **总结** — they packed 主旨+骨架+证据 and read as condensed articles. User rejected them: "我再次强调是导读，不是总结". The ACCEPTED versions are shorter AND differently shaped: **钩子/反常识点 first, one method/value sentence, optional evaluation closer (值得读/值得关注)** — they sell the note, they don't summarize it. When in doubt, ask: "does this make the reader want to open the note, or does it replace reading it?"

**Palantir FDE (accepted, 92):**
```
数据库里没有一家公司：调货该谁批、哪个仓不能动，这些知识只活在员工脑中。Palantir 用 Ontology + FDE 驻场把它变成模型能安全执行的系统。想做 FDE 或 AI 进企业，这篇值得读。
```
Hook = 反常识 claim (数据库里没有一家公司) → method (Ontology+FDE 显式化) → evaluation closer (值得读).

**Grok Imagine tutorial (accepted, 76):**
```
用一句话点子做出成片：四个 Grok skills 组成完整流水线。最值钱的是铁律：视频模型零记忆，角色卡防漂移、prompt 封死上下文，照做就能跨镜头一致。
```
Hook = 一句话点子到成片 → the one distinctive rule (零记忆铁律) → implicit promise (照做就能一致).

**Base Power (accepted, 61):**
```
发电成本崩盘了，电价却涨得比通胀快两倍：瓶颈全在输电。a16z 这篇讲电网为什么难改，以及 AI 调度为什么可能是最便宜的解法。
```
**Palette (accepted, 66):**
```
AI 视频终于可以逐对象修改：Palette 用自然语言改视频里的每个元素，而不是整段重生成。创始人是 MIT 艺术项目出身，方向值得关注。
```

### REJECTED 总结-style versions (do NOT reproduce — for contrast only)

**Palantir FDE (rejected, 112):** `AI 进企业最难的不是模型，是把数据、规则、权力变成可安全执行的系统。Palantir 的解法：Ontology + FDE 驻场，把隐性知识显式化；最难建模的是动词，每个动作带审批边界。从可衡量的决策闭环起步，医院与水厂案例已验证。` — reads as a compressed article (thesis + 2 skeleton points + evidence); no hook, no closer. **Grok (rejected, 104):** `Grok Imagine 做短片流水线：点子 → 分镜剧本 → 参考资产 → 逐 beat 生成 → 剪辑。铁律：视频模型零记忆，用三视图角色卡（浅灰背景防漂移）+ 密封 prompt（封死上下文）强制一致性，STATE 笔记跨镜传状态。` — dumps the whole pipeline; the accepted version keeps only the hook + the one rule. **Base Power (rejected, 118) / Palette (rejected, 112):** same pattern — full thesis+evidence, no 钩子.

Compression notes carried over from the four-step method: for tutorials the pipeline IS the 主旨 but at 导读 size only the single most distinctive rule survives; cut background/process-description (40 亿、三层结构、创始人背景) FIRST; noun-evidence (医院/水厂案例) only if space allows.

## Canonical older example ("Don't be a meat proxy", 2026-08-04, 157 chars — pre-120 standard)

```
别把 AI 输出原样转发，对方自己能聊，还更快、更能控上下文。

AI 回复啰嗦、常带貌似合理的胡话、术语密集；读懂、验证、用自己的话重写，才是你加的价值。

代码评审最典型：复制粘贴 ticket 和 reviewer 反馈，实现者其实是 reviewer + Claude Code，你只是肉代理。

该用 AI 就用，但回复前先过自己的脑子和手。
```

Four short paragraphs separated by `\n\n` inside the YAML summary field. RIA structure present in content with NO labels: conclusion first → 拆解 (concepts) → 落地行动 last. (At the ≤120 standard this compresses to 3 paragraphs — drop one 拆解 paragraph, keep conclusion + action.)

## Why earlier drafts were rejected (full iteration log)

1. **386 chars, rigid labels** (`**核心结论**：… **R**：… **I 工具卡片**：…`) — too long AND sounded templated. (Google Agent Skills, 2026-08-02)
2. **233 chars, rigid labels** — passed length, but labels were AI-ish scaffolding; user asked for de-AI'd smooth 表达. (2026-08-02)
3. **249 chars, natural connectors** (`读完最值得记住的一句 / 一句话理解 / 想落地就做三件事`) — accepted that day, BUT later rejected: "去掉'读完最值得记住的一句'开头" + "格式化的范式不用增加这些词汇" (2026-08-04)
4. **186 chars, bold labels inline** (`**核心**：… **拆解**：… **行动**：…`) — label words still present; rejected. (2026-08-04)
5. **157 chars, no labels, content-distinguished paragraphs** — accepted. (2026-08-04)
6. **147→112 chars (2026-08-08)** — user tightened 150→120; the 112-char version (Palantir) accepted.

## Rules distilled

- **NO paradigm label words**: no `**核心**`/`**拆解**`/`**行动**`/`R`/`I`/`A` tags anywhere — distinguish parts BY CONTENT and separate them with `\n\n` line breaks (2-4 short paragraphs).
- **No fixed opening phrase**: no 「读完最值得记住的一句」 or similar conversational opener. Start directly with the conclusion.
- **Bold only for key terms** worth emphasizing (optional), never for paradigm labels.
- **No AI-isms**: 值得注意的是 / 总而言之 / 赋能 / 抓手 / 沉淀 / 闭环 / 在这个快速发展的时代 — banned.
- **Gate constraints inside the summary**: no `——`, no protected terms (智能体/提示词/资源). Gate scans the WHOLE file including frontmatter — a `——` in summary = FAIL. **The `——` check bites summaries hard at ≤120 chars because every cut pass rewrites the field — re-grep `——` after every rewrite** (hit twice 2026-08-08: Base Power + Palette).
- **Newlines inside the YAML field are fine** (gate counts stripped chars; yaml dump handles multiline).
- **Length budget**: draft directly at 100-115 stripped chars (≤120) in ONE pass — do NOT draft at 200+ and trim down; each trim pass is a full gate cycle and the tool-loop detector fires on repeated FAILs. Compress in ONE command that prints the stripped len and rewrites the field.
- **Apply to BOTH bilingual and native notes.**
- After a rewrite, re-run the gate (`--json`/`--source-text` unchanged) — frontmatter re-dump can introduce quoting drift (`type: "clipper"` → unquote) or date format changes.

## Batch summary rewrite (multiple files at once)

When the user asks to rewrite summaries across many notes (e.g. "以最新一个md文件为例" then "导读设置为120字以内" — a new standard applied to existing notes):

1. **Read all files first** (batch `read_file` calls) to understand content before writing any. For long notes, read past the truncation point — the tail carries the conclusion/action.
2. **Aim 100-115 stripped chars on the FIRST draft** — the ≤120 budget is tight; 主旨 + 2 骨架点 + 1 句证据/判断 only. Writing 250+ char drafts and iteratively trimming wastes 3-4 rounds.
3. **YAML round-trip quoting fix** — `yaml.safe_dump` quotes scalars and dates that should be unquoted/quoted differently. After dumping, normalize with regex:
   ```python
   new_fm = re.sub(r"type: 'clipper'", 'type: clipper', new_fm)
   new_fm = re.sub(r"published: '(\d{4}-\d{2}-\d{2})'", r'published: \1', new_fm)
   new_fm = re.sub(r"created: '([^']+)'", r'created: "\1"', new_fm)
   new_fm = re.sub(r"source: '([^']+)'", r'source: "\1"', new_fm)
   ```
   Without these, the gate will flag `type: 'clipper'` (should be unquoted) and datetime formats.
4. **Verify with `scripts/verify_summary_chars.py`** — run after all writes to check the ≤120 limit, no em-dash, no protected terms, no fixed openings, no paradigm labels across the whole vault or a glob.
   ```bash
   python3 ~/.hermes/skills/content/clip-note/scripts/verify_summary_chars.py --file "The*"
   ```
5. **Char-count reality check:** English terms count per-letter (`nvidia-smi`, `dynamic workflows`, `localhost` are 10-15 chars each), so hand-estimates run 15-40% LOW. Draft at 100-115 and expect 1-2 trims on a batch. Cut middle-paragraph detail first; never the conclusion.

## Verification script

`scripts/verify_summary_chars.py` — scans vault `.md` files, checks each summary for: ≤120 stripped chars, no `——`, no protected terms, no fixed openings, no paradigm labels. Pass `--file "glob"` to narrow scope. Use after any batch summary edit.
