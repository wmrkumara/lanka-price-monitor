"""
build_pages.py  -  TopGoviya.lk SEO price pages
------------------------------------------------
Reads data.json and writes:
  price/<commodity>.html   one Google-friendly page per commodity (43+)
  price/index.html         hub page listing every commodity
  sitemap.xml              keeps your existing pages, adds/refreshes the price pages

Runs daily from GitHub Actions right after update.py.
Uses only the Python standard library - nothing extra to install.
"""
import json, os, re, html
from datetime import date, datetime, timedelta

SITE = "https://topgoviya.lk"
OUT_DIR = "price"
GA_ID = "G-ZBN8Z32S4J"

# ---------------------------------------------------------------- translations
# (copied from index.html so the pages use exactly the same words as the site)
TR = {
"NAMES": {
"Beans": {
"si": "බෝංචි",
"ta": "பீன்ஸ்"
},
"Carrot": {
"si": "කැරට්",
"ta": "கேரட்"
},
"Cabbage": {
"si": "ගෝවා",
"ta": "முட்டைக்கோஸ்"
},
"Tomato": {
"si": "තක්කාලි",
"ta": "தக்காளி"
},
"Brinjal": {
"si": "වම්බටු",
"ta": "கத்தரிக்காய்"
},
"Pumpkin": {
"si": "වට්ටක්කා",
"ta": "பூசணி"
},
"Snake gourd": {
"si": "පතෝල",
"ta": "புடலங்காய்"
},
"Green Chilli": {
"si": "අමු මිරිස්",
"ta": "பச்சை மிளகாய்"
},
"Lime": {
"si": "දෙහි",
"ta": "எலுமிச்சை"
},
"Red Onion (Local)": {
"si": "රතු ළූණු (දේශීය)",
"ta": "சிவப்பு வெங்காயம் (உள்ளூர்)"
},
"Red Onion (lmp)": {
"si": "රතු ළූණු (ආනයනික)",
"ta": "சிவப்பு வெங்காயம் (இறக்குமதி)"
},
"Big Onion (Imp)": {
"si": "ලොකු ළූණු (ආනයනික)",
"ta": "பெரிய வெங்காயம் (இறக்குமதி)"
},
"Potato (Local)": {
"si": "අර්තාපල් (දේශීය)",
"ta": "உருளைக்கிழங்கு (உள்ளூர்)"
},
"Potato (Imp)": {
"si": "අර්තාපල් (ආනයනික)",
"ta": "உருளைக்கிழங்கு (இறக்குமதி)"
},
"Dried Chilli (Imp)": {
"si": "වියළි මිරිස් (ආනයනික)",
"ta": "உலர் மிளகாய் (இறக்குமதி)"
},
"Coconut (Avg.)": {
"si": "පොල් (සාමාන්‍ය)",
"ta": "தேங்காய் (சராசரி)"
},
"Banana (Sour)": {
"si": "කෙසෙල් (ඇඹුල්)",
"ta": "வாழைப்பழம் (புளிப்பு)"
},
"Papaw": {
"si": "පැපොල්",
"ta": "பப்பாளி"
},
"Pineapple": {
"si": "අන්නාසි",
"ta": "அன்னாசி"
},
"Samba": {
"si": "සම්බා",
"ta": "சம்பா"
},
"Nadu": {
"si": "නාඩු",
"ta": "நாடு"
},
"Kekulu (White)": {
"si": "කැකුළු (සුදු)",
"ta": "கெகுளு (வெள்ளை)"
},
"Kekulu (Red)": {
"si": "කැකුළු (රතු)",
"ta": "கெகுளு (சிவப்பு)"
},
"Ponni Samba (Imp)": {
"si": "පොන්නි සම්බා (ආනයනික)",
"ta": "பொன்னி சம்பா (இறக்குமதி)"
},
"Kelawalla": {
"si": "කෙළවල්ලා",
"ta": "கெளவல்லா"
},
"Thalapath": {
"si": "තලපත්",
"ta": "தலபத்"
},
"Paraw": {
"si": "පරාවා",
"ta": "பராவ்"
},
"Salaya": {
"si": "සාලයා",
"ta": "சாளை"
},
"Hurulla": {
"si": "හුරුල්ලා",
"ta": "ஹுருல்லா"
},
"Linna": {
"si": "ලින්නා",
"ta": "லின்னா"
},
"Beetroot": {
"si": "බීට්රූට්",
"ta": "பீட்ரூட்"
},
"Leeks": {
"si": "ලීක්ස්",
"ta": "லீக்ஸ்"
},
"Knol-khol": {
"si": "නෝල්කෝල්",
"ta": "நோல்கோல்"
},
"Drumstick": {
"si": "මුරුංගා",
"ta": "முருங்கை"
},
"Manioc": {
"si": "මඤ්ඤොක්කා",
"ta": "மரவள்ளி"
},
"Ash Plantain": {
"si": "අල කෙසෙල්",
"ta": "வாழைக்காய்"
},
"Keeri Samba": {
"si": "කීරි සම්බා",
"ta": "கீரி சம்பா"
},
"Apple (Imp)": {
"si": "ඇපල් (ආනයනික)",
"ta": "ஆப்பிள் (இறக்குமதி)"
},
"Balaya": {
"si": "බලයා",
"ta": "பாலாயா"
},
"Big Onion (Local)": {
"si": "ලොකු ළූණු (දේශීය)",
"ta": "பெரிய வெங்காயம் (உள்ளூர்)"
},
"Coconut oil": {
"si": "පොල් තෙල්",
"ta": "தேங்காய் எண்ணெய்"
},
"Coconut Oil": {
"si": "පොල් තෙල්",
"ta": "தேங்காய் எண்ணெய்"
},
"Egg (White)": {
"si": "බිත්තර (සුදු)",
"ta": "முட்டை (வெள்ளை)"
},
"Katta": {
"si": "කට්ටා",
"ta": "கட்டா"
},
"Katta (Imp)": {
"si": "කට්ටා (ආනයනික)",
"ta": "கட்டா (இறக்குமதி)"
},
"Kekulu (White) (Imp)": {
"si": "කැකුළු (සුදු) (ආනයනික)",
"ta": "கெகுளு (வெள்ளை) (இறக்குமதி)"
},
"Nadu (Imp)": {
"si": "නාඩු (ආනයනික)",
"ta": "நாடு (இறக்குமதி)"
},
"Orange (Imp)": {
"si": "දොඩම් (ආනයනික)",
"ta": "ஆரஞ்சு (இறக்குமதி)"
},
"Red Dhal": {
"si": "රතු පරිප්පු",
"ta": "சிவப்பு பருப்பு"
},
"Sprat (Imp)": {
"si": "හාල් මැස්සෝ (ආනයනික)",
"ta": "மத்தி (இறக்குமதி)"
},
"Sugar (White)": {
"si": "සීනි (සුදු)",
"ta": "சர்க்கரை (வெள்ளை)"
}
},
"CATS": {
"Vegetables": {
"si": "එළවළු",
"ta": "காய்கறிகள்"
},
"Other": {
"si": "වෙනත්",
"ta": "பிற"
},
"Rice": {
"si": "සහල්",
"ta": "அரிசி"
},
"Fish": {
"si": "මාළු",
"ta": "மீன்"
},
"Fruits": {
"si": "පළතුරු",
"ta": "பழங்கள்"
}
},
"MARKETS": {
"Pettah": {
"si": "පිටකොටුව",
"ta": "பேட்டை"
},
"Dambulla": {
"si": "දඹුල්ල",
"ta": "தம்புள்ள"
},
"Narahenpita": {
"si": "නාරාහේන්පිට",
"ta": "நாரஹேன்பிட்ட"
},
"Negombo": {
"si": "මීගමුව",
"ta": "நீர்கொழும்பு"
},
"Marandagahamula": {
"si": "මාරන්දගහමුල",
"ta": "மரந்தகஹமுல"
}
},
"UNITS": {
"Rs./kg": {
"si": "රු./කි.ග්‍රෑ.",
"ta": "ரூ./கி."
},
"Rs./Nut": {
"si": "රු./ගෙඩිය",
"ta": "ரூ./காய்"
},
"Rs./Each": {
"si": "රු./එකක්",
"ta": "ரூ./ஒன்று"
},
"Rs./Ltr": {
"si": "රු./ලීටරය",
"ta": "ரூ./லிட்டர்"
}
},
"EMOJIS": {
"Beans": "🫘",
"Carrot": "🥕",
"Cabbage": "🥬",
"Tomato": "🍅",
"Brinjal": "🍆",
"Pumpkin": "🎃",
"Snake gourd": "🥒",
"Green Chilli": "🫑",
"Lime": "🍋",
"Red Onion (Local)": "🧅",
"Red Onion (lmp)": "🧅",
"Big Onion (Imp)": "🧅",
"Big Onion (Local)": "🧅",
"Potato (Local)": "🥔",
"Potato (Imp)": "🥔",
"Dried Chilli (Imp)": "🌶️",
"Coconut (Avg.)": "🥥",
"Coconut oil": "🫙",
"Banana (Sour)": "🍌",
"Papaw": "🥭",
"Pineapple": "🍍",
"Apple (Imp)": "🍎",
"Orange (Imp)": "🍊",
"Samba": "🍚",
"Nadu": "🍚",
"Kekulu (White)": "🍚",
"Kekulu (Red)": "🍚",
"Ponni Samba (Imp)": "🍚",
"Nadu (Imp)": "🍚",
"Keeri Samba": "🍚",
"Kelawalla": "🐟",
"Thalapath": "🐠",
"Paraw": "🐡",
"Salaya": "🐟",
"Hurulla": "🦈",
"Linna": "🐟",
"Balaya": "🐟",
"Red Dhal": "🫘",
"Sugar (White)": "🍬",
"Egg (White)": "🥚",
"Katta (Imp)": "🦐",
"Sprat (Imp)": "🐟",
"Beetroot": "🟣",
"Leeks": "🌿",
"Knol-khol": "🥦",
"Drumstick": "🌿",
"Manioc": "🥕",
"Ash Plantain": "🍌"
}
}

