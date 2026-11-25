name: Keppetipola PDF update

# Runs by itself when a PDF is uploaded to the folder keppetipola_pdfs/
# (you can also run it by hand: Actions -> Keppetipola PDF update -> Run workflow)
on:
  push:
    paths:
      - "keppetipola_pdfs/**"
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: keppetipola-pdf
  cancel-in-progress: false

jobs:
  update:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v5
        with:
          ref: main

      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install PDF reader
        run: pip install pypdf

      - name: Read the PDF and update keppetipola_dec.json
        run: python keppetipola_pdf_update.py

      - name: Show report
        if: always()
        run: cat keppetipola_pdf_report.txt || true

      - name: Save changes
        if: always()
        run: |
          git config user.name  "price-bot"
          git config user.email "price-bot@users.noreply.github.com"
          git add keppetipola_dec.json keppetipola_pdf_report.txt || true
          if git diff --staged --quiet; then
            echo "No changes to save."
          else
            git commit -m "Keppetipola prices from PDF ($(date +%Y-%m-%d))"
            git pull --rebase origin main
            git push origin main
          fi
