"""
build_market_pages.py  -  TopGoviya.lk market pages
---------------------------------------------------
Reads harti_data.json (+ data.json for CBSL Dambulla) and writes:
  market/<market>.html        one Google-friendly page per HARTI market (10)
  market/index.html           hub page listing all 10 markets
  harti_market_history.json   small per-market price history (kept 120 days)
  sitemap.xml                 keeps every other page, adds/refreshes /market/ pages

Runs daily from GitHub Actions after harti_update.py.
Uses build_pages.py (same folder) for the shared look, and only the
Python standard library.
"""
import json, os, re
from urllib.parse import quote
from datetime import datetime, timedelta

from build_pages import CSS, GA_ID, SITE, e, money, fdate, slug, MONTHS, NAMES as CBSL_NAMES, EMOJIS, UNITS

OUT_DIR = "market"
HIST_FILE = "harti_market_history.json"
KEEP_DAYS = 120
HARTI_URL = "https://www.harti.gov.lk/daily-price.php"
CBSL_URL = "https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report"

# ---------------------------------------------------------------- names (same as live wholesale.html)
MKT = {
    "Peliyagoda":      {"si": "පෑලියගොඩ",    "ta": "பேலியகோட",    "slug": "peliyagoda"},
    "Kandy":           {"si": "මහනුවර",      "ta": "கண்டி",        "slug": "kandy"},
    "Dambulla":        {"si": "දඹුල්ල",      "ta": "தம்புள்ள",     "slug": "dambulla"},
    "Meegoda":         {"si": "මීගොඩ",       "ta": "மீகொட",       "slug": "meegoda"},
    "Norochchole":     {"si": "නොරොච්චෝලේ", "ta": "நொரோச்சோலே",  "slug": "norochchole"},
    "Thambuththegama": {"si": "තඹුත්තේගම",   "ta": "தம்புத்தேகம",  "slug": "thambuththegama"},
    "Keppetipola":     {"si": "කෑප්පෙටිපොළ", "ta": "கெப்பெட்டிபொல", "slug": "keppetipola"},
    "Nuwaraeliya":     {"si": "නුවරඑළිය",    "ta": "நுவரெலியா",    "slug": "nuwara-eliya"},
    "Bandarawela":     {"si": "බණ්ඩාරවෙල",   "ta": "பண்டாரவெல",    "slug": "bandarawela"},
    "Veyangoda":       {"si": "වේයන්ගොඩ",    "ta": "வேயன்கொட",     "slug": "veyangoda"},
}
# English name people search for (Nuwaraeliya is written "Nuwara Eliya" in searches)
MKT_EN = {"Nuwaraeliya": "Nuwara Eliya"}

H_SI = {
 "Beans":"බෝංචි","Carrot":"කැරට්","Leeks":"ලීක්ස්","Beetroot":"බීට්රූට්",
 "Beetroot (N.Eliya)":"බීට්රූට් (නුවරඑළිය)","Knolkhol":"නෝල්කෝල්","Raddish":"රාබු",
 "Cabbage (N.Eliya)":"ගෝවා (නුවරඑළිය)","Cabbage (Kandy)":"ගෝවා (නුවර)","Tomato":"තක්කාලි",
 "Ladies Fingers":"බණ්ඩක්කා","Brinjals":"වම්බටු","Capsicum":"මාළු මිරිස්","Pumpkin":"වට්ටක්කා",
 "Cucumber":"පිපිඤ්ඤා","Bitter Gourd":"කරවිල","Snake Gourd":"පතෝල","Drumstick":"මුරුංගා",
 "Luffa":"වැටකොළු","Long Beans":"මෑකරල්","Ash Plantains":"අළු කෙසෙල්",
 "Green Chillies":"අමු මිරිස්","Lime":"දෙහි","Sweet Potato":"බතල","Manioc":"මඤ්ඤොක්කා",
 "Eggplant":"එළබටු","Potato (Imported)":"අර්තාපල් (ආනයනික)",
 "Potato (Welimada)":"අර්තාපල් (වැලිමඩ)","Potato (N.Eliya)":"අර්තාපල් (නුවරඑළිය)",
 "Big Onion (Imported)":"ලොකු ළූණු (ආනයනික)",
 "Banana Ambul":"ඇඹුල් කෙසෙල්","Banana Kolikuttu":"කොලිකුට්ටු","Banana Seeni":"සීනි කෙසෙල්",
 "Papaya":"පැපොල්","Pineapple (Large)":"අන්නාසි (ලොකු)","Avocado":"අලිගැටපේර",
 "Passion Fruit":"වැල් දොඩම්","Anamalu":"ආනමාළු කෙසෙල්","Pineapple (Medium)":"අන්නාසි (මධ්‍යම)",
 "Pineapple (Small)":"අන්නාසි (කුඩා)","Mango (Betti)":"අඹ (බෙට්ටි)","Mango (Karathakolomban)":"අඹ (කර්තකොළඹ)",
 "Woodapple":"දිවුල්","Orange":"දොඩම්",
}
H_TA = {
 "Beans":"பீன்ஸ்","Carrot":"கேரட்","Leeks":"லீக்ஸ்","Beetroot":"பீட்ரூட்",
 "Beetroot (N.Eliya)":"பீட்ரூட் (நுவரெலியா)","Knolkhol":"நோல்கோல்","Raddish":"ராடிஷ்",
 "Cabbage (N.Eliya)":"முட்டைக்கோஸ் (நுவரெலியா)","Cabbage (Kandy)":"முட்டைக்கோஸ் (கண்டி)",
 "Tomato":"தக்காளி","Ladies Fingers":"வெண்டைக்காய்","Brinjals":"கத்தரிக்காய்",
 "Capsicum":"குடை மிளகாய்","Pumpkin":"பூசணி","Cucumber":"வெள்ளரிக்காய்",
 "Bitter Gourd":"பாகற்காய்","Snake Gourd":"புடலங்காய்","Drumstick":"முருங்கை",
 "Luffa":"பீர்க்கங்காய்","Long Beans":"தட்டைப்பயறு","Ash Plantains":"வாழைக்காய்",
 "Green Chillies":"பச்சை மிளகாய்","Lime":"எலுமிச்சை","Sweet Potato":"சர்க்கரைவள்ளி",
 "Manioc":"மரவள்ளி","Eggplant":"கத்திரிக்காய்",
 "Potato (Imported)":"உருளை (இறக்குமதி)","Potato (Welimada)":"உருளை (வெலிமட)",
 "Potato (N.Eliya)":"உருளை (நுவரெலியா)","Big Onion (Imported)":"பெரிய வெங்காயம் (இறக்குமதி)",
 "Banana Ambul":"ஆம்பல் வாழை","Banana Kolikuttu":"கொலிக்குட்டு","Banana Seeni":"சர்க்கரை வாழை",
 "Anamalu":"ஆனைமாலு வாழை","Papaya":"பப்பாளி","Pineapple (Large)":"அன்னாசி (பெரியது)",
 "Pineapple (Medium)":"அன்னாசி (நடுத்தரம்)","Pineapple (Small)":"அன்னாசி (சிறியது)","Avocado":"அவோகேடோ",
 "Passion Fruit":"பேஷன் பழம்","Mango (Betti)":"மாம்பழம் (பெட்டி)",
 "Mango (Karathakolomban)":"மாம்பழம் (கறுத்தக்கொழும்பான்)","Woodapple":"விளாம்பழம்","Orange":"தோடம்பழம்",
}
CAT_SI = {"Up Country Vegetables": "උඩරට එළවළු", "Low Country Vegetables": "පහතරට එළවළු",
          "Potatoes & Onions": "අර්තාපල් හා ළූණු", "Fruits & Banana": "පළතුරු හා කෙසෙල්"}
