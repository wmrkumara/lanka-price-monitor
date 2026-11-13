"""
menu_update.py  -  ONE-TIME: add the "🥕 කැප්පෙටිපොළ" button to the main menu
------------------------------------------------------------------------------
On every main-folder page whose menu has the "🥬 දඹුල්ල" button, it adds
"🥕 කැප්පෙටිපොළ" right after it (same look, green instead of gold), linking to
market/keppetipola.html. Pages without that button are not touched.
Safe to run twice: pages that already have the Keppetipola button are skipped.
"""
import glob, re

GREEN = "#5f7f24"
changed = []

for p in sorted(glob.glob("*.html")):
    s = open(p, encoding="utf-8").read()
    if "market/keppetipola.html\" class=\"navlink" in s or "🥕 කැප්පෙටිපොළ" in s:
        continue
    m = re.search(r'([ \t]*)(<a [^>]*>)🥬 දඹුල්ල</a>', s)
    if not m:
        continue
    pad, tag = m.group(1), m.group(2)
    new = re.sub(r'href="[^"]*"', 'href="market/keppetipola.html"', tag)
    new = new.replace(' aria-current="page"', "")
    new = new.replace('class="navlink dec"', 'class="navlink kep"')
    new = new.replace("background:#a9802a", "background:" + GREEN)
    link = "\n" + pad + new + "🥕 කැප්පෙටිපොළ</a>"
    s = s[:m.end()] + link + s[m.end():]
    if 'class="navlink kep"' in s and ".navlink.kep{" not in s and ".navlink.dec{" in s:
        s = s.replace(".navlink.dec{", ".navlink.kep{background:%s;color:#fff}\n.navlink.dec{" % GREEN, 1)
    open(p, "w", encoding="utf-8").write(s)
    changed.append(p)

print(f"Keppetipola button added on {len(changed)} pages:")
for p in changed:
    print("  ", p)
