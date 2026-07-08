#!/usr/bin/env python3
"""Canonical structural check for the IrisNoir static site. Run: python verify.py"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).parent
VOID = {"meta", "link", "img", "br", "hr", "input", "source"}


def main() -> int:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    fails: list[str] = []

    class Balance(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack: list[str] = []

        def handle_starttag(self, tag, attrs):
            if tag not in VOID:
                self.stack.append(tag)

        def handle_endtag(self, tag):
            if not self.stack or self.stack.pop() != tag:
                fails.append(f"tag mismatch near </{tag}>")

    p = Balance()
    p.feed(html)
    if p.stack:
        fails.append(f"unclosed tags: {p.stack}")

    ids = set(re.findall(r'id="([^"]+)"', html))
    fails += [f"broken anchor #{h}" for h in re.findall(r'href="#([^"]+)"', html) if h not in ids]
    # strip <script> blocks so dynamic JS string literals aren't scanned as static assets
    scanless = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    fails += [f"missing asset {s}" for s in re.findall(r'(?:src|href)="((?!https?:|mailto:|#)[^"]+)"', scanless)
              if not (ROOT / s).exists()]

    if css.count("{") != css.count("}"):
        fails.append("CSS brace mismatch")
    defined = set(re.findall(r"\.([a-z][a-z0-9-]*)", css))
    used = {c for cl in re.findall(r'class="([^"]+)"', html) for c in cl.split()}
    if used - defined:
        fails.append(f"classes with no CSS rule: {used - defined}")
    declared = set(re.findall(r"--([a-z0-9-]+)\s*:", css))
    fails += [f"undeclared CSS var --{v}" for v in set(re.findall(r"var\(--([a-z0-9-]+)", css))
              if v not in declared]

    if fails:
        print("FAIL")
        for f in fails:
            print(" -", f)
        return 1
    print(f"PASS: html balanced, {len(ids)} ids, anchors ok, assets ok, css balanced, {len(used)} classes styled, vars ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
