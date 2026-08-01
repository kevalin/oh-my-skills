#!/usr/bin/env python3
"""
Obsidian Web Clipper — clip any web article into a bilingual Obsidian note.

Usage:
  python clip.py <url> [--vault ~/Documents/obsidian/MyVault] [--dedup-only]

Converts a web article or X/Twitter post into a bilingual (EN/CN) Obsidian note
with YAML frontmatter, local images, and duplicate detection.
Fixed EN→ZH: English articles translate to Chinese; Chinese articles save as-is.
Dedup always runs first; --dedup-only stops after the check (no fetch/save).
"""

import argparse
import hashlib
import os
import re
import sys
import json
import time
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta


# ── Config ──────────────────────────────────────────────────────
DEFAULT_VAULT = os.path.expanduser("~/Documents/obsidian/Interpreter")
TARGET_LANG = "zh"  # fixed: English → Chinese; Chinese saved as-is
ASSETS_DIR = "assets"

TZ = timezone(timedelta(hours=8))

# ── Helpers ─────────────────────────────────────────────────────

def slugify(text, max_len=80):
    """Turn a title into a filename-safe slug (English side only)."""
    # Strip Chinese side: keep text before <br> or ' - ' (when right side has CJK)
    cn = re.compile(r'[\u4e00-\u9fff]')
    if '<br>' in text:
        text = text.split('<br>')[0]
    elif ' - ' in text:
        left, right = text.split(' - ', 1)
        if cn.search(right):
            text = left
    text = re.sub(r'[<>:"/\\|?*]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip().rstrip('. ')
    if len(text) > max_len:
        text = text[:max_len].rsplit(' ', 1)[0]
    return text


def find_duplicate(vault_dir, source_url):
    """Check if a note with this source URL already exists in the vault."""
    import subprocess
    try:
        result = subprocess.run(
            ['rg', '-l', '--fixed-strings', source_url, str(vault_dir)],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: slow grep
        matches = []
        for md in vault_dir.glob("*.md"):
            try:
                content = md.read_text(encoding='utf-8', errors='ignore')
                if source_url in content:
                    matches.append(str(md))
            except Exception:
                pass
        return matches


def fetch_content(url):
    """Fetch and extract article content. Returns dict with title, text, images, source_type."""
    import requests

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
    }

    # Try Jina Reader first (good for most web articles)
    jina_url = f"https://r.jina.ai/{url}"
    try:
        r = requests.get(jina_url, headers={**headers, 'Accept': 'text/markdown'}, timeout=30)
        if r.status_code == 200 and len(r.text) > 200:
            # Parse title from first line, strip "Title: " prefix from Jina
            lines = r.text.strip().split('\n')
            title = lines[0].lstrip('#').strip()
            title = re.sub(r'^Title:\s*', '', title).strip()
            if not title:
                title = "Untitled"
            # Collect image URLs
            images = re.findall(r'!\[.*?\]\((https?://[^\)]+)\)', r.text)
            return {
                'title': title,
                'text': r.text,
                'source_type': 'web',
                'images': list(set(images)),
                'canonical_url': url,
            }
    except Exception:
        pass

    # Fallback: raw fetch + basic extraction
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.title = ""
                self.in_title = False
                self.skip = False
                self.images = []
            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == 'title':
                    self.in_title = True
                if tag in ('script', 'style', 'nav', 'footer'):
                    self.skip = True
                if tag == 'img' and 'src' in attrs_dict:
                    src = attrs_dict['src']
                    if src.startswith('http'):
                        self.images.append(src)
                if tag == 'meta' and attrs_dict.get('property') == 'og:title':
                    self.title = attrs_dict.get('content', '')
            def handle_endtag(self, tag):
                if tag == 'title':
                    self.in_title = False
                if tag in ('script', 'style', 'nav', 'footer'):
                    self.skip = False
            def handle_data(self, data):
                if self.in_title and not self.title:
                    self.title = data.strip()
                if not self.skip:
                    text = data.strip()
                    if text:
                        self.text.append(text)

        extractor = TextExtractor()
        extractor.feed(r.text)
        title = extractor.title or url.split('/')[-1] or "Untitled"
        return {
            'title': title,
            'text': '\n\n'.join(extractor.text),
            'source_type': 'web',
            'images': list(set(extractor.images)),
            'canonical_url': url,
        }
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}")


def download_images(images, asset_dir):
    """Download images to local asset directory, return mapping of URL → local path."""
    import requests
    mapping = {}
    asset_path = Path(asset_dir)
    asset_path.mkdir(parents=True, exist_ok=True)

    for i, img_url in enumerate(images):
        try:
            r = requests.get(img_url, timeout=15)
            if r.status_code == 200:
                ext = img_url.rsplit('.', 1)[-1].split('?')[0]
                if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
                    ext = 'jpg'
                filename = f"clip-{i:03d}.{ext}"
                filepath = asset_path / filename
                filepath.write_bytes(r.content)
                mapping[img_url] = f"{ASSETS_DIR}/{filename}"
        except Exception:
            continue

    return mapping


def detect_language(text, sample_size=2000):
    """Detect if text is primarily Chinese. Returns 'zh' or 'en'."""
    sample = text[:sample_size]
    cjk_count = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', sample))
    total_chars = len(re.sub(r'\s', '', sample))
    if total_chars == 0:
        return 'en'
    return 'zh' if cjk_count / total_chars > 0.3 else 'en'


