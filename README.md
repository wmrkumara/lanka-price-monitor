# Lanka Price Monitor

A self-updating website built from the Central Bank of Sri Lanka (CBSL)
Daily Price Reports. Every morning a script downloads the new report PDF,
extracts the prices, and refreshes the site.

## Files
- `index.html`        the website (open it in any browser to preview)
- `data.json`         the data the site reads (auto-generated)
- `update.py`         downloads new CBSL PDFs + rebuilds data.json
- `requirements.txt`  Python packages needed by update.py
- `.github/workflows/daily.yml`  runs update.py automatically every day

------------------------------------------------------------------
## Option A — Free, automatic, runs itself (recommended)
Hosts the site on GitHub Pages and updates it daily with GitHub Actions.

1. Create a free account at github.com and make a new PUBLIC repository,
   e.g. "lanka-price-monitor".
2. Upload ALL these files, keeping the .github/workflows/ folder structure.
3. In the repo: Settings -> Pages -> "Deploy from a branch" -> branch: main,
   folder: / (root) -> Save. After a minute your site is live at
   https://YOURNAME.github.io/lanka-price-monitor/
4. In the repo: Settings -> Actions -> General -> Workflow permissions ->
   choose "Read and write permissions" -> Save.
5. Go to the Actions tab -> "Update price data" -> Run workflow (to test now).
   From then on it runs every morning on its own and the site updates.

That's it. You never touch it again. Share the github.io link with users.

------------------------------------------------------------------
## Option B — Manual (no GitHub)
1. Install Python, then: pip install -r requirements.txt
2. Each day run:  python update.py     (this refreshes data.json)
3. Upload the whole folder to any web host (Netlify drop, cPanel, etc.),
   or just open index.html locally to view.

------------------------------------------------------------------
## How people use it
They open the link on a phone or computer. No app to install, no login.
They can search a commodity, see today's price and the trend, compare
markets, and see the day's biggest movers.

## Notes
- The site shows retail prices (Dambulla for produce, Negombo for fish).
- update.py keeps a copy of each PDF in pdfs/ so it only downloads new ones.
- A built-in check prints a warning if any price jumps more than 60% in a
  day, in case a PDF parses wrongly.

------------------------------------------------------------------
## Backfill: launch with history instead of starting from zero
By default the site builds history forward from the day you launch.
To start with months/years of past data already loaded:

    pip install -r requirements.txt
    python backfill.py                       # last 365 days
    python backfill.py 2025-06-01 2026-05-29 # a specific range

It downloads the older reports into pdfs/ and rebuilds data.json.
Commit data.json and pdfs/ afterwards. (Run this once locally, or as a
one-off manual GitHub Action.) The daily update.py continues from there.

## Chart time ranges
Each commodity's detail chart has 1M / 3M / 1Y / All buttons, so long
histories stay readable. With only a little data, all ranges show
everything; the buttons become useful as history accumulates.
