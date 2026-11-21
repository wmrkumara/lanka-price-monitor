/* events.js — TopGoviya.lk: counts the actions that matter in Google Analytics (GA4)
   share            WhatsApp / Share buttons
   price_download   PDF / image downloads (price lists, daily images, official reports)
   ask_question     price assistant (typed or voice) — sent from assistant.js
   calculator_use   first number typed into a calculator on a page
   language_change  Sinhala / Tamil / English switch
   install_prompt_shown / install_click / install_choice / install_dismiss / app_installed
                    "Add to home screen" banner (phones only, see the part at the bottom)
   app_open         the site was opened from the home-screen icon (once per visit)
   No personal data is sent; only the page and what was tapped. Loaded on every page. */
(function () {
  function ev(name, params) {
    try { if (typeof gtag === "function") gtag("event", name, Object.assign({ page_path: location.pathname }, params || {})); } catch (e) {}
  }
  window.tgEvent = ev;

  document.addEventListener("click", function (e) {
    var el = e.target.closest ? e.target.closest("a,button") : null;
    if (!el) return;
    var href = el.getAttribute("href") || "", oc = el.getAttribute("onclick") || "", id = el.id || "";
    var txt = (el.innerText || el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 40);   /* visible text only */
    var all = href + " " + oc + " " + id + " " + txt;

    if (el.closest(".lang") && el.getAttribute("data-lang")) {
      ev("language_change", { language: el.getAttribute("data-lang") });
    } else if (/tgPdf|tgImage|download|downloadCard|saveImage/i.test(oc) || /\.(pdf|png|jpe?g|csv)(\?|#|$)/i.test(href) || /බාගන්න|download/i.test(txt)) {
      var kind = /pdf/i.test(all) ? "pdf" : (/csv/i.test(all) ? "csv" : "image");
      ev("price_download", { file_type: kind, item: txt || href.split("/").pop() });
    } else if (/wa\.me|api\.whatsapp|whatsapp:\/\/|facebook\.com\/sharer|tgShare|share/i.test(href + " " + oc + " " + id) || /WhatsApp|Share|බෙදාගන්න/i.test(txt)) {
      ev("share", { method: /wa\.me|whatsapp/i.test(all) ? "whatsapp" : (/facebook/i.test(all) ? "facebook" : "share"), content_type: location.pathname.split("/")[1] || "home", item_id: txt });
    }
  }, true);

  /* calculators: count once per page, when someone first types a number */
  var counted = false;
  document.addEventListener("input", function (e) {
    var t = e.target;
    if (counted || !t || t.id === "search" || !(t.type === "number" || t.inputMode === "decimal" || t.inputMode === "numeric")) return;
    counted = true;
    var name = /breakeven/.test(location.pathname) ? "breakeven" : (/loan/.test(location.pathname) ? "loan" : "price_calculator");
    ev("calculator_use", { calculator: name });
  }, true);
})();

/* ===== "Add to home screen" banner (20 Nov 2026) =====
   Goal: turn first-time visitors into daily visitors. Phones only.
   - Android Chrome: a real "Install" button (uses the browser's own install box)
   - iPhone: short steps (Share → Add to Home Screen)
   - Facebook / Instagram / other in-app browsers on Android: button to open the page in Chrome
   Shows after 15 seconds on the first visit, after 4 seconds from the second visit.
   ✕ hides it for 7 days. Not shown when the site is already opened from the home screen,
   or on pages that already have their own install banner (#pwa-banner). */
(function () {
  function ev(n, p) { if (window.tgEvent) window.tgEvent(n, p); }
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function put(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  var DAY = 864e5, HIDE = "tgInstallHideUntil";

  var standalone = (window.matchMedia && matchMedia("(display-mode: standalone)").matches) || navigator.standalone === true;
  if (standalone) {                                   /* opened from the home-screen icon */
    try { if (!sessionStorage.getItem("tgAppOpen")) { sessionStorage.setItem("tgAppOpen", "1"); ev("app_open"); } } catch (e) {}
    return;
  }
  var ua = navigator.userAgent || "";
  var ios = /iPhone|iPad|iPod/i.test(ua), android = /Android/i.test(ua);
  if (!ios && !android) return;                       /* computers: no banner */

  /* the install file must be linked on the page (some pages did not have it) */
  if (!document.querySelector('link[rel="manifest"]')) {
    var l = document.createElement("link"); l.rel = "manifest"; l.href = "/manifest.json"; document.head.appendChild(l);
  }

  var visits = (+get("tgVisits") || 0) + 1; put("tgVisits", visits);
  var deferred = null, shown = false;
  window.addEventListener("beforeinstallprompt", function (e) { e.preventDefault(); deferred = e; });
  window.addEventListener("appinstalled", function () {
    ev("app_installed"); put(HIDE, Date.now() + 3650 * DAY); var b = document.getElementById("tg-install"); if (b) b.remove();
  });
  if (Date.now() < (+get(HIDE) || 0)) return;

  var inapp = /FBAN|FBAV|FB_IAB|FBIOS|Instagram|Line\/|; wv\)/i.test(ua);
  var T = {
    si: { t: "📲 TopGoviya ඔබේ phone එකට", s: "හැමදාම මිල එක tap එකකින්. නොමිලේ, ඉඩ අඩුයි.", b: "එකතු කරන්න",
          ios: "Safari හි පහළ Share ⬆️ ඔබා “Add to Home Screen” තෝරන්න", ok: "හරි",
          app: "Chrome එකෙන් විවෘත කර phone එකට එකතු කරන්න", open: "Chrome එකෙන් විවෘත කරන්න" },
    ta: { t: "📲 TopGoviya உங்கள் போனில்", s: "தினசரி விலை ஒரே தட்டலில். இலவசம்.", b: "சேர்க்க",
          ios: "Safari-யில் Share ⬆️ அழுத்தி “Add to Home Screen” தேர்வு செய்யவும்", ok: "சரி",
          app: "Chrome-இல் திறந்து போனில் சேர்க்கவும்", open: "Chrome-இல் திறக்க" },
    en: { t: "📲 Add TopGoviya to your phone", s: "Today's prices in one tap. Free and tiny.", b: "Add",
          ios: "In Safari, tap Share ⬆️ then “Add to Home Screen”", ok: "OK",
          app: "Open in Chrome to add it to your phone", open: "Open in Chrome" }
  };

  function show() {
    if (shown || document.getElementById("pwa-banner") || document.getElementById("tg-install")) return;
    var mode = ios ? "ios" : (deferred ? "chrome" : (inapp ? "inapp" : ""));
    if (!mode) return;                                /* browser cannot install: say nothing */
    shown = true;
    var L = T[(document.documentElement.lang || "si").slice(0, 2)] || T.si;
    var sub = mode === "ios" ? L.ios : (mode === "inapp" ? L.app : L.s);
    var btn = mode === "ios" ? L.ok : (mode === "inapp" ? L.open : L.b);
    var d = document.createElement("div");
    d.id = "tg-install"; d.setAttribute("role", "dialog");
    d.style.cssText = "position:fixed;left:10px;right:10px;bottom:calc(10px + env(safe-area-inset-bottom,0px));z-index:99999;" +
      "padding:12px 12px 12px 14px;border-radius:16px;background:#0e4f4a;color:#fff;" +
      "box-shadow:0 6px 24px rgba(0,0,0,.35);font-family:inherit;max-width:520px;margin:0 auto;line-height:1.35";
    d.innerHTML = '<div style="display:flex;align-items:center;gap:10px">' +
      '<img src="/icon-96x96.png" alt="" width="44" height="44" style="border-radius:10px;flex:none">' +
      '<div style="flex:1;min-width:0"><div style="font-weight:700;font-size:15px">' + L.t + '</div>' +
      '<div style="font-size:13px;opacity:.9">' + sub + '</div></div>' +
      '<button type="button" data-a="x" aria-label="Close" style="flex:none;align-self:flex-start;border:0;background:none;color:#fff;font-size:20px;padding:0 4px;cursor:pointer;opacity:.8">✕</button></div>' +
      '<button type="button" data-a="go" style="display:block;width:100%;margin-top:10px;border:0;border-radius:10px;background:#ffd43b;color:#0e4f4a;font:inherit;font-weight:700;font-size:15px;padding:11px 12px;cursor:pointer">' + btn + '</button>';
    document.body.appendChild(d);
    ev("install_prompt_shown", { method: mode });

    d.addEventListener("click", function (e) {
      var a = e.target.closest ? e.target.closest("[data-a]") : null;
      if (!a) return;
      if (a.getAttribute("data-a") === "x") {
        ev("install_dismiss", { method: mode }); put(HIDE, Date.now() + 7 * DAY); d.remove(); return;
      }
      ev("install_click", { method: mode });
      if (mode === "chrome" && deferred) {
        deferred.prompt();
        deferred.userChoice.then(function (c) {
          ev("install_choice", { outcome: c.outcome });
          put(HIDE, Date.now() + (c.outcome === "accepted" ? 3650 : 7) * DAY);
        });
        deferred = null; d.remove();
      } else if (mode === "inapp") {
        location.href = "intent://" + location.host + location.pathname + location.search +
          "#Intent;scheme=https;package=com.android.chrome;S.browser_fallback_url=" + encodeURIComponent(location.href) + ";end";
      } else {                                        /* iPhone: they follow the steps themselves */
        put(HIDE, Date.now() + 7 * DAY); d.remove();
      }
    });
  }
  setTimeout(show, visits >= 2 ? 4000 : 15000);
})();

/* Follow box — YouTube Subscribe + Facebook Follow. Never blocks the page.
   Shows after the visitor has read part of the page (scrolled 45%) or after 40 s,
   never at the same time as the "Add to home screen" banner.
   "Later" / × = hidden 7 days; Subscribe / Follow tapped = hidden 60 days.
   Counted in GA: follow_box_shown, follow_click (platform), follow_dismiss. */
(function () {
  var K = "tgFollowHideUntil", DAY = 864e5;
  function get() { try { return +localStorage.getItem(K) || 0; } catch (e) { return 0; } }
  function put(d) { try { localStorage.setItem(K, Date.now() + d * DAY); } catch (e) {} }
  function ev(n, p) { if (window.tgEvent) window.tgEvent(n, p); }
  if (Date.now() < get() || document.getElementById("tg-follow")) return;
  var L = {
    si: ["📺 දිනපතා එළවළු මිල — නොමිලේ", "සෑම උදෑසනකම දඹුල්ල මිල YouTube Short එකක් සහ Facebook පෝස්ට් එකක්. මිල අහිමි නොවෙන්න.", "පසුව"],
    ta: ["📺 தினசரி காய்கறி விலை — இலவசம்", "ஒவ்வொரு காலையிலும் தம்புள்ள விலை YouTube Short மற்றும் Facebook பதிவு.", "பின்னர்"],
    en: ["📺 Daily vegetable prices — free", "A Dambulla price Short on YouTube and a Facebook post every morning.", "Later"]
  };
  var shown = false, box = null;
  function lang() { var l = (document.documentElement.lang || "si").slice(0, 2); return L[l] ? l : "si"; }
  function fill() {
    if (!box) return; var t = L[lang()];
    box.querySelector(".ft").textContent = t[0]; box.querySelector(".fs").textContent = t[1]; box.querySelector(".fl").textContent = t[2];
  }
  function hide(days, why) {
    if (!box) return; put(days); if (why) ev("follow_dismiss");
    box.style.transform = "translateY(140%)"; var b = box; setTimeout(function () { b.remove(); }, 400);
  }
  function show() {
    if (shown) return;
    if (document.getElementById("tg-install") || document.getElementById("pwa-banner")) { setTimeout(show, 8000); return; }
    shown = true;
    var css = document.createElement("style");
    css.textContent =
      "#tg-follow{position:fixed;left:10px;right:10px;bottom:calc(10px + env(safe-area-inset-bottom,0px));max-width:420px;margin:0 auto;z-index:99998;" +
      "background:#fffdf7;border:1px solid #e3d9c4;border-top:4px solid #0e4f4a;border-radius:14px;box-shadow:0 8px 30px rgba(0,0,0,.18);" +
      "padding:14px 14px 10px;font-size:14px;color:#191d1a;transform:translateY(140%);transition:transform .35s ease;font-family:inherit}" +
      "#tg-follow .ft{display:block;font-size:15.5px;font-weight:700;margin:0 28px 4px 0;line-height:1.4}" +
      "#tg-follow .fs{margin:0 0 10px;color:#5d574c;line-height:1.5}" +
      "#tg-follow .fr{display:flex;gap:8px}" +
      "#tg-follow a{flex:1;display:flex;align-items:center;justify-content:center;gap:6px;padding:10px 8px;border-radius:10px;color:#fff;font-weight:700;text-decoration:none;font-size:14px}" +
      "#tg-follow .yt{background:#d62e1f}#tg-follow .fb{background:#1b6fd8}" +
      "#tg-follow .fl{display:block;margin:8px auto 0;background:none;border:0;color:#5d574c;font-size:14.5px;font-weight:600;padding:6px 18px;cursor:pointer;text-decoration:underline;font-family:inherit}" +
      "#tg-follow .fx{position:absolute;top:6px;right:8px;background:none;border:0;font-size:22px;line-height:1;color:#7a7264;cursor:pointer;padding:4px 8px}";
    document.head.appendChild(css);
    box = document.createElement("div"); box.id = "tg-follow"; box.setAttribute("role", "dialog");
    box.innerHTML = '<button class="fx" type="button" aria-label="close">×</button><span class="ft"></span><p class="fs"></p>' +
      '<div class="fr"><a class="yt" href="https://www.youtube.com/@TopGoviyaLK?sub_confirmation=1" target="_blank" rel="noopener">▶ Subscribe</a>' +
      '<a class="fb" href="https://www.facebook.com/TopGoviyaLK" target="_blank" rel="noopener">f Follow</a></div><button class="fl" type="button"></button>';
    document.body.appendChild(box); fill();
    requestAnimationFrame(function () { requestAnimationFrame(function () { box.style.transform = "none"; }); });
    ev("follow_box_shown");
    box.querySelector(".fx").onclick = function () { hide(7, 1); };
    box.querySelector(".fl").onclick = function () { hide(7, 1); };
    box.querySelector(".yt").addEventListener("click", function () { ev("follow_click", { platform: "youtube" }); hide(60); });
    box.querySelector(".fb").addEventListener("click", function () { ev("follow_click", { platform: "facebook" }); hide(60); });
  }
  document.addEventListener("click", function (e) { if (e.target.closest && e.target.closest(".lang button")) setTimeout(fill, 50); });
  function onScroll() {
    var h = document.documentElement.scrollHeight - innerHeight;
    if (h > 0 && scrollY / h >= 0.45) { removeEventListener("scroll", onScroll); show(); }
  }
  addEventListener("scroll", onScroll, { passive: true });
  setTimeout(show, 40000);
})();
