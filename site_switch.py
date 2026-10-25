"""
site_switch.py  -  ONE-TIME switch: the Dambulla DEC page becomes the TopGoviya.lk home page
-----------------------------------------------------------------------------------------
Run once by the "Switch home page" robot. It:
  1. keeps the old home page as retail.html (CBSL retail prices, calculators, AI insights),
     with its own address and a retail-focused Google title,
  2. makes dambulla.html the new index.html (home page): removes the test "noindex" tag,
     sets the home address, sets the home page title,
  3. turns dambulla.html into a short page that sends visitors to the home page,
  4. points every "📊 CBSL" menu button on the site to retail.html,
  5. tells the robots: update_index.py now updates retail.html,
     make_dec_image.py refreshes the preview address in index.html
     (backfill.yml is a workflow file, so that one line is changed by hand),
  6. adds retail.html to sitemap.xml.
Everything can be undone from GitHub history.
"""
import glob, os, re, sys

HOME = "https://topgoviya.lk/"
OLD_TITLE = "අද එළවළු මිල | Dambulla Vegetable Price Today Sri Lanka | TopGoviya"
RETAIL_TITLE = "අද එළවළු සිල්ලර මිල | Vegetable Retail Prices Today Sri Lanka | TopGoviya"
NEW_TITLE = "අද එළවළු මිල | දඹුල්ල තොග මිල අද | Dambulla Vegetable Price Today Sri Lanka | TopGoviya"
log = []


def rd(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def wr(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def main():
    if not os.path.exists("dambulla.html"):
        sys.exit("dambulla.html not found - upload the new Dambulla page first.")
    new = rd("dambulla.html")
    if 'class="navlink dec"' not in new:
        sys.exit("dambulla.html is not the new Dambulla page (menu missing) - upload the latest file first.")
    if os.path.exists("retail.html"):
        sys.exit("retail.html already exists - the switch was already done. Nothing changed.")

    # 1. old home page -> retail.html
    old = rd("index.html")
    r = old.replace('href="https://topgoviya.lk/"', 'href="https://topgoviya.lk/retail.html"', 1)
    r = r.replace('<meta property="og:url" content="https://topgoviya.lk/">',
                  '<meta property="og:url" content="https://topgoviya.lk/retail.html">')
    r = r.replace(OLD_TITLE, RETAIL_TITLE)
    wr("retail.html", r)
    log.append("index.html copied to retail.html (address + title updated)")

    # 2. new page -> index.html
    n = re.sub(r"\n<!-- TEST PAGE:[^\n]*-->\n<meta name=\"robots\"[^\n]*>", "", new)
    n = n.replace('<meta property="og:url" content="https://topgoviya.lk/dambulla.html">',
                  '<meta property="og:url" content="https://topgoviya.lk/">')
    n = re.sub(r"<title>[^<]*</title>", "<title>" + NEW_TITLE + "</title>", n, count=1)
    if 'rel="canonical"' not in n:
        n = n.replace('<meta property="og:type"', '<link rel="canonical" href="https://topgoviya.lk/">\n<meta property="og:type"', 1)
    wr("index.html", n)
    log.append("dambulla.html is now index.html (noindex removed, home address + title set)")

    # 3. dambulla.html -> forward to home page
    wr("dambulla.html", """<!DOCTYPE html><html lang="si"><head><meta charset="UTF-8">
<title>දඹුල්ල එළවළු මිල අද | TopGoviya</title>
<link rel="canonical" href="https://topgoviya.lk/">
<meta http-equiv="refresh" content="0; url=/">
<meta name="viewport" content="width=device-width, initial-scale=1">
</head><body><p><a href="/">දඹුල්ල එළවළු මිල අද → TopGoviya.lk</a></p>
<script>location.replace("/")</script></body></html>
""")
    log.append("dambulla.html now forwards to the home page")

    # 4. CBSL menu buttons -> retail.html (main-folder pages)
    count = 0
    for p in glob.glob("*.html"):
        s = rd(p)
        s2 = s.replace('href="index.html" class="navlink retail"', 'href="retail.html" class="navlink retail"')
        if s2 != s:
            wr(p, s2)
            count += 1
    log.append(f"CBSL menu button now opens retail.html on {count} pages")

    # 5. robots
    if os.path.exists("update_index.py"):
        s = rd("update_index.py")
        s2 = s.replace('INDEX = "index.html"', 'INDEX = "retail.html"')
        if s2 != s:
            wr("update_index.py", s2)
            log.append("update_index.py now updates retail.html")
    # NOTE: .github/workflows/backfill.yml is NOT changed here - robots are not allowed to
    # edit workflow files. Add "retail.html" to its "git add" line by hand (one small edit).
    if os.path.exists("make_dec_image.py"):
        s = rd("make_dec_image.py")
        s2 = s.replace('PAGES = ["dambulla.html"]', 'PAGES = ["index.html"]')
        if s2 != s:
            wr("make_dec_image.py", s2)
            log.append("make_dec_image.py now refreshes the preview in index.html")

    # 6. sitemap
    if os.path.exists("sitemap.xml"):
        s = rd("sitemap.xml")
        if "topgoviya.lk/retail.html" not in s and "</urlset>" in s:
            s = s.replace("</urlset>", "  <url><loc>https://topgoviya.lk/retail.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>\n</urlset>")
            wr("sitemap.xml", s)
            log.append("retail.html added to sitemap.xml")

    print("\n".join("✓ " + x for x in log))


if __name__ == "__main__":
    main()
