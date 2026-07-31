# Setup Guide — Interpreter

Detailed step-by-step for first-time setup.

## Requirements

| Component | Minimum | Check |
|-----------|---------|-------|
| Python | 3.10+ | `python3 --version` |
| requests | Latest | `pip install requests` |
| ripgrep | (optional) | `rg --version` |
| Obsidian | Any version | Just a vault directory |

No agent-specific runtime is required — this skill works with any coding agent
(Claude Code, Codex, OpenCode, Gemini CLI, Hermes, etc.). The agent reads
`SKILL.md` as its runbook; the scripts are plain Python/shell.

## Step 1: Locate your Obsidian vault

```bash
# Common locations
~/Documents/obsidian/MyVault      # macOS/Linux
~/Documents/Obsidian/MyVault       # Linux (capital O)
/mnt/c/Users/You/Documents/...     # Windows WSL
```

## Step 2: Install the skill

Copy the whole `interpreter/` directory into your agent's skills folder, or
reference it in-place:

```bash
# Example: Claude Code / Codex skills directory
mkdir -p ~/.claude/skills/
cp -r interpreter ~/.claude/skills/

# Or keep it anywhere and point your agent at the SKILL.md path
```

Verify:

```bash
ls interpreter/
# SKILL.md  scripts/  references/
```

## Step 3: Install dependency

```bash
pip install requests
```

## Step 4: Configure

Tell your agent your settings (or set them in your agent's config):

```
My native language is zh.
My Obsidian vault is at ~/Documents/obsidian/Notes.
```

If you're behind a proxy (common in CN networks), export it:

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

## Step 5: Test

Ask your agent to clip a page:

```
clip https://paulgraham.com/greatwork.html
```

Expected output: `How to Do Great Work.md ✅`

If the source is already in your native language, the agent saves directly with
no translation pass.

## Language detection

The scripts distinguish Chinese vs English by CJK character ratio (>30% =
Chinese). For other languages (Japanese, Korean, etc.), set `--native-lang`
explicitly to avoid misclassification.

## Filename rule

Files are saved flat at `<vault>/<Title>.md`. The filename is the **English
side** of the title (Chinese side stripped), slugged for filesystem safety.
See `SKILL.md` section 10 for the exact rule.

## Validation

After saving, run the gate scripts in `scripts/` (see SKILL.md section 9).
They are deterministic — any agent gets the same PASS/FAIL verdict.

## Uninstall

```bash
rm -rf ~/.claude/skills/interpreter
```

Your notes stay in your vault.
