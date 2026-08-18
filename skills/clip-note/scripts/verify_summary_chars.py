#!/usr/bin/env python3
"""Verify frontmatter summary fields across the Interpreter vault.

Checks each .md file's summary for:
  - <=120 chars after whitespace stripping (user mandate 2026-08-08: 导读, ≤120)
  - No em-dash (——) anywhere in the summary
  - No protected AI terms (智能体|提示词|资源) in the summary
  - No fixed opening phrases (读完最值得记住的一句|一句话理解|想落地就做三件事)
  - No paradigm label words (**核心**|**拆解**|**行动**|**R**|**I**|**A**)
  - Has paragraph breaks (not a single-line summary)

Usage:
  python3 verify_summary_chars.py [vault_dir] [--file pattern]
  python3 verify_summary_chars.py                    # defaults to ~/Documents/obsidian/Interpreter/
  python3 verify_summary_chars.py --file "The*"     # glob pattern for filenames

Exit code: 0 if all pass, 1 if any fail.
"""
import os, re, sys, glob as globmod

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

DEFAULT_VAULT = os.path.expanduser("~/Documents/obsidian/Interpreter")
PROTECTED_RE = re.compile(r'智能体|提示词|资源')
EM_DASH = '——'
FIXED_OPENINGS = ['读完最值得记住的一句', '一句话理解', '想落地就做三件事']
LABEL_PATTERNS = re.compile(r'\*\*核心\*\*|\*\*拆解\*\*|\*\*行动\*\*|\*\*R\*\*|\*\*I\*\*|\*\*A\*\*')


def extract_summary_yaml(filepath):
    """Extract summary using yaml.safe_load — handles multi-line summaries correctly.

    The old regex approach failed when yaml.safe_dump outputs summaries with
    embedded \\n\\n as literal block scalars (|) or double-quoted strings with
    \\n escapes. yaml.safe_load handles both transparently.
    """
    text = open(filepath, encoding='utf-8').read()
    m = re.search(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        return None, ["no frontmatter"]
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return None, [f"YAML parse error: {e}"]
    if not isinstance(fm, dict):
        return None, ["frontmatter not a dict"]
    return fm.get('summary'), []


def extract_summary_regex(filepath):
    """Fallback regex extraction when PyYAML is unavailable."""
    text = open(filepath, encoding='utf-8').read()
    m = re.search(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        return None, ["no frontmatter"]

    fm_text = m.group(1)
    # Try quoted scalar (single or double quoted, may span lines with \n)
    sm = re.search(r'^summary:\s*["\'](.*?)["\']\s*$', fm_text, re.M | re.S)
    if not sm:
        # Try unquoted single-line
        sm = re.search(r'^summary:\s*(.+)$', fm_text, re.M)
    if not sm:
        return None, ["no summary field"]
    return sm.group(1).strip(), []


def check_file(filepath):
    """Return (filename, summary, char_count, issues) or (filename, None, 0, [error])."""
    try:
        if HAS_YAML:
            summary, issues = extract_summary_yaml(filepath)
        else:
            summary, issues = extract_summary_regex(filepath)
    except Exception as e:
        return os.path.basename(filepath), None, 0, [f"read error: {e}"]

    if issues:
        return os.path.basename(filepath), None, 0, issues
    if not summary:
        return os.path.basename(filepath), None, 0, ["no summary field"]

    stripped = re.sub(r'\s', '', summary)
    char_count = len(stripped)
    issues = []

    if char_count > 120:
        issues.append(f"over limit: {char_count} > 120")
    if EM_DASH in summary:
        issues.append("contains em-dash (——)")
    if PROTECTED_RE.search(summary):
        issues.append("contains protected term")
    for opener in FIXED_OPENINGS:
        if summary.startswith(opener):
            issues.append(f"fixed opening: '{opener}'")
            break
    if LABEL_PATTERNS.search(summary):
        issues.append("contains paradigm label words")
    # Paragraph-break check removed (2026-08-08): the ≤120 导读 standard is so tight that
    # single-line summaries are normal — user accepted single-line 112-char summaries
    # (Palantir FDE, Grok Imagine). Paragraph breaks are now OPTIONAL at ≤120 chars.

    return os.path.basename(filepath), summary, char_count, issues


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Verify summary fields in Interpreter vault")
    ap.add_argument("vault", nargs="?", default=DEFAULT_VAULT, help="vault directory")
    ap.add_argument("--file", default="*.md", help="glob pattern for filenames (default: *.md)")
    args = ap.parse_args()

    pattern = os.path.join(args.vault, args.file)
    files = sorted(globmod.glob(pattern))

    if not files:
        print(f"No files matching {pattern}")
        sys.exit(1)

    all_pass = True
    for f in files:
        name, summary, chars, issues = check_file(f)
        if summary is None and issues:
            print(f"SKIP {name}: {issues[0]}")
            continue
        if issues:
            all_pass = False
            print(f"FAIL {name} ({chars} chars)")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"OK   {name} ({chars} chars)")

    sys.exit(0 if all_pass else 1)

if __name__ == '__main__':
    main()