NAMES, CATS, MARKETS, UNITS, EMOJIS = TR["NAMES"], TR["CATS"], TR["MARKETS"], TR["UNITS"], TR["EMOJIS"]

MONTHS = {
    "en": ["January","February","March","April","May","June","July","August","September","October","November","December"],
    "si": ["ජනවාරි","පෙබරවාරි","මාර්තු","අප්‍රේල්","මැයි","ජූනි","ජූලි","අගෝස්තු","සැප්තැම්බර්","ඔක්තෝබර්","නොවැම්බර්","දෙසැම්බර්"],
    "ta": ["ஜனவரி","பிப்ரவரி","மார்ச்","ஏப்ரல்","மே","ஜூன்","ஜூலை","ஆகஸ்ட்","செப்டம்பர்","அக்டோபர்","நவம்பர்","டிசம்பர்"],
}
# "per kg" phrasing inside a sentence
PER = {
    "Rs./kg":   {"en": "per kg",    "si": "කිලෝග්‍රෑමයක", "ta": "ஒரு கிலோ"},
    "Rs./Nut":  {"en": "per nut",   "si": "ගෙඩියක",       "ta": "ஒரு காய்"},
    "Rs./Each": {"en": "each",      "si": "එකක",          "ta": "ஒன்றுக்கு"},
    "Rs./Ltr":  {"en": "per litre", "si": "ලීටරයක",       "ta": "ஒரு லிட்டர்"},
}

