# oh-my-skills

A curated collection of reusable AI agent skills — production-tested, opinionated, and portable.

Built by [K L](https://github.com/kevalin). Works with any coding agent (Claude Code, Codex, OpenCode, Gemini CLI, Hermes Agent, etc.) — no platform-specific runtime required.

## Skills

| Skill | Description | Status |
|-------|-------------|--------|
| [interpreter](skills/interpreter/) | Turn any URL into a polished bilingual (EN/CN) or native-language Obsidian note. Language detection, translation, local images, duplicate detection, validation gates. | 🟢 Production (390+ notes archived) |

## Quick Start

### 1. Install a skill

Copy the skill directory into your agent's skills folder, or reference it in-place:

```bash
# Claude Code / Codex / OpenCode style
mkdir -p ~/.claude/skills/
cp -r skills/interpreter ~/.claude/skills/

# Hermes Agent
mkdir -p ~/.hermes/skills/content/
cp -r skills/interpreter ~/.hermes/skills/content/
```

### 2. Configure

Tell your agent your native language and vault path once:

```
My native language is zh.
My Obsidian vault is at ~/Documents/obsidian/Notes.
```

### 3. Use it

```
clip https://example.com/article
```

That's it. The agent fetches, detects language, translates only when needed, downloads images, and saves a polished markdown note.

## How It Works

The `interpreter` skill is a two-layer system:

1. **`scripts/`** — deterministic core (pure Python/shell): fetch (Jina Reader → raw HTML fallback), duplicate detection, language detection (CJK ratio), image download, fxtwitter X Article parsing, and 4 validation gates. Same input always produces the same verdict.
2. **Agent pipeline** — the intelligent layer: `<br>` bilingual formatting, protected terminology (agent/MCP/tool/prompt stay English), AI-ism stripping, CTA removal, YAML frontmatter per Obsidian Clipper spec, relationship layer, proofreading checklist, and validation gates.

The full 11-step pipeline is documented in [SKILL.md](skills/interpreter/SKILL.md).

## Philosophy

- **One URL in, one polished note out.** No configuration ceremony.
- **English side stays pure.** Source text is preserved byte-for-byte for verification; all enrichment lives on the Chinese side.
- **Native language first.** If the source is already in your language, it saves directly — no wasteful translation pass.
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
