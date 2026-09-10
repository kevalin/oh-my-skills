#!/usr/bin/env python3
"""Batch migration tool to convert legacy bilingual (<br>) notes into decoupled EN/ZH notes.

Usage:
  python3 migrate_decoupled.py [--vault DIR] [--dry-run] [--limit N] [--file GLOB]
"""

from __future__ import annotations
import argparse
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_VAULT = Path("/Users/kevalin/Documents/obsidian/Interpreter")


def strip_wikilinks(text: str) -> str:
    """Replace [[target|alias]] with alias, and [[target]] with target."""
    s = re.sub(r'\[\[([^|\]\n]+)\|([^\]\n]+)\]\]', r'\2', text)
    s = re.sub(r'\[\[([^\]\n]+)\]\]', r'\1', s)
    return s


def sanitize_filename(name: str) -> str:
    """Sanitize name to make it safe for filesystems and Obsidian without creating folders."""
    # First strip wikilinks if any
    s = strip_wikilinks(name)
    # Map slash/backslash to fullwidth to prevent Obsidian folder splitting
    s = s.replace("/", "／").replace("\\", "＼")
    # Replace illegal filename characters and brackets
    s = re.sub(r'[\[\]:\*\?"<>\|]', " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Trim trailing periods or spaces
    s = s.rstrip(". ")
    # Cap length at 120 chars
    if len(s) > 120:
        s = s[:120].rsplit(" ", 1)[0]
    return s.strip()


def split_frontmatter(text: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def parse_frontmatter_dict(yaml_text: str) -> dict:
    if yaml is not None:
        try:
            return yaml.safe_load(yaml_text) or {}
        except Exception:
            pass
    data = {}
    for line in yaml_text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip('"\'')
    return data


def extract_titles(filename_stem: str, yaml_text: str, body: str) -> tuple[str, str]:
    """Extract (en_title, zh_title) accurately without misidentifying mid-body headings."""
    fm = parse_frontmatter_dict(yaml_text)
    
    # Extract raw title with multiline support (note re.M | re.S)
    raw_title = ""
    m_title = re.search(r"^title:\s*[\x22\x27]?(.*?)(?=\n[a-zA-Z_-]+:\s|\n---|\Z)", yaml_text, re.S | re.M)
    if m_title:
        # Collapse newlines in title
        raw_title = re.sub(r"\s+", " ", m_title.group(1)).strip().strip("\"'")
    else:
        raw_title = str(fm.get("title", "")).strip()

    # Look for H1 (# ) ONLY in the first 15 lines of body
    raw_h1 = ""
    body_head = "\n".join(body.splitlines()[:15])
    m_h1 = re.search(r"^#\s+(.+)$", body_head, re.M)
    if m_h1:
        raw_h1 = m_h1.group(1).strip()

    en_title = ""
    zh_title = ""

    # Strategy 1: <br> in frontmatter title
    if "<br>" in raw_title:
        parts = raw_title.split("<br>", 1)
        en_title = parts[0].strip()
        zh_title = parts[1].strip()
    # Strategy 2: <br> in top H1
    elif "<br>" in raw_h1:
        parts = raw_h1.split("<br>", 1)
        en_title = parts[0].strip()
        zh_title = parts[1].strip()
    # Strategy 3: " - " separator with Chinese in second part
    elif " - " in raw_title and re.search(r"[\u4e00-\u9fff]", raw_title.split(" - ", 1)[1]):
        parts = raw_title.split(" - ", 1)
        en_title = parts[0].strip()
        zh_title = parts[1].strip()
    # Strategy 4: " / " separator in top H1
    elif " / " in raw_h1 and re.search(r"[\u4e00-\u9fff]", raw_h1.split(" / ", 1)[1]):
        parts = raw_h1.split(" / ", 1)
        en_title = parts[0].strip()
        zh_title = parts[1].strip()

    # If en_title not resolved from <br>, default to filename_stem
    if not en_title:
        en_title = filename_stem if filename_stem else raw_title

    # Fallback for zh_title
    if not zh_title:
        # Check if filename itself has chinese
        if re.search(r"[\u4e00-\u9fff]", filename_stem):
            zh_title = filename_stem
        else:
            # If no Chinese title exists, keep en_title as zh_title
            zh_title = en_title

    # Clean markdown formatting and wikilinks from titles
    en_title = strip_wikilinks(re.sub(r"[*_`#]", "", en_title)).strip()
    zh_title = strip_wikilinks(re.sub(r"[*_`#]", "", zh_title)).strip()

    return en_title, zh_title


def split_body(body: str) -> tuple[str, str]:
    """Split bilingual body into (en_body, zh_body)."""
    en_lines: list[str] = []
    zh_lines: list[str] = []

    in_code = False
    in_rel_internal = False
    in_rel_candidates = False

    for line in body.splitlines():
        trimmed = line.strip()

        # Code blocks: keep verbatim in both
        if trimmed.startswith("```"):
            in_code = not in_code
            en_lines.append(line)
            zh_lines.append(line)
            continue
        if in_code:
            en_lines.append(line)
            zh_lines.append(line)
            continue

        # Blank lines, dividers, or bare images: keep in both
        if not trimmed:
            en_lines.append("")
            zh_lines.append("")
            continue
        if trimmed == "---":
            en_lines.append(line)
            zh_lines.append(line)
            continue
        if trimmed.startswith("![") and "<br>" not in trimmed:
            en_lines.append(line)
            zh_lines.append(line)
            continue

        # Relationship sections
        if trimmed in {"## Internal Links", "## Internal Links<br>内部链接", "## 内部链接"}:
            in_rel_internal = True
            in_rel_candidates = False
            en_lines.append("## Internal Links")
            zh_lines.append("## 内部链接")
            continue
        if trimmed in {"## Link Candidates", "## Link Candidates<br>链接候选", "## 链接候选"}:
            in_rel_internal = False
            in_rel_candidates = True
            en_lines.append("## Link Candidates")
            zh_lines.append("## 链接候选")
            continue

        # Inside relationship sections
        if in_rel_internal or in_rel_candidates:
            if "<br>" in line:
                p_en, p_zh = line.split("<br>", 1)
                en_lines.append(p_en.strip())
                zh_lines.append(p_zh.strip())
            else:
                en_lines.append(line)
                zh_lines.append(line)
            continue

        # Regular lines with <br>
        if "<br>" in line:
            parts = line.split("<br>", 1)
            en_part = parts[0].rstrip()
            zh_part = parts[1].lstrip()

            # Handle list markers or headings
            # 1. Headings (e.g. ## English<br>Chinese)
            m_h = re.match(r"^(#{1,6}\s+)", en_part)
            if m_h:
                h_prefix = m_h.group(1)
                # Strip heading prefix if duplicated on ZH side
                zh_part = re.sub(r"^#{1,6}\s*", "", zh_part)
                zh_part = h_prefix + zh_part

            # 2. Ordered lists (e.g. 1. English<br>Chinese)
            m_ol = re.match(r"^(\s*\d+\.\s+)", en_part)
            if m_ol:
                ol_prefix = m_ol.group(1)
                zh_part = re.sub(r"^\s*\d+\.\s*", "", zh_part)
                zh_part = ol_prefix + zh_part

            # 3. Bullet lists (e.g. - English<br>Chinese)
            m_ul = re.match(r"^(\s*[-*]\s+)", en_part)
            if m_ul:
                ul_prefix = m_ul.group(1)
                zh_part = re.sub(r"^\s*[-*]\s*", "", zh_part)
                zh_part = ul_prefix + zh_part

            # 4. Blockquotes (e.g. > English<br>Chinese)
            m_bq = re.match(r"^(\s*>\s*)", en_part)
            if m_bq:
                bq_prefix = m_bq.group(1)
                zh_part = re.sub(r"^\s*>\s*", "", zh_part)
                zh_part = bq_prefix + zh_part

            en_lines.append(en_part)
            zh_lines.append(zh_part)
        else:
            # Non-<br> lines
            # If it's mostly Chinese, give to zh; if mostly English, give to en
            cjk_count = len(re.findall(r"[\u4e00-\u9fff]", line))
            latin_count = len(re.findall(r"[a-zA-Z]", line))
            if cjk_count > latin_count:
                zh_lines.append(line)
            else:
                en_lines.append(line)

    return "\n".join(en_lines).strip(), "\n".join(zh_lines).strip()


def build_frontmatter(original_yaml: str, title: str, is_zh: bool, en_title: str, zh_title: str) -> str:
    """Build updated YAML frontmatter for either EN or ZH note."""
    lines = []
    has_title = False
    has_type = False
    has_source_note = False
    has_trans_note = False
    has_aliases = False
    has_orig_title = False

    # Pre-parse tags
    in_multiline_title = False
    for raw_line in original_yaml.splitlines():
        line = raw_line.rstrip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("title:"):
            lines.append(f'title: "{title}"')
            has_title = True
            in_multiline_title = True
            continue

        if in_multiline_title:
            if line.startswith((" ", "\t")):
                continue
            in_multiline_title = False

        if line.startswith("type:"):
            lines.append("type: clipper")
            has_type = True
        elif line.startswith("translation_note:"):
            if not is_zh:
                lines.append(f'translation_note: "[[{zh_title}]]"')
                has_trans_note = True
        elif line.startswith("source_note:"):
            if is_zh:
                lines.append(f'source_note: "[[sources/{en_title}]]"')
                has_source_note = True
        elif line.startswith("original_title:"):
            if is_zh:
                lines.append(f'original_title: "{en_title}"')
                has_orig_title = True
        elif line.startswith("aliases:"):
            has_aliases = True
            lines.append(line)
        else:
            lines.append(line)

    if not has_type:
        lines.insert(0, "type: clipper")
    if not has_title:
        lines.insert(1, f'title: "{title}"')

    if is_zh:
        if not has_orig_title and en_title:
            lines.append(f'original_title: "{en_title}"')
        if not has_source_note and en_title:
            lines.append(f'source_note: "[[sources/{en_title}]]"')
        if not has_aliases and en_title and en_title != zh_title:
            lines.append(f'aliases:\n  - "{en_title}"')
    else:
        if not has_trans_note and zh_title:
            lines.append(f'translation_note: "[[{zh_title}]]"')

    return "---\n" + "\n".join(lines) + "\n---\n"


def process_note(file_path: Path, vault_dir: Path, dry_run: bool = False) -> tuple[bool, str]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    if "<br>" not in text:
        return False, "Not a bilingual file (no <br>)"

    yaml_text, body = split_frontmatter(text)
    if not yaml_text:
        return False, "No YAML frontmatter"

    en_title, zh_title = extract_titles(file_path.stem, yaml_text, body)
    if not en_title:
        en_title = file_path.stem

    en_clean = sanitize_filename(en_title)
    zh_clean = sanitize_filename(zh_title)
    en_filename = en_clean if en_clean.endswith(".md") else f"{en_clean}.md"
    zh_filename = zh_clean if zh_clean.endswith(".md") else f"{zh_clean}.md"

    en_body, zh_body = split_body(body)

    # Ensure H1 title at top of body if not present
    if not re.search(r"^#\s+", en_body):
        en_body = f"# {en_title}\n\n" + en_body
    else:
        en_body = re.sub(r"^#\s+.*$", f"# {en_title}", en_body, count=1, flags=re.M)

    if not re.search(r"^#\s+", zh_body):
        zh_body = f"# {zh_title}\n\n" + zh_body
    else:
        zh_body = re.sub(r"^#\s+.*$", f"# {zh_title}", zh_body, count=1, flags=re.M)

    en_fm = build_frontmatter(yaml_text, en_title, is_zh=False, en_title=en_title, zh_title=zh_title)
    zh_fm = build_frontmatter(yaml_text, zh_title, is_zh=True, en_title=en_title, zh_title=zh_title)

    en_full = en_fm + "\n" + en_body + "\n"
    zh_full = zh_fm + "\n" + zh_body + "\n"

    sources_dir = vault_dir / "sources"
    en_dest = sources_dir / en_filename
    zh_dest = vault_dir / zh_filename

    if dry_run:
        return True, f"[DRY-RUN] {file_path.name} -> sources/{en_filename} & {zh_filename}"

    # Write files
    sources_dir.mkdir(exist_ok=True)
    en_dest.write_text(en_full, encoding="utf-8")
    zh_dest.write_text(zh_full, encoding="utf-8")

    # If original file is different from zh_dest and not in sources, remove original
    if file_path.resolve() != zh_dest.resolve() and file_path.resolve() != en_dest.resolve():
        file_path.unlink()

    return True, f"Migrated {file_path.name} -> sources/{en_filename} & {zh_filename}"


def main():
    ap = argparse.ArgumentParser(description="Batch migrate bilingual notes to decoupled en/zh")
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--dry-run", action="store_true", help="Preview migrations without writing")
    ap.add_argument("--limit", type=int, default=None, help="Limit number of files to process")
    ap.add_argument("--file", default=None, help="Glob pattern for specific file(s)")
    args = ap.parse_args()

    vault_dir = args.vault.expanduser()
    if not vault_dir.is_dir():
        print(f"Error: vault dir {vault_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    pattern = args.file or "*.md"
    all_files = sorted(vault_dir.glob(pattern))

    migrated = 0
    skipped = 0

    print(f"Scanning {len(all_files)} files in {vault_dir} (pattern='{pattern}')...")

    for f in all_files:
        if f.is_dir() or f.parent.name == "sources":
            continue

        success, msg = process_note(f, vault_dir, dry_run=args.dry_run)
        if success:
            migrated += 1
            print(f"[{migrated}] {msg}")
            if args.limit and migrated >= args.limit:
                print(f"Reached limit {args.limit}.")
                break
        else:
            skipped += 1

    print(f"\nFinished: {migrated} migrated, {skipped} skipped.")


if __name__ == "__main__":
    main()
