#!/usr/bin/env python3
"""Save a Chinese-original X Article fxtwitter JSON as an Obsidian Interpreter note.

Usage:
  python save-x-article-from-fxtwitter.py --json /tmp/x_<id>.json --source-url 'https://x.com/.../status/<id>'

This is for Chinese-original X Articles. English articles still need bilingual EN/CN translation.
"""
from __future__ import annotations

import argparse
import json
import re
from email.utils import parsedate_to_datetime
from pathlib import Path


def clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def esc_yaml(s: str) -> str:
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def sanitize_filename(s: str) -> str:
    s = s.strip().replace(":", " -").replace("：", " - ")
    s = re.sub(r'[\\/*?"<>|]', "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:180].rstrip(" .")


def is_promo_caption(s: str) -> bool:
    s = clean(s)
    return any(x in s for x in ["关注", "收藏", "转发", "点赞", "Follow", "Subscribe", "Sign up"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="fxtwitter JSON dump path")
    ap.add_argument("--source-url", required=True, help="canonical original X URL")
    ap.add_argument("--out-dir", default="~/Documents/obsidian/Interpreter")
    ap.add_argument("--tags", default="ai,clipper", help="comma-separated tags")
    args = ap.parse_args()

    data = json.loads(Path(args.json).read_text())
    tweet = data["tweet"]
    article = tweet["article"]
    content = article["content"]

    created_dt = parsedate_to_datetime(tweet.get("created_at"))
    title = article.get("title", "").strip()
    preview = clean(article.get("preview_text"))
    author_name = tweet.get("author", {}).get("name") or ""
    screen = tweet.get("author", {}).get("screen_name") or ""
    author = f"{author_name} (@{screen})".strip()
    cover = (article.get("cover_media") or {}).get("media_info", {}).get("original_img_url")

    media_by_id = {
        str(m.get("media_id")): m.get("media_info", {}).get("original_img_url")
        for m in (article.get("media_entities") or [])
    }
    entity_map = {int(e["key"]): e["value"] for e in content.get("entityMap", [])}

    def render_atomic(block: dict) -> list[str]:
        outs: list[str] = []
        for r in block.get("entityRanges", []):
            val = entity_map.get(int(r.get("key")), {})
            typ = val.get("type")
            d = val.get("data", {})
            if typ == "MEDIA":
                if is_promo_caption(d.get("caption")):
                    continue
                items = d.get("mediaItems") or []
                if items:
                    url = media_by_id.get(str(items[0].get("mediaId")))
                    if url:
                        outs.append(f"![Article image]({url})")
            elif typ == "MARKDOWN":
                md = (d.get("markdown") or "").strip("\n")
                if md:
                    outs.append(md)
            elif typ == "DIVIDER":
                outs.append("---")
        return outs

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    lines: list[str] = [
        "---",
        "type: clipper",
        f'title: "{esc_yaml(title)}"',
        f'source: "{esc_yaml(args.source_url)}"',
        "author:",
        f'  - "[[{esc_yaml(author)}]]"',
        f"published: {created_dt.date().isoformat()}",
        f'created: "{created_dt.isoformat().replace("+00:00", "Z")}"',
    ]
    if preview:
        lines.append(f'description: "{esc_yaml(preview)}"')
    lines.append("tags:")
    lines.extend([f'  - "{esc_yaml(tag)}"' for tag in tags])
    lines.append('platform: "X (Twitter) - Article"')
    if cover:
        lines.append(f'image: "{cover}"')
    lines.extend(["---", "", f"# {title}", ""])
    if cover:
        lines.extend([f"![Cover image]({cover})", ""])

    for block in content.get("blocks", []):
        typ = block.get("type")
        raw = (block.get("text") or "").rstrip()
        if typ == "atomic":
            for item in render_atomic(block):
                lines.extend([item, ""])
            continue
        if not raw.strip():
            continue
        text = raw.strip()
        if typ in ("header-one", "header-two"):
            lines.append(f"## {text}")
        elif typ == "header-three":
            lines.append(f"### {text}")
        elif typ == "unordered-list-item":
            lines.append(f"- {text}")
        elif typ == "ordered-list-item":
            lines.append(f"1. {text}")
        elif typ == "blockquote":
            lines.extend([f"> {line}" for line in text.splitlines()])
        else:
            lines.append(text)
        lines.append("")

    md = "\n".join(lines).rstrip() + "\n"
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (sanitize_filename(title) + ".md")
    out.write_text(md)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