def format_note(title, source_text, source_url, author, published_date, image_mapping, source_type, description=""):
    """Format the note as bilingual Obsidian markdown (EN/CN <br> on same line)."""
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S %z")

    # Clean source text
    text = source_text

    # Clean Jina Reader boilerplate
    text = re.sub(r'(?im)^URL Source:.*\n?', '', text)
    text = re.sub(r'(?im)^Markdown Content:\n?', '', text)
    text = re.sub(r'(?im)^Published Date:.*\n?', '', text)
    text = re.sub(r'(?im)^Content:\n?', '', text)
    # Strip bare "Title: ..." line Jina inserts after heading
    text = re.sub(r'(?im)^Title:.*\n?', '', text)
    # Strip Jina AI disclosure/footer lines
    text = re.sub(r'(?im)^>.*?is a free online tool.*\n?', '', text)
    text = re.sub(r'(?im)^>.*?Jina AI.*\n?', '', text)

    # Remove Markdown title (first # line) — we use our own
    text = re.sub(r'^#\s+.*\n', '', text)

    # Replace remote image URLs with local paths
    for remote, local in image_mapping.items():
        text = text.replace(remote, local)
        # Also handle markdown image syntax
        text = text.replace(f']({remote})', f']({local})')

    # Strip very long runs of whitespace
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    # Basic formatting: each paragraph gets EN on one line (translation will be added by LLM)
    # For now, output the raw English text — the agent adds translations
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Build body — raw English, agent will translate inline
    body_lines = []
    for p in paragraphs[:50]:  # cap at 50 paragraphs
        # Skip very short lines (likely UI residue)
        if len(p) < 3:
            continue
        body_lines.append(p)

    body = '\n\n'.join(body_lines)

    # Summary (first 200 chars of body, Chinese will be filled by agent)
    summary = paragraphs[0][:200] if paragraphs else ""

    frontmatter = f"""---
title: "{title}"
source: "{source_url}"
author:
  - "{author}"
published: {published_date}
created: "{now}"
description: "{description}"
summary: "{summary}"
tags:
  - clipper
  - {source_type}
type: clipper
---

# {title}

{body}

---
## Internal Links

## Link Candidates

- [{author}]({source_url})
"""

    return frontmatter


def main():
    parser = argparse.ArgumentParser(description="Clip a web article into Obsidian")
    parser.add_argument("url", help="URL to clip")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help="Obsidian vault path")
    parser.add_argument("--author", default="", help="Author name override")
    parser.add_argument("--force", action="store_true", help="Skip duplicate check")
    parser.add_argument("--dedup-only", action="store_true", help="Only check for duplicates, do not fetch/save")

    args = parser.parse_args()
    vault_dir = Path(args.vault).expanduser().resolve()

    if not vault_dir.exists():
        print(f"Error: Vault directory does not exist: {vault_dir}")
        print("Create it first, or use --vault to specify a different path.")
        sys.exit(1)

    # Step 0.5: Dedup-only mode — check duplicates and exit, no side effects
    if args.dedup_only:
        dupes = find_duplicate(vault_dir, args.url)
        if dupes:
            print(f"⚠️  This URL already exists in your vault:")
            for d in dupes:
                print(f"   {d}")
            sys.exit(1)
        print("✅ Not found — safe to clip")
        sys.exit(0)

    # Step 1: Check duplicates
    if not args.force:
        dupes = find_duplicate(vault_dir, args.url)
        if dupes:
            print(f"⚠️  This URL already exists in your vault:")
            for d in dupes:
                print(f"   {d}")
            print("Use --force to skip duplicate check.")
            sys.exit(0)

    # Step 2: Fetch content
    print(f"📥 Fetching {args.url} ...")
    content = fetch_content(args.url)
    title = content['title']
    print(f"   Title: {title}")
    print(f"   Images: {len(content['images'])}")

    # Step 2.5: Detect source language
    source_lang = detect_language(content['text'])
    needs_translation = (source_lang != TARGET_LANG)
    print(f"   Source language: {source_lang} | Translate: {needs_translation}")

    # Step 3: Set up paths (flat layout — note at vault root, images in vault/assets/)
    slug = slugify(title)
    asset_dir = vault_dir / ASSETS_DIR

    # Step 4: Download images
    image_mapping = {}
    if content['images']:
        print(f"🖼️  Downloading {len(content['images'])} images ...")
        image_mapping = download_images(content['images'], asset_dir)
        print(f"   Downloaded: {len(image_mapping)}")

    # Step 5: Format note
    published_date = datetime.now(TZ).strftime("%Y-%m-%d")
    author = args.author or urllib.parse.urlparse(args.url).netloc

    raw_note = format_note(
        title=title,
        source_text=content['text'],
        source_url=content['canonical_url'],
        author=author,
        published_date=published_date,
        image_mapping=image_mapping,
        source_type=content['source_type'],
    )

    # Write raw note (agent will add translations)
    note_path = vault_dir / f"{slug}.md"
    note_path.write_text(raw_note, encoding='utf-8')

    # Step 6: Output summary (for agent to consume)
    print(f"\n✅ Note saved: {note_path}")
    print(f"   Images: {asset_dir}/ ({len(image_mapping)} files)")
    print(f"\n─── RAW NOTE ───")
    print(raw_note[:2000])
    if len(raw_note) > 2000:
        print(f"\n... ({len(raw_note)} total chars, truncated)")

    # Return structured output for agent
    result = {
        "status": "raw",
        "note_path": str(note_path),
        "asset_dir": str(asset_dir),
        "title": title,
        "source_url": content['canonical_url'],
        "source_language": source_lang,
        "target_language": TARGET_LANG,
        "needs_translation": needs_translation,
        "image_count": len(image_mapping),
        "char_count": len(raw_note),
    }
    print(f"\n─── JSON ───")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()