# How people type the crop name in English letters ("Singlish") when they search,
# e.g. "thakkali mila", "dehi rate". Left out when it is the same as the English name.
SINGLISH = {
 "Beans":"bonchi","Cabbage":"gowa","Tomato":"thakkali","Brinjal":"wambatu","Pumpkin":"wattakka",
 "Snake gourd":"pathola","Green Chilli":"amu miris","Lime":"dehi","Red Onion (Local)":"rathu lunu",
 "Red Onion (lmp)":"rathu lunu","Big Onion (Local)":"loku lunu","Big Onion (Imp)":"loku lunu",
 "Potato (Local)":"ala","Potato (Imp)":"ala","Dried Chilli (Imp)":"viyali miris","Coconut (Avg.)":"pol",
 "Coconut oil":"pol thel","Red Dhal":"parippu","Sugar (White)":"seeni","Egg (White)":"biththara",
 "Katta":"katta","Sprat (Imp)":"haal masso","Banana (Sour)":"embul kesel","Papaw":"papol","Pineapple":"annasi",
 "Orange (Imp)":"dodam","Samba":"samba haal","Nadu":"nadu haal","Kekulu (White)":"kekulu haal",
 "Kekulu (Red)":"rathu kekulu haal","Nadu (Imp)":"nadu haal","Kekulu (White) (Imp)":"kekulu haal",
 "Kelawalla":"kelawalla","Thalapath":"thalapath","Balaya":"balaya","Paraw":"parawa","Salaya":"salaya",
 "Hurulla":"hurulla","Linna":"linna","Katta (Imp)":"katta",
}
def sl(n): return SINGLISH.get(n, "")

def e(s):  return html.escape(str(s), quote=True)

# Copyright line for every page (the year updates itself). The prices belong to the official sources.
COPYRIGHT = (f'<span id="tg-copy">© {datetime.now().year} TopGoviya.lk · සියලු හිමිකම් ඇවිරිණි / All rights reserved · '
             'මිල දත්ත: මහ බැංකුව, HARTI, DEA (නිල මූලාශ්‍ර) / Price data: CBSL, HARTI &amp; DEA</span>')
def n_si(n): return (NAMES.get(n) or {}).get("si", n)
def n_ta(n): return (NAMES.get(n) or {}).get("ta", n)
def m_tr(m, l): return m if l == "en" else (MARKETS.get(m) or {}).get(l, m)
def c_tr(c, l): return c if l == "en" else (CATS.get(c) or {}).get(l, c)
def u_tr(u, l): return u if l == "en" else (UNITS.get(u) or {}).get(l, u)
def emoji(n): return EMOJIS.get(n, "🌿")
def money(v): return "—" if v is None else f"{round(v):,}"

def fdate(d, l):
    m = MONTHS[l][d.month - 1]
    return f"{d.year} {m} {d.day}" if l == "si" else f"{d.day} {m} {d.year}"

def slug(name):
    s = name.lower().replace("(lmp)", "(imp)")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

# ---------------------------------------------------------------- data helpers
def valid(series):
    return [(i, v) for i, v in enumerate(series) if v is not None]

def year_ago(series, dates, idx):
    """Price about one year before dates[idx] (closest report within 10 days)."""
    target = dates[idx] - timedelta(days=365)
    best, gap = None, 11
    for i, v in valid(series):
        g = abs((dates[i] - target).days)
        if g < gap:
            best, gap = (i, v), g
    return best

# ---------------------------------------------------------------- SVG chart
def chart_svg(points, dates, wpoints=None):
    """points = retail [(index, value)] for the last ~30 days; wpoints = wholesale (optional)."""
    if len(points) < 2:
        return ""
    wpoints = wpoints if (wpoints and len(wpoints) >= 2) else []
    W, H, L, R, T, B = 640, 220, 50, 16, 18, 34
    vals = [v for _, v in points] + [v for _, v in wpoints]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.15 or max(hi * 0.05, 5)
    lo, hi = lo - pad, hi + pad
    i0 = min([points[0][0]] + [p[0] for p in wpoints[:1]])
    i1 = max([points[-1][0]] + [p[0] for p in wpoints[-1:]])
    X = lambda i: L + (i - i0) * (W - L - R) / ((i1 - i0) or 1)
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / ((hi - lo) or 1))
    def path(pts): return " ".join(("M" if k == 0 else "L") + f"{X(i):.1f} {Y(v):.1f}" for k, (i, v) in enumerate(pts))
    line = path(points)
    area = line + f" L{X(points[-1][0]):.1f} {H-B} L{X(points[0][0]):.1f} {H-B} Z"
    grid = ""
    for k in range(4):
        v = lo + (hi - lo) * k / 3
        y = Y(v)
        grid += f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="#e3d9c4"/>'
        grid += f'<text x="{L-8}" y="{y+4:.1f}" text-anchor="end" class="ax">{round(v):,}</text>'
    d0, d1 = dates[i0], dates[i1]
    xl = (f'<text x="{L}" y="{H-10}" class="ax">{d0.day} {MONTHS["en"][d0.month-1][:3]}</text>'
          f'<text x="{W-R}" y="{H-10}" text-anchor="end" class="ax">{d1.day} {MONTHS["en"][d1.month-1][:3]}</text>')
    wl = ""
    if wpoints:
        wl = (f'<path d="{path(wpoints)}" fill="none" stroke="#a9802a" stroke-width="2.2" stroke-dasharray="6 4" stroke-linejoin="round" stroke-linecap="round"/>'
              f'<circle cx="{X(wpoints[-1][0]):.1f}" cy="{Y(wpoints[-1][1]):.1f}" r="4" fill="#a9802a"/>')
    lx, ly = X(points[-1][0]), Y(points[-1][1])
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="30 day price chart" class="chart">'
            f'<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0e4f4a" stop-opacity=".16"/>'
            f'<stop offset="1" stop-color="#0e4f4a" stop-opacity="0"/></linearGradient></defs>'
            f'{grid}{xl}<path d="{area}" fill="url(#a)"/>{wl}'
            f'<path d="{line}" fill="none" stroke="#0e4f4a" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4.5" fill="#0e4f4a" stroke="#fffdf7" stroke-width="2"/></svg>')

def wholesale_latest(c, latest_idx):
    """CBSL wholesale price for the latest report + which market it is from. None if not reported today."""
    w = c.get("wholesaleSeries") or []
    v = valid(w)
    if not v or v[-1][0] != latest_idx:
        return None
    price = v[-1][1]
    wm = c.get("wholesaleMarkets") or {}
    mkt = c["primaryMarket"] if wm.get(c["primaryMarket"]) == price else next((k for k, x in wm.items() if x == price), c["primaryMarket"])
    return price, mkt, v

