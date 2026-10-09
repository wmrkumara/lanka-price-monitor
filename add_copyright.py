"""
add_copyright.py  -  adds the TopGoviya.lk copyright line to the hand-made pages
------------------------------------------------------------------------------
The robot-made pages (price/, market/, spice/) get the line from their builders.
This script covers every other .html page in the main folder (index.html,
wholesale.html, spices.html, about.html ...):
  - adds the line once, just before </body>, if the page doesn't have it yet
  - otherwise only updates the year (so it changes by itself every January)
It also closes a <script> left open just before </body> (that bug stopped the homepage
spice banner from loading). Nothing else in the pages is touched. Runs daily from GitHub Actions.
"""
import glob, re

from build_pages import COPYRIGHT

BLOCK = ('<div id="tg-copy-wrap" style="text-align:center;font-size:12px;line-height:1.6;color:#7a7264;'
         'max-width:900px;margin:8px auto 76px;padding:0 16px">' + COPYRIGHT + '</div>\n')


def main():
    changed = []
    for path in sorted(glob.glob("*.html")):
        s = open(path, encoding="utf-8").read()
        if 'id="tg-copy"' in s:
            new = re.sub(r'(<span id="tg-copy">)[^<]*(</span>)', lambda m: COPYRIGHT, s, count=1)
        elif "</body>" in s:
            i = s.rfind("</body>")
            # Repair: a <script> left open before </body> would swallow the rest of the page
            # (it stopped the homepage spice banner from loading). Close it first.
            fix = "</script>\n" if s.rfind("<script", 0, i) > s.rfind("</script>", 0, i) else ""
            new = s[:i] + fix + BLOCK + s[i:]
        else:
            continue
        if new != s:
            open(path, "w", encoding="utf-8").write(new)
            changed.append(path)
    print(f"Copyright line: {len(changed)} page(s) updated" + (f" ({', '.join(changed)})" if changed else ""))


if __name__ == "__main__":
    main()