CAT_ORDER = ["Up Country Vegetables", "Low Country Vegetables", "Potatoes & Onions", "Fruits & Banana"]

# HARTI crop -> CBSL crop (to link to the /price/ page of the same crop)
TO_CBSL = {"Beans":"Beans","Carrot":"Carrot","Cabbage (Kandy)":"Cabbage","Cabbage (N.Eliya)":"Cabbage",
           "Tomato":"Tomato","Brinjals":"Brinjal","Pumpkin":"Pumpkin","Snake Gourd":"Snake gourd",
           "Green Chillies":"Green Chilli","Lime":"Lime","Potato (N.Eliya)":"Potato (Local)",
           "Potato (Welimada)":"Potato (Local)","Potato (Imported)":"Potato (Imp)",
           "Big Onion (Imported)":"Big Onion (Imp)","Beetroot":"Beetroot","Leeks":"Leeks",
           "Knolkhol":"Knol-khol","Drumstick":"Drumstick","Manioc":"Manioc","Ash Plantains":"Ash Plantain"}

def hsi(n): return H_SI.get(n, n)
def hta(n): return H_TA.get(n, n)
def men(m): return MKT_EN.get(m, m)
def d_(s): return datetime.strptime(s, "%Y-%m-%d").date()
def short(d): return f"{d.day} {MONTHS['en'][d.month-1][:3]}"

# ---------------------------------------------------------------- history
# Markets whose column in the HARTI report carries the previous day's prices.
# Used only if harti_data.json has no "marketDates" (harti_update.py reads the real dates).
LAG_DAYS = {"Meegoda": 1, "Veyangoda": 1}

# ---------------------------------------------------------------- official report links
def _pdf_date(fname):
    """Report date from a HARTI PDF file name (same rules as harti_update.py)."""
    m = re.search(r"[\(\s_]?(20\d{2})\.(\d{2})\.(\d{2})[\)\s_]?", fname)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"daily[_\s](\d{2})-(\d{2})-(\d{4})", fname)
    if m: return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m = re.search(r"(20\d{2})[_-](\d{2})[_-](\d{2})", fname)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None

_HARTI_PDFS = None
def harti_pdf_for(report_date):
    """File name in harti_pdfs/ for a report date, or None."""
    global _HARTI_PDFS
    if _HARTI_PDFS is None:
        _HARTI_PDFS = {}
        for f in sorted(os.listdir("harti_pdfs")) if os.path.isdir("harti_pdfs") else []:
            if f.lower().endswith(".pdf"):
                d = _pdf_date(f)
                # prefer the full daily report when a day has two files
                if d and (d not in _HARTI_PDFS or f.startswith("Vegetable_Pricenew")):
                    _HARTI_PDFS[d] = f
    return _HARTI_PDFS.get(report_date)

def official_harti_link(harti, market, last):
    """'Official HARTI report' link to the original PDF our prices came from."""
    if not last:
        return ""
    report = harti["dates"][-1] if in_latest_report(harti, market) else \
        (d_(last) + timedelta(days=LAG_DAYS.get(market, 0))).isoformat()
    f = harti_pdf_for(report)
    if not f:
        return ""
    return (f'<p class="asof" style="margin-top:6px">📑 <a href="../harti_pdfs/{quote(f)}" rel="noopener">'
            f'HARTI මුල් වාර්තාව (නිල PDF) — {fdate(d_(report), "si")}</a> · Official HARTI report. '
            f'මිලක් වැරදි යැයි සිතේද? <a href="../data-sources.html">අපට දන්වන්න</a> / Spotted a wrong price? Tell us.</p>')

def official_cbsl_link(cd):
    f = f"price_report_{cd.strftime('%Y%m%d')}_e.pdf"
    if not os.path.exists(os.path.join("pdfs", f)):
        return ""
    return (f'<p class="asof" style="margin-top:6px">📑 <a href="../pdfs/{f}" rel="noopener">'
            f'මහ බැංකු මුල් වාර්තාව (නිල PDF) — {fdate(cd, "si")}</a> · Official Central Bank report.</p>')

def in_latest_report(harti, market):
    return any(isinstance((c.get("markets") or {}).get(market), dict) and c["markets"][market].get("mid") is not None
               for c in harti["commodities"])

