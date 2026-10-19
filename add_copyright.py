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


EXTRA_SITEMAP = ["contact.html", "useful-links.html"]


def ensure_sitemap():
    """Adds hand-made pages listed in EXTRA_SITEMAP to sitemap.xml if they are missing."""
    if not os.path.exists("sitemap.xml"):
        return
    xml = open("sitemap.xml", encoding="utf-8").read()
    add = "".join(f"  <url>\n    <loc>https://topgoviya.lk/{p}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.5</priority>\n  </url>\n"
                  for p in EXTRA_SITEMAP if os.path.exists(p) and f"https://topgoviya.lk/{p}<" not in xml)
    if add:
        open("sitemap.xml", "w", encoding="utf-8").write(xml.replace("</urlset>", add + "</urlset>"))


TOP_CONTACT = ('<style id="tgc-style">.tgc-top{display:inline-flex;align-items:center;gap:4px;margin:0 8px 0 auto;padding:5px 11px;text-transform:none;letter-spacing:0;'
               'border-radius:999px;background:#0e4f4a;color:#fff!important;font-weight:700;font-size:13px;text-decoration:none;white-space:nowrap}'
               '.tgc-top .tgc-ta,.tgc-top .tgc-en{display:none}html[lang="ta"] .tgc-top .tgc-si,html[lang="en"] .tgc-top .tgc-si{display:none}'
               'html[lang="ta"] .tgc-top .tgc-ta,html[lang="en"] .tgc-top .tgc-en{display:inline}</style>'
               '<a class="tgc-top" href="contact.html"><svg width="14" height="14" viewBox="0 0 24 24" fill="#25D366" aria-hidden="true" style="flex-shrink:0;vertical-align:-2px"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg> <span class="tgc-si">අමතන්න</span><span class="tgc-ta">தொடர்பு</span>'
               '<span class="tgc-en">Contact</span></a>')


def add_top_contact(path, s):
    """A small Contact button next to the language switch (pages that have one), once."""
    if path == "contact.html" or "tgc-top" in s:
        return s
    k = s.find('<div class="lang"')
    return s[:k] + TOP_CONTACT + s[k:] if k >= 0 else s


def add_quick_calc(path, s):
    """Break-even page: load quick-calc.js (the ⚡ Quick calculation card), once."""
    if path != "breakeven.html" or "quick-calc.js" in s or "</body>" not in s:
        return s
    k = s.rfind("</body>")
    return s[:k] + '<script defer src="quick-calc.js?v=1"></script>\n' + s[k:]


def fix_canonical(path, s):
    """If a page tells Google its 'official address' is a page that does not exist,
    point it back to the page's real address (found: the Netherlands article, Oct 2026)."""
    def repl(m):
        url = m.group(2)
        local = url.replace("https://topgoviya.lk/", "", 1) if url.startswith("https://topgoviya.lk/") else None
        if local is None:
            return m.group(0)
        target = local or "index.html"
        if target.endswith("/"):
            target += "index.html"
        if os.path.exists(target):
            return m.group(0)
        return m.group(1) + "https://topgoviya.lk/" + ("" if path == "index.html" else path) + m.group(3)
    s = re.sub(r'(<link rel="canonical" href=")([^"]+)(")', repl, s, count=1)
    return re.sub(r'(<meta property="og:url" content=")([^"]+)(")', repl, s, count=1)


def main():
    changed = []
    for path in sorted(glob.glob("*.html")):
        s = open(path, encoding="utf-8").read()
        new = s
        if 'id="tg-copy"' in new:
            new = re.sub(r'<span id="tg-copy">.*?</span>', lambda m: COPYRIGHT, new, count=1, flags=re.S)
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
        new = add_top_contact(path, new)
        new = add_quick_calc(path, new)
        new = fix_canonical(path, new)
        if new != s:
            open(path, "w", encoding="utf-8").write(new)
            changed.append(path)
    ensure_sitemap()
    print(f"Copyright line / globe: {len(changed)} page(s) updated" + (f" ({', '.join(changed)})" if changed else ""))


if __name__ == "__main__":
    main()
