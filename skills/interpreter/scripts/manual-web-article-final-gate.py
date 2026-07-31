#!/usr/bin/env python3
"""Manual final gate for non-X Interpreter web/article notes.

Checks the saved Obsidian note for the user's canonical K L bilingual format and,
optionally, material source coverage against a plain-text source dump.

Usage:
  python scripts/manual-web-article-final-gate.py \
    --file ~/Documents/obsidian/Interpreter/article.md \
    --source-text /tmp/article_source.txt
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_KEYS = [
    "type", "title", "source", "author", "published", "created", "description", "tags", "related"
]
UI_RESIDUE = [
    "Log in", "Sign up", "Read more<br>", "Copy<br>", "Subscribe now", "Keep reading",
    "Share this post", "Upgrade to", "Want to publish", "Trending", "Like", "Repost",
]
PLACEHOLDERS = ["[image not available]", "<!-- atomic unavailable", "TODO", "TBD"]


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def frontmatter_keys(yaml_text: str) -> set[str]:
    keys = set()
    for line in yaml_text.splitlines():
        if line and not line.startswith((" ", "-")) and ":" in line:
            keys.add(line.split(":", 1)[0].strip())
    return keys


def is_structural_line(s: str) -> bool:
    if not s:
        return True
    if s.startswith("!["):
        return True
    if s in {"---", "## Internal Links", "## Link Candidates"}:
        return True
    if s.startswith("- [["):
        return True
    if s.startswith("@"):
        return True
    return False


def check_orphan_bilingual_lines(body: str) -> list[str]:
    issues = []
    in_code = False
    for lineno, line in enumerate(body.splitlines(), 1):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or is_structural_line(s):
            continue
        if s.startswith(("#", "- ", ">", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")) or len(s) > 40:
            if "<br>" not in s:
                issues.append(f"line {lineno}: missing <br>: {s[:100]}")
    return issues


def english_side_text(text: str) -> str:
    out = []
    for line in text.splitlines():
        if "<br>" in line:
            out.append(line.split("<br>", 1)[0])
    return "\n".join(out)


def find_unescaped_dollars(en: str) -> bool:
    # Strip inline code spans before checking bare dollars.
    en = re.sub(r"`[^`]*`", "", en)
    return bool(re.search(r"(?<!\\)\$", en))


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\\$", "$")) .strip()


def source_coverage(source: str, saved: str) -> list[str]:
    saved_norm = normalize(saved)
    missing = []
    for line in source.splitlines():
        raw = line.strip()
        if len(raw) < 25:
            continue
        low = raw.lower()
        if any(x in low for x in ["subscribe", "sign up", "log in", "share this", "privacy policy"]):
            continue
        if normalize(raw) not in saved_norm:
            missing.append(raw[:140])
    return missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, type=Path)
    ap.add_argument("--source-text", type=Path, help="Optional cleaned source text dump for coverage check")
    ap.add_argument("--no-related-required", action="store_true", help="Do not require related/Internal Links/Link Candidates")
    args = ap.parse_args()

    text = args.file.expanduser().read_text(encoding="utf-8")
    yaml_text, body = split_frontmatter(text)
    issues: list[str] = []

    keys = frontmatter_keys(yaml_text)
    missing_keys = [k for k in REQUIRED_KEYS if k not in keys and not (args.no_related_required and k == "related")]
    if missing_keys:
        issues.append("missing frontmatter keys: " + ", ".join(missing_keys))
    if "type" in keys and not re.search(r"^type:\s*clipper\s*$", yaml_text, re.M):
        issues.append("frontmatter type should be exact: type: clipper")
    if not args.no_related_required:
        if "## Internal Links" not in text or "## Link Candidates" not in text:
            issues.append("missing Internal Links or Link Candidates section")
    for token in UI_RESIDUE:
        if token in text:
            issues.append(f"possible UI/CTA residue: {token}")
    for token in PLACEHOLDERS:
        if token in text:
            issues.append(f"placeholder residue: {token}")
    issues.extend(check_orphan_bilingual_lines(body))
    if "<br>##" in text or "<br>###" in text or "<br>- " in text:
        issues.append("Chinese side appears to contain Markdown heading/list marker after <br>")
    if find_unescaped_dollars(english_side_text(text)):
        issues.append("unescaped bare $ on English side of bilingual lines")
    if args.source_text:
        source = args.source_text.expanduser().read_text(encoding="utf-8")
        missing = source_coverage(source, text)
        if missing:
            issues.append(f"source coverage missing {len(missing)} blocks; first examples: {missing[:5]}")

    if issues:
        print("FAIL")
        for issue in issues:
            print("- " + issue)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
