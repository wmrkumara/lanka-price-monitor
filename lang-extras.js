/* lang-extras.js — TopGoviya.lk homepage: translates parts the main page script does not
   (the spice price banner at the top) when the language switch (සිංහල / தமிழ் / EN) changes.
   Follows the page language from <html lang="...">, which the page sets on every switch. */
(function () {
  var T = {
    si: { title: "නව! කුළුබඩු ගොවිපළ දොරටු මිල වාර්තාව",
          sub: "DEA · 2023–2026 · සතිපතා · ගම්මිරිස්, කුරුඳු, කරාබු සහ තවත්",
          pepper: "ගම්මිරිස්", cinnamon: "කුරුඳු", clove: "කරාබු", btn: "වාර්තාව බලන්න →", rs: "රු." },
    en: { title: "New! Spice farm gate price report",
          sub: "DEA · 2023–2026 · weekly · pepper, cinnamon, clove and more",
          pepper: "Pepper", cinnamon: "Cinnamon", clove: "Clove", btn: "View report →", rs: "Rs." },
    ta: { title: "புதிது! மசாலா பண்ணை விலை அறிக்கை",
          sub: "DEA · 2023–2026 · வாராந்திரம் · மிளகு, கறுவா, கராம்பு மற்றும் பல",
          pepper: "மிளகு", cinnamon: "கறுவா", clove: "கராம்பு", btn: "அறிக்கையைப் பார்க்க →", rs: "ரூ." }
  };
  function lang() { var l = (document.documentElement.getAttribute("lang") || "si").slice(0, 2); return T[l] ? l : "si"; }
  function set(id, txt) { var e = document.getElementById(id); if (e && e.textContent !== txt) e.textContent = txt; }

  function prices(t) {
    ["sb-pepper", "sb-cinnamon", "sb-clove"].forEach(function (id) {
      var e = document.getElementById(id); if (!e) return;
      var v = e.textContent.replace(/^(රු\.|Rs\.|ரூ\.)\s?/, "");
      var want = /\d/.test(v) ? t.rs + v : e.textContent;
      if (e.textContent !== want) e.textContent = want;
    });
  }

  function apply() {
    var t = T[lang()];
    set("sb-title", t.title); set("sb-sub", t.sub); set("sb-btn", t.btn);
    var labels = document.querySelectorAll("#sb-prices .sp-label");
    [t.pepper, t.cinnamon, t.clove].forEach(function (txt, i) { if (labels[i] && labels[i].textContent !== txt) labels[i].textContent = txt; });
    prices(t);
  }

  function start() {
    apply();
    /* language switch -> the page changes <html lang> */
    new MutationObserver(apply).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
    /* prices arrive a moment later from dea_data.json */
    var box = document.getElementById("sb-prices");
    if (box) new MutationObserver(function () { prices(T[lang()]); }).observe(box, { childList: true, subtree: true, characterData: true });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
