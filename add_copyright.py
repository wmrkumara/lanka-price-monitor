"""
add_copyright.py  -  adds the TopGoviya.lk copyright line to the hand-made pages
------------------------------------------------------------------------------
The robot-made pages (price/, market/, spice/) get the line from their builders.
This script covers every other .html page in the main folder (index.html,
wholesale.html, spices.html, about.html ...). It also adds a 🌐 sign to the
language switcher on pages that have one, and links to the 11 spice price pages
on the hand-made spice pages, and link-preview pictures for pages listed in PAGE_PREVIEWS:
  - adds the line once, just before </body>, if the page doesn't have it yet
  - otherwise only updates the year (so it changes by itself every January)
It also closes a <script> left open just before </body> (that bug stopped the homepage
spice banner from loading). Nothing else in the pages is touched. Runs daily from GitHub Actions.
"""
import glob, os, re

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


# Fixed link-preview pictures (share/...) for hand-made pages that have none
PAGE_PREVIEWS = {"breakeven.html": "share/breakeven.png", "breakeven-calculator-guide.html": "share/breakeven.png"}


def add_preview(path, s):
    """Adds og:image / twitter tags so WhatsApp and Facebook show a picture (only if missing)."""
    img = PAGE_PREVIEWS.get(path)
    if not img or 'property="og:image"' in s or not os.path.exists(img):
        return s
    url = "https://topgoviya.lk/" + img
    tags = (f'\n<meta property="og:image" content="{url}">\n<meta property="og:image:width" content="1200">'
            f'\n<meta property="og:image:height" content="630">')
    if 'name="twitter:card"' in s:
        s = re.sub(r'<meta name="twitter:card" content="[^"]*">', '<meta name="twitter:card" content="summary_large_image">', s, count=1)
    else:
        tags += '\n<meta name="twitter:card" content="summary_large_image">'
    tags += f'\n<meta name="twitter:image" content="{url}">'
    m = re.search(r'<meta property="og:description"[^>]*>', s) or re.search(r'<meta property="og:title"[^>]*>', s)
    if m:
        return s[:m.end()] + tags + s[m.end():]
    k = s.find("</head>")
    return s[:k] + tags + "\n" + s[k:] if k >= 0 else s


def add_events(s):
    """Loads events.js (Google Analytics action counts) once per page."""
    if "events.js" in s or "</body>" not in s:
        return s
    k = s.rfind("</body>")
    return s[:k] + '<script defer src="/events.js?v=1"></script>\n' + s[k:]


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
        new = add_preview(path, new)
        new = add_events(new)
        if new != s:
            open(path, "w", encoding="utf-8").write(new)
            changed.append(path)
    print(f"Copyright line / globe: {len(changed)} page(s) updated" + (f" ({', '.join(changed)})" if changed else ""))


if __name__ == "__main__":
    main()
