#!/usr/bin/env python3
"""Batch final gate for K L / Interpreter X Article translations.

Usage:
  python batch-x-article-final-gate.py \
    --pair /tmp/x_123.json=/home/user/Documents/obsidian/Interpreter/Title.md \
    --pair /tmp/x_456.json=/home/user/Documents/obsidian/Interpreter/Other.md

Checks:
- Obsidian Web Clipper frontmatter essentials, including type: clipper.
- published is date-only; created datetime is quoted in the raw YAML.
- Body uses bilingual <br> lines; no double <br><br> artifacts or list markers after <br>.
- No common X UI chrome / atomic placeholders / unbalanced code fences.
- No common protected AI term drift in Chinese side.
- Material source coverage against fxtwitter JSON after approved normalizations.

This is intentionally conservative: CTA/promo skips are configurable, and warnings should be
manually inspected when they match legitimate article prose.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - script should still report raw checks
    yaml = None

DEFAULT_CTA_RE = re.compile(
    r"(follow my linkedin|comment\s+gtm|yourmax\.ai|if this sounds interesting|"
    r"we[’']?re hiring|stay tuned|if you want to give it a go|"
    r"to pursue this vision, we[’']?ve raised|save this|bookmark|repost|share)",
    re.I,
)
# UI chrome should catch platform residue, not legitimate article prose such as
# "bookmarks" inside a workflow description. Engagement labels are only treated
# as UI residue on short standalone metric lines.
UI_RE = re.compile(r"(?mi)^\s*(?:Log in|Sign up|Don't miss what)\s*$|^\s*(?:\d+\s*)?(?:Reposts|Likes|Bookmarks)\s*$")
PROTECTED_TERM_RE = re.compile(r"智能体|提示词|资源")


def split_frontmatter(text: str):
    if not text.startswith("---") or text.count("---") < 2:
        return None, text
    parts = text.split("---", 2)
    return parts[1], parts[2]


def strip_md(s: str) -> str:
    s = s.replace("\\$", "$")
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = s.replace("**", "").replace("*", "").replace("`", "")
    s = s.replace("<br>", " ")
    return re.sub(r"\s+", " ", s or "").strip()


def english_blob(markdown: str) -> str:
    lines: list[str] = []
    in_fence = False
    for line in markdown.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            lines.append(line)
            continue
        if in_fence:
            lines.append(line)
            continue
        if "<br>" in line:
            lines.append(line.split("<br>", 1)[0])
        elif line.startswith(("# ", "## ", "### ", "- ")) or re.match(r"\d+\. ", line):
            lines.append(line)
    return strip_md("\n".join(lines))


def text_blocks(json_path: Path) -> list[str]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    article = data.get("tweet", {}).get("article", {})
    blocks = article.get("content", {}).get("blocks", [])
    return [b.get("text", "") for b in blocks if b.get("text", "").strip()]


def check_pair(json_path: Path, md_path: Path, cta_re: re.Pattern[str], min_word_coverage: float):
    issues: list[str] = []
    if not json_path.exists():
        return [f"missing JSON: {json_path}"]
    if not md_path.exists():
        return [f"missing markdown: {md_path}"]

    text = md_path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    name = md_path.name

    if fm is None:
        issues.append("missing YAML frontmatter")
    else:
        for field in ["title:", "source:", "author:", "published:", "created:", "description:", "tags:", "type: clipper"]:
            if field not in fm:
                issues.append(f"missing frontmatter field: {field}")
        if re.search(r'^published:\s+"', fm, re.M):
            issues.append("published should be date-only and unquoted")
        if re.search(r"^published:\s+\d{4}-\d{2}-\d{2}T", fm, re.M):
            issues.append("published should not be a full datetime")
        if re.search(r"^created:\s+\d", fm, re.M):
            issues.append("created datetime should be quoted in raw YAML")
        if yaml is not None:
            try:
                parsed = yaml.safe_load(fm)
                if parsed.get("type") != "clipper":
                    issues.append("YAML type is not clipper")
                if not str(parsed.get("source", "")).startswith("https://"):
                    issues.append("YAML source is missing or non-HTTPS")
            except Exception as exc:
                issues.append(f"YAML parse failed: {exc}")

    if "<br>" not in body:
        issues.append("body has no <br> bilingual lines")
    if "<br><br>" in body:
        issues.append("double <br><br> artifact found; collapse internal source newlines before <br>")
    if re.search(r"<br>\s*[-*]\s+", body):
        issues.append("Chinese side starts with a bullet marker after <br>")
    if re.search(r"<br>\s*\d+\.\s+", body):
        issues.append("Chinese side starts with an ordered-list marker after <br>")
    first_heading = next((ln for ln in body.splitlines() if ln.startswith("# ")), "")
    if first_heading and "<br>" not in first_heading:
        issues.append("H1 lacks <br> bilingual title")
    if UI_RE.search(text):
        issues.append("possible X UI/metric residual; inspect context")
    if "<!-- [image not available] -->" in text or "<!-- atomic unavailable" in text:
        issues.append("atomic/image placeholder remains")
    if text.count("```") % 2:
        issues.append("unbalanced fenced code blocks")
    if "——" in text or re.search(r"[\u4e00-\u9fff]—|—[\u4e00-\u9fff]", text):
        issues.append("Chinese em dash found; verify the source also used a dash")
    if PROTECTED_TERM_RE.search(body):
        issues.append("possible protected AI term translated into Chinese")

    eblob = english_blob(text)
    missing: list[tuple[float, str]] = []
    skipped = 0
    blocks = text_blocks(json_path)
    for raw in blocks:
        normalized = strip_md(raw)
        if not normalized:
            continue
        if cta_re.search(normalized):
            skipped += 1
            continue
        # fxtwitter blocks can contain embedded newlines; the canonical note often collapses them.
        parts = [strip_md(part) for part in re.split(r"\n+", raw) if strip_md(part)]
        if normalized in eblob or all(part in eblob for part in parts):
            continue
        words = [w.lower() for w in re.findall(r"[A-Za-z0-9$/.:-]+", normalized) if len(w) > 1]
        coverage = sum(1 for w in words if w in eblob.lower()) / max(1, len(words))
        if coverage < min_word_coverage:
            missing.append((coverage, normalized[:220]))
    if missing:
        issues.append(f"material source coverage missing {len(missing)} block(s): " + "; ".join(f"{cov:.2f} {snippet}" for cov, snippet in missing[:5]))

    if issues:
        return [f"{name}: {issue}" for issue in issues]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", action="append", required=True, help="/tmp/x_ID.json=/path/to/file.md")
    parser.add_argument("--skip-cta-regex", default=None, help="Additional regex for intentional CTA/promo omissions")
    parser.add_argument("--min-word-coverage", type=float, default=0.92)
    args = parser.parse_args()

    cta_re = DEFAULT_CTA_RE
    if args.skip_cta_regex:
        cta_re = re.compile(DEFAULT_CTA_RE.pattern + "|" + args.skip_cta_regex, re.I)

    all_issues: list[str] = []
    for pair in args.pair:
        if "=" not in pair:
            all_issues.append(f"invalid --pair {pair!r}; expected json=file")
            continue
        left, right = pair.split("=", 1)
        all_issues.extend(check_pair(Path(left).expanduser(), Path(right).expanduser(), cta_re, args.min_word_coverage))

    if all_issues:
        print("FAIL")
        for issue in all_issues:
            print("-", issue)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