# ---------------------------------------------------------------- shared page shell
CSS = """
:root{--paper:#f4efe4;--card:#fffdf7;--ink:#191d1a;--soft:#3a403a;--muted:#6f685b;--line:#e3d9c4;--line2:#cdbf9f;
--petrol:#0e4f4a;--gold:#a9802a;--up:#b23a2e;--upbg:#f7e6e2;--down:#2c7a52;--downbg:#e3efe6;--amber:#8a5a00;--amberbg:#fbefd4}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--paper);color:var(--ink);font-family:'Hanken Grotesk','Noto Sans Sinhala','Noto Sans Tamil',sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--petrol)}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:18px 0;border-bottom:2px solid var(--ink);font-size:14px}
.top .brand{font-family:'Newsreader',serif;font-size:21px;font-weight:600;color:var(--ink);text-decoration:none}
.crumb{font-size:13px;color:var(--muted);margin:18px 0 0}
.crumb a{color:var(--muted)}
h1{font-family:'Newsreader','Noto Sans Sinhala',serif;font-weight:500;font-size:clamp(34px,7vw,52px);line-height:1.05;margin:10px 0 4px;letter-spacing:-.01em}
.alt{font-size:16px;color:var(--soft);margin:0}
.hero{display:flex;flex-wrap:wrap;align-items:flex-end;gap:14px 22px;margin:26px 0 8px}
.big{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:clamp(46px,11vw,72px);line-height:1;letter-spacing:-.03em}
.big small{font-size:15px;font-weight:500;color:var(--muted);letter-spacing:0;margin-left:6px}
.big .rs{font-family:'Noto Sans Sinhala','Hanken Grotesk',sans-serif;font-size:.36em;font-weight:600;color:var(--muted);margin-right:8px;letter-spacing:0;vertical-align:.55em}
.duo{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0 0}
.duo div{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.duo b{display:block;font-family:'JetBrains Mono',monospace;font-size:22px}
.duo span{font-size:13px;color:var(--muted)}
.duo .w{border-left:4px solid var(--gold)}.duo .r{border-left:4px solid var(--petrol)}.duo .g{border-left:4px solid var(--line2)}
.key{font-size:13px;color:var(--muted);margin:8px 0 0}.key i{display:inline-block;width:18px;height:3px;vertical-align:middle;margin:0 5px 0 12px}
td.w{color:#7a5c1c}
.chg{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:15px;padding:5px 11px;border-radius:9px;display:inline-block}
.chg.up{color:var(--up);background:var(--upbg)}.chg.down{color:var(--down);background:var(--downbg)}.chg.flat{color:var(--muted);background:#efeada}
.asof{font-size:14px;color:var(--soft);margin:4px 0 0}
.stale{background:var(--amberbg);color:var(--amber);border-radius:10px;padding:9px 13px;font-size:14px;margin:12px 0 0}
.story{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin:26px 0}
.story p{margin:0 0 10px}.story p:last-child{margin:0}
h2{font-family:'Newsreader','Noto Sans Sinhala',serif;font-weight:500;font-size:25px;margin:36px 0 10px}
h2 span{font-family:'Hanken Grotesk',sans-serif;font-size:14px;color:var(--muted);font-weight:500;margin-left:8px}
.chart{width:100%;height:auto;display:block;background:var(--card);border:1px solid var(--line);border-radius:14px}
.ax{font:10.5px 'JetBrains Mono',monospace;fill:#7a7264}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:15px;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--line)}
th{font-size:13px;color:var(--muted);font-weight:600;background:#faf6ec}
td.n{font-family:'JetBrains Mono',monospace;font-weight:600;text-align:right;white-space:nowrap}
th.n{text-align:right}
tr:last-child td{border-bottom:0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.stat b{display:block;font-family:'JetBrains Mono',monospace;font-size:20px}
.stat span{font-size:13px;color:var(--muted)}
.cta{display:block;text-align:center;background:var(--petrol);color:#fff;text-decoration:none;font-weight:700;border-radius:12px;padding:15px 18px;margin:30px 0 0;font-size:16px}
.cta:hover{background:#0a3a36}
.cta:focus-visible,a:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.rel{display:flex;flex-wrap:wrap;gap:8px}
.rel a{background:var(--card);border:1px solid var(--line2);border-radius:999px;padding:7px 14px;text-decoration:none;font-size:14px;color:var(--soft)}
.rel a:hover{border-color:var(--petrol);color:var(--petrol)}
.note{font-size:13px;color:var(--muted);margin:34px 0 0;padding-top:16px;border-top:1px solid var(--line2)}
footer{font-size:13px;color:var(--muted);padding:18px 0 50px}
footer a{font-weight:700}
.cat{font-family:'Newsreader','Noto Sans Sinhala',serif;font-size:22px;margin:30px 0 8px}
"""

def shell(title, desc, canonical, body, jsonld, lang="si"):
    return f"""<!DOCTYPE html>
<html lang="{lang}">
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
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>
<body>
<div class="wrap">
<header class="top"><a class="brand" href="../index.html">TopGoviya.lk</a><a href="index.html">සියලු මිල ගණන් / All prices</a></header>
{body}
<p class="note">මිල ගණන් මඟ පෙන්වීමක් පමණි. ඔබගේ තීරණ ඔබගේ වගකීම වේ.<br>
Prices are indicative only. Decisions are your responsibility. Source: Central Bank of Sri Lanka daily price reports (not an official publication).<br>
விலைகள் வழிகாட்டல் மட்டுமே. உங்கள் முடிவுகளுக்கு நீங்களே பொறுப்பு.</p>
<footer>{COPYRIGHT}<br>Design &amp; development by <a href="https://ebooklanka.com" target="_blank" rel="noopener">ebooklanka.com</a> · Built in Gampola, Sri Lanka</footer>
</div>
</body>
</html>
"""

