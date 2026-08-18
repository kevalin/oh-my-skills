#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump a Chinese-original (native) X Article body VERBATIM from fxtwitter JSON.

Usage:
    python dump-native-body.py /tmp/x_<id>.json /tmp/cn_body.txt

Emits one block per paragraph, in order, with type mapping:
  header-one/two -> '# ' / '## ' prefix
  blockquote     -> '> ' prefix
  ordered-list-item / unordered-list-item -> plain line (list numbers are NOT
                    required by the native gate — verified on xiangxiang103
                    Codex tutorial and Russell Palantir FDE note)
  atomic         -> SKIPPED (media/markdown placeholders; markdown atomic
                    content must be extracted separately via entityMap)
  unstyled       -> plain line
Skips empty blocks. No translation, no <br>, no condensation — the note body
must reproduce this output byte-for-byte (minus the type prefixes) to pass
native-mode source coverage.

Why parameterized: an earlier hardcoded dump script (/tmp/dump_cn.py) was
pinned to one tweet's JSON and silently dumped the WRONG article's text when
reused — always pass src and out explicitly.
"""
import json
import sys


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    src, out = sys.argv[1], sys.argv[2]
    d = json.load(open(src))
    blocks = d["tweet"]["article"]["content"]["blocks"]
    lines = []
    for b in blocks:
        typ = b.get("type")
        if typ == "atomic":
            continue
        txt = b.get("text", "").strip()
        if not txt:
            continue
        if typ == "header-two":
            lines.append("## " + txt)
        elif typ == "header-one":
            lines.append("# " + txt)
        elif typ == "blockquote":
            lines.append("> " + txt)
        else:  # unstyled, ordered-list-item, unordered-list-item
            lines.append(txt)
    open(out, "w", encoding="utf-8").write("\n\n".join(lines))
    print(f"dumped {len(lines)} blocks -> {out}")


if __name__ == "__main__":
    main()
