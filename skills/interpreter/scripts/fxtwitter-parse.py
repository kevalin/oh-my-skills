#!/usr/bin/env python3
"""Dump an fxtwitter X Article JSON into a readable source file + resolve media.

For any X Article, this converts the block stream + entityMap + media_entities
into a single markdown source dump (with atomic blocks resolved) so the agent
can translate it into a bilingual Obsidian note.

Usage:
  python fxtwitter-parse.py /tmp/x_<ID>.json [--out /tmp/x_<ID>_source.md] [--images]

  --images   Also print a media URL manifest (media_id -> original_img_url)
             so the caller can download images with the proxy.

Output:
  - stdout: block count, title, cover URL, media list (or JSON manifest with --images)
  - file:   /tmp/x_<ID>_source.md (or --out), block-by-block markdown source
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def split_br(t: str) -> str:
    """Collapse embedded newlines inside a text block (fxtwitter uses \\n)."""
    return re.sub(r"\s+", " ", t or "").strip()


def resolve_atomic(block: dict, entity_map: list[dict], media_entities: list[dict]) -> str:
    """Resolve an atomic block's entity reference into a concrete line."""
    ent_refs = block.get("entityRanges") or []
    if not ent_refs:
        return ""
    key = str(ent_refs[0].get("key", ""))
    for ent in entity_map:
        if str(ent.get("key")) != key:
            continue
        value = ent.get("value", {})
        etype = value.get("type", "")
        data = value.get("data", {})
        if etype == "MEDIA":
            media_id = (data.get("mediaItems") or [{}])[0].get("mediaId", "")
            return f"[IMAGE:{media_id}]"
        if etype == "MARKDOWN":
            md = data.get("markdown", "")
            return f"```\n{md}\n```" if md else ""
        if etype == "LINK":
            return data.get("url", "")
        if etype == "TWEET":
            return f"[EMBEDDED_TWEET:{data.get('url', '')}]"
        if etype == "DIVIDER":
            return "---"
        return f"[ATOMIC:{etype}]"
    return ""


def parse(json_path: Path) -> dict:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    tweet = data.get("tweet", {})
    article = tweet.get("article", {})
    content = article.get("content", {})
    blocks = content.get("blocks", [])
    entity_map = content.get("entityMap", [])
    media_entities = article.get("media_entities", [])

    lines: list[str] = []
    for i, b in enumerate(blocks):
        btype = b.get("type", "")
        text = split_br(b.get("text", ""))
        if btype == "atomic":
            resolved = resolve_atomic(b, entity_map, media_entities)
            if resolved:
                lines.append(f"<!-- BLOCK {i} ({btype}) -->\n{resolved}")
        elif text:
            marker = ""
            if btype in ("header-one", "header-two"):
                marker = "# " if btype == "header-one" else "## "
            elif btype == "unordered-list-item":
                marker = "- "
            elif btype == "ordered-list-item":
                marker = "1. "
            elif btype == "blockquote":
                marker = "> "
            lines.append(f"<!-- BLOCK {i} ({btype}) -->\n{marker}{text}")

    cover = (article.get("cover_media") or {}).get("media_info", {}).get("original_img_url", "")
    media_map = {
        m.get("media_id"): (m.get("media_info") or {}).get("original_img_url", "")
        for m in media_entities
    }

    return {
        "title": article.get("title", ""),
        "cover": cover,
        "block_count": len(blocks),
        "media": media_map,
        "source_text": "\n\n".join(lines),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--images", action="store_true")
    args = ap.parse_args()

    if not args.json_path.exists():
        print(f"missing JSON: {args.json_path}", file=sys.stderr)
        return 1

    result = parse(args.json_path)
    out_path = args.out or args.json_path.with_name(args.json_path.stem + "_source.md")
    out_path.write_text(result["source_text"], encoding="utf-8")

    print(f"title: {result['title']}")
    print(f"blocks: {result['block_count']}")
    print(f"cover: {result['cover']}")
    print(f"media entities: {len(result['media'])}")
    print(f"source dump: {out_path}")
    if args.images:
        print("--- media manifest ---")
        for mid, url in result["media"].items():
            print(f"{mid}\t{url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
