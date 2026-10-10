"""
add_copyright.py  -  adds the TopGoviya.lk copyright line to the hand-made pages
------------------------------------------------------------------------------
The robot-made pages (price/, market/, spice/) get the line from their builders.
This script covers every other .html page in the main folder (index.html,
wholesale.html, spices.html, about.html ...). It also adds a 🌐 sign to the
language switcher on pages that have one, and links to the 11 spice price pages
on the hand-made spice pages:
  - adds the line once, just before </body>, if the page doesn't have it yet
  - otherwise only updates the year (so it changes by itself every January)
It also closes a <script> left open just before </body> (that bug stopped the homepage
spice banner from loading). Nothing else in the pages is touched. Runs daily from GitHub Actions.
"""
import glob, re

from build_pages import COPYRIGHT

BLOCK = ('<div id="tg-copy-wrap" style="text-align:center;font-size:12px;line-height:1.6;color:#7a7264;'
         'max-width:900px;margin:8px auto 76px;padding:0 16px">' + COPYRIGHT + '</div>\n')


GLOBE = ('<span class="tg-globe" aria-hidden="true" style="display:inline-flex;align-items:center;'
         'padding:0 3px 0 10px;font-size:14px;line-height:1;opacity:.8">🌐</span>')


def add_globe(s):
    """Puts a 🌐 at the start of the language switcher (<div class="lang" ...>), once."""
    if "tg-globe" in s:
        return s
    return re.sub(r'(<div class="lang"[^>]*>)', lambda m: m.group(1) + GLOBE, s, count=1)


SPICE_PAGES = ["spices.html", "spice-report.html", "spice-price-guide.html", "cinnamon-price-2026.html"]


def spice_links():
    """A row of links to the 11 spice price pages (spice/<name>.html)."""
    try:
        from build_spice_pages import SPICES
    except Exception:
        return ""
    chip = ("display:inline-flex;align-items:center;gap:4px;padding:6px 12px;border-radius:999px;border:1px solid #0e4f4a;"
            "color:#0e4f4a;background:#fffdf7;font-size:13px;font-weight:700;text-decoration:none")
    links = "".join(f'<a href="spice/{s["slug"]}.html" style="{chip}">{s["emo"]} {s["si"]} මිල අද</a>' for s in SPICES)
    return ('<div id="tg-spice-links" style="max-width:1100px;margin:24px auto 0;padding:0 16px">'
            '<div style="font-weight:700;color:#0e4f4a;margin-bottom:8px">🌶️ කුළුබඩු මිල අද — එක් එක් කුළුබඩුව / Spice price pages</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px">{links}</div></div>\n')


def add_spice_links(path, s):
    if path not in SPICE_PAGES or 'id="tg-spice-links"' in s:
        return s
    block = spice_links()
    if not block:
        return s
    k = s.find('<div id="tg-copy-wrap"')
    if k < 0:
        k = s.rfind("</body>")
    return s[:k] + block + s[k:] if k >= 0 else s


def main():
    changed = []
    for path in sorted(glob.glob("*.html")):
        s = open(path, encoding="utf-8").read()
        new = s
        if 'id="tg-copy"' in new:
            new = re.sub(r'(<span id="tg-copy">)[^<]*(</span>)', lambda m: COPYRIGHT, new, count=1)
        elif "</body>" in new:
            i = new.rfind("</body>")
            # Repair: a <script> left open before </body> would swallow the rest of the page
            # (it stopped the homepage spice banner from loading). Close it first.
            fix = "</script>\n" if new.rfind("<script", 0, i) > new.rfind("</script>", 0, i) else ""
            new = new[:i] + fix + BLOCK + new[i:]
        new = add_globe(new)
        new = add_spice_links(path, new)
        if new != s:
            open(path, "w", encoding="utf-8").write(new)
            changed.append(path)
    print(f"Copyright line / globe: {len(changed)} page(s) updated" + (f" ({', '.join(changed)})" if changed else ""))


if __name__ == "__main__":
    main()
