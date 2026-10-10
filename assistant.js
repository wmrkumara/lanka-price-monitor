/* assistant.js — TopGoviya.lk Sinhala price assistant
   Upgrades the homepage search (voice + typing) so farmers can ask naturally:
     "අද තක්කාලි මිල කීයද?"  "thakkali mila"  "எலுமிச்சை விலை"  "gammiris mila"  "පෑලියගොඩ මිල"
   - an item  -> opens its price card and reads the price aloud (existing feature)
   - a spice  -> opens /spice/<name>.html
   - a market -> opens /market/<name>.html
   Works only with the page's own data; nothing is sent anywhere. Loaded by index.html. */
(function () {
  const AS = {"items": {"Beans": ["bonchi"], "Cabbage": ["gowa"], "Tomato": ["takkali", "thakkali", "tomato"], "Brinjal": ["wambatu"], "Pumpkin": ["wattakka"], "Snake gourd": ["pathola"], "Green Chilli": ["amu miris", "miris", "මිරිස්"], "Lime": ["dehi", "දෙහි"], "Red Onion (Local)": ["rathu lunu", "රතු ලූණු"], "Red Onion (lmp)": ["rathu lunu"], "Big Onion (Local)": ["loku lunu", "lunu", "ලූණු", "ලොකු ලූණු"], "Big Onion (Imp)": ["loku lunu"], "Potato (Local)": ["ala", "arthapal", "අර්තාපල්", "අල"], "Potato (Imp)": ["ala"], "Dried Chilli (Imp)": ["viyali miris"], "Coconut (Avg.)": ["pol", "pol gedi", "පොල්"], "Coconut oil": ["pol thel"], "Red Dhal": ["parippu"], "Sugar (White)": ["seeni"], "Egg (White)": ["biththara", "egg", "බිත්තර"], "Katta": ["katta"], "Sprat (Imp)": ["haal masso"], "Banana (Sour)": ["ambul kesel", "embul kesel", "kesel", "කෙසෙල්"], "Papaw": ["papol"], "Pineapple": ["annasi"], "Orange (Imp)": ["dodam"], "Samba": ["samba", "samba haal", "සම්බා"], "Nadu": ["nadu", "nadu haal", "නාඩු"], "Kekulu (White)": ["kekulu haal"], "Kekulu (Red)": ["rathu kekulu haal"], "Nadu (Imp)": ["nadu haal"], "Kekulu (White) (Imp)": ["kekulu haal"], "Kelawalla": ["kelawalla"], "Thalapath": ["thalapath"], "Balaya": ["balaya"], "Paraw": ["parawa"], "Salaya": ["salaya"], "Hurulla": ["hurulla"], "Linna": ["linna"], "Katta (Imp)": ["katta"]}, "spices": [{"slug": "pepper", "si": "ගම්මිරිස්", "names": ["ගම්මිරිස්", "black pepper", "மிளகு", "gammiris", "කළු ගම්මිරිස්", "black pepper", "gammiris"]}, {"slug": "cinnamon", "si": "කුරුඳු", "names": ["කුරුඳු", "cinnamon", "கறுவா", "kurundu"]}, {"slug": "clove", "si": "කරාබු නැටි", "names": ["කරාබු නැටි", "clove", "கராம்பு", "karabu", "කරාබු", "karabu nati"]}, {"slug": "cardamom", "si": "එනසාල්", "names": ["එනසාල්", "cardamom", "ஏலக்காய்", "enasal"]}, {"slug": "nutmeg", "si": "සාදික්කා", "names": ["සාදික්කා", "nutmeg & mace", "சாதிக்காய்", "sadikka", "වසාවාසි", "mace", "wasawasi"]}, {"slug": "coffee", "si": "කෝපි", "names": ["කෝපි", "coffee", "கோப்பி", "kopi"]}, {"slug": "cocoa", "si": "කොකෝවා", "names": ["කොකෝවා", "cocoa", "கொக்கோ", "kokowa"]}, {"slug": "arecanut", "si": "පුවක්", "names": ["පුවක්", "areca nut", "பாக்கு", "puwak"]}, {"slug": "ginger", "si": "ඉඟුරු", "names": ["ඉඟුරු", "ginger", "இஞ்சி", "inguru"]}, {"slug": "turmeric", "si": "කහ", "names": ["කහ", "turmeric", "மஞ்சள்", "kaha"]}, {"slug": "goraka", "si": "ගොරකා", "names": ["ගොරකා", "goraka", "கொறுக்காய்", "goraka"]}], "markets": [{"slug": "peliyagoda", "si": "පෑලියගොඩ", "names": ["පෑලියගොඩ", "பேலியகோட", "peliyagoda", "peliyagoda", "පැලියගොඩ", "peliyagoda"]}, {"slug": "kandy", "si": "මහනුවර", "names": ["මහනුවර", "கண்டி", "kandy", "kandy", "නුවර", "kandy"]}, {"slug": "dambulla", "si": "දඹුල්ල", "names": ["දඹුල්ල", "தம்புள்ள", "dambulla", "dambulla", "දබුල්ල", "dabulla"]}, {"slug": "meegoda", "si": "මීගොඩ", "names": ["මීගොඩ", "மீகொட", "meegoda", "meegoda"]}, {"slug": "norochchole", "si": "නොරොච්චෝලේ", "names": ["නොරොච්චෝලේ", "நொரோச்சோலே", "norochchole", "norochchole"]}, {"slug": "thambuththegama", "si": "තඹුත්තේගම", "names": ["තඹුත්තේගම", "தம்புத்தேகம", "thambuththegama", "thambuththegama"]}, {"slug": "keppetipola", "si": "කෑප්පෙටිපොළ", "names": ["කෑප්පෙටිපොළ", "கெப்பெட்டிபொல", "keppetipola", "keppetipola", "කැප්පෙටිපොළ", "කැප්පෙටිපොල"]}, {"slug": "nuwara-eliya", "si": "නුවරඑළිය", "names": ["නුවරඑළිය", "நுவரெலியா", "nuwaraeliya", "nuwara eliya", "නුවරඑලිය", "nuwaraeliya"]}, {"slug": "bandarawela", "si": "බණ්ඩාරවෙල", "names": ["බණ්ඩාරවෙල", "பண்டாரவெல", "bandarawela", "bandarawela"]}, {"slug": "veyangoda", "si": "වේයන්ගොඩ", "names": ["වේයන්ගොඩ", "வேயன்கொட", "veyangoda", "veyangoda"]}]};

  /* make Sinhala / Singlish / Tamil text comparable: lower case, no joiners,
     the common spellings people type (ළ -> ල, ණ -> න), no punctuation */
  function norm(t) {
    return (t || "").toLowerCase()
      .replace(/[\u200c\u200d]/g, "")
      .replace(/ළ/g, "ල").replace(/ණ/g, "න")
      .replace(/[?？!.,:;"'()\[\]{}|\/\\-]/g, " ")
      .replace(/\s+/g, " ").trim();
  }
  /* words that are part of the question, not the item */
  const FILLER = ["අද", "මිල", "ගාන", "ගණන", "කීයද", "කීයද්", "කොච්චරද", "මොකක්ද", "දැන්", "today", "price", "prices", "rate",
    "mila", "ada", "kiyada", "keeyada", "gana", "what", "is", "the", "of", "in", "sri", "lanka", "now",
    "விலை", "இன்று", "என்ன", "market", "වෙලඳපොල", "සිල්ලර", "තොග"];

  function clean(q) {
    return " " + norm(q).split(" ").filter(w => w && !FILLER.includes(w)).join(" ") + " ";
  }

  /* best match: the longest known name found in the question */
  function best(qc, list) {
    let top = null, len = 0;
    for (const it of list) {
      for (const raw of it.names) {
        const n = norm(raw);
        if (!n) continue;
        const hit = n.length <= 3 ? qc.includes(" " + n + " ") : qc.includes(n);
        if (hit && n.length > len) { top = it; len = n.length; }
      }
    }
    return top ? { it: top, len: len } : null;
  }

  function itemList() {
    if (typeof DATA === "undefined" || !DATA.length) return [];
    return DATA.map(d => {
      const names = [d.name];
      try { if (typeof NAMES !== "undefined" && NAMES[d.name]) Object.values(NAMES[d.name]).forEach(n => names.push(n)); } catch (e) {}
      (AS.items[d.name] || []).forEach(n => names.push(n));
      return { d: d, names: names };
    });
  }

  function go(url) { (window.tgGoOverride || function (u) { location.href = u; })(url); }
  function toast(msg, ms) { try { showToast(msg, ms || 3000); } catch (e) {} }
  function L(si, ta, en) { const l = (typeof lang !== "undefined") ? lang : "si"; return l === "ta" ? ta : l === "en" ? en : si; }

  function track(speak, result, name) {
    try { if (window.tgEvent) window.tgEvent("ask_question", { method: speak ? "voice" : "text", result: result, item: name || "" }); } catch (e) {}
  }

  /* returns true when something was found and opened */
  function ask(query, speak) {
    const r = ask2(query, speak);
    return r;
  }
  function ask2(query, speak) {
    const qc = clean(query);
    if (!qc.trim()) { const g0 = general(query); track(speak, g0 ? "list" : "none", ""); return g0; }
    const item = best(qc, itemList());
    const spice = best(qc, AS.spices);
    const market = best(qc, AS.markets);
    if (item && (!spice || item.len >= spice.len)) {
      const d = item.it.d;
      const searchEl = document.getElementById("search");
      if (searchEl) { searchEl.value = query; try { state.q = ""; renderGrid(); } catch (e) {} }
      track(speak, "item", d.name);
      setTimeout(() => {
        try { openDetail(d.id); } catch (e) {}
        if (speak) setTimeout(() => { try { speakPrice(d); } catch (e) {} }, 600);
      }, 300);
      return true;
    }
    if (spice) {
      track(speak, "spice", spice.it.slug);
      toast(L("🌶️ " + spice.it.si + " මිල — පිටුව විවෘත වේ…", "🌶️ " + spice.it.si + " …", "🌶️ Opening spice prices…"));
      setTimeout(() => go("spice/" + spice.it.slug + ".html"), 700);
      return true;
    }
    if (market) {
      track(speak, "market", market.it.slug);
      toast(L("🧺 " + market.it.si + " වෙළඳපොළ මිල — පිටුව විවෘත වේ…", "🧺 " + market.it.si + " …", "🧺 Opening market prices…"));
      setTimeout(() => go("market/" + market.it.slug + ".html"), 700);
      return true;
    }
    const g = general(query);
    track(speak, g ? "list" : "none", g ? "" : String(query).slice(0, 60));
    return g;
  }

  /* a general question ("අද එලවලු මිල", "vegetable prices today"): show the full list */
  function general(query) {
    const g = norm(query);
    if (!/එලවලු|elawalu|vegetable|காய்கறி|මිල|price|விலை/.test(g)) return false;
    const grid = document.getElementById("grid");
    if (grid) { try { state.q = ""; renderGrid(); } catch (e) {} grid.scrollIntoView({ behavior: "smooth", block: "start" }); }
    toast(L("📋 අද සියලු මිල — පහතින්", "📋 இன்றைய அனைத்து விலைகள்", "📋 All of today's prices"));
    return true;
  }

  /* 1) voice search: the page calls findAndOpenCommodity(transcript) */
  const oldFind = (typeof findAndOpenCommodity === "function") ? findAndOpenCommodity : null;
  window.findAndOpenCommodity = function (query) {
    if (ask(query, true)) return true;
    return oldFind ? oldFind(query) : false;
  };

  /* 2) typing: show the right card while typing Singlish / common spellings; Enter = open it */
  function hookSearch() {
    const el = document.getElementById("search");
    if (!el || el.dataset.tgAssist) return;
    el.dataset.tgAssist = "1";
    el.addEventListener("input", () => {
      try {
        const q = el.value.toLowerCase();
        if (!q || q.length < 2) return;
        const plain = DATA.filter(d => d.name.toLowerCase().includes(q) || tName(d.name).toLowerCase().includes(q));
        if (plain.length) return;                       /* normal search already finds it */
        const m = best(clean(el.value), itemList());
        if (m) { state.q = m.it.d.name.toLowerCase(); renderGrid(); }
      } catch (e) {}
    });
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { if (ask(el.value, false)) e.preventDefault(); }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", hookSearch); else hookSearch();
  setTimeout(hookSearch, 2500);

  window.tgAsk = ask;   /* for testing */
})();
