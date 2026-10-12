/* quick-calc.js — TopGoviya.lk break-even calculator: "⚡ Quick calculation" card
   3 boxes (crop, harvest kg, total cost) -> instant break-even price per kg, compared with
   the highest HARTI wholesale price today. Added at the top of breakeven.html by the robot;
   the detailed calculator below is unchanged. Nothing is sent anywhere. */
(function () {
  var CROPS = [{"n": "Beans", "si": "බෝංචි", "ta": "பீன்ஸ்"}, {"n": "Carrot", "si": "කැරට්", "ta": "கேரட்"}, {"n": "Leeks", "si": "ලීක්ස්", "ta": "லீக்ஸ்"}, {"n": "Beetroot", "si": "බීට්රූට්", "ta": "பீட்ரூட்"}, {"n": "Knolkhol", "si": "නෝල්කෝල්", "ta": "நோல்கோல்"}, {"n": "Raddish", "si": "රාබු", "ta": "ராடிஷ்"}, {"n": "Cabbage (Kandy)", "si": "ගෝවා (නුවර)", "ta": "முட்டைக்கோஸ் (கண்டி)"}, {"n": "Tomato", "si": "තක්කාලි", "ta": "தக்காளி"}, {"n": "Ladies Fingers", "si": "බණ්ඩක්කා", "ta": "வெண்டைக்காய்"}, {"n": "Brinjals", "si": "වම්බටු", "ta": "கத்தரிக்காய்"}, {"n": "Capsicum", "si": "මාළු මිරිස්", "ta": "குடை மிளகாய்"}, {"n": "Pumpkin", "si": "වට්ටක්කා", "ta": "பூசணி"}, {"n": "Cucumber", "si": "පිපිඤ්ඤා", "ta": "வெள்ளரிக்காய்"}, {"n": "Bitter Gourd", "si": "කරවිල", "ta": "பாகற்காய்"}, {"n": "Snake Gourd", "si": "පතෝල", "ta": "புடலங்காய்"}, {"n": "Luffa", "si": "වැටකොළු", "ta": "பீர்க்கங்காய்"}, {"n": "Long Beans", "si": "මෑකරල්", "ta": "தட்டைப்பயறு"}, {"n": "Ash Plantains", "si": "අළු කෙසෙල්", "ta": "வாழைக்காய்"}, {"n": "Green Chillies", "si": "අමු මිරිස්", "ta": "பச்சை மிளகாய்"}, {"n": "Lime", "si": "දෙහි", "ta": "எலுமிச்சை"}, {"n": "Sweet Potato", "si": "බතල", "ta": "சர்க்கரைவள்ளி"}, {"n": "Manioc", "si": "මඤ්ඤොක්කා", "ta": "மரவள்ளி"}, {"n": "Potato (N.Eliya)", "si": "අර්තාපල් (නුවරඑළිය)", "ta": "உருளை (நுவரெலியா)"}, {"n": "Banana Ambul", "si": "ඇඹුල් කෙසෙල්", "ta": "ஆம்பல் வாழை"}, {"n": "Banana Kolikuttu", "si": "කොලිකුට්ටු", "ta": "கொலிக்குட்டு"}, {"n": "Banana Seeni", "si": "සීනි කෙසෙල්", "ta": "சர்க்கரை வாழை"}, {"n": "Papaya", "si": "පැපොල්", "ta": "பப்பாளி"}, {"n": "Pineapple (Large)", "si": "අන්නාසි (ලොකු)", "ta": "அன்னாசி (பெரியது)"}, {"n": "Avocado", "si": "අලිගැටපේර", "ta": "அவோகேடோ"}, {"n": "Eggplant", "si": "එළබටු", "ta": "கத்திரிக்காய்"}, {"n": "Cabbage (N.Eliya)", "si": "ගෝවා (නුවරඑළිය)", "ta": "முட்டைக்கோஸ் (நுவரெலியா)"}, {"n": "Drumstick", "si": "මුරුංගා", "ta": "முருங்கை"}, {"n": "Potato (Imported)", "si": "අර්තාපල් (ආනයනික)", "ta": "உருளை (இறக்குமதி)"}, {"n": "Big Onion (Imported)", "si": "ලොකු ළූණු (ආනයනික)", "ta": "பெரிய வெங்காயம் (இறக்குமதி)"}, {"n": "Anamalu", "si": "ආනමාළු කෙසෙල්", "ta": "ஆனைமாலு வாழை"}, {"n": "Passion Fruit", "si": "වැල් දොඩම්", "ta": "பேஷன் பழம்"}, {"n": "Pineapple (Medium)", "si": "අන්නාසි (මධ්‍යම)", "ta": "அன்னாசி (நடுத்தரம்)"}, {"n": "Pineapple (Small)", "si": "අන්නාසි (කුඩා)", "ta": "அன்னாசி (சிறியது)"}, {"n": "Mango (Betti)", "si": "අඹ (බෙට්ටි)", "ta": "மாம்பழம் (பெட்டி)"}, {"n": "Mango (Karathakolomban)", "si": "අඹ (කර්තකොළඹ)", "ta": "மாம்பழம் (கறுத்தக்கொழும்பான்)"}, {"n": "Woodapple", "si": "දිවුල්", "ta": "விளாம்பழம்"}, {"n": "Orange", "si": "දොඩම්", "ta": "தோடம்பழம்"}, {"n": "Potato (Welimada)", "si": "අර්තාපල් (වැලිමඩ)", "ta": "உருளை (வெலிமட)"}, {"n": "Beetroot (N.Eliya)", "si": "බීට්රූට් (නුවරඑළිය)", "ta": "பீட்ரூட் (நுவரெலியா)"}];
  var MKT = {"Peliyagoda": {"si": "පෑලියගොඩ", "ta": "பேலியகோட"}, "Kandy": {"si": "මහනුවර", "ta": "கண்டி"}, "Dambulla": {"si": "දඹුල්ල", "ta": "தம்புள்ள"}, "Meegoda": {"si": "මීගොඩ", "ta": "மீகொட"}, "Norochchole": {"si": "නොරොච්චෝලේ", "ta": "நொரோச்சோலே"}, "Thambuththegama": {"si": "තඹුත්තේගම", "ta": "தம்புத்தேகம"}, "Keppetipola": {"si": "කෑප්පෙටිපොළ", "ta": "கெப்பெட்டிபொல"}, "Nuwaraeliya": {"si": "නුවරඑළිය", "ta": "நுவரெலியா"}, "Bandarawela": {"si": "බණ්ඩාරවෙල", "ta": "பண்டாரவெல"}, "Veyangoda": {"si": "වේයන්ගොඩ", "ta": "வேயன்கொட"}};
  var WASTE = 10;   /* % of harvest assumed lost (same default as the detailed form) */
  var T = {
    si: { title: "⚡ ඉක්මන් ගණනය", sub: "අගයන් 3ක් පමණයි — ප්‍රතිඵලය එසැණින්", ex: "උදාහරණයක් — ඔබේ අගයන් දමන්න",
          crop: "භෝගය", harvest: "අපේක්ෂිත අස්වැන්න (කි.ග්‍රෑ.)", cost: "මුළු වගා වියදම (රු.)",
          be: "ලාභ අලාභ සීමාව", per: "කි.ග්‍රෑ. එකකට", best: "අද වැඩිම තොග මිල", profit: "ඇස්තමේන්තුගත ලාභය",
          loss: "ඇස්තමේන්තුගත අලාභය", nodata: "මෙම භෝගයට අද HARTI මිලක් නැත.", note: "අස්වැන්නෙන් " + WASTE + "% හානිය සලකා ඇත. ප්‍රවාහන වියදම, ගුණාත්මකභාවය හා ඉල්ලුම අනුව සැබෑ ලාභය වෙනස් වේ.",
          more: "සවිස්තර ගණනය (වියදම් වෙන වෙනම) ↓", above: "ඔබේ ලාභ අලාභ සීමාවට වඩා", rs: "රු." },
    ta: { title: "⚡ விரைவு கணக்கீடு", sub: "3 மதிப்புகள் மட்டும் — உடனடி முடிவு", ex: "உதாரணம் — உங்கள் மதிப்புகளை இடுங்கள்",
          crop: "பயிர்", harvest: "எதிர்பார்க்கும் அறுவடை (கி.கி.)", cost: "மொத்த பயிர்ச்செலவு (ரூ.)",
          be: "இலாப நட்ட சமநிலை விலை", per: "ஒரு கி.கி.க்கு", best: "இன்றைய அதிக மொத்த விலை", profit: "மதிப்பிடப்பட்ட இலாபம்",
          loss: "மதிப்பிடப்பட்ட நட்டம்", nodata: "இந்தப் பயிருக்கு இன்று HARTI விலை இல்லை.", note: "அறுவடையில் " + WASTE + "% இழப்பு கணக்கிடப்பட்டுள்ளது. போக்குவரத்து, தரம், தேவை ஆகியவற்றால் உண்மையான இலாபம் மாறும்.",
          more: "விரிவான கணக்கீடு (செலவுகள் தனித்தனியாக) ↓", above: "உங்கள் சமநிலை விலையை விட", rs: "ரூ." },
    en: { title: "⚡ Quick calculation", sub: "Just 3 numbers — instant answer", ex: "Example — enter your own numbers",
          crop: "Crop", harvest: "Expected harvest (kg)", cost: "Total growing cost (Rs.)",
          be: "Break-even price", per: "per kg", best: "Highest wholesale price today", profit: "Estimated profit",
          loss: "Estimated loss", nodata: "No HARTI price for this crop today.", note: WASTE + "% harvest loss is included. Transport, quality and demand change your real profit.",
          more: "Detailed calculation (costs one by one) ↓", above: "vs your break-even", rs: "Rs." }
  };
  function L() { var l = (document.documentElement.getAttribute("lang") || "si").slice(0, 2); return T[l] ? l : "si"; }
  function money(v) { return Math.round(v).toLocaleString("en-US"); }
  var DATA = null;

  function marketsFor(name) {
    var src = (typeof MARKET_DATA !== "undefined" && MARKET_DATA) ? MARKET_DATA : DATA;
    if (!src) return null;
    var c = (src.commodities || []).find(function (x) { return x.name === name; });
    if (!c) return null;
    var out = [];
    Object.keys(c.markets || {}).forEach(function (m) { var v = c.markets[m]; if (v && v.mid) out.push([m, v.mid]); });
    out.sort(function (a, b) { return b[1] - a[1]; });
    return { list: out, date: (src.marketDates || {})[out.length ? out[0][0] : ""] || (src.dates || []).slice(-1)[0] };
  }

  function build() {
    var row = document.querySelector(".lang-row");
    if (!row || document.getElementById("qc-card")) return;
    var card = document.createElement("div");
    card.id = "qc-card";
    card.innerHTML =
      '<style>#qc-card{background:var(--card,#fffdf7);border:2px solid #0e4f4a;border-radius:16px;padding:16px 16px 14px;margin:0 0 22px}' +
      '#qc-card h2{margin:0;font-size:20px;color:#0e4f4a}#qc-card .qs{font-size:13px;color:#7a7264;margin:2px 0 10px}' +
      '#qc-card .qex{display:inline-block;font-size:12px;background:#f3e8cc;color:#7a5a12;border-radius:999px;padding:2px 10px;margin-bottom:10px}' +
      '#qc-card label{display:block;font-weight:700;font-size:14px;margin:8px 0 4px}' +
      '#qc-card select,#qc-card input{width:100%;font:inherit;font-size:16px;padding:10px 12px;border:1px solid #cdbf9f;border-radius:10px;background:#fff;color:#191d1a;box-sizing:border-box}' +
      '#qc-card .qg{display:grid;grid-template-columns:1fr 1fr;gap:10px;align-items:end}' +
      '#qc-res{margin-top:12px;border-radius:12px;background:#f4efe4;padding:12px 14px}' +
      '#qc-res .big{font-size:26px;font-weight:800;color:#0e4f4a;font-family:"JetBrains Mono",monospace}' +
      '#qc-res .lbl{font-size:13px;color:#4a514a}#qc-res .row2{margin-top:8px;padding-top:8px;border-top:1px dashed #cdbf9f}' +
      '#qc-res .pos{color:#2c7a52;font-weight:800}#qc-res .neg{color:#b23a2e;font-weight:800}' +
      '#qc-card .qn{font-size:12px;color:#7a7264;margin-top:8px;line-height:1.5}' +
      '#qc-more{display:inline-block;margin-top:10px;font-weight:700;color:#0e4f4a;cursor:pointer;background:none;border:0;font:inherit;font-size:14px;padding:0;text-decoration:underline}</style>' +
      '<h2 id="qc-t"></h2><div class="qs" id="qc-s"></div><div class="qex" id="qc-ex"></div>' +
      '<label for="qc-crop" id="qc-lc"></label><select id="qc-crop"></select>' +
      '<div class="qg"><div><label for="qc-h" id="qc-lh"></label><input id="qc-h" type="number" inputmode="decimal" min="1" value="1000"></div>' +
      '<div><label for="qc-c" id="qc-lco"></label><input id="qc-c" type="number" inputmode="decimal" min="1" value="250000"></div></div>' +
      '<div id="qc-res"></div><div class="qn" id="qc-n"></div><button type="button" id="qc-more"></button>';
    row.insertAdjacentElement("afterend", card);
    ["qc-h", "qc-c", "qc-crop"].forEach(function (id) { document.getElementById(id).addEventListener("input", calc); });
    document.getElementById("qc-crop").addEventListener("change", calc);
    document.getElementById("qc-more").addEventListener("click", function () {
      /* copy the quick numbers into the detailed form and scroll to it */
      var c = CROPS.find(function (x) { return x.n === document.getElementById("qc-crop").value; });
      var cn = document.getElementById("cropName"), hv = document.getElementById("harvest");
      if (cn && c) cn.value = c.n;
      if (hv) hv.value = document.getElementById("qc-h").value;
      var s1 = document.getElementById("sec1-label");
      if (s1) s1.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    texts();
  }

  function texts() {
    var t = T[L()], sel = document.getElementById("qc-crop"); if (!sel) return;
    document.getElementById("qc-t").textContent = t.title; document.getElementById("qc-s").textContent = t.sub;
    document.getElementById("qc-ex").textContent = t.ex; document.getElementById("qc-lc").textContent = t.crop;
    document.getElementById("qc-lh").textContent = t.harvest; document.getElementById("qc-lco").textContent = t.cost;
    document.getElementById("qc-n").textContent = t.note; document.getElementById("qc-more").textContent = t.more;
    var cur = sel.value || "Beans", l = L();
    sel.innerHTML = CROPS.map(function (c) { return '<option value="' + c.n + '">' + (l === "en" ? c.n : (c[l] || c.n)) + (l === "en" ? "" : " / " + c.n) + '</option>'; }).join("");
    sel.value = cur;
    calc();
  }

  function calc() {
    var t = T[L()], l = L(), res = document.getElementById("qc-res"); if (!res) return;
    var h = parseFloat(document.getElementById("qc-h").value), c = parseFloat(document.getElementById("qc-c").value);
    if (!(h > 0) || !(c > 0)) { res.innerHTML = ""; return; }
    var net = h * (1 - WASTE / 100), be = c / net;
    var html = '<div class="lbl">' + t.be + ' (' + t.per + ')</div><div class="big">' + t.rs + ' ' + money(be) + '</div>';
    var m = marketsFor(document.getElementById("qc-crop").value);
    if (m && m.list.length) {
      var top = m.list[0], mk = (MKT[top[0]] || {})[l] || top[0], diff = top[1] - be, gain = diff * net;
      html += '<div class="row2"><div class="lbl">' + t.best + ' · HARTI ' + (m.date || "") + '</div>' +
              '<div><b>' + (l === "en" ? top[0] : mk) + '</b> — ' + t.rs + ' ' + money(top[1]) + ' <span class="lbl">(' +
              (diff >= 0 ? "+" : "−") + t.rs + ' ' + money(Math.abs(diff)) + ' ' + t.above + ')</span></div>' +
              '<div style="margin-top:6px" class="' + (gain >= 0 ? "pos" : "neg") + '">' + (gain >= 0 ? t.profit : t.loss) + ': ' +
              t.rs + ' ' + money(Math.abs(gain)) + '</div></div>';
    } else {
      html += '<div class="row2 lbl">' + t.nodata + '</div>';
    }
    res.innerHTML = html;
    try { if (window.tgEvent && !calc.sent) { calc.sent = 1; } } catch (e) {}
  }

  function start() {
    build();
    new MutationObserver(texts).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
    if (typeof MARKET_DATA === "undefined" || !MARKET_DATA) {
      fetch("harti_data.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { DATA = d; calc(); }).catch(function () {});
    }
    setTimeout(calc, 1500);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
