#!/usr/bin/env python3
"""Verify a Chinese-original X Article note saved from fxtwitter JSON.

Usage:
  python verify-chinese-x-article.py --json /tmp/x_<post_id>.json --file ~/Documents/obsidian/Interpreter/<note>.md --source-url https://x.com/user/status/<post_id> --expect-images 1

Checks:
- Web Clipper YAML fields including type: clipper, source, summary, related.
- Chinese-original note has no bilingual <br> body format.
- Markdown images are local assets/... paths only and files exist.
- Non-CTA fxtwitter text blocks are present after normalizing markdown links/wikilinks/emphasis.
- No placeholders or unbalanced code fences.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    print(f"FAIL: PyYAML unavailable: {exc}")
    sys.exit(2)

CTA_RE = re.compile(
    r"(关注|欢迎关注|感谢阅读|感谢看到这里|转发|收藏|点赞|下篇见|follow\s+@|subscribe|repost|bookmark|share\s+this|more\s+articles\s+available)",
    re.I,
)


def collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def visible_text(md: str) -> str:
    md = re.sub(r"^---\n.*?\n---\n", "", md, flags=re.S)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    md = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", md)
    md = re.sub(r"\[\[([^\]]+)\]\]", r"\1", md)
    md = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"[*_`#>-]+", " ", md)
    return collapse(md)


def load_yaml(text: str) -> dict[str, Any]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise AssertionError("missing YAML frontmatter")
    data = yaml.safe_load(m.group(1))
    if not isinstance(data, dict):
        raise AssertionError("YAML frontmatter is not a mapping")
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, type=Path)
    ap.add_argument("--file", required=True, type=Path)
    ap.add_argument("--source-url", required=True)
    ap.add_argument("--expect-images", type=int, default=None)
    args = ap.parse_args()

    raw = json.loads(args.json.read_text(encoding="utf-8"))
    text = args.file.expanduser().read_text(encoding="utf-8")
    note_dir = args.file.expanduser().parent
    errors: list[str] = []

    try:
        y = load_yaml(text)
        required = ["type", "title", "source", "author", "published", "created", "description", "summary", "tags", "related"]
        missing = [k for k in required if k not in y]
        if missing:
            errors.append(f"missing YAML fields: {missing}")
        if y.get("type") != "clipper":
            errors.append("type is not clipper")
        if y.get("source") != args.source_url:
            errors.append(f"source mismatch: {y.get('source')!r}")
        if not isinstance(y.get("summary"), str) or not y.get("summary") or len(y.get("summary", "")) >= 250:
            errors.append("summary missing/empty/or >=250 chars")
    except Exception as exc:
        errors.append(str(exc))

    if "<br>" in text:
        errors.append("Chinese-original note should not use bilingual <br> body format")
    if "<!--" in text:
        errors.append("HTML comment/placeholder remains")
    if text.count("```") % 2:
        errors.append("unbalanced fenced code blocks")

    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    if args.expect_images is not None and len(imgs) != args.expect_images:
        errors.append(f"image count {len(imgs)} != expected {args.expect_images}")
    for p in imgs:
        if p.startswith(("http://", "https://")):
            errors.append(f"remote image remains: {p}")
        elif not p.startswith("assets/"):
            errors.append(f"non-assets image path: {p}")
        elif not (note_dir / p).exists():
            errors.append(f"missing local asset: {p}")
    if re.search(r"pbs\.twimg\.com|twimg\.com|substackcdn\.com", text):
        errors.append("remote CDN URL remains in note")

    vis = visible_text(text)
    article = (raw.get("tweet") or {}).get("article") or {}
    blocks = ((article.get("content") or {}).get("blocks") or [])
    missing_blocks = []
    skipped_cta = []
    for i, b in enumerate(blocks):
        s = collapse(b.get("text") or "")
        if not s:
            continue
        if CTA_RE.search(s):
            skipped_cta.append(i)
            continue
        if s not in vis:
            missing_blocks.append((i, s[:120]))
    if missing_blocks:
        errors.append("missing non-CTA source blocks: " + repr(missing_blocks[:8]))

    if errors:
        print("FAIL")
        for e in errors:
            print("-", e)
        if skipped_cta:
            print("skipped_cta_blocks:", skipped_cta)
        return 1
    print(f"PASS Chinese X Article gate: blocks={len(blocks)} images={len(imgs)} skipped_cta={skipped_cta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
