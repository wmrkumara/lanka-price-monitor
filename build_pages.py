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

def e(s):  return html.escape(str(s), quote=True)
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
def chart_svg(points, dates):
    """points = [(index, value)] for the last ~30 days."""
    if len(points) < 2:
        return ""
    W, H, L, R, T, B = 640, 220, 50, 16, 18, 34
    vals = [v for _, v in points]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.15 or max(hi * 0.05, 5)
    lo, hi = lo - pad, hi + pad
    i0, i1 = points[0][0], points[-1][0]
    X = lambda i: L + (i - i0) * (W - L - R) / ((i1 - i0) or 1)
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / ((hi - lo) or 1))
    line = " ".join(("M" if k == 0 else "L") + f"{X(i):.1f} {Y(v):.1f}" for k, (i, v) in enumerate(points))
    area = line + f" L{X(i1):.1f} {H-B} L{X(i0):.1f} {H-B} Z"
    grid = ""
    for k in range(4):
        v = lo + (hi - lo) * k / 3
        y = Y(v)
        grid += f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="#e3d9c4"/>'
        grid += f'<text x="{L-8}" y="{y+4:.1f}" text-anchor="end" class="ax">{round(v):,}</text>'
    d0, d1 = dates[i0], dates[i1]
    xl = (f'<text x="{L}" y="{H-10}" class="ax">{d0.day} {MONTHS["en"][d0.month-1][:3]}</text>'
          f'<text x="{W-R}" y="{H-10}" text-anchor="end" class="ax">{d1.day} {MONTHS["en"][d1.month-1][:3]}</text>')
    lx, ly = X(points[-1][0]), Y(points[-1][1])
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="30 day price chart" class="chart">'
            f'<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0e4f4a" stop-opacity=".18"/>'
            f'<stop offset="1" stop-color="#0e4f4a" stop-opacity="0"/></linearGradient></defs>'
            f'{grid}{xl}<path d="{area}" fill="url(#a)"/>'
            f'<path d="{line}" fill="none" stroke="#0e4f4a" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4.5" fill="#a9802a" stroke="#fffdf7" stroke-width="2"/></svg>')

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
<footer>Design &amp; development by <a href="https://ebooklanka.com" target="_blank" rel="noopener">ebooklanka.com</a> · Built in Gampola, Sri Lanka</footer>
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

    stale = ""
    if li != latest_idx:
        stale = (f'<p class="stale">⚠ මෙම භාණ්ඩය අවසන් වරට වාර්තා වූයේ {fdate(d,"si")} දිනයි. '
                 f'Last reported on {fdate(d,"en")}.</p>')

    # markets table
    rows = ""
    for mk, mv in (c.get("markets") or {}).items():
        rows += (f'<tr><td>{e(m_tr(mk,"si"))} <span style="color:var(--muted)">/ {e(mk)}</span></td>'
                 f'<td class="n">{"රු. " + money(mv) if mv is not None else "—"}</td></tr>')
    markets_html = (f'<h2>වෙළඳපොළ අනුව මිල<span>Price by market</span></h2>'
                    f'<div class="scroll"><table><thead><tr><th>වෙළඳපොළ / Market</th><th class="n">{e(u_tr(unit,"si"))}</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div>') if rows else ""

    # 30-day chart
    cutoff = dates[latest_idx] - timedelta(days=31)
    pts30 = [(i, x) for i, x in v if dates[i] >= cutoff]
    svg = chart_svg(pts30, dates)
    chart_html = f'<h2>පසුගිය දින 30<span>Last 30 days</span></h2>{svg}' if svg else ""

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

    body = f"""
<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / <a href="index.html">මිල ගණන්</a> / {e(n_si(name))}</p>
<h1>{emoji(name)} {e(n_si(name))} මිල අද</h1>
<p class="alt">{e(name)} price today in Sri Lanka<br>{e(n_ta(name))} விலை இன்று</p>
<div class="hero">
  <div class="big">රු. {money(price)}<small>{e(u_tr(unit,'si'))}</small></div>
  <span class="chg {direction}">{arrow} {sign}{pct:.1f}%</span>
</div>
<p class="asof">{e(m_tr(mkt,'si'))} ({e(mkt)}) සිල්ලර මිල · {fdate(d,'si')}</p>
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
<a class="cta" href="../index.html">සම්පූර්ණ ප්‍රස්ථාර, වසර 4ක ඉතිහාසය හා ලාභ ගණකය බලන්න</a>
{rel_html}
"""
    url = f"{SITE}/{OUT_DIR}/{slug(name)}.html"
    title = f"{n_si(name)} මිල අද | {name} Price Today Sri Lanka – TopGoviya.lk"
    desc = (f"{name} retail price today: Rs. {money(price)} {per['en']} at {mkt} ({fdate(d,'en')}). "
            f"Compare markets and see the 30-day trend. {n_si(name)} අද මිල රු. {money(price)}.")
    jsonld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "TopGoviya.lk", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Prices", "item": f"{SITE}/{OUT_DIR}/"},
        {"@type": "ListItem", "position": 3, "name": f"{name} price", "item": url}]}
    return shell(title, desc, url, body, jsonld)

# ---------------------------------------------------------------- hub page
def hub_page(items, dates, latest_idx):
    order = ["Vegetables", "Fruits", "Other", "Rice", "Fish"]
    cats = sorted({c["category"] for c in items}, key=lambda x: order.index(x) if x in order else 99)
    body = (f'<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / මිල ගණන්</p>'
            f'<h1>අද එළවළු, පළතුරු හා ආහාර මිල</h1>'
            f'<p class="alt">Today\'s vegetable, fruit, rice and fish prices in Sri Lanka<br>இன்றைய காய்கறி, பழம், அரிசி, மீன் விலைகள்</p>'
            f'<p class="asof" style="margin-top:14px">නවතම වාර්තාව / Latest report: {fdate(dates[latest_idx],"si")}</p>')
    for cat in cats:
        rows = ""
        for c in sorted([x for x in items if x["category"] == cat], key=lambda x: x["name"]):
            v = valid(c["series"])
            if not v:
                continue
            price = v[-1][1]
            rows += (f'<tr><td><a href="{slug(c["name"])}.html">{emoji(c["name"])} {e(n_si(c["name"]))}</a> '
                     f'<span style="color:var(--muted)">/ {e(c["name"])}</span></td>'
                     f'<td class="n">රු. {money(price)} <span style="color:var(--muted);font-weight:500;font-size:12px">{e(u_tr(c["unit"],"si"))}</span></td></tr>')
        body += f'<h2 class="cat">{e(c_tr(cat,"si"))} <span>{e(cat)}</span></h2><div class="scroll"><table><tbody>{rows}</tbody></table></div>'
    body += '<a class="cta" href="../index.html">සම්පූර්ණ ප්‍රස්ථාර හා ගණක බලන්න</a>'
    url = f"{SITE}/{OUT_DIR}/"
    title = "අද එළවළු මිල | Vegetable Prices Today Sri Lanka – TopGoviya.lk"
    desc = (f"Today's retail prices for {len(items)} vegetables, fruits, rice and fish in Sri Lanka "
            f"({fdate(dates[latest_idx],'en')}). Daily from CBSL reports. අද එළවළු හා ආහාර මිල ගණන්.")
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
