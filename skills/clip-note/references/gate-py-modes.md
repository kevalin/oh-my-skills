# gate.py consolidated behavior (2026-07-31; summary limit updated 2026-08-04)

The 5 gate/audit scripts (`batch-x-article-final-gate.py`,
`manual-web-article-final-gate.py`, `manual-bilingual-final-check.py`,
`verify-chinese-x-article.py`, `audit-bilingual-format.py`) were merged into a
single `gate.py` with **auto-detected modes**. This file documents what each
mode checks so future edits don't re-introduce false positives.

## Mode detection

| Mode | Trigger |
|------|---------|
| **native** (Chinese-original X) | `--json` given AND note body has NO `<br>` |
| **bilingual X** | `--json` given AND note has `<br>` |
| **web** | `--source-text` given (no `--json`) |
| **structural-only** | `--file` alone |
| **audit** | `--audit <vault>` (vault-wide `<br>` scan; `--fix` collapses `<br><br>`, `--only-br` skips `$`/em-dash checks) |

**Native-mode detection is a whole-text `<br>` scan, not just the body**: any
`<br>` anywhere in the file — including a `<br>` bilingual relationship layer
(`## Internal Links<br>内部链接`) — flips a Chinese-original note into
bilingual-X mode and fails every structural check (H1 lacks `<br>`, orphan
lines, missing `<br>` everywhere). Native notes must stay 100% `<br>`-free:
monolingual relationship sections, no `image:` alt tricks. (Hit 2026-07 on the
Graph engineering 中文教程 note.)

## Check ownership (do not re-mix)

| Check | Owned by |
|-------|----------|
| `UI_RE` (standalone metric lines: Reposts/Likes/Bookmarks, Log in/Sign up) | X modes only |
| `UI_RESIDUE` word list (`Like`, `Sign up`, `Subscribe now`, ...) | web mode only |
| Chinese em-dash drift (`——`) | X modes only |
| `published`/`created` format (date-only, quoted datetime) | X modes only |
| Local-only images (`assets/...`, no remote CDN) | native mode only |
| Exact `source` URL match (`--source-url`) | native mode only |
| `summary` <200 chars | native mode only |
| Unescaped `$` on English side | web mode only |
| Orphan non-`<br>` lines, `<br>` structure, H1 bilingual, code fences | all bilingual modes |
| `PROTECTED_TERM_RE` = `智能体|提示词|资源` | all modes (compact ONLY) |

## Why these boundaries exist (failure history)

1. **Broad protected-term regex broke real notes**: `智能体|代理|工具|提示|资源`
   flagged `工具` — but `tool` legitimately translates to 工具, and 提示 often
   means "remind" not "prompt". The compact `智能体|提示词|资源` (from the
   original batch gate) is the only safe version.
2. **`Like` word check is web-only**: in narrative text "Like" is a common
   English word. The original web gate listed it; the X gate used the stricter
   `UI_RE` standalone-line pattern. Merging made bilingual-X notes fail on
   prose containing "like".
3. **em-dash check is X-only**: web articles legitimately contain `——` in
   translated Chinese (source had ` - ` pause). Original batch gate checked it;
   original web gate did not.
4. **Image localization is native-only**: bilingual X notes keep remote
   `pbs.twimg.com` URLs (cover/figures not localized in that flow); only
   Chinese-original notes require local `assets/` paths.
5. **`published` format check is X-only**: older web notes carry quoted
   `published: "2026-07-31"` and pass the web gate; X batch gate enforced
   date-only. Applying it to web mode fails historic notes.

## Verification recipe (used at consolidation time)

```bash
GATE=~/.hermes/skills/content/interpreter-content-pipeline/scripts/gate.py
V=~/Documents/obsidian/Interpreter

# web bilingual (expect PASS)
python $GATE --file "$V/Graph Engineering build 1000+ agent loops in one window, from one prompt (full 5-step course).md"

# bilingual X (expect PASS; JSON from fxtwitter)
python $GATE --file "$V/Lessons from Building Claude Code How We Use Skills.md" --json /tmp/x_2033949937936085378.json

# native Chinese-original (expect PASS; --expect-images must match real count)
python $GATE --file "$V/YC 的 AI 最新风向标，所有想做 OPC 的人都值得一读.md" \
  --json /tmp/x_2080442267618476409.json \
  --source-url "https://x.com/elliotchen100/status/2080442267618476409" --expect-images 3

# audit (reports historic violations in old notes — expected, not a script bug)
python $GATE --audit "$V" --only-br
```

## Note: old verify-chinese vs new gate.py native coverage

The old `verify-chinese-x-article.py` used `visible_text()` which stripped ALL
`*`/`-`/`#` chars (including hyphens inside prose), causing false "missing
non-CTA source blocks" on long sentences. New `strip_md()` only strips paired
markdown markers — a correctness improvement, not a regression.