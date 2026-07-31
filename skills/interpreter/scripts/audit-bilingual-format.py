#!/usr/bin/env python3
"""Audit (and optionally fix) `<br>` bilingual format across an Interpreter vault.

Scans every note for format violations of the canonical bilingual layout:
- lines that should carry `<br>` but don't (orphan English/Chinese lines)
- `<br><br>` double artifacts
- Chinese side starting with a list/heading marker after `<br>`
- bare unescaped `$` on the English side of `<br>` lines

Usage:
  python audit-bilingual-format.py ~/Documents/obsidian/Interpreter [--fix] [--only-br]

  --only-br   Only check the `<br>` mechanical rules (orphans, double <br>,
              markers after <br>); skip $ and heading checks.

Exit code: 0 = clean, 1 = violations found (list printed per file).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BR_LINE_RE = re.compile(r"<br>")


def is_structural(s: str) -> bool:
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


def is_heading_or_list(s: str) -> bool:
    return s.startswith(("#", "- ", ">")) or bool(re.match(r"\d+\. ", s))


def audit_file(path: Path, fix: bool, only_br: bool) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return [f"{path.name}: no YAML frontmatter"]
    parts = text.split("---", 2)
    if len(parts) < 3:
        return [f"{path.name}: malformed frontmatter"]
    body = parts[2]

    issues: list[str] = []
    lines = body.splitlines()
    in_code = False
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or is_structural(s):
            continue
        # Orphan check: substantive lines missing <br>
        if is_heading_or_list(s) or len(s) > 40:
            if BR_LINE_RE not in s:
                issues.append(f"L{idx + 1}: missing <br>: {s[:80]}")
        # Double <br> artifact
        if "<br><br>" in s:
            issues.append(f"L{idx + 1}: double <br><br>")
        # Chinese side starting with marker
        if re.search(r"<br>\s*[-*]\s+", s) or re.search(r"<br>\s*\d+\.\s+", s):
            issues.append(f"L{idx + 1}: marker after <br>: {s[:80]}")
        if re.search(r"<br>\s*[#]+\s*[\u4e00-\u9fff]", s):
            issues.append(f"L{idx + 1}: heading marker after <br>: {s[:80]}")

    if not only_br:
        # Unescaped $ on English side
        for idx, line in enumerate(lines):
            s = line.strip()
            if "<br>" not in s:
                continue
            en = s.split("<br>", 1)[0]
            en = re.sub(r"`[^`]*`", "", en)
            if re.search(r"(?<!\\)\$", en):
                issues.append(f"L{idx + 1}: unescaped $ on English side")
        # Chinese em-dash drift (—— without source dash)
        for idx, line in enumerate(lines):
            if "——" in line:
                issues.append(f"L{idx + 1}: Chinese em-dash —— (verify source had dash)")

    if fix:
        fixed = []
        for line in lines:
            # collapse <br><br> to <br> — only when it's clearly an artifact
            new = line.replace("<br><br>", "<br>")
            fixed.append(new)
        if fixed != lines:
            path.write_text(text.replace("\n".join(lines), "\n".join(fixed)), encoding="utf-8")
            issues.append(f"{path.name}: auto-fixed {sum(1 for a, b in zip(lines, fixed) if a != b)} line(s)")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault", type=Path)
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--only-br", action="store_true")
    args = ap.parse_args()

    if not args.vault.is_dir():
        print(f"not a directory: {args.vault}", file=sys.stderr)
        return 1

    total_files = 0
    total_issues = 0
    for md in sorted(args.vault.glob("*.md")):
        issues = audit_file(md, args.fix, args.only_br)
        if issues:
            total_files += 1
            total_issues += len(issues)
            for issue in issues:
                print(f"{md.name}: {issue}")

    if total_issues:
        print(f"\nFAIL: {total_issues} issue(s) in {total_files} file(s)")
        return 1
    print(f"PASS: {len(list(args.vault.glob('*.md')))} files, no violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
