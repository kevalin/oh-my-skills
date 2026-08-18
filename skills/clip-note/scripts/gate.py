#!/usr/bin/env python3
"""Unified validation gate for clip-note bilingual (EN/CN) Obsidian notes.

One entry point for every check the clip-note pipeline needs. Mode is
auto-detected from the arguments and the note itself:

  # 1. Structural check (+ optional source coverage)
  python gate.py --file note.md [--json x_123.json] [--source-text src.txt]
                  [--expect-images N] [--no-related-required]
                  [--skip-cta-regex RE] [--min-word-coverage 0.92]

  # 2. Vault-wide <br> format audit (optionally auto-fix)
  python gate.py --audit ~/Documents/obsidian/Interpreter [--fix] [--only-br]

Detection rules:
  - --json given, note has NO <br>   -> Chinese-original X Article gate
  - --json given, note HAS <br>      -> bilingual X Article gate
  - --source-text given              -> web article gate
  - neither                          -> structural-only bilingual check

Exit code: 0 = PASS, 1 = FAIL, 2 = usage/runtime error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

# ── Regexes (EN/CN fixed pair) ──────────────────────────────────────

CTA_RE = re.compile(
    r"(follow my linkedin|comment\s+gtm|yourmax\.ai|if this sounds interesting|"
    r"we[’']?re hiring|stay tuned|if you want to give it a go|"
    r"to pursue this vision, we[’']?ve raised|save this|bookmark|repost|share|"
    r"关注|欢迎关注|感谢阅读|感谢看到这里|转发|收藏|点赞|下篇见|"
    r"follow\s+@|subscribe|sign up|more\s+articles\s+available)",
    re.I,
)
# UI chrome catches platform residue, not legitimate prose.
UI_RE = re.compile(
    r"(?mi)^\s*(?:Log in|Sign up|Don't miss what)\s*$"
    r"|^\s*(?:\d+\s*)?(?:Reposts|Likes|Bookmarks)\s*$"
)
UI_RESIDUE = [
    "Log in", "Sign up", "Read more<br>", "Copy<br>", "Subscribe now",
    "Keep reading", "Share this post", "Upgrade to", "Want to publish",
    "Trending", "Like", "Repost",
]
PLACEHOLDERS = ["[image not available]", "<!-- atomic unavailable", "TODO", "TBD"]
PROTECTED_TERM_RE = re.compile(r"智能体|提示词|资源")
REQUIRED_KEYS_BILINGUAL = ["type", "title", "source", "author", "published", "created", "description", "tags"]
REQUIRED_KEYS_NATIVE = ["type", "title", "source", "author", "published", "created", "description", "summary", "tags", "related"]


# ── Shared helpers ──────────────────────────────────────────────────

def split_frontmatter(text: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def frontmatter_keys(yaml_text: str) -> set[str]:
    keys = set()
    for line in yaml_text.splitlines():
        if line and not line.startswith((" ", "-")) and ":" in line:
            keys.add(line.split(":", 1)[0].strip())
    return keys


def strip_md(s: str) -> str:
    s = s.replace("\\$", "$")
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    s = s.replace("**", "").replace("*", "").replace("`", "")
    s = s.replace("<br>", " ")
    return re.sub(r"\s+", " ", s or "").strip()


def collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


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


# ── Check groups ────────────────────────────────────────────────────

def check_frontmatter(text: str, required: list[str], allow_skip_related: bool, check_format: bool = False) -> list[str]:
    issues: list[str] = []
    yaml_text, _ = split_frontmatter(text)
    if not yaml_text:
        return ["missing YAML frontmatter"]
    keys = frontmatter_keys(yaml_text)
    missing = [k for k in required if k not in keys and not (allow_skip_related and k == "related")]
    if missing:
        issues.append("missing frontmatter keys: " + ", ".join(missing))
    if check_format:
        if re.search(r'^published:\s+"', yaml_text, re.M):
            issues.append("published should be date-only and unquoted")
        if re.search(r"^published:\s+\d{4}-\d{2}-\d{2}T", yaml_text, re.M):
            issues.append("published should not be a full datetime")
        if re.search(r"^created:\s+\d", yaml_text, re.M):
            issues.append("created datetime should be quoted in raw YAML")
    if yaml is not None:
        try:
            parsed = yaml.safe_load(yaml_text) or {}
            if parsed.get("type") != "clipper":
                issues.append("frontmatter type must be exact: type: clipper")
            if not str(parsed.get("source", "")).startswith("https://"):
                issues.append("YAML source is missing or non-HTTPS")
        except Exception as exc:
            issues.append(f"YAML parse failed: {exc}")
    return issues


def check_br_structure(text: str) -> list[str]:
    issues: list[str] = []
    _, body = split_frontmatter(text)
    if "<br>" not in body:
        issues.append("body has no <br> bilingual lines")
    if "<br><br>" in body:
        issues.append("double <br><br> artifact found")
    if re.search(r"<br>\s*[-*]\s+", body):
        issues.append("Chinese side starts with a bullet marker after <br>")
    if re.search(r"<br>\s*\d+\.\s+", body):
        issues.append("Chinese side starts with an ordered-list marker after <br>")
    if re.search(r"<br>\s*#{1,6}\s+", body):
        issues.append("Chinese side repeats a heading marker after <br>")
    first_heading = next((ln for ln in body.splitlines() if ln.startswith("# ")), "")
    if first_heading and "<br>" not in first_heading:
        issues.append("H1 lacks <br> bilingual title")
    if "## Internal Links" not in text or "## Link Candidates" not in text:
        issues.append("missing Internal Links or Link Candidates section")
    return issues


def check_orphans(body: str) -> list[str]:
    issues: list[str] = []
    in_code = False
    appendix_heading = re.compile(r"^(##\s+)?(Internal Links|Link Candidates)(<br>|$)")
    for lineno, line in enumerate(body.splitlines(), 1):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or is_structural_line(s):
            continue
        if "<br>" in s:
            continue
        if re.match(r"^(#{1,6}\s+|>\s+|-\s+|\d+\.\s+).+", s) or len(s) > 40:
            if s.startswith("@") or appendix_heading.search(s):
                continue
            issues.append(f"L{lineno}: missing <br>: {s[:100]}")
    return issues


def check_residue(text: str, x_mode: bool = False, check_protected: bool = True) -> list[str]:
    issues: list[str] = []
    if x_mode:
        if UI_RE.search(text):
            issues.append("possible X UI/metric residual; inspect context")
    else:
        for token in UI_RESIDUE:
            if token in text:
                issues.append(f"possible UI/CTA residue: {token}")
    for token in PLACEHOLDERS:
        if token in text:
            issues.append(f"placeholder residue: {token}")
    if "<!--" in text:
        issues.append("HTML comment/placeholder remains")
    if text.count("```") % 2:
        issues.append("unbalanced fenced code blocks")
    if x_mode and ("——" in text or re.search(r"[\u4e00-\u9fff]—|—[\u4e00-\u9fff]", text)):
        issues.append("Chinese em dash found; verify the source also used a dash")
    if check_protected and PROTECTED_TERM_RE.search(text):
        issues.append("possible protected AI term translated into Chinese")
    return issues


def check_images(text: str, note_dir: Path, expect: int | None, local_only: bool = False) -> list[str]:
    issues: list[str] = []
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    if expect is not None and len(imgs) != expect:
        issues.append(f"image count {len(imgs)} != expected {expect}")
    if local_only:
        for p in imgs:
            if p.startswith(("http://", "https://")):
                issues.append(f"remote image remains: {p}")
            elif not p.startswith("assets/"):
                issues.append(f"non-assets image path: {p}")
            elif not (note_dir / p).exists():
                issues.append(f"missing local asset: {p}")
        if re.search(r"pbs\.twimg\.com|twimg\.com|substackcdn\.com", text):
            issues.append("remote CDN URL remains in note")
    return issues


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


def check_x_bilingual(json_path: Path, md_text: str, cta_re: re.Pattern[str], min_cov: float) -> list[str]:
    """Bilingual X Article: English side must cover non-CTA source blocks."""
    issues: list[str] = []
    eblob = english_blob(md_text)
    missing: list[tuple[float, str]] = []
    for raw in text_blocks(json_path):
        normalized = strip_md(raw)
        if not normalized:
            continue
        if cta_re.search(normalized):
            continue
        parts = [strip_md(p) for p in re.split(r"\n+", raw) if strip_md(p)]
        if normalized in eblob or all(p in eblob for p in parts):
            continue
        words = [w.lower() for w in re.findall(r"[A-Za-z0-9$/.:-]+", normalized) if len(w) > 1]
        coverage = sum(1 for w in words if w in eblob.lower()) / max(1, len(words))
        if coverage < min_cov:
            missing.append((coverage, normalized[:220]))
    if missing:
        issues.append("material source coverage missing " + str(len(missing)) + " block(s): "
                      + "; ".join(f"{cov:.2f} {snippet}" for cov, snippet in missing[:5]))
    return issues


def check_x_native(json_path: Path, md_text: str, source_url: str, cta_re: re.Pattern[str]) -> list[str]:
    """Chinese-original X Article: full visible text must cover non-CTA blocks."""
    issues: list[str] = []
    if "<br>" in md_text:
        issues.append("Chinese-original note should not use bilingual <br> body format")
    if source_url:
        yaml_text, _ = split_frontmatter(md_text)
        if re.search(rf"^source:\s*[\"']?{re.escape(source_url)}[\"']?\s*$", yaml_text, re.M) is None:
            issues.append(f"source mismatch: expected {source_url!r}")
    if "summary" in md_text:
        m = re.search(r"^summary:\s*[\"']?(.*?)[\"']?\s*$", md_text[:2000], re.M)
        if m and (len(m.group(1).strip()) >= 250 or not m.group(1).strip()):
            issues.append("summary empty or >=250 chars")
    vis = strip_md(re.sub(r"^---\n.*?\n---\n", "", md_text, flags=re.S))
    missing: list[tuple[int, str]] = []
    skipped: list[int] = []
    for i, raw in enumerate(text_blocks(json_path)):
        s = collapse(raw)
        if not s:
            continue
        if cta_re.search(s):
            skipped.append(i)
            continue
        if s not in vis:
            missing.append((i, s[:120]))
    if missing:
        issues.append("missing non-CTA source blocks: " + repr(missing[:8]))
    return issues


def check_web_coverage(source_path: Path, md_text: str) -> list[str]:
    issues: list[str] = []
    saved_norm = strip_md(md_text)
    missing = []
    for line in source_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if len(raw) < 25:
            continue
        low = raw.lower()
        if any(x in low for x in ["subscribe", "sign up", "log in", "share this", "privacy policy"]):
            continue
        if strip_md(raw) not in saved_norm:
            missing.append(raw[:140])
    if missing:
        issues.append(f"source coverage missing {len(missing)} lines; first examples: {missing[:5]}")
    return issues


def gate_file(args) -> int:
    path = args.file.expanduser()
    if not path.exists():
        print(f"FAIL: file not found: {path}")
        return 1
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    native = args.json is not None and "<br>" not in text
    x_bilingual = args.json is not None and not native

    if native:
        issues.extend(check_frontmatter(text, REQUIRED_KEYS_NATIVE, allow_skip_related=False, check_format=True))
        issues.extend(check_residue(text, check_protected=False))
        issues.extend(check_images(text, path.parent, args.expect_images, local_only=True))
        if args.json:
            cta = re.compile(CTA_RE.pattern + ("|" + args.skip_cta_regex if args.skip_cta_regex else ""), re.I)
            issues.extend(check_x_native(args.json, text, args.source_url or "", cta))
    else:
        issues.extend(check_frontmatter(text, REQUIRED_KEYS_BILINGUAL, allow_skip_related=args.no_related_required, check_format=x_bilingual))
        if not args.no_related_required:
            issues.extend(check_br_structure(text))
        _, body = split_frontmatter(text)
        issues.extend(check_orphans(body))
        issues.extend(check_residue(text, x_mode=x_bilingual))
        issues.extend(check_images(text, path.parent, args.expect_images))
        if not x_bilingual and "\\$" not in text and re.search(r"(?<!\\)\$", english_blob(text)):
            issues.append("unescaped bare $ on English side of bilingual lines")
        cta = re.compile(CTA_RE.pattern + ("|" + args.skip_cta_regex if args.skip_cta_regex else ""), re.I)
        if args.json:
            issues.extend(check_x_bilingual(args.json, text, cta, args.min_word_coverage))
        if args.source_text:
            issues.extend(check_web_coverage(args.source_text, text))

    if issues:
        print("FAIL")
        for issue in issues:
            print("-", issue)
        return 1
    print("PASS")
    return 0


# ── Audit mode (vault-wide) ─────────────────────────────────────────

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
        if in_code or is_structural_line(s):
            continue
        if (s.startswith(("#", "- ", ">")) or re.match(r"\d+\. ", s) or len(s) > 40) and "<br>" not in s:
            issues.append(f"L{idx + 1}: missing <br>: {s[:80]}")
        if "<br><br>" in s:
            issues.append(f"L{idx + 1}: double <br><br>")
        if re.search(r"<br>\s*[-*]\s+", s) or re.search(r"<br>\s*\d+\.\s+", s):
            issues.append(f"L{idx + 1}: marker after <br>: {s[:80]}")
        if re.search(r"<br>\s*[#]+\s*[\u4e00-\u9fff]", s):
            issues.append(f"L{idx + 1}: heading marker after <br>: {s[:80]}")
    if not only_br:
        for idx, line in enumerate(lines):
            s = line.strip()
            if "<br>" not in s:
                continue
            en = re.sub(r"`[^`]*`", "", s.split("<br>", 1)[0])
            if re.search(r"(?<!\\)\$", en):
                issues.append(f"L{idx + 1}: unescaped $ on English side")
            if "——" in line:
                issues.append(f"L{idx + 1}: Chinese em-dash —— (verify source had dash)")
    if fix:
        new_lines = [line.replace("<br><br>", "<br>") for line in lines]
        if new_lines != lines:
            path.write_text(text.replace("\n".join(lines), "\n".join(new_lines)), encoding="utf-8")
            issues.append(f"{path.name}: auto-fixed {sum(1 for a, b in zip(lines, new_lines) if a != b)} line(s)")
    return issues


def audit_vault(vault: Path, fix: bool, only_br: bool) -> int:
    if not vault.is_dir():
        print(f"not a directory: {vault}", file=sys.stderr)
        return 2
    total_files = total_issues = 0
    for md in sorted(vault.glob("*.md")):
        issues = audit_file(md, fix, only_br)
        if issues:
            total_files += 1
            total_issues += len(issues)
            for issue in issues:
                print(f"{md.name}: {issue}")
    if total_issues:
        print(f"\nFAIL: {total_issues} issue(s) in {total_files} file(s)")
        return 1
    print(f"PASS: {len(list(vault.glob('*.md')))} files, no violations")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Unified clip-note validation gate")
    ap.add_argument("--file", type=Path, help="Saved .md note to validate")
    ap.add_argument("--json", type=Path, help="fxtwitter JSON dump for X Article coverage")
    ap.add_argument("--source-text", type=Path, help="Cleaned source text dump for web coverage")
    ap.add_argument("--source-url", default="", help="Canonical X URL (native mode source match)")
    ap.add_argument("--expect-images", type=int, default=None)
    ap.add_argument("--no-related-required", action="store_true", help="Bilingual: do not require related/Internal Links/Link Candidates")
    ap.add_argument("--skip-cta-regex", default=None, help="Extra regex for intentional CTA/promo omissions")
    ap.add_argument("--min-word-coverage", type=float, default=0.92)
    ap.add_argument("--audit", type=Path, help="Vault directory for <br> format audit")
    ap.add_argument("--fix", action="store_true", help="Audit mode: auto-fix double <br><br>")
    ap.add_argument("--only-br", action="store_true", help="Audit mode: only <br> mechanical rules")
    args = ap.parse_args()

    if args.audit:
        return audit_vault(args.audit, args.fix, args.only_br)
    if not args.file:
        print("error: --file or --audit required", file=sys.stderr)
        return 2
    return gate_file(args)


if __name__ == "__main__":
    sys.exit(main())
