# Vault Maintenance: Mass Rename to title.md

When the filename rule changes (or historical files predate it), retrofit the
whole vault. Procedure proven on 390+ files (2026-07):

## 1. Analyze first — never rename blind

```python
# Per file: parse frontmatter `title`, extract English side
# (split on '<br>' OR ' - ' when the right side contains CJK),
# slugify illegal chars, then dry-run compute old→new map.
```

Classify files into buckets:
- `EN - CN.md` (double name) → `EN.md`
- pure-Chinese name (Chinese-source article) → keep as-is
- already-correct English name → keep
- other legacy formats (author suffix, `X Article <id>`, colon→` - `) → fix

Count collisions FIRST: (a) target already exists, (b) two sources map to the
same target. Both mean historical duplicates — merge before renaming.

## 2. Merge duplicates before rename

Same source + same title → keep the more complete version (bilingual title /
valid `published` / larger body), move the other into `_duplicates/` at vault
root. **Never delete** — moving is reversible. Merge FIRST so the rename plan
has zero collisions.

## 3. Rename in rounds

Two rounds were needed on the real vault:
- Round 1: `<br>`-separated bilingual titles
- Round 2: ` - `-separated titles (web articles) where the right side has CJK

Re-generate the plan between rounds — each round can surface new cases.

## 4. Update wikilinks with a CHAINED mapping

Build `old → new` from rename manifests + duplicate moves. Then scan every
`.md` for `[[old]]` and replace.

**Pitfall — mapping chains break:** if a duplicate's kept version was itself
renamed later, a single-level `old → kept-name` mapping leaves stale links.
Example: `The Stanford STORM Method - ... - 中文.md` → kept → slugged final
name; 3 links still pointed at the intermediate kept name. Fix: resolve the
mapping transitively (walk `old → mid → final`) before replacing, or do a
second sweep for any link whose target no longer resolves.

## 5. Verify

- 0 EN-CN double names remaining
- 0 wikilinks pointing at old double names (or any non-existent target)
- 0 duplicate groups recreated by the rename
- no empty/shortened names
- gate scripts still PASS on a sample of renamed notes

## Notes

- Concept links (`[[Agent]]`, `[[MCP]]` — no such file) are normal Obsidian
  practice (uncreated-note links); do NOT count them as orphans.
- Missing images referenced as `assets/...` are pre-existing issues — renaming
  `.md` files never touches `assets/`, don't get drawn into fixing them.
- Files with missing `title` frontmatter (24 on the real vault) block renaming
  — decide per-file: extract from H1 or leave the legacy name.
