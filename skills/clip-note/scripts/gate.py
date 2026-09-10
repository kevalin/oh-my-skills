#!/usr/bin/env python3
"""Unified validation gate for clip-note Obsidian notes.

Supports:
1. Decoupled English Source note (in sources/)
2. Decoupled Chinese Translation note (in vault root)
3. Chinese-original native note
4. Legacy bilingual (<br>) note
5. Vault-wide audit

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
except Exception:
    yaml = None

# ── Regexes ──────────────────────────────────────────────────────────

CTA_RE = re.compile(
    r"(follow my linkedin|comment\s+gtm|yourmax\.ai|if this sounds interesting|"
    r"we[’']?re hiring|stay tuned|if you want to give it a go|"
    r"to pursue this vision, we[’']?ve raised|save this|bookmark|repost|share|"
    r"关注|欢迎关注|感谢阅读|感谢看到这里|转发|收藏|点赞|下篇见|"
    r"follow\s+@|subscribe|sign up|more\s+articles\s+available)",
    re.I,
)
UI_RE = re.compile(
    r"(?mi)^\s*(?:Log in|Sign up|Don't miss what)\s*$"
    r"|^\s*(?:\d+\s*)?(?:Reposts|Likes|Bookmarks)\s*$"
)
UI_RESIDUE = [
    "Log in", "Sign up", "Read more", "Copy", "Subscribe now",
    "Keep reading", "Share this post", "Upgrade to", "Want to publish",
    "Trending", "Like", "Repost",
]
PLACEHOLDERS = ["[image not available]", "<!-- atomic unavailable", "TODO", "TBD"]
PROTECTED_TERM_RE = re.compile(r"智能体|提示词|资源")

REQUIRED_KEYS_EN_SOURCE = ["type", "title", "source", "author", "published", "created", "description", "tags", "translation_note"]
REQUIRED_KEYS_ZH_TRANSLATION = ["type", "title", "original_title", "source", "source_note", "author", "published", "created", "description", "summary", "tags"]
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
    if s in {"---", "## Internal Links", "## Link Candidates", "## 内部链接", "## 链接候选"}:
        return True
    if s.startswith("- [["):
        return True
    if s.startswith("@"):
        return True
    return False


# ── Check groups ────────────────────────────────────────────────────

def check_frontmatter(text: str, required: list[str], allow_skip_related: bool = False, check_format: bool = False) -> list[str]:
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


def check_images(text: str, note_dir: Path, expect: int | None, check_r2_or_local: bool = True) -> list[str]:
    issues: list[str] = []
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    if expect is not None and len(imgs) != expect:
        issues.append(f"image count {len(imgs)} != expected {expect}")
    for p in imgs:
        if p.startswith(("http://", "https://")):
            if "r2.dev" in p or "cloudflare" in p:
                continue
            if re.search(r"pbs\.twimg\.com|twimg\.com|substackcdn\.com", p):
                issues.append(f"remote CDN image remains un-migrated: {p}")
        elif p.startswith("assets/"):
            if not (note_dir / p).exists() and not (note_dir.parent / p).exists():
                issues.append(f"missing local asset: {p}")
    return issues


def check_residue(text: str, x_mode: bool = False, check_protected: bool = True) -> list[str]:
    issues: list[str] = []
    if x_mode:
        if UI_RE.search(text):
            issues.append("possible X UI/metric residual; inspect context")
    for token in PLACEHOLDERS:
        if token in text:
            issues.append(f"placeholder residue: {token}")
    if "<!--" in text:
        issues.append("HTML comment/placeholder remains")
    if text.count("```") % 2:
        issues.append("unbalanced fenced code blocks")
    if "——" in text:
        issues.append("Chinese em dash found; replace with ： or ， or 。")
    if check_protected and PROTECTED_TERM_RE.search(text):
        issues.append("possible protected AI term translated into Chinese (智能体|提示词|资源)")
    return issues


def text_blocks(json_path: Path) -> list[str]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    article = data.get("tweet", {}).get("article", {})
    blocks = article.get("content", {}).get("blocks", [])
    return [b.get("text", "") for b in blocks if b.get("text", "").strip()]


def check_en_coverage(json_path: Path, md_text: str, cta_re: re.Pattern[str], min_cov: float) -> list[str]:
    issues: list[str] = []
    _, body = split_frontmatter(md_text)
    eblob = strip_md(body)
    missing: list[tuple[float, str]] = []
    for raw in text_blocks(json_path):
        normalized = strip_md(raw)
        if not normalized or cta_re.search(normalized):
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


# ── Gate runner ─────────────────────────────────────────────────────

def gate_file(args) -> int:
    path = args.file.expanduser()
    if not path.exists():
        print(f"FAIL: file not found: {path}")
        return 1
    text = path.read_text(encoding="utf-8")
    yaml_text, body = split_frontmatter(text)
    keys = frontmatter_keys(yaml_text)
    issues: list[str] = []

    cta = re.compile(CTA_RE.pattern + ("|" + args.skip_cta_regex if args.skip_cta_regex else ""), re.I)

    # 1. Decoupled English Source note
    if "translation_note" in keys or "sources/" in str(path) or path.parent.name == "sources":
        if "<br>" in body:
            issues.append("English source note must not contain <br>")
        issues.extend(check_frontmatter(text, REQUIRED_KEYS_EN_SOURCE, check_format=True))
        issues.extend(check_residue(text, x_mode=True, check_protected=False))
        issues.extend(check_images(text, path.parent, args.expect_images))
        if args.json:
            issues.extend(check_en_coverage(args.json, text, cta, args.min_word_coverage))

    # 2. Decoupled Chinese Translation note
    elif "source_note" in keys:
        if "<br>" in body:
            issues.append("Chinese translation note must not contain <br>")
        issues.extend(check_frontmatter(text, REQUIRED_KEYS_ZH_TRANSLATION, check_format=True))
        issues.extend(check_residue(text, x_mode=True, check_protected=True))
        issues.extend(check_images(text, path.parent, args.expect_images))

        # Check summary <= 120 stripped chars
        m = re.search(r"^summary:\s*[\"']?(.*?)[\"']?\s*$", yaml_text, re.M)
        if m:
            s_len = len(re.sub(r"\s", "", m.group(1)))
            if s_len > 120:
                issues.append(f"summary exceeds 120 stripped chars: {s_len}")
        else:
            issues.append("missing frontmatter summary")

        # Check source_note link
        m_link = re.search(r"^source_note:\s*[\"']?\[\[(.*?)\]\]", yaml_text, re.M)
        if not m_link:
            issues.append("source_note must be an internal wikilink like '[[sources/Title]]'")
        else:
            target_name = m_link.group(1).replace("sources/", "")
            target_filename = target_name if target_name.endswith(".md") else f"{target_name}.md"
            source_file = path.parent / "sources" / target_filename
            if not source_file.exists():
                issues.append(f"source_note target does not exist: {source_file}")

    # 3. Chinese-original native note (source=zh)
    elif "<br>" not in body and "source_note" not in keys:
        issues.extend(check_frontmatter(text, REQUIRED_KEYS_NATIVE, allow_skip_related=False, check_format=True))
        issues.extend(check_residue(text, check_protected=False))
        issues.extend(check_images(text, path.parent, args.expect_images))

    # 4. Legacy bilingual note (<br>)
    else:
        issues.extend(check_frontmatter(text, REQUIRED_KEYS_BILINGUAL, allow_skip_related=args.no_related_required, check_format=True))
        if "<br>" not in body:
            issues.append("body has no <br> bilingual lines")
        issues.extend(check_residue(text, x_mode=True))
        issues.extend(check_images(text, path.parent, args.expect_images))
        if args.json:
            issues.extend(check_en_coverage(args.json, text, cta, args.min_word_coverage))

    if issues:
        print("FAIL")
        for issue in issues:
            print("-", issue)
        return 1
    print("PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Unified clip-note validation gate")
    ap.add_argument("--file", type=Path, help="Saved .md note to validate")
    ap.add_argument("--json", type=Path, help="fxtwitter JSON dump for X Article coverage")
    ap.add_argument("--source-text", type=Path, help="Cleaned source text dump for web coverage")
    ap.add_argument("--source-url", default="", help="Canonical X URL")
    ap.add_argument("--expect-images", type=int, default=None)
    ap.add_argument("--no-related-required", action="store_true")
    ap.add_argument("--skip-cta-regex", default=None)
    ap.add_argument("--min-word-coverage", type=float, default=0.92)
    args = ap.parse_args()

    if not args.file:
        print("error: --file is required", file=sys.stderr)
        return 2
    return gate_file(args)


if __name__ == "__main__":
    sys.exit(main())