def update_history(harti):
    """Add today's per-market snapshot to harti_market_history.json; keep KEEP_DAYS."""
    hist = {"markets": {}}
    if os.path.exists(HIST_FILE):
        try:
            hist = json.load(open(HIST_FILE, encoding="utf-8"))
        except Exception:
            pass
    hm = hist.setdefault("markets", {})
    today = harti["dates"][-1]
    # One-time fix: earlier history filed Meegoda / Veyangoda under the report date,
    # but HARTI gives those two markets' prices for the day before.
    if not hist.get("marketDatesFixed"):
        for m, lag in LAG_DAYS.items():
            for n in list(hm.get(m, {})):
                hm[m][n] = {(d_(k) - timedelta(days=lag)).isoformat(): x for k, x in hm[m][n].items()}
        hist["marketDatesFixed"] = True
    mdates = harti.get("marketDates") or {}
    for c in harti["commodities"]:
        for m, v in (c.get("markets") or {}).items():
            if isinstance(v, dict) and v.get("mid") is not None:
                day = mdates.get(m) or (d_(today) - timedelta(days=LAG_DAYS.get(m, 0))).isoformat()
                hm.setdefault(m, {}).setdefault(c["name"], {})[day] = [v.get("min"), v.get("max"), v["mid"]]
    cutoff = (d_(today) - timedelta(days=KEEP_DAYS)).isoformat()
    for m in hm:
        for n in list(hm[m]):
            hm[m][n] = {k: x for k, x in sorted(hm[m][n].items()) if k >= cutoff}
            if not hm[m][n]:
                del hm[m][n]
    hist["note"] = "Per-market HARTI wholesale history (min, max, mid) kept by build_market_pages.py"
    hist["updated"] = today
    json.dump(hist, open(HIST_FILE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return hm

def market_snapshot(hm, market):
    """Latest report date for this market and its items: {name: (min,max,mid)}."""
    items = hm.get(market, {})
    dates = sorted({d for x in items.values() for d in x})
    if not dates:
        return None, {}
    last = dates[-1]
    return last, {n: x[last] for n, x in items.items() if last in x}

def week_ago(series, last):
    """Mid price from the report about one week before `last` (5-9 days earlier, closest to 7)."""
    t = d_(last)
    best, gap = None, 99
    for k, v in series.items():
        days = (t - d_(k)).days
        if 5 <= days <= 9 and abs(days - 7) < gap:
            best, gap = (k, v), abs(days - 7)
    return best

# ---------------------------------------------------------------- CBSL Dambulla block
def cbsl_dambulla(cbsl):
    dates = cbsl["dates"]
    li = len(dates) - 1
    rows = []
    for c in cbsl["commodities"]:
        s = c.get("series") or []
        ws = c.get("wholesaleSeries") or []
        r = (c.get("markets") or {}).get("Dambulla")
        w = (c.get("wholesaleMarkets") or {}).get("Dambulla")
        r_ok = r is not None and len(s) > li and s[li] is not None
        w_ok = w is not None and len(ws) > li and ws[li] is not None
        if r_ok or w_ok:
            rows.append((c, w if w_ok else None, r if r_ok else None))
    return d_(dates[li]), rows

# ---------------------------------------------------------------- download / share buttons
# The phone makes the image and PDF from this page's prices (nothing is stored on GitHub).
DL_JS = r'''<script>
/* TopGoviya.lk - price list image / PDF made on the phone (nothing stored on the server) */
(function(){
const D = __DL_DATA__, K = D.key, CB = D.kind === 'cbsl';
const W = 1080, X = 44, TW = 992, ROWS = 24;
const C = {petrol:'#0e4f4a', gold:'#a9802a', cream:'#f4efe4', card:'#fffdf7', ink:'#191d1a', soft:'#3a403a',
           muted:'#7a7264', line:'#e3d9c4', head:'#efe8d8', cat:'#e6efec', up:'#b23a2e', upbg:'#f7e6e2',
           down:'#2c7a52', downbg:'#e3efe6', flat:'#8a8170', flatbg:'#efeada'};
const SI = "'Noto Sans Sinhala', sans-serif", MONO = "'JetBrains Mono', monospace";
const money = n => Math.round(n).toLocaleString('en-US');

function parts(){
  const lines = D.lines, n = Math.ceil(lines.length / ROWS), size = Math.ceil(lines.length / n) + 1;
  const out = []; let cur = [], cat = null;
  for (const L of lines){
    if (L.c){ cat = L.c; if (cur.length >= size - 2){ out.push(cur); cur = []; } cur.push(L); }
    else { if (cur.length >= size){ out.push(cur); cur = [{c: cat}]; } cur.push(L); }
  }
  if (cur.length) out.push(cur);
  return out;
}
function rr(ctx, x, y, w, h, r, fill){ ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r);
  ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); }
function wrap(ctx, text, maxW){ const words = text.split(' '), out = []; let line = '';
  for (const w of words){ const t = line ? line + ' ' + w : w;
    if (ctx.measureText(t).width > maxW && line){ out.push(line); line = w; } else line = t; }
  if (line) out.push(line); return out; }

function draw(lines, part, nparts, logo, qr){
  const cv = document.createElement('canvas'), ctx = cv.getContext('2d');
  // footer text lines (needed for height)
  cv.width = W; cv.height = 10; ctx.font = '22px ' + SI;
  const foot = [].concat(...D.foot.map(t => wrap(ctx, t, TW - 210)));
  const stale = D.stale ? 70 : 0;
  const R1 = 690, R2 = 830, R3 = TW + X - 16, NAMEMAX = CB ? R2 - 200 : R1 - 175;
  const fitsEn = L => { ctx.font = '600 29px ' + SI; const nw = ctx.measureText(L.s).width;
    ctx.font = '18px ' + SI; return X + 16 + nw + 10 + ctx.measureText(L.e).width < NAMEMAX; };
  const rowH = L => L.c ? 44 : (fitsEn(L) ? 60 : 82);
  const HH = (!CB && D.wkd) ? 70 : 50;
  const tableH = HH + lines.reduce((h, L) => h + rowH(L), 0);
  const nItems = lines.filter(L => !L.c).length, allItems = D.lines.filter(L => !L.c).length;
  const H = 140 + 250 + stale + tableH + 40 + Math.max(190, 50 + foot.length * 34) + 30;
  cv.width = W; cv.height = H;
  ctx.fillStyle = C.cream; ctx.fillRect(0, 0, W, H);
  // top band
  ctx.fillStyle = C.petrol; ctx.fillRect(0, 0, W, 140);
  if (logo){ rr(ctx, X, 28, 84, 84, 18, '#fff'); ctx.drawImage(logo, X + 4, 32, 76, 76); }
  ctx.fillStyle = '#fff'; ctx.font = '600 40px ' + SI; ctx.fillText('TopGoviya.lk', X + 106, 70);
  ctx.fillStyle = '#e7d3a3'; ctx.font = '24px ' + SI; ctx.fillText('දත්තය බලලා තීරණ ගන්න', X + 106, 106);
  // title
  let y = 140 + 78;
  ctx.fillStyle = C.petrol; ctx.font = '600 60px ' + SI; ctx.fillText(D.si + ' වෙළඳපොළ', X, y);
  y += 52; ctx.fillStyle = C.soft; ctx.font = '600 32px ' + SI; const t2 = D.sub;
  ctx.fillText(t2, X, y); const w2 = ctx.measureText(t2).width;
  ctx.fillStyle = C.muted; ctx.font = '22px ' + SI; ctx.fillText(' · ' + D.subEn, X + w2 + 6, y);
  // date pill
  y += 26; ctx.font = '600 32px ' + SI; const dt = D.date + ' · ' + D.src;
  const dw = ctx.measureText(dt).width + 60; rr(ctx, X, y, dw, 60, 30, C.gold);
  ctx.fillStyle = '#fff'; ctx.fillText(dt, X + 30, y + 42);
  ctx.fillStyle = C.muted; ctx.font = '600 24px ' + SI;
  ctx.fillText((nparts > 1 ? '(' + part + '/' + nparts + ') · භාණ්ඩ ' + nItems + ' / ' + allItems : 'භාණ්ඩ ' + allItems), X + dw + 16, y + 40);
  y += 60 + 24;
  if (D.stale){ ctx.fillStyle = '#fff3d6'; ctx.fillRect(X, y, TW, 56); ctx.fillStyle = C.gold; ctx.fillRect(X, y, 10, 56);
    ctx.fillStyle = '#5a4a1a'; ctx.font = '22px ' + SI; ctx.fillText(D.stale, X + 24, y + 36); y += stale; }
  // table
  rr(ctx, X, y, TW, tableH, 18, C.card);
  ctx.save(); ctx.beginPath(); ctx.rect(X, y, TW, HH); ctx.clip(); rr(ctx, X, y, TW, tableH, 18, C.head); ctx.restore();
  ctx.fillStyle = C.muted; ctx.font = '600 21px ' + SI; ctx.textAlign = 'left'; ctx.fillText('භාණ්ඩය', X + 16, y + 33);
  ctx.textAlign = 'right';
  if (CB){ ctx.fillText('තොග / Wholesale', R2 + 20, y + 33); ctx.fillText('සිල්ලර / Retail', R3, y + 33); }
  else { ctx.fillText('අවම – උපරිම', R1, y + 33); ctx.fillText('මධ්‍යගතය', R2, y + 33); ctx.fillText('සතියකට පෙර', R3, y + 33);
    if (D.wkd){ ctx.font = '600 19px ' + SI; ctx.fillStyle = C.gold; ctx.fillText('(' + D.wkd + ' වාර්තාව)', R3, y + 58);
      ctx.fillStyle = C.muted; ctx.font = '600 19px ' + SI; ctx.fillText('(' + D.nowd + ')', R2, y + 58); } }
  y += HH;
  for (const L of lines){
    ctx.textAlign = 'left';
    if (L.c){ ctx.fillStyle = C.cat; ctx.fillRect(X, y, TW, 44); ctx.fillStyle = C.petrol; ctx.font = '600 25px ' + SI;
      ctx.fillText(L.c, X + 16, y + 31); y += 44; continue; }
    const one = fitsEn(L), h = one ? 60 : 82, mid = one ? 0 : 11;
    ctx.fillStyle = C.line; ctx.fillRect(X, y, TW, 1);
    ctx.fillStyle = C.ink; ctx.font = '600 29px ' + SI; ctx.fillText(L.s, X + 16, y + 40);
    const nw = ctx.measureText(L.s).width; ctx.font = '18px ' + SI; ctx.fillStyle = C.muted;
    if (one) ctx.fillText(L.e, X + 16 + nw + 10, y + 40); else ctx.fillText(L.e, X + 16, y + 68);
    y += mid;
    ctx.textAlign = 'right';
    if (CB){
      ctx.font = '600 29px ' + MONO; ctx.fillStyle = C.gold; ctx.fillText(L.ws != null ? money(L.ws) : '—', R2 + 20, y + 40);
      ctx.font = '700 31px ' + MONO; ctx.fillStyle = C.ink; ctx.fillText(L.rt != null ? money(L.rt) : '—', R3, y + 40);
      y += h - mid; continue;
    }
    ctx.font = '500 23px ' + MONO; ctx.fillStyle = C.muted; ctx.fillText(money(L.lo) + '–' + money(L.hi), R1, y + 39);
    ctx.font = '700 31px ' + MONO; ctx.fillStyle = C.ink; ctx.fillText(money(L.m), R2, y + 40);
    if (L.w){
      const pct = (L.m - L.w) / L.w * 100, k = Math.abs(pct) < 0.5 ? 'flat' : (pct > 0 ? 'up' : 'down');
      const tx = ({up:'▲', down:'▼', flat:'■'})[k] + (pct > 0 ? '+' : '') + pct.toFixed(0) + '%';
      ctx.font = '700 20px ' + MONO; const cw = ctx.measureText(tx).width + 16;
      rr(ctx, R3 - cw, y + 16, cw, 30, 8, C[k + 'bg']); ctx.fillStyle = C[k]; ctx.textAlign = 'center'; ctx.fillText(tx, R3 - cw / 2, y + 38);
      ctx.textAlign = 'right'; ctx.font = '500 25px ' + MONO; ctx.fillStyle = C.soft; ctx.fillText((L.x ? '*' : '') + money(L.w), R3 - cw - 8, y + 40);
      if (L.x){ ctx.font = '16px ' + SI; ctx.fillStyle = C.muted; ctx.fillText('(' + L.x + ')', R3, y + 58); }
    } else { ctx.fillStyle = C.muted; ctx.font = '25px ' + MONO; ctx.fillText('—', R3, y + 40); }
    y += h - mid;
  }
  // footer
  y += 30; ctx.fillStyle = '#cdbf9f'; ctx.fillRect(X, y, TW, 2); y += 24; ctx.textAlign = 'left';
  if (qr){ rr(ctx, X, y, 170, 170, 12, '#fff'); ctx.imageSmoothingEnabled = false; ctx.drawImage(qr, X + 8, y + 8, 154, 154); ctx.imageSmoothingEnabled = true; }
  const fx = X + 196; ctx.fillStyle = C.petrol; ctx.font = '600 32px ' + SI; ctx.fillText(D.url.replace('https://', ''), fx, y + 34);
  ctx.fillStyle = C.soft; ctx.font = '22px ' + SI; foot.forEach((t, i) => ctx.fillText(t, fx, y + 74 + i * 34));
  return cv;
}

function loadImg(src){ return new Promise(r => { if (!src) return r(null); const im = new Image();
  im.onload = () => r(im); im.onerror = () => r(null); im.src = src; }); }

async function make(){
  try { await Promise.all(['600 30px "Noto Sans Sinhala"', '400 22px "Noto Sans Sinhala"', '700 30px "JetBrains Mono"', '500 24px "JetBrains Mono"']
    .map(f => document.fonts.load(f, 'අ1'))); } catch(e){}
  let qrSrc = null;
  try { const q = qrcode(0, 'M'); q.addData(D.url); q.make(); qrSrc = q.createDataURL(6, 0); } catch(e){}
  const [logo, qr] = await Promise.all([loadImg(D.logo), loadImg(qrSrc)]);
  const ps = parts();
  return ps.map((p, i) => draw(p, i + 1, ps.length, logo, qr));
}
const blobOf = (cv, type, q) => new Promise(r => cv.toBlob(r, type, q));
function save(blob, name){ const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 4000); }
const base = () => D.slug + '-' + D.fname + '-' + D.iso;

async function pdfBlob(cvs){
  // simple A4 PDF with one JPEG per page (no extra library needed)
  const enc = new TextEncoder(), chunks = [], offs = []; let len = 0;
  const put = x => { const b = typeof x === 'string' ? enc.encode(x) : x; chunks.push(b); len += b.length; };
  const obj = (n, body) => { offs[n] = len; put(n + ' 0 obj\n'); body(); put('\nendobj\n'); };
  const pages = []; for (const cv of cvs){ const b = new Uint8Array(await (await blobOf(cv, 'image/jpeg', 0.88)).arrayBuffer());
    pages.push({b, w: cv.width, h: cv.height}); }
  const n = pages.length, PW = 595.28, PH = 841.89, M = 22;
  put('%PDF-1.4\n');
  obj(1, () => put('<< /Type /Catalog /Pages 2 0 R >>'));
  obj(2, () => put('<< /Type /Pages /Count ' + n + ' /Kids [' + pages.map((_, i) => (3 + i * 3) + ' 0 R').join(' ') + '] >>'));
  pages.forEach((p, i) => {
    const po = 3 + i * 3, im = po + 1, co = po + 2;
    const s = Math.min((PW - 2 * M) / p.w, (PH - 2 * M) / p.h), w = p.w * s, h = p.h * s, x = (PW - w) / 2, y = PH - M - h;
    const cs = 'q ' + w.toFixed(2) + ' 0 0 ' + h.toFixed(2) + ' ' + x.toFixed(2) + ' ' + y.toFixed(2) + ' cm /Im0 Do Q';
    obj(po, () => put('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ' + PW + ' ' + PH + '] /Resources << /XObject << /Im0 ' + im + ' 0 R >> >> /Contents ' + co + ' 0 R >>'));
    obj(im, () => { put('<< /Type /XObject /Subtype /Image /Width ' + p.w + ' /Height ' + p.h +
      ' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ' + p.b.length + ' >>\nstream\n'); put(p.b); put('\nendstream'); });
    obj(co, () => put('<< /Length ' + cs.length + ' >>\nstream\n' + cs + '\nendstream'));
  });
  const xref = len, total = 3 + n * 3;
  put('xref\n0 ' + total + '\n0000000000 65535 f \n');
  for (let i = 1; i < total; i++) put(String(offs[i]).padStart(10, '0') + ' 00000 n \n');
  put('trailer\n<< /Size ' + total + ' /Root 1 0 R >>\nstartxref\n' + xref + '\n%%EOF');
  return new Blob(chunks, {type: 'application/pdf'});
}

async function run(btn, job){ const t = btn.innerHTML; btn.disabled = true; btn.innerHTML = '⏳ ...';
  try { await job(); } catch(e){ console.error(e); alert('සමාවන්න, නැවත උත්සාහ කරන්න. Sorry, please try again.'); }
  btn.disabled = false; btn.innerHTML = t; }

window['tgImage_' + K] = btn => run(btn, async () => { const cvs = await make();
  for (let i = 0; i < cvs.length; i++){ save(await blobOf(cvs[i], 'image/png'), base() + (cvs.length > 1 ? '-' + (i + 1) : '') + '.png');
    await new Promise(r => setTimeout(r, 600)); } });
window['tgPdf_' + K] = btn => run(btn, async () => { save(await pdfBlob(await make()), base() + '.pdf'); });
window['tgShare_' + K] = btn => run(btn, async () => { const cvs = await make(), files = [];
  for (let i = 0; i < cvs.length; i++) files.push(new File([await blobOf(cvs[i], 'image/png')],
    base() + (cvs.length > 1 ? '-' + (i + 1) : '') + '.png', {type: 'image/png'}));
  const msg = D.msg;
  if (navigator.canShare && navigator.canShare({files})) await navigator.share({files, text: msg});
  else { for (const f of files) save(f, f.name); } });

const bar = document.getElementById('tg-dl-' + K);
if (bar){ bar.style.display = 'flex';
  const sh = document.getElementById('tg-share-' + K);
  try { if (!(navigator.canShare && navigator.canShare({files: [new File([''], 'a.png', {type: 'image/png'})]}))) sh.style.display = 'none'; }
  catch(e){ sh.style.display = 'none'; } }
})();
</script>
'''

DL_FOOT = [
    "දත්ත: HARTI දෛනික තොග මිල වාර්තාව (හෙක්ටර් කොබ්බෑකඩුව ගොවිකටයුතු පර්යේෂණ හා පුහුණු කිරීමේ ආයතනය).",
    "රු. / කි.ග්‍රෑ. · මධ්‍යගතය = (අවම + උපරිම) ÷ 2 · සතියකට පෙර = සතියකට පෙර වාර්තාවේ මධ්‍යගතය.",
    "මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ. ප්‍රවාහන වියදම අනුව සැබෑ ලාභය වෙනස් වේ.",
]

DL_LIB = '<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js"></script>\n'

CBSL_FOOT = [
    "දත්ත: ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාව, දඹුල්ල වෙළඳපොළ. Central Bank of Sri Lanka daily price report.",
    "තොග = වෙළඳපොළ තොග මිල · සිල්ලර = පාරිභෝගිකයා ගෙවන මිල. ඒකකය සඳහන් නොකළ භාණ්ඩ රු. / කි.ග්‍රෑ.",
    "මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.",
]


def dl_buttons(key, data, label=""):
    """PDF / image / share buttons + the data the phone uses to draw the list."""
    btn = ("display:inline-flex;align-items:center;gap:6px;padding:10px 16px;border-radius:999px;font:inherit;"
           "font-weight:700;font-size:14px;cursor:pointer;")
    lab = f" {label}" if label else ""
    return (f'<div id="tg-dl-{key}" style="display:none;gap:8px;flex-wrap:wrap;margin:14px 0 4px">'
            f'<button onclick="tgPdf_{key}(this)" style="{btn}background:var(--card);color:var(--petrol);border:1px solid var(--petrol)">📄{lab} PDF බාගන්න</button>'
            f'<button onclick="tgImage_{key}(this)" style="{btn}border:0;background:var(--petrol);color:#fff">🖼️{lab} Image බාගන්න</button>'
            f'<button id="tg-share-{key}" onclick="tgShare_{key}(this)" style="{btn}border:0;background:#25d366;color:#fff">📤 WhatsApp / Share</button>'
            f'</div>'
            + DL_JS.replace("__DL_DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))


SI_MON = ["ජන", "පෙබ", "මාර්", "අප්‍රේ", "මැයි", "ජූනි", "ජූලි", "අගෝ", "සැප්", "ඔක්", "නොවැ", "දෙසැ"]


def short_si(iso):
    d = d_(iso)
    return f"{SI_MON[d.month - 1]} {d.day}"


def main_wk_date(rows):
    """The 'one week ago' report date used by most items (None if no item has one)."""
    from collections import Counter
    c = Counter(r["wkdate"] for r in rows if r.get("wkdate"))
    return c.most_common(1)[0][0] if c else None


def download_bar(market, rows, last, latest_all, url, lagged=False):
    """HARTI wholesale price list (min / max / mid / last week) for one market."""
    if not rows or not last:
        return ""
    info = MKT[market]
    wkd = main_wk_date(rows)
    lines, cur = [], None
    for r in rows:
        if r["cat"] != cur:
            cur = r["cat"]
            lines.append({"c": CAT_SI.get(cur, cur)})
        other = r.get("wkdate") and r["wkdate"] != wkd
        lines.append({"s": hsi(r["name"]), "e": r["name"], "lo": r["min"], "hi": r["max"], "m": r["mid"], "w": r["wk"],
                      "x": short_si(r["wkdate"]) if other else ""})
    foot = list(DL_FOOT)
    if wkd:
        foot[1] = (f"රු. / කි.ග්‍රෑ. · මධ්‍යගතය = (අවම + උපරිම) ÷ 2 · සතියකට පෙර = {fdate(d_(wkd), 'si')} වාර්තාවේ මධ්‍යගතය"
                   + (" (* = වෙනත් දිනයක වාර්තාව, දිනය සමඟ)." if any(L.get("x") for L in lines) else "."))
    stale = ""
    if last < latest_all and not lagged:
        stale = f"HARTI නවතම වාර්තාවේ ({fdate(d_(latest_all), 'si')}) මෙම වෙළඳපොළ මිල නොතිබුණි. මෙහි ඇත්තේ {fdate(d_(last), 'si')} මිලයි."
    date_si = fdate(d_(last), "si")
    data = {"key": "h", "kind": "harti", "slug": info["slug"], "fname": "price-list", "si": info["si"],
            "sub": "එළවළු තොග මිල ලැයිස්තුව", "subEn": men(market) + " wholesale price list",
            "src": "HARTI වාර්තාව", "date": date_si, "iso": last, "url": url, "logo": "../icon-192x192.png",
            "stale": stale, "foot": foot, "lines": lines, "wkd": short_si(wkd) if wkd else "", "nowd": short_si(last),
            "msg": f"{info['si']} වෙළඳපොළ තොග මිල ({date_si}, HARTI) {url}"}
    return dl_buttons("h", data)


CBSL_CAT_SI = {"Vegetables": "එළවළු", "Other": "වෙනත්", "Fruits": "පළතුරු", "Rice": "සහල්", "Fish": "මාළු"}


def cbsl_download_bar(cd, crow, url):
    """CBSL Dambulla wholesale + retail price list."""
    if not crow:
        return ""
    lines, cur = [], None
    for c, w, r in crow:
        if c.get("category") != cur:
            cur = c.get("category")
            lines.append({"c": CBSL_CAT_SI.get(cur, cur)})
        unit = c.get("unit", "Rs./kg")
        en = c["name"] + ("" if unit == "Rs./kg" else " · " + ((UNITS.get(unit) or {}).get("si", unit)))
        lines.append({"s": (CBSL_NAMES.get(c["name"]) or {}).get("si", c["name"]), "e": en, "ws": w, "rt": r})
    date_si = fdate(cd, "si")
    data = {"key": "c", "kind": "cbsl", "slug": "dambulla", "fname": "cbsl-price-list", "si": "දඹුල්ල",
            "sub": "තොග හා සිල්ලර මිල ලැයිස්තුව", "subEn": "Dambulla wholesale & retail (CBSL)",
            "src": "මහ බැංකු වාර්තාව", "date": date_si, "iso": cd.isoformat(), "url": url + "#cbsl",
            "logo": "../icon-192x192.png", "stale": "", "foot": CBSL_FOOT, "lines": lines,
            "msg": f"දඹුල්ල තොග හා සිල්ලර මිල ({date_si}, මහ බැංකුව) {url}"}
    return dl_buttons("c", data, "CBSL")


# ---------------------------------------------------------------- page shell
def shell(title, desc, canonical, body, jsonld):
    return f"""<!DOCTYPE html>
<html lang="si">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="TopGoviya.lk">
<meta name="theme-color" content="#0e4f4a">
<link rel="icon" type="image/png" sizes="192x192" href="../icon-192x192.png">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&family=Noto+Sans+Sinhala:wght@400;600&family=Noto+Sans+Tamil:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}
.rng{{font-size:12.5px;color:var(--muted);font-weight:500}}
td.mid{{font-family:'JetBrains Mono',monospace;font-weight:700;text-align:right;white-space:nowrap}}
.tip{{font-size:13.5px;color:var(--soft);background:var(--amberbg);border-radius:10px;padding:10px 13px;margin:10px 0 0}}
</style>
{DL_LIB}<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>
<body>
<div class="wrap">
<header class="top"><a class="brand" href="../index.html">TopGoviya.lk</a><a href="index.html">වෙළඳපොළ 10 / All markets</a></header>
{body}
<p class="note">මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.<br>
Prices are indicative only. Decisions are your responsibility. Wholesale prices: <a href="{HARTI_URL}" rel="noopener">HARTI daily wholesale price report</a>;
Dambulla retail and wholesale: <a href="{CBSL_URL}" rel="noopener">Central Bank of Sri Lanka daily price report</a>. Not an official publication.
<a href="../data-sources.html">How we collect the data →</a><br>
விலைகள் வழிகாட்டல் மட்டுமே. உங்கள் முடிவுகளுக்கு நீங்களே பொறுப்பு.</p>
<footer>Design &amp; development by <a href="https://ebooklanka.com" target="_blank" rel="noopener">ebooklanka.com</a> · Built in Gampola, Sri Lanka</footer>
</div>
</body>
</html>
"""

def crop_cell(name):
    cb = TO_CBSL.get(name)
    label = f'{EMOJIS.get(cb, "🌿") if cb else "🌿"} {e(hsi(name))}'
    if cb and os.path.exists(os.path.join("price", slug(cb) + ".html")):
        label = f'<a href="../price/{slug(cb)}.html">{label}</a>'
    return f'{label} <span style="color:var(--muted)">/ {e(name)}</span>'

def chg_badge(now, old):
    if old is None:
        return "—"
    dd = now - old
    pct = dd / old * 100 if old else 0
    cls = "flat" if abs(pct) < 0.5 else ("up" if dd > 0 else "down")
    arrow = {"up": "▲", "down": "▼", "flat": "■"}[cls]
    return f'<span class="chg {cls}" style="font-size:12px;padding:2px 7px">{arrow} {"+" if pct > 0 else ""}{pct:.0f}%</span>'

# ---------------------------------------------------------------- one market page
def market_page(market, hm, harti, cats, cbsl):
    info = MKT[market]
    si, ta, en = info["si"], info["ta"], men(market)
    last, snap = market_snapshot(hm, market)
    latest_all = harti["dates"][-1]
    url = f"{SITE}/{OUT_DIR}/{info['slug']}.html"

    # rows with weekly change
    rows = []
    for n, (mn, mx, mid) in snap.items():
        wk = week_ago(hm[market][n], last)
        rows.append({"name": n, "cat": cats.get(n, "Up Country Vegetables"), "min": mn, "max": mx, "mid": mid,
                     "wk": wk[1][2] if wk else None, "wkdate": wk[0] if wk else None})
    rows.sort(key=lambda r: (CAT_ORDER.index(r["cat"]) if r["cat"] in CAT_ORDER else 9, r["name"]))

    # where pays more today (same report date only, HARTI rule: highlight the highest to sell)
    better = []
    if last:
        for r in rows:
            best_m, best_v, best_d = None, r["mid"], last
            for m2 in MKT:
                if m2 == market:
                    continue
                ser = hm.get(m2, {}).get(r["name"], {})
                for day in (last, (d_(last) - timedelta(days=1)).isoformat()):
                    v = ser.get(day)
                    if v:
                        if v[2] > best_v:
                            best_m, best_v, best_d = m2, v[2], day
                        break
            if best_m and best_v >= r["mid"] * 1.10:
                better.append((r, best_m, best_v, best_d))
        better.sort(key=lambda x: (x[2] - x[0]["mid"]) / x[0]["mid"], reverse=True)

    movers = [r for r in rows if r["wk"]]
    up = sorted([r for r in movers if r["mid"] > r["wk"]], key=lambda r: (r["mid"] - r["wk"]) / r["wk"], reverse=True)
    dn = sorted([r for r in movers if r["mid"] < r["wk"]], key=lambda r: (r["mid"] - r["wk"]) / r["wk"])

    # ---- story in 3 languages
    if last:
        d = d_(last)
        s_si = f"{fdate(d,'si')} HARTI තොග මිල වාර්තාව අනුව {si} වෙළඳපොළේ භාණ්ඩ {len(rows)}ක තොග මිල පහත දැක්වේ (රු./කි.ග්‍රෑ.)."
        s_en = f"On {fdate(d,'en')}, the HARTI daily report listed wholesale prices for {len(rows)} items at {en} market (Rs. per kg)."
        s_ta = f"{fdate(d,'ta')} HARTI அறிக்கையின்படி {ta} சந்தையில் {len(rows)} பொருட்களின் மொத்த விலை (ரூ./கி.)."
        if up:
            r = up[0]
            s_si += f" සතියකට පෙර සිට වැඩිම ඉහළ යාම: {hsi(r['name'])} (රු. {money(r['wk'])} → රු. {money(r['mid'])})."
            s_en += f" Biggest weekly rise: {r['name']} (Rs. {money(r['wk'])} → Rs. {money(r['mid'])})."
            s_ta += f" வாராந்திர அதிக உயர்வு: {hta(r['name'])} (ரூ. {money(r['wk'])} → ரூ. {money(r['mid'])})."
        if dn:
            r = dn[0]
            s_si += f" වැඩිම පහළ යාම: {hsi(r['name'])} (රු. {money(r['wk'])} → රු. {money(r['mid'])})."
            s_en += f" Biggest weekly fall: {r['name']} (Rs. {money(r['wk'])} → Rs. {money(r['mid'])})."
            s_ta += f" அதிக வீழ்ச்சி: {hta(r['name'])} (ரூ. {money(r['wk'])} → ரூ. {money(r['mid'])})."
    else:
        s_si = f"{si} වෙළඳපොළ සඳහා මෑත HARTI මිල වාර්තා නොමැත."
        s_en = f"HARTI has not reported prices for {en} market recently."
        s_ta = f"{ta} சந்தைக்கு சமீபத்திய HARTI விலைகள் இல்லை."

    stale = ""
    if last and last < latest_all and in_latest_report(harti, market):
        stale = (f'<p class="asof" style="background:var(--card);border:1px solid var(--line);border-radius:10px;padding:9px 12px">'
                 f'ℹ️ HARTI {fdate(d_(latest_all),"si")} වාර්තාවේ {si} වෙළඳපොළ මිල දී ඇත්තේ <b>{fdate(d_(last),"si")}</b> දිනයටයි '
                 f'(මෙම වෙළඳපොළ සෑම විටම පෙර දින මිල ලබා දේ). '
                 f'The HARTI {fdate(d_(latest_all),"en")} report gives {en} prices for {fdate(d_(last),"en")}.</p>')
    elif last and last < latest_all:
        stale = (f'<p class="stale">⚠ HARTI නවතම වාර්තාවේ ({fdate(d_(latest_all),"si")}) {si} මිල නොතිබුණි. '
                 f'පහත දැක්වෙන්නේ {fdate(d_(last),"si")} මිලයි. Not in the latest HARTI report; '
                 f'showing {fdate(d_(last),"en")}.</p>')

    # ---- HARTI table
    wkd_main = main_wk_date(rows)
    table = ""
    cur = None
    for r in rows:
        if r["cat"] != cur:
            if cur is not None:
                table += "</tbody></table></div>"
            cur = r["cat"]
            table += (f'<h2 class="cat">{e(CAT_SI.get(cur, cur))} <span>{e(cur)}</span></h2><div class="scroll"><table>'
                      f'<thead><tr><th>භාණ්ඩය / Item</th><th class="n">අවම–උපරිම<br>Min–Max</th>'
                      f'<th class="n">මධ්‍යගතය<br>Mid</th><th class="n">සතියකට පෙර<br>1 week ago'
                      + (f'<br><span style="color:var(--gold)">({short_si(wkd_main)})</span>' if wkd_main else "")
                      + '</th></tr></thead><tbody>')
        other = r.get("wkdate") and r["wkdate"] != wkd_main
        wk = ((f'{"*" if other else ""}{money(r["wk"])} {chg_badge(r["mid"], r["wk"])}'
               + (f'<br><small style="color:var(--muted)">({short_si(r["wkdate"])})</small>' if other else ""))
              if r["wk"] else "—")
        table += (f'<tr><td>{crop_cell(r["name"])}</td>'
                  f'<td class="n rng">{money(r["min"])}–{money(r["max"])}</td>'
                  f'<td class="mid">{money(r["mid"])}</td><td class="n">{wk}</td></tr>')
    if cur is not None:
        table += "</tbody></table></div>"
    wk_dates = [wkd_main] if wkd_main else []
    has_other = any(r.get("wkdate") and r["wkdate"] != wkd_main for r in rows)
    table_note = ('<p class="asof" style="margin-top:10px">රුපියල් / කි.ග්‍රෑ. · Rs. per kg · HARTI තොග මිල මධ්‍යගතය = (අවම + උපරිම) ÷ 2'
                  + (f' · සතියකට පෙර = {fdate(d_(wk_dates[-1]),"si")} වාර්තාව (තනි දිනයක මිල, සාමාන්‍යයක් නොවේ / a single day, not an average)' if wk_dates else "")
                  + (' · * = එම භාණ්ඩය එදින වාර්තාවේ නොතිබූ නිසා ළඟම දිනයේ (දවස් 5–9 පෙර) මිල' if has_other else "") + '</p>')

    # ---- where pays more
    better_html = ""
    if better:
        lis = "".join(
            f'<tr><td>{e(hsi(r["name"]))} <span style="color:var(--muted)">/ {e(r["name"])}</span></td>'
            f'<td class="n">රු. {money(r["mid"])}</td>'
            f'<td>📍 {e(MKT[m2]["si"])} <span style="color:var(--muted)">/ {e(men(m2))}</span></td>'
            f'<td class="n"><b>රු. {money(v)}</b>'
            + (f'<br><small style="color:var(--muted)">({short_si(bd)})</small>' if bd != last else "") + '</td></tr>'
            for r, m2, v, bd in better[:8])
        better_html = (f'<h2>වැඩි මිලක් ලැබුණු වෙළඳපොළ<span>Where the same crop sold higher on {short(d_(last))}</span></h2>'
                       f'<div class="scroll"><table><thead><tr><th>භාණ්ඩය / Item</th><th class="n">{e(si)}</th>'
                       f'<th>ඉහළම වෙළඳපොළ / Highest market</th><th class="n">මිල / Price</th></tr></thead><tbody>{lis}</tbody></table></div>'
                       f'<p class="tip">🚚 ප්‍රවාහන වියදම වෙළඳපොළ අනුව වෙනස් වේ. සැබෑ ලාභය ගණනය කිරීමට ඔබේ වියදම '
                       f'<a href="../wholesale.html">තොග මිල පිටුවේ ගණකයට</a> ඇතුළත් කරන්න. '
                       f'Transport cost changes the real profit — enter your own cost in the calculator.</p>')

    # ---- CBSL block (Dambulla only)
    cbsl_html = ""
    cbsl_count = 0
    cbsl_first = False
    cd = None
    if market == "Dambulla" and cbsl:
        cd, crow = cbsl_dambulla(cbsl)
        # Show the CBSL table first when it is newer than the HARTI report
        cbsl_first = bool(crow) and (not last or cd > d_(last))
        cbsl_count = len(crow)
        if crow:
            trs = "".join(
                f'<tr><td><a href="../price/{slug(c["name"])}.html">{EMOJIS.get(c["name"], "🌿")} '
                f'{e((CBSL_NAMES.get(c["name"]) or {}).get("si", c["name"]))}</a> '
                f'<span style="color:var(--muted)">/ {e(c["name"])}</span></td>'
                f'<td class="n w">{money(w) if w is not None else "—"}</td>'
                f'<td class="n">{money(r) if r is not None else "—"}</td></tr>'
                for c, w, r in crow)
            newest = ""
            if cbsl_first:
                newest = (f'<p class="tip" style="margin:0 0 12px;background:var(--goodbg,#e3efe6)">🟢 <b>නවතම මිල — {fdate(cd,"si")}</b>. '
                          f'HARTI {fdate(cd,"si")} වාර්තාව තවම නිකුත් කර නැත; HARTI මිල ({fdate(d_(last),"si") if last else "—"}) පහළින් ඇත. '
                          f'<span lang="en">Newest prices: CBSL report, {fdate(cd,"en")}. The HARTI report for this day is not out yet; '
                          f'HARTI prices from {fdate(d_(last),"en") if last else "—"} are below.</span></p>')
            cbsl_html = (f'<h2 id="cbsl">CBSL දඹුල්ල තොග හා සිල්ලර මිල<span>Central Bank report, {fdate(cd,"en")}</span></h2>'
                         + newest +
                         f'<p class="asof" style="margin:0 0 10px">මහ බැංකුවේ දෛනික මිල වාර්තාවේ දඹුල්ල මිල (රු.) · '
                         f'Central Bank of Sri Lanka daily price report, Dambulla.</p>'
                         + cbsl_download_bar(cd, crow, url) +
                         f'<div class="scroll"><table><thead><tr><th>භාණ්ඩය / Item</th><th class="n">තොග<br>Wholesale</th>'
                         f'<th class="n">සිල්ලර<br>Retail</th></tr></thead><tbody>{trs}</tbody></table></div>'
                         + official_cbsl_link(cd))

    # ---- summary cards
    duo = ""
    if last:
        duo = (f'<div class="duo">'
               f'<div class="r"><b>{len(rows)}</b><span>භාණ්ඩ / items · HARTI</span></div>'
               f'<div class="w"><b>▲ {len(up)} · ▼ {len(dn)}</b><span>සතියකට පෙරට වඩා / vs 1 week ago</span></div>'
               + (f'<div class="g"><b>{cbsl_count}</b><span>CBSL තොග හා සිල්ලර / retail items</span></div>' if cbsl_count else "")
               + '</div>')

    harti_h2 = (f'<h2>HARTI {e(si)} තොග මිල<span>HARTI wholesale report, {fdate(d_(last),"en") if last else "—"}</span></h2>')
    others = "".join(f'<a href="{MKT[m]["slug"]}.html">📍 {e(MKT[m]["si"])} / {e(men(m))}</a>' for m in MKT if m != market)

    body = f"""
<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / <a href="index.html">වෙළඳපොළ මිල</a> / {e(si)}</p>
<h1>🧺 {e(si)} එළවළු මිල අද</h1>
<p class="alt">{e(en)} market price today – vegetable wholesale prices<br>{e(ta)} சந்தை விலை இன்று</p>
{cbsl_html if cbsl_first else ''}
{harti_h2 if cbsl_first else ''}
<p class="asof" style="margin-top:14px"><b>📦 තොග මිල / Wholesale</b> · 📍 {e(si)} ({e(en)}) · {fdate(d_(last),'si') if last else '—'} · HARTI</p>
{download_bar(market, rows, last, latest_all, url, in_latest_report(harti, market))}
{duo}
{stale}
<div class="story">
  <p>{e(s_si)}</p>
  <p lang="en">{e(s_en)}</p>
  <p lang="ta">{e(s_ta)}</p>
</div>
{table}
{table_note if rows else ''}
{official_harti_link(harti, market, last)}
{better_html}
{'' if cbsl_first else cbsl_html}
<a class="cta" href="../wholesale.html">වෙළඳපොළ 10ක ප්‍රස්ථාර හා ලාභ ගණකය බලන්න / Charts &amp; calculator →</a>
<h2>අනෙක් වෙළඳපොළ<span>Other markets</span></h2>
<div class="rel">{others}</div>
"""
    dtxt = fdate(d_(last), "en") if last else ""
    title = f"{si} එළවළු මිල අද | {en} Market Price Today Sri Lanka – TopGoviya"
    top3 = ", ".join(f"{r['name']} Rs. {money(r['mid'])}" for r in rows[:3])
    if cbsl_first:
        top3 = ", ".join(f"{c['name']} Rs. {money(r)} retail" for c, w, r in crow[:3] if r is not None)
    if cbsl_first:
        desc = (f"{en} market price today ({fdate(cd,'en')}): CBSL wholesale and retail prices for {cbsl_count} items, "
                f"plus HARTI wholesale prices for {len(rows)} vegetables ({dtxt})")
    else:
        desc = (f"{en} market price today ({dtxt}): wholesale prices for {len(rows)} vegetables from the HARTI report"
                + (", plus CBSL Dambulla retail and wholesale" if cbsl_count else ""))
    desc = (desc
            + f". {top3}. {si} එළවළු මිල අද · {en.lower()} elawalu mila.")
    jsonld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "TopGoviya.lk", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Market prices", "item": f"{SITE}/{OUT_DIR}/"},
        {"@type": "ListItem", "position": 3, "name": f"{en} market price", "item": url}]}
    return shell(title, desc, url, body, jsonld), last, len(rows)

# ---------------------------------------------------------------- hub page
def hub_page(summary, latest_all, harti=None):
    rows = "".join(
        f'<tr><td><a href="{MKT[m]["slug"]}.html">📍 {e(MKT[m]["si"])}</a> <span style="color:var(--muted)">/ {e(men(m))}</span></td>'
        f'<td class="n">{n}</td><td class="n">{fdate(d_(last),"si") if last else "—"}'
        f'{" ⚠" if last and last < latest_all and not (harti and in_latest_report(harti, m)) else ""}</td></tr>'
        for m, (last, n) in summary.items())
    body = (f'<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / වෙළඳපොළ මිල</p>'
            f'<h1>🧺 වෙළඳපොළ එළවළු මිල අද</h1>'
            f'<p class="alt">Today\'s vegetable market prices in Sri Lanka – 10 wholesale markets<br>இன்றைய சந்தை விலைகள் – 10 சந்தைகள்</p>'
            f'<p class="asof" style="margin-top:14px">HARTI නවතම වාර්තාව / Latest HARTI report: {fdate(d_(latest_all),"si")}</p>'
            f'<div class="story" style="font-size:14.5px"><p>දඹුල්ල, පෑලියගොඩ, කෑප්පෙටිපොළ ඇතුළු ආර්ථික මධ්‍යස්ථාන 10ක HARTI තොග මිල. '
            f'වෙළඳපොළක් තට්ටු කර එදින භාණ්ඩ මිල, සතියකට පෙර මිල හා වැඩි මිලක් ලැබුණු වෙළඳපොළ බලන්න.</p>'
            f'<p lang="en">HARTI wholesale prices for 10 markets including Dambulla, Peliyagoda and Keppetipola. '
            f'Tap a market for its price list, last week\'s prices and where the same crop sold higher.</p></div>'
            f'<div class="scroll"><table><thead><tr><th>වෙළඳපොළ / Market</th><th class="n">භාණ්ඩ<br>Items</th>'
            f'<th class="n">වාර්තා දිනය<br>Report date</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="asof" style="margin-top:10px">⚠ = HARTI නවතම වාර්තාවේ නොතිබුණි / not in the latest report (showing its last report)</p>'
            f'<a class="cta" href="../price/index.html">සිල්ලර මිල (CBSL) බලන්න / Retail prices →</a>')
    url = f"{SITE}/{OUT_DIR}/"
    title = "වෙළඳපොළ එළවළු මිල අද | Sri Lanka Market Prices Today – Dambulla, Peliyagoda | TopGoviya"
    desc = (f"Vegetable wholesale prices today at 10 Sri Lankan markets – Dambulla, Peliyagoda, Keppetipola, Meegoda and more "
            f"(HARTI, {fdate(d_(latest_all),'en')}). අද වෙළඳපොළ එළවළු මිල.")
    jsonld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": url}
    return shell(title, desc, url, body, jsonld)

# ---------------------------------------------------------------- sitemap
def update_sitemap(slugs, lastmod):
    path = "sitemap.xml"
    if os.path.exists(path):
        xml = open(path, encoding="utf-8").read()
    else:
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n</urlset>\n'
    xml = re.sub(r"\s*<url>\s*<loc>[^<]*/" + OUT_DIR + r"/[^<]*</loc>.*?</url>", "", xml, flags=re.S)
    new = f"  <url>\n    <loc>{SITE}/{OUT_DIR}/</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.9</priority>\n  </url>\n"
    for s in slugs:
        new += f"  <url>\n    <loc>{SITE}/{OUT_DIR}/{s}.html</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.9</priority>\n  </url>\n"
    xml = xml.replace("</urlset>", new + "</urlset>")
    open(path, "w", encoding="utf-8").write(xml)

# ---------------------------------------------------------------- main
def main():
    harti = json.load(open("harti_data.json", encoding="utf-8"))
    cbsl = json.load(open("data.json", encoding="utf-8")) if os.path.exists("data.json") else None
    cats = {c["name"]: c.get("category", "") for c in harti["commodities"]}
    hm = update_history(harti)
    os.makedirs(OUT_DIR, exist_ok=True)
    summary, made = {}, []
    for m in MKT:
        page, last, n = market_page(m, hm, harti, cats, cbsl)
        open(os.path.join(OUT_DIR, MKT[m]["slug"] + ".html"), "w", encoding="utf-8").write(page)
        summary[m] = (last, n)
        made.append(MKT[m]["slug"])
    latest_all = harti["dates"][-1]
    open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8").write(hub_page(summary, latest_all, harti))
    update_sitemap(made, latest_all)
    print(f"Built {len(made)} market pages + hub page, sitemap updated.")
    for m, (last, n) in summary.items():
        print(f"  {m:16} {n:3} items  {last}")

if __name__ == "__main__":
    main()
