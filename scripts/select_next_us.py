#!/usr/bin/env python3
import re, sys, pathlib, json, unicodedata
p = pathlib.Path("docs/features/hsa_user_stories.md")
t = p.read_text(encoding="utf-8")

# Each story starts with '## ' and contains a '**Status:** <STATE>' line
blocks = re.split(r'(?m)^##\s+', t)
candidates = []
for b in blocks:
    if not b.strip(): continue
    title = b.splitlines()[0].strip()
    m = re.search(r'\*\*Status:\*\*\s*(\w+)', b)
    if m and m.group(1).upper() == "TODO":
        # slugify
        slug = unicodedata.normalize('NFKD', title.lower())
        slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
        candidates.append((title, slug))
if not candidates:
    print(json.dumps({"title": None, "slug": None}))
    sys.exit(0)
title, slug = candidates[0]
print(json.dumps({"title": title, "slug": slug}))
