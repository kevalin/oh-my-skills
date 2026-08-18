# oh-my-skills

A curated collection of reusable AI agent skills — production-tested, opinionated, and portable.

Built by [K L](https://github.com/kevalin). Works with any coding agent (Claude Code, Codex, OpenCode, Gemini CLI, Hermes Agent, etc.) — no platform-specific runtime required.

## Skills

| Skill | Description | Status |
|-------|-------------|--------|
| [clip-note](skills/clip-note/) | Turn any URL into a polished bilingual (EN/CN) Obsidian note. Fixed EN→ZH: English articles translate to Chinese, Chinese articles save as-is. Local images, duplicate detection, validation gates. | 🟢 Production (390+ notes archived) |
| [crap-design](skills/crap-design/) | Universal CRAP design rules from "The Non-Designer's Design Book" (Robin Williams) — Contrast, Repetition, Alignment, Proximity plus type and color laws, with validation checklists for any layout, typography, color, or cover design. Includes real violation-fix cases. | 🟢 Production |
| [storm-research](skills/storm-research/) | AI-assisted multi-perspective deep research (STORM): pin the question, parallel perspective research, cross-validation, contradiction map, verdict-first synthesis with evidence labels, and peer review. Covers deep research reports, business feasibility, website teardowns, company due diligence, and article/paper briefings. | 🟢 Production |

## Quick Start

### 1. Install a skill

Copy the skill directory into your agent's skills folder, or reference it in-place:

```bash
# Claude Code / Codex / OpenCode style
mkdir -p ~/.claude/skills/
cp -r skills/clip-note ~/.claude/skills/

# Hermes Agent
mkdir -p ~/.hermes/skills/content/
cp -r skills/clip-note ~/.hermes/skills/content/
```

### 2. Configure

Tell your agent your Obsidian vault path once:

```
My Obsidian vault is at ~/Documents/obsidian/Notes.
```

### 3. Use it

```
clip https://example.com/article
```

That's it. The agent fetches, translates English articles to Chinese, downloads images, and saves a polished markdown note.

## How It Works

The `clip-note` skill is a two-layer system:

1. **`scripts/`** — deterministic core (pure Python/shell): fetch (Jina Reader → raw HTML fallback), duplicate detection, language detection (CJK ratio), image download, fxtwitter X Article parsing, and 4 validation gates. Same input always produces the same verdict.
2. **Agent pipeline** — the intelligent layer: `<br>` bilingual formatting, protected terminology (agent/MCP/tool/prompt stay English), AI-ism stripping, CTA removal, YAML frontmatter per Obsidian Clipper spec, relationship layer, proofreading checklist, and validation gates.

The full 11-step pipeline is documented in [SKILL.md](skills/clip-note/SKILL.md).

## Philosophy

- **One URL in, one polished note out.** No configuration ceremony.
- **English side stays pure.** Source text is preserved byte-for-byte for verification; all enrichment lives on the Chinese side.
- **Fixed EN→ZH.** English articles translate to Chinese; Chinese articles save as-is — no wasteful translation pass.
- **Gates over vibes.** Every note passes structural + terminology validation before confirmation.
- **Deterministic validation.** The gate scripts are agent-agnostic: any agent running them gets identical PASS/FAIL verdicts.

## Requirements

- Any coding agent with shell access (Claude Code, Codex, OpenCode, Gemini CLI, Hermes, etc.)
- Python 3.10+
- `requests` (`pip install requests`)
- `ripgrep` (optional, for fast duplicate detection)
- Obsidian (any version — it's just a vault directory)

## License

MIT