# ---------------------------------------------------------------- one commodity page
def commodity_page(c, dates, latest_idx, all_items):
    name, unit, mkt = c["name"], c["unit"], c["primaryMarket"]
    s = c["series"]
    v = valid(s)
    if not v:
        return None
    li, price = v[-1]
    prev = v[-2] if len(v) > 1 else None
    d = dates[li]
    per = PER.get(unit, {"en": "", "si": "", "ta": ""})

    # change vs previous report
    if prev:
        diff = price - prev[1]
        pct = diff / prev[1] * 100 if prev[1] else 0
        direction = "flat" if abs(pct) < 0.5 else ("up" if diff > 0 else "down")
    else:
        diff, pct, direction = 0, 0, "flat"
    arrow = {"up": "▲", "down": "▼", "flat": "■"}[direction]
    sign = "+" if pct > 0 else ""

    # sentences in 3 languages
    if prev:
        pdt = dates[prev[0]]
        ch_si = {"up": f"පෙර වාර්තාවට ({fdate(pdt,'si')}) සාපේක්ෂව රු. {money(abs(diff))} කින් ({abs(pct):.1f}%) ඉහළ ගොස් ඇත.",
                 "down": f"පෙර වාර්තාවට ({fdate(pdt,'si')}) සාපේක්ෂව රු. {money(abs(diff))} කින් ({abs(pct):.1f}%) පහළ ගොස් ඇත.",
                 "flat": f"පෙර වාර්තාවට ({fdate(pdt,'si')}) සාපේක්ෂව මිල වෙනස් වී නැත."}[direction]
        ch_en = {"up": f"That is up Rs. {money(abs(diff))} ({abs(pct):.1f}%) from the previous report on {fdate(pdt,'en')}.",
                 "down": f"That is down Rs. {money(abs(diff))} ({abs(pct):.1f}%) from the previous report on {fdate(pdt,'en')}.",
                 "flat": f"The price is unchanged from the previous report on {fdate(pdt,'en')}."}[direction]
        ch_ta = {"up": f"முந்தைய அறிக்கையை ({fdate(pdt,'ta')}) விட ரூ. {money(abs(diff))} ({abs(pct):.1f}%) உயர்ந்துள்ளது.",
                 "down": f"முந்தைய அறிக்கையை ({fdate(pdt,'ta')}) விட ரூ. {money(abs(diff))} ({abs(pct):.1f}%) குறைந்துள்ளது.",
                 "flat": f"முந்தைய அறிக்கையுடன் ({fdate(pdt,'ta')}) ஒப்பிடுகையில் மாற்றமில்லை."}[direction]
    else:
        ch_si = ch_en = ch_ta = ""
    p_si = f"{fdate(d,'si')} දින {m_tr(mkt,'si')} වෙළඳපොළේ {n_si(name)} {per['si']} සිල්ලර මිල රු. {money(price)} කි. {ch_si}"
    p_en = f"On {fdate(d,'en')}, the retail price of {name} at {mkt} market was Rs. {money(price)} {per['en']}. {ch_en}"
    p_ta = f"{fdate(d,'ta')} அன்று {m_tr(mkt,'ta')} சந்தையில் {n_ta(name)} சில்லறை விலை {per['ta']} ரூ. {money(price)}. {ch_ta}"

    wl0 = wholesale_latest(c, latest_idx) if li == latest_idx else None
    if wl0:
        wp0, wm0 = wl0[0], wl0[1]
        gap0 = price - wp0
        p_si += f" {m_tr(wm0,'si')} තොග මිල රු. {money(wp0)} කි; සිල්ලර හා තොග මිල අතර පරතරය රු. {money(gap0)} කි."
        p_en += f" The CBSL wholesale price at {wm0} was Rs. {money(wp0)}, a retail–wholesale gap of Rs. {money(gap0)}."
        p_ta += f" {m_tr(wm0,'ta')} மொத்த விலை ரூ. {money(wp0)}; சில்லறை–மொத்த இடைவெளி ரூ. {money(gap0)}."

    stale = ""
    if li != latest_idx:
        stale = (f'<p class="stale">⚠ මෙම භාණ්ඩය අවසන් වරට වාර්තා වූයේ {fdate(d,"si")} දිනයි. '
                 f'Last reported on {fdate(d,"en")}.</p>')

    # CBSL wholesale (same report) - None if not reported today
    wl = wholesale_latest(c, latest_idx) if li == latest_idx else None
    wprice, wmkt, wv = wl if wl else (None, None, [])

    # markets table: wholesale + retail side by side
    rmk = c.get("markets") or {}
    wmk = c.get("wholesaleMarkets") or {} if wl else {}
    order_m = list(dict.fromkeys(list(wmk.keys()) + list(rmk.keys())))
    rows = ""
    for mk in order_m:
        wv_ = wmk.get(mk); rv_ = rmk.get(mk)
        rows += (f'<tr><td>{e(m_tr(mk,"si"))} <span style="color:var(--muted)">/ {e(mk)}</span></td>'
                 + (f'<td class="n w">{"රු. " + money(wv_) if wv_ is not None else "—"}</td>' if wl else "")
                 + f'<td class="n">{"රු. " + money(rv_) if rv_ is not None else "—"}</td></tr>')
    whead = '<th class="n">තොග / Wholesale</th>' if wl else ""
    markets_html = (f'<h2>වෙළඳපොළ අනුව මිල<span>Price by market, {e(u_tr(unit,"si"))}</span></h2>'
                    f'<div class="scroll"><table><thead><tr><th>වෙළඳපොළ / Market</th>{whead}<th class="n">සිල්ලර / Retail</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div>') if rows else ""

    # 30-day chart (retail solid, wholesale dashed)
    cutoff = dates[latest_idx] - timedelta(days=31)
    pts30 = [(i, x) for i, x in v if dates[i] >= cutoff]
    wpts30 = [(i, x) for i, x in wv if dates[i] >= cutoff]
    svg = chart_svg(pts30, dates, wpts30)
    key = (f'<p class="key"><i style="background:#0e4f4a"></i>සිල්ලර / Retail ({e(mkt)})'
           f'<i style="background:repeating-linear-gradient(90deg,#a9802a 0 6px,transparent 6px 10px)"></i>තොග / Wholesale ({e(wmkt)})</p>') if (svg and len(wpts30) >= 2) else ""
    chart_html = f'<h2>පසුගිය දින 30<span>Last 30 days</span></h2>{svg}{key}' if svg else ""

    # stats
    stats = []
    if pts30:
        stats.append((money(min(x for _, x in pts30)), "දින 30 අවම / 30-day low"))
        stats.append((money(max(x for _, x in pts30)), "දින 30 උපරිම / 30-day high"))
    ya = year_ago(s, dates, li)
    if ya:
        stats.append((money(ya[1]), f"වසරකට පෙර / 1 year ago ({dates[ya[0]].day} {MONTHS['en'][dates[ya[0]].month-1][:3]} {dates[ya[0]].year})"))
    stats_html = ('<div class="stats" style="margin-top:14px">' +
                  "".join(f'<div class="stat"><b>{a}</b><span>{e(b)}</span></div>' for a, b in stats) +
                  '</div>') if stats else ""

    # last 10 reports
    hist = ""
    last10 = v[-10:][::-1]
    for k, (i, x) in enumerate(last10):
        older = last10[k + 1][1] if k + 1 < len(last10) else None
        if older:
            dd = x - older
            cls = "up" if dd > 0 else ("down" if dd < 0 else "flat")
            chg = f'<span class="chg {cls}" style="font-size:12px;padding:2px 7px">{"+" if dd > 0 else ""}{money(dd)}</span>'
        else:
            chg = ""
        hist += f'<tr><td>{fdate(dates[i],"si")}</td><td class="n">රු. {money(x)}</td><td class="n">{chg}</td></tr>'
    hist_html = (f'<h2>පසුගිය වාර්තා 10<span>Last 10 reports, {e(mkt)}</span></h2>'
                 f'<div class="scroll"><table><thead><tr><th>දිනය / Date</th><th class="n">මිල / Price</th><th class="n">වෙනස / Change</th></tr></thead>'
                 f'<tbody>{hist}</tbody></table></div>')

    # related links (same category first)
    same = [x for x in all_items if x["category"] == c["category"] and x["name"] != name]
    rel = "".join(f'<a href="{slug(x["name"])}.html">{emoji(x["name"])} {e(n_si(x["name"]))}</a>' for x in same[:12])
    rel_html = f'<h2>{e(c_tr(c["category"],"si"))} මිල<span>Other {e(c["category"].lower())} prices</span></h2><div class="rel">{rel}</div>' if rel else ""

    if wl:
        gap = price - wprice
        gpct = gap / wprice * 100 if wprice else 0
        duo_html = (f'<div class="duo">'
                    f'<div class="w"><b>රු. {money(wprice)}</b><span>තොග මිල / Wholesale · 📍 {e(m_tr(wmkt,"si"))}</span></div>'
                    f'<div class="r"><b>රු. {money(price)}</b><span>සිල්ලර මිල / Retail · 📍 {e(m_tr(mkt,"si"))}</span></div>'
                    f'<div class="g"><b>රු. {money(gap)}</b><span>පරතරය / Gap ({gpct:.0f}%)</span></div></div>'
                    f'<p class="asof" style="margin-top:8px">මූලාශ්‍රය: CBSL දෛනික මිල වාර්තාව · '
                    f'<a href="../wholesale.html">HARTI වෙළඳපොළ 10ක තොග මිල →</a></p>')
    else:
        duo_html = '<p class="asof" style="margin-top:6px"><a href="../wholesale.html">HARTI තොග මිල බලන්න / See HARTI wholesale prices →</a></p>'

    # ---- FAQ: short factual answers built from the same numbers (Sinhala + English)
    faq = []   # (question_si, question_en, answer_si, answer_en)
    a_si = f"{fdate(d,'si')} දින {m_tr(mkt,'si')} වෙළඳපොළේ සිල්ලර මිල {per['si']} රු. {money(price)}."
    a_en = f"On {fdate(d,'en')}, the retail price at {mkt} was Rs. {money(price)} {per['en']}."
    if wl:
        a_si += f" {m_tr(wmkt,'si')} තොග මිල රු. {money(wprice)}."
        a_en += f" The wholesale price at {wmkt} was Rs. {money(wprice)}."
    faq.append((f"{n_si(name)} මිල අද කීයද?", f"What is the {name} price today in Sri Lanka?", a_si, a_en))
    if prev:
        faq.append((f"{n_si(name)} මිල ඉහළ ගියාද, පහළ ගියාද?", f"Did the {name} price go up or down?", ch_si, ch_en))
    if li == latest_idx:
        rv = [(m_, x) for m_, x in (c.get("markets") or {}).items() if x is not None]
        if len(rv) >= 2:
            lo_m, lo_v = min(rv, key=lambda t: t[1]); hi_m, hi_v = max(rv, key=lambda t: t[1])
            faq.append((f"අද {n_si(name)} අඩුම මිලට ලැබෙන්නේ කොහේද?", f"Which market has the cheapest {name} today?",
                        f"සිල්ලර මිල අඩුම {m_tr(lo_m,'si')} (රු. {money(lo_v)}), වැඩිම {m_tr(hi_m,'si')} (රු. {money(hi_v)}).",
                        f"The lowest retail price was at {lo_m} (Rs. {money(lo_v)}) and the highest at {hi_m} (Rs. {money(hi_v)})."))
    yr = [(i, x) for i, x in v if dates[i] >= dates[li] - timedelta(days=365)]
    if len(yr) >= 20:
        (hi_i, hi_x), (lo_i, lo_x) = max(yr, key=lambda t: t[1]), min(yr, key=lambda t: t[1])
        faq.append((f"පසුගිය මාස 12 තුළ {n_si(name)} ඉහළම හා අඩුම මිල?", f"What were the highest and lowest {name} prices in the last 12 months?",
                     f"{m_tr(mkt,'si')} සිල්ලර: ඉහළම රු. {money(hi_x)} ({fdate(dates[hi_i],'si')}), අඩුම රු. {money(lo_x)} ({fdate(dates[lo_i],'si')}).",
                     f"At {mkt} (retail): highest Rs. {money(hi_x)} on {fdate(dates[hi_i],'en')}, lowest Rs. {money(lo_x)} on {fdate(dates[lo_i],'en')}."))
    ya_ = year_ago(s, dates, li)
    if ya_:
        faq.append((f"වසරකට පෙර {n_si(name)} මිල කීයද?", f"What was the {name} price a year ago?",
                     f"{fdate(dates[ya_[0]],'si')} දින {m_tr(mkt,'si')} සිල්ලර මිල රු. {money(ya_[1])} විය (අද රු. {money(price)}).",
                     f"On {fdate(dates[ya_[0]],'en')} it was Rs. {money(ya_[1])} at {mkt} (today Rs. {money(price)})."))
    faq.append((f"මෙම මිල ගණන් කොහෙන්ද?", f"Where do these {name} prices come from?",
                 "ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාවෙන් (සතියේ දින) ස්වයංක්‍රීයව ලබා ගනී. මිල ගණන් මඟපෙන්වීමක් පමණි.",
                 "From the Central Bank of Sri Lanka daily price report (weekdays), collected automatically. Prices are indicative only."))
    faq_html = ('<h2>නිතර අසන ප්‍රශ්න<span>Frequently asked questions</span></h2><div class="story" style="font-size:14.5px">'
                + "".join(f'<h3 style="font-size:15.5px;margin:12px 0 4px">{e(qs)} <span style="color:var(--muted);font-weight:500">/ {e(qe)}</span></h3>'
                          f'<p style="margin:0">{e(as_)}</p><p lang="en" style="margin:2px 0 0;color:var(--soft)">{e(ae)}</p>'
                          for qs, qe, as_, ae in faq) + '</div>')

    # ---- trust line: the official PDF this price came from + how to report a wrong price
    pdf_name = f"price_report_{d.strftime('%Y%m%d')}_e.pdf"
    trust_html = ('<p class="asof" style="margin-top:14px">'
                  + (f'📑 <a href="../pdfs/{pdf_name}" rel="noopener">මහ බැංකු මුල් වාර්තාව (නිල PDF) — {fdate(d,"si")}</a> · '
                     f'Official CBSL report. ' if os.path.exists(os.path.join("pdfs", pdf_name)) else "")
                  + 'මිලක් වැරදි යැයි සිතේද? <a href="../data-sources.html">අපට දන්වන්න</a> / Spotted a wrong price? Tell us.</p>')

    body = f"""
<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / <a href="index.html">මිල ගණන්</a> / {e(n_si(name))}</p>
<h1>{emoji(name)} {e(n_si(name))} මිල අද</h1>
<p class="alt">{e(name)} price today in Sri Lanka{(" · " + e(sl(name)) + " mila ada · " + e(sl(name)) + " rate today") if sl(name) else ""}<br>{e(n_ta(name))} விலை இன்று</p>
<div class="hero">
  <div class="big"><span class="rs">රු.</span>{money(price)}<small>{e(u_tr(unit,'si'))}</small></div>
  <span class="chg {direction}">{arrow} {sign}{pct:.1f}%</span>
</div>
<p class="asof"><b>🏷️ සිල්ලර මිල / Retail price</b> · 📍 {e(m_tr(mkt,'si'))} ({e(mkt)}) · {fdate(d,'si')}</p>
{duo_html}
{stale}
<div class="story">
  <p>{e(p_si)}</p>
  <p lang="en">{e(p_en)}</p>
  <p lang="ta">{e(p_ta)}</p>
</div>
{markets_html}
{chart_html}
{stats_html}
{hist_html}
{faq_html}
{trust_html}
<a class="cta" href="../index.html">සම්පූර්ණ ප්‍රස්ථාර, වසර 4ක ඉතිහාසය හා ලාභ ගණකය බලන්න</a>
{rel_html}
"""
    url = f"{SITE}/{OUT_DIR}/{slug(name)}.html"
    title = (f"{n_si(name)} මිල අද" + (f" ({sl(name).title()} Mila)" if sl(name) else "")
             + f" – තොග හා සිල්ලර | {name} Price Today Sri Lanka – TopGoviya.lk")
    wtxt = f"Wholesale Rs. {money(wprice)} at {wmkt}, retail Rs. {money(price)} at {mkt}" if wl else f"Retail Rs. {money(price)} at {mkt}"
    desc = (f"{name} price today ({fdate(d,'en')}): {wtxt} {per['en']}. "
            f"Compare markets and the 30-day trend. {n_si(name)} තොග හා සිල්ලර මිල."
            + (f" {n_si(name).replace('ළ', 'ල')} මිල." if 'ළ' in n_si(name) else "")
            + (f" {sl(name)} mila ada, {sl(name)} rate." if sl(name) else ""))
    first = dates[v[0][0]]
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "TopGoviya.lk", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Prices", "item": f"{SITE}/{OUT_DIR}/"},
            {"@type": "ListItem", "position": 3, "name": f"{name} price", "item": url}]},
        {"@type": "Dataset", "name": f"{name} price in Sri Lanka – daily retail and wholesale",
         "description": (f"Daily {name} prices in Sri Lanka ({unit}) at {mkt} and other markets, from the Central Bank of Sri Lanka "
                         f"daily price report, {fdate(first,'en')} to {fdate(d,'en')}. Latest retail price Rs. {money(price)} on {fdate(d,'en')}."),
         "url": url, "inLanguage": ["si", "en", "ta"], "spatialCoverage": "Sri Lanka",
         "temporalCoverage": f"{first.isoformat()}/{d.isoformat()}", "dateModified": d.isoformat(),
         "variableMeasured": f"{name} price ({unit})",
         "isBasedOn": "https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report",
         "creator": {"@type": "Organization", "name": "TopGoviya.lk", "url": SITE + "/"}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": qe, "acceptedAnswer": {"@type": "Answer", "text": ae}} for qs, qe, as_, ae in faq]}]}
    return shell(title, desc, url, body, jsonld)

# ---------------------------------------------------------------- hub page
def hub_page(items, dates, latest_idx):
    order = ["Vegetables", "Fruits", "Other", "Rice", "Fish"]
    cats = sorted({c["category"] for c in items}, key=lambda x: order.index(x) if x in order else 99)
    body = (f'<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / මිල ගණන්</p>'
            f'<h1>අද එළවළු, පළතුරු හා ආහාර මිල</h1>'
            f'<p class="alt">Today\'s wholesale and retail prices in Sri Lanka · elawalu mila ada · elawalu rate today<br>இன்றைய மொத்த மற்றும் சில்லறை விலைகள்</p>'
            f'<p class="asof" style="margin-top:14px"><b>🏷️ තොග හා සිල්ලර මිල / Wholesale &amp; retail / மொத்த &amp; சில்லறை</b><br>'
            f'නවතම වාර්තාව / Latest report: {fdate(dates[latest_idx],"si")} · CBSL</p>'
            f'<div class="story" style="margin:18px 0 0;font-size:14.5px">'
            f'<p>තොග මිල යනු වෙළඳපොළේ තොග වශයෙන් විකිණෙන මිලයි (ගොවියාට ලැබෙන මිල සාමාන්‍යයෙන් මීට අඩුයි). සිල්ලර මිල යනු පාරිභෝගිකයා ගෙවන මිලයි. දෙකම මහ බැංකුවේ දෛනික මිල වාර්තාවෙනි, '
            f'📍 සලකුණින් පෙන්වන වෙළඳපොළ අනුව. අනෙක් වෙළඳපොළවල් සැසඳීමට භාණ්ඩයක් තට්ටු කරන්න.</p>'
            f'<p lang="en">Wholesale is the bulk trading price at the market (farm-gate prices are usually lower); retail is what shoppers pay. Both come from the Central Bank of Sri Lanka '
            f'daily price report, at the market shown with 📍. Tap an item to compare other markets.</p>'
            f'<p lang="ta">மொத்த விலை சந்தையின் மொத்த வியாபார விலை (பண்ணை விலை பொதுவாக குறைவு); சில்லறை விலை வாங்குபவர் செலுத்துவது. இரண்டும் இலங்கை மத்திய வங்கி அறிக்கையிலிருந்து.</p>'
            f'<p><a href="../wholesale.html">HARTI වෙළඳපොළ 10ක තොග මිල බලන්න / HARTI wholesale for 10 markets →</a></p></div>')
    for cat in cats:
        rows = ""
        for c in sorted([x for x in items if x["category"] == cat], key=lambda x: x["name"]):
            v = valid(c["series"])
            if not v:
                continue
            price = v[-1][1]
            wl = wholesale_latest(c, latest_idx) if v[-1][0] == latest_idx else None
            same_mkt = wl and wl[1] == c["primaryMarket"]
            mk_line = (f'📍 {e(m_tr(c["primaryMarket"],"si"))} / {e(c["primaryMarket"])}' if (not wl or same_mkt)
                       else f'📍 තොග {e(m_tr(wl[1],"si"))} · සිල්ලර {e(m_tr(c["primaryMarket"],"si"))}')
            rows += (f'<tr><td><a href="{slug(c["name"])}.html">{emoji(c["name"])} {e(n_si(c["name"]))}</a> '
                     f'<span style="color:var(--muted)">/ {e(c["name"])}</span>'
                     f'<br><span style="font-size:12.5px;color:var(--muted)">{mk_line} · {e(u_tr(c["unit"],"si"))}</span></td>'
                     f'<td class="n w">{money(wl[0]) if wl else "—"}</td>'
                     f'<td class="n">{money(price)}</td></tr>')
        body += (f'<h2 class="cat">{e(c_tr(cat,"si"))} <span>{e(cat)}</span></h2><div class="scroll"><table>'
                 f'<thead><tr><th>භාණ්ඩය / Item</th><th class="n">තොග<br>Wholesale</th><th class="n">සිල්ලර<br>Retail</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table></div>')
    body += '<p class="asof" style="margin-top:10px">මිල රුපියල් වලින් / Prices in Rs. · — = එදින වාර්තා නොවීය / not reported that day</p>'
    body += '<a class="cta" href="../index.html">සම්පූර්ණ ප්‍රස්ථාර හා ගණක බලන්න</a>'
    url = f"{SITE}/{OUT_DIR}/"
    title = "අද එළවළු මිල (Elawalu Mila Ada) – තොග හා සිල්ලර | Vegetable Prices Today Sri Lanka – TopGoviya.lk"
    desc = (f"Today's wholesale and retail prices for {len(items)} vegetables, fruits, rice and fish in Sri Lanka "
            f"({fdate(dates[latest_idx],'en')}). Daily from CBSL reports. අද එලවලු මිල, තොග හා සිල්ලර. elawalu mila ada, thakkali mila, dehi mila.")
    jsonld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": url}
    return shell(title, desc, url, body, jsonld)

# ---------------------------------------------------------------- sitemap
def update_sitemap(slugs, lastmod):
    path = "sitemap.xml"
    if os.path.exists(path):
        xml = open(path, encoding="utf-8").read()
    else:
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n</urlset>\n'
    # remove old /price/ entries, keep every other page exactly as it was
    xml = re.sub(r"\s*<url>\s*<loc>[^<]*/" + OUT_DIR + r"/[^<]*</loc>.*?</url>", "", xml, flags=re.S)
    new = f"  <url>\n    <loc>{SITE}/{OUT_DIR}/</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.9</priority>\n  </url>\n"
    for s in slugs:
        new += f"  <url>\n    <loc>{SITE}/{OUT_DIR}/{s}.html</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>\n"
    xml = xml.replace("</urlset>", new + "</urlset>")
    open(path, "w", encoding="utf-8").write(xml)

# ---------------------------------------------------------------- main
def main():
    db = json.load(open("data.json", encoding="utf-8"))
    dates = [datetime.strptime(x, "%Y-%m-%d").date() for x in db["dates"]]
    latest_idx = len(dates) - 1
    items = db["commodities"]
    os.makedirs(OUT_DIR, exist_ok=True)
    made = []
    for c in items:
        page = commodity_page(c, dates, latest_idx, items)
        if page:
            s = slug(c["name"])
            open(os.path.join(OUT_DIR, s + ".html"), "w", encoding="utf-8").write(page)
            made.append(s)
    open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8").write(hub_page(items, dates, latest_idx))
    update_sitemap(made, dates[latest_idx].isoformat())
    print(f"Built {len(made)} commodity pages + hub page, sitemap updated.")

if __name__ == "__main__":
    main()
