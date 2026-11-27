/* ===== TopGoviya.lk — shared top menu =====
   One file builds the top bar + the "සියලු පිටු" app-style page grid on every page.
   To add / remove / rename a page: edit ONLY this file (TABS and GROUPS below).
   Version 1 | 27 Nov 2026 | Built in Gampola */
(function () {
  'use strict';
  var host = document.getElementById('tgNav');
  if (!host || host.getAttribute('data-ready')) return;
  host.setAttribute('data-ready', '1');

  /* ---------- 1. THE PAGES (edit here) ---------- */
  /* h = link, i = icon, si / ta / en = names, n = 1 shows the red "New" tag in the grid */

  /* Top bar: keep to 5 */
  var TABS = [
    { h: '/index.html',          i: '🥬', si: 'දඹුල්ල',      ta: 'தம்புள்ள',            en: 'Dambulla' },
    { h: '/market/keppetipola.html', i: '🥕', si: 'කැප්පෙටිපොළ', ta: 'கெப்பெட்டிபொல',    en: 'Keppetipola' },
    { h: '/mage-wagawa.html',    i: '📱', si: 'මගේ වගාව',    ta: 'என் பயிர்',            en: 'My Farm', hot: 1 },
    { h: '/spices.html',         i: '🌶️', si: 'කුළුබඩු',     ta: 'வாசனைப் பொருள்',      en: 'Spices' },
    { h: '/retail.html',         i: '📊', si: 'සිල්ලර මිල',  ta: 'சில்லறை விலை',        en: 'Retail prices' }
  ];

  /* The grid that opens with the ☰ button: every page, in groups */
  var GROUPS = [
    { si: 'වෙළඳපොළ මිල', ta: 'சந்தை விலைகள்', en: 'Market prices', items: [
      { h: '/index.html',               i: '🥬', si: 'දඹුල්ල',        ta: 'தம்புள்ள',                en: 'Dambulla' },
      { h: '/market/keppetipola.html',  i: '🥕', si: 'කැප්පෙටිපොළ',   ta: 'கெப்பெட்டிபொல',          en: 'Keppetipola' },
      { h: '/retail.html',              i: '📊', si: 'සිල්ලර මිල',    ta: 'சில்லறை விலை',            en: 'Retail prices' },
      { h: '/wholesale.html',           i: '📦', si: 'තොග මිල',       ta: 'மொத்த விலை',              en: 'Wholesale' },
      { h: '/spices.html',              i: '🌶️', si: 'කුළුබඩු මිල',   ta: 'வாசனைப் பொருள் விலை',    en: 'Spice prices' },
      { h: '/tea.html',                 i: '🍃', si: 'තේ / Tea',      ta: 'தேயிலை / Tea',            en: 'Tea prices' },
      { h: '/wee-mila.html',            i: '🌾', si: 'වී මිල',        ta: 'நெல் விலை',               en: 'Paddy price', n: 1 },
      { h: '/elawalu-mila-kalaya.html', i: '📅', si: 'මිල වැඩි මාස',  ta: 'விலை உயரும் மாதங்கள்',   en: 'High-price months', n: 1 }
    ]},
    { si: 'ගොවි මෙවලම්', ta: 'விவசாயி கருவிகள்', en: 'Farmer tools', items: [
      { h: '/mage-wagawa.html',    i: '📱', si: 'මගේ වගාව App', ta: 'என் பயிர் App',     en: 'My Farm App', n: 1 },
      { h: '/breakeven.html',      i: '🧮', si: 'ලාභ අලාභ',     ta: 'இலாப நட்டம்',      en: 'Break-even' },
      { h: '/loan-calculator.html',i: '🏦', si: 'ණය ගණකය',      ta: 'கடன் கணிப்பான்',   en: 'Loan calculator' },
      { h: '/weather.html',        i: '🌤️', si: 'කාලගුණය',      ta: 'காலநிலை',          en: 'Weather' },
      { h: '/krushi-pola.html',    i: '🧺', si: 'කෘෂි පොළ',     ta: 'க்ருஷி பொல',       en: 'Krushi Pola' }
    ]},
    { si: 'තොරතුරු', ta: 'தகவல்', en: 'Information', items: [
      { h: '/reports.html',           i: '📄', si: 'මිල වාර්තා',          ta: 'விலை அறிக்கைகள்',      en: 'Price reports' },
      { h: '/blog.html',              i: '📝', si: 'ලිපි',                ta: 'கட்டுரைகள்',           en: 'Blog', n: 1 },
      { h: '/spice-price-guide.html', i: '📖', si: 'කුළුබඩු මාර්ගෝපදේශය', ta: 'வாசனைப் பொருள் வழிகாட்டி', en: 'Spice guide' },
      { h: '/insights.html',          i: '💡', si: 'විශ්ලේෂණ',            ta: 'பகுப்பாய்வு',          en: 'Insights' },
      { h: '/bulletin.html',          i: '📈', si: 'කෘෂි දත්ත බුලටිනය',   ta: 'விவசாய தரவு அறிக்கை',  en: 'Agri bulletin' },
      { h: '/data-sources.html',      i: '✅', si: 'දත්ත මූලාශ්‍ර',       ta: 'தரவு மூலங்கள்',        en: 'Data sources' },
      { h: '/about.html',             i: 'ℹ️', si: 'අප ගැන',              ta: 'எங்களைப் பற்றி',       en: 'About us' },
      { h: '/contact.html',           i: '<svg width="27" height="27" viewBox="0 0 24 24" fill="#25D366" aria-hidden="true" style="display:block;margin:0 auto"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>', si: 'අමතන්න',              ta: 'தொடர்பு',              en: 'Contact' }
    ]}
  ];

  var TXT = {
    all:   { si: 'සියලු පිටු', ta: 'அனைத்தும்', en: 'All pages' },
    title: { si: 'සියලු පිටු', ta: 'அனைத்து பக்கங்கள்', en: 'All pages' },
    isNew: { si: 'අලුත්', ta: 'புதிது', en: 'New' },
    wa:    { si: 'WhatsApp හරහා අපට කතා කරන්න', ta: 'WhatsApp மூலம் எங்களைத் தொடர்பு கொள்ளுங்கள்', en: 'Chat with us on WhatsApp' },
    waS:   { si: 'මිලක් වැරදිද? ගැටලුවක්ද? පණිවිඩයක් එවන්න', ta: 'விலை தவறா? பிரச்சனையா? செய்தி அனுப்புங்கள்', en: 'Wrong price? Any problem? Send us a message' }
  };

  /* ---------- 2. HELPERS ---------- */
  function sp(o) {
    return '<span class="ls">' + o.si + '</span><span class="lt">' + o.ta + '</span><span class="le">' + o.en + '</span>';
  }
  function norm(p) {
    p = String(p || '/').split('?')[0].split('#')[0];
    p = p.replace(/index\.html$/, '').replace(/\.html$/, '').replace(/\/+$/, '');
    return p === '' ? '/' : p;
  }
  var here = norm(location.pathname);
  var onEn = here.indexOf('/en/') === 0;

  /* ---------- 3. CSS ---------- */
  var css =
    '.tgn{background:#0a3a36;border-bottom:2px solid #a9802a;position:relative;z-index:60;font-family:"Hanken Grotesk","Noto Sans Sinhala","Noto Sans Tamil",sans-serif}' +
    '.tgn *,.tgn-ov *{box-sizing:border-box}' +
    '.tgn-in{max-width:1280px;margin:0 auto;padding:8px 16px;display:flex;align-items:center;gap:8px}' +
    '.tgn-brand{font-family:"Newsreader",serif;font-size:17px;font-weight:500;color:#fff;text-decoration:none;white-space:nowrap;display:inline-flex;align-items:center;gap:8px;padding-right:14px;margin-right:2px;border-right:1px solid rgba(255,255,255,.18);flex:0 0 auto}' +
    '.tgn-brand em{font-style:italic;color:#ffd98a}' +
    '.tgn-brand .tgn-lm{background:#f4efe4;border-radius:50%;width:30px;height:30px;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}' +
    '.tgn-brand .tgn-lm img{width:21px;height:21px;object-fit:contain}' +
    '.tgn-tabs{display:flex;gap:6px;flex:1 1 auto;min-width:0;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}' +
    '.tgn-tabs::-webkit-scrollbar{display:none}' +
    '.tgn-tab{flex:0 0 auto;display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:9px;background:rgba(255,255,255,.1);color:rgba(255,255,255,.88);font-size:13.5px;font-weight:700;text-decoration:none;white-space:nowrap;line-height:1.2;transition:background .15s}' +
    '.tgn-tab:hover{background:rgba(255,255,255,.2);color:#fff}' +
    '.tgn-tab.hot{box-shadow:inset 0 0 0 1px rgba(255,217,138,.6);color:#ffe9b8}' +
    '.tgn-tab.on{background:#a9802a;color:#fff;box-shadow:none}' +
    '.tgn-right{display:flex;gap:6px;margin-left:auto;flex:0 0 auto}' +
    '.tgn-btn{display:inline-flex;align-items:center;gap:7px;padding:8px 13px;border-radius:9px;border:0;font:inherit;font-size:13.5px;font-weight:800;text-decoration:none;cursor:pointer;white-space:nowrap;line-height:1.2}' +
    '.tgn-all{background:#ffd98a;color:#3b2a05}' +
    '.tgn-all:hover{background:#ffe3a8}' +
    '.tgn-all .tgn-bars{font-size:17px;line-height:1}' +
    '.tgn-en{background:#fff;color:#0a3a36;letter-spacing:.04em}' +
    '.tgn-en:hover{background:#f4efe4}' +
    '.tgn a:focus-visible,.tgn button:focus-visible,.tgn-ov a:focus-visible,.tgn-ov button:focus-visible{outline:3px solid #ffd98a;outline-offset:2px}' +
    /* language switching: same method the pages already use */
    '.tgn-lg .lt,.tgn-lg .le{display:none}' +
    'html[lang="ta"] .tgn-lg .ls,html[lang="en"] .tgn-lg .ls{display:none}' +
    'html[lang="ta"] .tgn-lg .lt,html[lang="en"] .tgn-lg .le{display:inline}' +
    /* the app grid */
    '.tgn-ov{position:fixed;left:0;top:0;right:0;bottom:0;z-index:1000;background:rgba(15,28,26,.55);-webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px);display:none;overflow-y:auto;-webkit-overflow-scrolling:touch;font-family:"Hanken Grotesk","Noto Sans Sinhala","Noto Sans Tamil",sans-serif}' +
    '.tgn-ov.open{display:block}' +
    '.tgn-pn{background:#f4efe4;width:100%;max-width:780px;margin:0 auto;min-height:100%;padding:0 14px 28px}' +
    '.tgn-ph{position:sticky;top:0;z-index:2;background:#f4efe4;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:14px 0 10px;border-bottom:1px solid #e3d9c4;margin-bottom:6px}' +
    '.tgn-pt{font-family:"Newsreader","Noto Sans Sinhala",serif;font-size:22px;font-weight:600;color:#0a3a36;margin:0}' +
    '.tgn-x{border:0;background:#e9e0cb;color:#3a403a;width:40px;height:40px;border-radius:11px;font-size:18px;cursor:pointer;flex:0 0 auto}' +
    '.tgn-x:hover{background:#f2d9d4;color:#b23a2e}' +
    '.tgn-wa{display:flex;align-items:center;gap:12px;margin:10px 0 2px;padding:12px 14px;background:#15803d;color:#fff;border-radius:14px;text-decoration:none;box-shadow:0 6px 16px -8px rgba(21,128,61,.7);-webkit-tap-highlight-color:transparent}' +
    '.tgn-wa:active{transform:scale(.985)}' +
    '.tgn-wa .tgn-wi{flex:0 0 auto;width:42px;height:42px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center}' +
    '.tgn-wa .tgn-wt{display:flex;flex-direction:column;gap:2px;min-width:0}' +
    '.tgn-wa .tgn-wt b{font-size:15.5px;font-weight:800;line-height:1.3}' +
    '.tgn-wa .tgn-wt small{font-size:12.5px;line-height:1.35;opacity:.95}' +
    '.tgn-gh{font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:800;color:#7a7264;margin:18px 2px 8px}' +
    '.tgn-gr{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}' +
    '.tgn-tile{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;text-align:center;padding:14px 6px 12px;min-height:92px;background:#fffdf7;border:1px solid #e3d9c4;border-radius:14px;color:#191d1a;text-decoration:none;font-size:13px;font-weight:700;line-height:1.3;transition:transform .15s,border-color .15s,box-shadow .15s}' +
    '.tgn-tile .tgn-ic{font-size:27px;line-height:1}' +
    '.tgn-tile:hover{transform:translateY(-2px);border-color:#0e4f4a;box-shadow:0 10px 22px -14px rgba(20,40,38,.5)}' +
    '.tgn-tile.on{border-color:#a9802a;box-shadow:inset 0 0 0 1px #a9802a}' +
    '.tgn-new{position:absolute;top:6px;right:6px;padding:1px 7px;border-radius:999px;background:#d9452b;color:#fff;font-size:10px;font-weight:800;line-height:1.5}' +
    '@media(min-width:640px){.tgn-gr{grid-template-columns:repeat(4,1fr)}}' +
    '@media(min-width:700px){.tgn-ov{padding:40px 16px}.tgn-pn{min-height:0;border-radius:18px;padding:0 24px 30px;box-shadow:0 40px 90px -30px rgba(10,30,28,.7)}.tgn-ph{border-radius:18px 18px 0 0}}' +
    /* phones: logo + buttons on row 1, the 5 pages on row 2 */
    '@media(max-width:700px){.tgn-in{flex-wrap:wrap;padding:8px 8px;gap:8px}.tgn-brand{order:1;border-right:0;padding-right:0;margin-right:0;margin-left:4px}.tgn-right{order:2;margin-right:4px}.tgn-tabs{order:3;flex:1 1 100%;gap:3px}.tgn-tab{flex:1 1 auto;justify-content:center;padding:9px 6px;font-size:12px}}' +
    '@media(max-width:820px){.tgn-tab .tgn-ic{display:none}}' +
    '@media(max-width:380px){.tgn-brand{font-size:15px}.tgn-btn{padding:8px 10px;font-size:13px}}' +
    '@media(prefers-reduced-motion:reduce){.tgn-tile,.tgn-tab{transition:none}}';

  var st = document.createElement('style');
  st.id = 'tgn-style';
  st.appendChild(document.createTextNode(css));
  document.head.appendChild(st);

  /* ---------- 4. TOP BAR ---------- */
  var tabsHtml = '';
  for (var a = 0; a < TABS.length; a++) {
    var t = TABS[a], cur = norm(t.h) === here;
    tabsHtml += '<a class="tgn-tab' + (t.hot ? ' hot' : '') + (cur ? ' on' : '') + '" href="' + t.h + '"' + (cur ? ' aria-current="page"' : '') + '>' +
      '<span class="tgn-ic" aria-hidden="true">' + t.i + '</span><span>' + sp(t) + '</span></a>';
  }
  var isKep = here.indexOf('keppetipola') !== -1;
  var enHref = onEn ? (isKep ? '/market/keppetipola.html' : '/index.html') : (isKep ? '/en/keppetipola-market-price-today.html' : '/en/dambulla-market-price-today.html');
  var enTxt = onEn ? 'සිං' : 'EN';
  var enLang = onEn ? 'si' : 'en';

  host.className = 'tgn tgn-lg';
  host.setAttribute('aria-label', 'Main menu');
  host.innerHTML =
    '<div class="tgn-in">' +
      '<a class="tgn-brand" href="/index.html"><span class="tgn-lm"><img src="/logo-mark.png" alt="TopGoviya" width="21" height="21"></span><span>Top<em>Goviya</em>.lk</span></a>' +
      '<div class="tgn-tabs">' + tabsHtml + '</div>' +
      '<div class="tgn-right">' +
        '<button type="button" class="tgn-btn tgn-all" id="tgnOpen" aria-haspopup="dialog" aria-expanded="false" aria-controls="tgnOv"><span class="tgn-bars" aria-hidden="true">☰</span><span>' + sp(TXT.all) + '</span></button>' +
        '<a class="tgn-btn tgn-en" href="' + enHref + '" lang="' + enLang + '" hreflang="' + enLang + '">' + enTxt + '</a>' +
      '</div>' +
    '</div>';

  /* ---------- 5. THE APP GRID ---------- */
  var gh = '';
  for (var g = 0; g < GROUPS.length; g++) {
    var G = GROUPS[g];
    gh += '<h3 class="tgn-gh">' + sp(G) + '</h3><div class="tgn-gr">';
    for (var k = 0; k < G.items.length; k++) {
      var it = G.items[k], on = norm(it.h) === here;
      gh += '<a class="tgn-tile' + (on ? ' on' : '') + '" href="' + it.h + '"' + (on ? ' aria-current="page"' : '') + '>' +
        (it.n ? '<span class="tgn-new">' + sp(TXT.isNew) + '</span>' : '') +
        '<span class="tgn-ic" aria-hidden="true">' + it.i + '</span><span>' + sp(it) + '</span></a>';
    }
    gh += '</div>';
  }

  var ov = document.createElement('div');
  ov.className = 'tgn-ov tgn-lg';
  ov.id = 'tgnOv';
  ov.setAttribute('role', 'dialog');
  ov.setAttribute('aria-modal', 'true');
  ov.setAttribute('aria-label', 'All pages');
  ov.innerHTML =
    '<div class="tgn-pn">' +
      '<div class="tgn-ph"><h2 class="tgn-pt">' + sp(TXT.title) + '</h2>' +
      '<button type="button" class="tgn-x" id="tgnClose" aria-label="Close">&#10005;</button></div>' +
      '<a class="tgn-wa" id="tgnWa" href="#" target="_blank" rel="noopener"><span class="tgn-wi"><svg width="26" height="26" viewBox="0 0 24 24" fill="#25D366" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg></span><span class="tgn-wt"><b>' + sp(TXT.wa) + '</b><small>' + sp(TXT.waS) + '</small></span></a>' + gh +
    '</div>';
  document.body.appendChild(ov);

  /* WhatsApp banner: number + ready message in the visitor's language (change the number here if it ever changes) */
  var WA_NUM = '94701500743';
  var WA_MSG = { si: 'ආයුබෝවන්, TopGoviya.lk ගැන: ', ta: 'வணக்கம், TopGoviya.lk பற்றி: ', en: 'Hello, about TopGoviya.lk: ' };
  var waA = document.getElementById('tgnWa');
  function setWa() {
    var l = document.documentElement.lang; if (!WA_MSG[l]) l = 'si';
    waA.href = 'https://wa.me/' + WA_NUM + '?text=' + encodeURIComponent(WA_MSG[l]);
  }
  setWa();
  waA.addEventListener('click', setWa);

  /* ---------- 6. OPEN / CLOSE ---------- */
  var openBtn = document.getElementById('tgnOpen');
  var closeBtn = document.getElementById('tgnClose');
  var prevOverflow = '';

  function openMenu() {
    prevOverflow = document.body.style.overflow;
    ov.className = 'tgn-ov tgn-lg open';
    document.body.style.overflow = 'hidden';
    openBtn.setAttribute('aria-expanded', 'true');
    closeBtn.focus();
  }
  function closeMenu() {
    ov.className = 'tgn-ov tgn-lg';
    document.body.style.overflow = prevOverflow;
    openBtn.setAttribute('aria-expanded', 'false');
    openBtn.focus();
  }
  function isOpen() { return ov.className.indexOf('open') > -1; }

  openBtn.addEventListener('click', function () { isOpen() ? closeMenu() : openMenu(); });
  closeBtn.addEventListener('click', closeMenu);
  ov.addEventListener('click', function (e) {
    if (e.target === ov) closeMenu();
    var a = e.target;
    while (a && a !== ov) { if (a.tagName === 'A') { closeMenu(); break; } a = a.parentNode; }
  });
  document.addEventListener('keydown', function (e) {
    if (!isOpen()) return;
    if (e.key === 'Escape' || e.keyCode === 27) { closeMenu(); return; }
    if (e.key === 'Tab' || e.keyCode === 9) {              /* keep Tab inside the open grid */
      var f = ov.querySelectorAll('a[href],button');
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
})();
