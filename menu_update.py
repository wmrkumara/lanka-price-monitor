"""
menu_update.py  -  ONE-TIME: same main menu on every page with a top menu bar
------------------------------------------------------------------------------
On each main-folder page that has a top menu (<nav class="topnav">), it:
  1. adds "🥬 දඹුල්ල" first (the home page, gold),
  2. points the "Retail / CBSL" button to retail.html (the old home page),
  3. adds "🧺 කෘෂි පොළ" right after it,
  4. moves the HARTI / Wholesale button to the end.
Each page keeps its own menu style. Pages without a top menu are not touched.
Safe to run twice: pages that already have "🥬 දඹුල්ල" are skipped.
"""
import glob, re

SKIP = {"index.html", "dambulla.html", "404.html"}
changed = []

for p in sorted(glob.glob("*.html")):
    if p in SKIP:
        continue
    s = open(p, encoding="utf-8").read()
    i = s.find('<nav class="topnav"')
    if i < 0:
        continue
    j = s.find("</nav>", i)
    nav = s[i:j]
    if "🥬 දඹුල්ල" in nav:
        continue
    m = re.search(r'<div class="(navlinks|links|topnav-links)">(.*?)\n(\s*)</div>', nav, re.S)
    if not m:
        print("  ? menu not recognised:", p)
        continue
    box, inner, indent = m.group(1), m.group(2), m.group(3)
    base = {"navlinks": "navlink", "links": "tab"}.get(box, "")
    cls = f' class="{base}"' if base else ""
    links = re.findall(r"[ \t]*<a [^>]*>.*?</a>", inner, re.S)
    pad = re.match(r"[ \t]*", links[0]).group(0) if links else indent + "  "
    def is_retail(a):
        return ('class="navlink retail"' in a) or (re.search(r'href="index\.html"', a) and re.search(r"Retail|CBSL|සිල්ලර", a))
    def is_harti(a):
        return 'href="wholesale.html"' in a
    out, harti = [], []
    out.append(f'{pad}<a href="index.html"{cls} style="background:#a9802a;color:#fff;border-radius:6px;padding:2px 8px">🥬 දඹුල්ල</a>')
    for a in links:
        if is_harti(a):
            harti.append(a); continue
        if is_retail(a):
            a = a.replace('href="index.html"', 'href="retail.html"')
            out.append(a)
            out.append(f'{pad}<a href="krushi-pola.html"{cls}>🧺 කෘෂි පොළ</a>')
            continue
        out.append(a)
    if not any("krushi-pola.html" in a for a in out):
        out.insert(1, f'{pad}<a href="krushi-pola.html"{cls}>🧺 කෘෂි පොළ</a>')
    out += harti
    new_inner = "\n" + "\n".join(x if x.startswith(pad) else pad + x.strip() for x in out)
    nav2 = nav[:m.start(2)] + new_inner + nav[m.end(2):]
    s = s[:i] + nav2 + s[j:]
    open(p, "w", encoding="utf-8").write(s)
    changed.append(p)

print("Menu updated on", len(changed), "pages:", ", ".join(changed) if changed else "none")
