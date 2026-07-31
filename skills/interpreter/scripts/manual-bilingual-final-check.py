#!/usr/bin/env python3
"""Lightweight final sanity check for Interpreter bilingual Markdown notes.

This complements the source-specific gates (for example batch-x-article-final-gate.py)
with a quick structural pass before sending the user's brief filename + ✅ response.
It does not prove source coverage; run the source-aware gate separately when a source
JSON/text dump is available.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover - PyYAML is normally available in Hermes envs
    yaml = None

PROTECTED_CN_TERMS = re.compile(r"智能体|代理|工具|提示|资源")


def parse_frontmatter(text: str):
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None, 0, "missing YAML frontmatter"
    if yaml is None:
        return {}, match.end(), None
    try:
        return yaml.safe_load(match.group(1)) or {}, match.end(), None
    except Exception as exc:
        return None, match.end(), f"invalid YAML: {exc}"


def orphan_lines(body: str):
    orphans = []
    in_code = False
    appendix_heading = re.compile(r"^(##\s+)?(Internal Links|Link Candidates)(<br>|$)")
    for lineno, line in enumerate(body.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        if stripped.startswith("![") or stripped in {"---", "***"}:
            continue
        if "<br>" not in line and (
            re.match(r"^(#{1,6}\s+|>\s+|-\s+|\d+\.\s+).+", line)
            or re.search(r"[A-Za-z]{3,}", line)
        ):
            # Attributions and source metadata lines are allowed to be single-language.
            if stripped.startswith("@") or appendix_heading.search(stripped):
                continue
            orphans.append((lineno, line[:160]))
    return orphans


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="Saved Interpreter .md file")
    ap.add_argument("--min-br", type=int, default=1, help="Minimum expected <br> lines")
    ap.add_argument("--expect-images", type=int, default=None, help="Optional exact expected image count")
    args = ap.parse_args()

    path = Path(args.file).expanduser()
    text = path.read_text(encoding="utf-8")
    fm, body_start, err = parse_frontmatter(text)
    failures = []
    if err:
        failures.append(err)
    body = text[body_start:] if body_start else text

    if fm is not None:
        for key in ("title", "source", "author", "published", "created", "type"):
            if key not in fm:
                failures.append(f"missing frontmatter key: {key}")
        if fm.get("type") != "clipper":
            failures.append("frontmatter type must be exact: type: clipper")

    br_count = body.count("<br>")
    image_count = body.count("![")
    code_fences = body.count("```")
    orphans = orphan_lines(body)

    if br_count < args.min_br:
        failures.append(f"too few <br> lines: {br_count} < {args.min_br}")
    if args.expect_images is not None and image_count != args.expect_images:
        failures.append(f"image count mismatch: {image_count} != {args.expect_images}")
    if code_fences % 2:
        failures.append(f"unbalanced code fences: {code_fences}")
    if orphans:
        failures.append(f"orphan non-<br> content lines: {len(orphans)}")
    # Only inspect the Chinese side of bilingual lines for em-dash drift. The
    # original English source may legitimately contain em/en dashes and should
    # not fail this check by itself.
    chinese_segments = []
    for line in text.splitlines():
        if "<br>" in line:
            chinese_segments.append(line.split("<br>", 1)[1])
    chinese_text = "\n".join(chinese_segments)
    if re.search(r"[^-]—|——", chinese_text):
        failures.append("possible Chinese em-dash drift")
    if PROTECTED_CN_TERMS.search(text):
        failures.append("possible protected AI-term translation drift")
    if re.search(r"<br>\s*(?:[-*+]\s+|\d+\.\s+|#{1,6}\s+)", text):
        failures.append("Chinese side appears to repeat Markdown/list marker after <br>")

    print(f"file: {path}")
    print(f"br_count: {br_count}")
    print(f"image_count: {image_count}")
    print(f"code_fences: {code_fences}")
    print(f"orphan_count: {len(orphans)}")
    if orphans:
        for lineno, line in orphans[:10]:
            print(f"orphan:{lineno}: {line}")
    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
