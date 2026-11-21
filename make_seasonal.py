"""make_seasonal.py — TopGoviya.lk seasonal price summary (for elawalu-mila-kalaya.html)

Reads the HARTI files the daily robot already keeps:
  harti_market_series.json   daily midpoint price since 2023 for Dambulla and Peliyagoda
  harti_data.json            latest prices in all 10 HARTI markets (and each market's last date)
  harti_market_history.json  daily prices for all 10 markets since July 2026

Writes one small file for the web page:
  seasonal_prices.json       month-by-month and week-by-week averages per year, seasonal index,
                             latest 10-market prices and 10-market daily averages (last 120 days)

Rules (accuracy first):
  - a month average is shown only if the month has at least MIN_DAYS_MONTH trading days
  - a week average is shown only if the week has at least MIN_DAYS_WEEK trading days
  - the seasonal index uses only years with at least 9 valid months, and needs 2+ such years
Run: python make_seasonal.py
"""
import json, datetime, statistics

MIN_DAYS_MONTH = 8
MIN_DAYS_WEEK = 2
HIST_MARKETS = ["Dambulla", "Peliyagoda"]

MKT = {
    "Peliyagoda": {"si": "පෑලියගොඩ", "ta": "பேலியகொட", "en": "Peliyagoda"},
    "Kandy": {"si": "මහනුවර", "ta": "கண்டி", "en": "Kandy"},
    "Dambulla": {"si": "දඹුල්ල", "ta": "தம்புள்ள", "en": "Dambulla"},
    "Meegoda": {"si": "මීගොඩ", "ta": "மீகொட", "en": "Meegoda"},
    "Norochchole": {"si": "නොරොච්චෝලේ", "ta": "நொரோச்சோலே", "en": "Norochchole"},
    "Thambuththegama": {"si": "තඹුත්තේගම", "ta": "தம்புத்தேகம", "en": "Thambuththegama"},
    "Keppetipola": {"si": "කෑප්පෙටිපොළ", "ta": "கெப்பெட்டிபொல", "en": "Keppetipola"},
    "Nuwaraeliya": {"si": "නුවරඑළිය", "ta": "நுவரெலியா", "en": "Nuwara Eliya"},
    "Bandarawela": {"si": "බණ්ඩාරවෙල", "ta": "பண்டாரவெல", "en": "Bandarawela"},
    "Veyangoda": {"si": "වේයන්ගොඩ", "ta": "வேயன்கொட", "en": "Veyangoda"},
}
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
CAT = {"Up Country Vegetables": {"si": "උඩරට එළවළු", "ta": "மலைநாட்டு காய்கறிகள்", "en": "Up country vegetables"},
       "Low Country Vegetables": {"si": "පහතරට එළවළු", "ta": "தாழ்நில காய்கறிகள்", "en": "Low country vegetables"},
       "Potatoes & Onions": {"si": "අර්තාපල් හා ළූණු", "ta": "உருளை & வெங்காயம்", "en": "Potatoes & onions"},
       "Fruits & Banana": {"si": "පළතුරු හා කෙසෙල්", "ta": "பழங்கள் & வாழை", "en": "Fruits & banana"}}


def r1(v):
    return None if v is None else round(v, 1)


def main():
    S = json.load(open("harti_market_series.json", encoding="utf-8"))
    D = json.load(open("harti_data.json", encoding="utf-8"))
    H = json.load(open("harti_market_history.json", encoding="utf-8"))["markets"]
    dates = S["dates"]
    years = sorted({d[:4] for d in dates})
    mdates = D.get("marketDates", {})
    last_day = max(dates)
    cutoff = (datetime.date.fromisoformat(last_day) - datetime.timedelta(days=120)).isoformat()

    items = []
    for c in D["commodities"]:
        name = c["name"]
        ser = S["series"].get(name, {})
        it = {"n": name, "si": H_SI.get(name, name), "ta": H_TA.get(name, name), "cat": c.get("category", ""),
              "unit": c.get("unit", "Rs./kg"), "m": {}, "w": {}, "idx": {}, "idxYears": {}}
        for mk in HIST_MARKETS:
            vals = ser.get(mk) or []
            month = {}; week = {}
            for d, v in zip(dates, vals):
                if v is None:
                    continue
                y, mo = d[:4], int(d[5:7])
                month.setdefault((y, mo), []).append(v)
                iy, iw, _ = datetime.date.fromisoformat(d).isocalendar()
                week.setdefault((str(iy), iw), []).append(v)
            m_out = {y: [r1(statistics.mean(month[(y, mo)])) if len(month.get((y, mo), [])) >= MIN_DAYS_MONTH else None
                         for mo in range(1, 13)] for y in years}
            w_out = {y: [r1(statistics.mean(week[(y, wk)])) if len(week.get((y, wk), [])) >= MIN_DAYS_WEEK else None
                         for wk in range(1, 54)] for y in years}
            if not any(v is not None for row in m_out.values() for v in row):
                continue
            it["m"][mk] = m_out
            it["w"][mk] = w_out
            # seasonal index: month average / that year's average, averaged over full-enough years
            ratios = {mo: [] for mo in range(12)}; used = []
            for y, row in m_out.items():
                ok = [v for v in row if v is not None]
                if len(ok) >= 9:
                    ya = statistics.mean(ok); used.append(y)
                    for mo, v in enumerate(row):
                        if v is not None:
                            ratios[mo].append(v / ya)
            if len(used) >= 2:
                it["idx"][mk] = [round(statistics.mean(ratios[mo]) * 100, 1) if len(ratios[mo]) >= 2 else None for mo in range(12)]
                it["idxYears"][mk] = used
        # latest prices in all markets
        # each market's latest price, taken from that market's own daily history (with its real date)
        today = {}
        for mk in MKT:
            hist = (H.get(mk) or {}).get(name) or {}
            days = [d for d, t in hist.items() if t and t[2] is not None]
            if days:
                d = max(days); t = hist[d]
                today[mk] = [t[0], t[1], t[2], d]
            else:
                v = (c.get("markets") or {}).get(mk)
                if v and v.get("mid") is not None and mdates.get(mk):
                    today[mk] = [v.get("min"), v.get("max"), v.get("mid"), mdates.get(mk)]
        it["today"] = today
        # 10-market daily average, last 120 days (only days with 3+ markets)
        per_day = {}
        for mk in MKT:
            hist = (H.get(mk) or {}).get(name) or {}
            for d, trip in hist.items():
                if d >= cutoff and trip and trip[2] is not None:
                    per_day.setdefault(d, []).append(trip[2])
        it["avg10"] = [[d, round(statistics.mean(v), 1), len(v)] for d, v in sorted(per_day.items()) if len(v) >= 3]
        if it["m"] or today:
            items.append(it)

    out = {"generated": last_day, "source": "HARTI daily wholesale prices (midpoint Rs./kg)",
           "sourceUrl": "https://www.harti.gov.lk/", "years": years, "markets": MKT, "categories": CAT,
           "rules": {"minDaysMonth": MIN_DAYS_MONTH, "minDaysWeek": MIN_DAYS_WEEK},
           "items": items}
    with open("seasonal_prices.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"seasonal_prices.json: {len(items)} items, up to {last_day}")


if __name__ == "__main__":
    main()
