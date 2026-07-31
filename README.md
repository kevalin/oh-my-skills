# oh-my-skills

A curated collection of reusable AI agent skills — production-tested, opinionated, and portable.

Built by [K L](https://github.com/kevalin) for use with [Hermes Agent](https://hermes-agent.nousresearch.com/docs).

## Skills

| Skill | Description | Status |
|-------|-------------|--------|
| [interpreter](skills/interpreter/) | Turn any URL into a polished bilingual (EN/CN) or native-language Obsidian note. Language detection, translation, local images, duplicate detection, validation gates. | 🟢 Production (390+ notes archived) |

## Quick Start

### 1. Install a skill

```bash
mkdir -p ~/.hermes/skills/content/
cp -r skills/interpreter ~/.hermes/skills/content/
```

### 2. Configure

Tell Hermes your native language and vault path once:

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

1. **`clip.py`** — deterministic core: fetch (Jina Reader → raw HTML fallback), duplicate detection, language detection (CJK ratio), image download, raw note generation.
2. **Agent pipeline** — the intelligent layer: `<br>` bilingual formatting, protected terminology (agent/MCP/tool/prompt stay English), AI-ism stripping, CTA removal, YAML frontmatter per Obsidian Clipper spec, relationship layer, proofreading checklist, and validation gates.

The full 11-step pipeline is documented in [SKILL.md](skills/interpreter/SKILL.md).

## Philosophy

- **One URL in, one polished note out.** No configuration ceremony.
- **English side stays pure.** Source text is preserved byte-for-byte for verification; all enrichment lives on the Chinese side.
- **Native language first.** If the source is already in your language, it saves directly — no wasteful translation pass.
- **Gates over vibes.** Every note passes structural + terminology validation before confirmation.

## Requirements

- [Hermes Agent](https://hermes-agent.nousresearch.com/docs)
- Python 3.10+
- `requests` (`pip install requests`)
- `ripgrep` (optional, for fast duplicate detection)
- Obsidian (any version — it's just a vault directory)

## License

MIT
