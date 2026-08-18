# Setup Guide — clip-note

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
cp -r clip-note ~/.hermes/skills/content/
```

Verify:

```bash
ls ~/.hermes/skills/content/clip-note/
# SKILL.md  scripts/  references/
```

## Step 3: Install dependency

```bash
pip install requests
```

## Step 4: Configure

Tell Hermes your Obsidian vault path:

```
My Obsidian vault is at ~/Documents/obsidian/Notes.
```

Or pass it each time:

```
clip <url> --vault ~/Documents/obsidian/Notes
```

## Step 5: Test

```bash
clip https://paulgraham.com/greatwork.html
```

The agent checks for duplicates first — if the URL is already in your vault, it
reports the existing filename and stops (no fetch, no translation). Only new
URLs proceed to fetching:

```bash
📥 Fetching https://paulgraham.com/greatwork.html ...
   Title: How to Do Great Work
   Images: 0
   Source language: en | Translate: True

✅ Note saved: ~/.../How to Do Great Work.md
```

You can also run the dedup check standalone (no fetch/save):

```bash
python scripts/clip.py <url> --dedup-only
```

If the source is already Chinese:

```
   Source language: zh | Translate: False
```

→ Agent saves directly, no translation pass.

## Language handling

Fixed EN→ZH: English articles are translated to Chinese; Chinese articles are saved as-is (no translation, no language-parameter flags).

## Proxy

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

## Uninstall

```bash
rm -rf ~/.hermes/skills/content/clip-note
```

Your notes stay in your vault.
