# Setup Guide — Interpreter

Detailed step-by-step for first-time setup.

## Requirements

| Component | Minimum | Check |
|-----------|---------|-------|
| Hermes Agent | Latest | `hermes --version` |
| Python | 3.10+ | `python3 --version` |
| requests | Latest | `pip install requests` |
| ripgrep | (optional) | `rg --version` |
| Obsidian | Any version | Just a vault directory |

## Step 1: Locate your Obsidian vault

```bash
# Common locations
~/Documents/obsidian/MyVault      # macOS/Linux
~/Documents/Obsidian/MyVault       # Linux (capital O)
/mnt/c/Users/You/Documents/...     # Windows WSL
```

## Step 2: Install the skill

```bash
mkdir -p ~/.hermes/skills/content/
cp -r interpreter ~/.hermes/skills/content/
```

Verify:

```bash
ls ~/.hermes/skills/content/interpreter/
# SKILL.md  scripts/  references/
```

## Step 3: Install dependency

```bash
pip install requests
```

## Step 4: Configure

Tell Hermes your settings:

```
My native language is zh.
My Obsidian vault is at ~/Documents/obsidian/Notes.
```

Or pass flags each time:

```
clip <url> --native-lang zh --vault ~/Documents/obsidian/Notes
```

## Step 5: Test

```
clip https://paulgraham.com/greatwork.html
```

Output:

```
📥 Fetching https://paulgraham.com/greatwork.html ...
   Title: How to Do Great Work
   Images: 0
   Source language: en | Native: zh | Translate: True

✅ Note saved: ~/.../How to Do Great Work/How to Do Great Work.md
```

If the source is already in your native language:

```
   Source language: zh | Native: zh | Translate: False
```

→ Agent saves directly, no translation pass.

## Language detection

The script distinguishes Chinese vs English by CJK character ratio (>30% = Chinese). For other languages (Japanese, Korean, etc.), set `--native-lang` explicitly to avoid misclassification.

## Proxy

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

## Uninstall

```bash
rm -rf ~/.hermes/skills/content/interpreter
```

Your notes stay in your vault.
