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

/* ===== "📲 Get the app" button on every page (22 Nov 2026) =====
   Small button, always visible at the bottom-left (sits under popups and the boxes above).
   - Android Chrome: opens the browser's own install box
   - iPhone: shows the Share → Add to Home Screen steps
   - Facebook / in-app browsers: opens the page in Chrome
   - Other phone browsers: shows "menu ⋮ → Add to Home screen"
   - Computers: shows a QR code to scan with the phone camera
   Not shown when the site is already opened as the app. GA: app_button_click (method). */
(function () {
  function ev(n, p) { if (window.tgEvent) window.tgEvent(n, p); }
  var standalone = (window.matchMedia && matchMedia("(display-mode: standalone)").matches) || navigator.standalone === true;
  if (standalone || document.getElementById("tg-app")) return;
  var ua = navigator.userAgent || "";
  var ios = /iPhone|iPad|iPod/i.test(ua), android = /Android/i.test(ua), phone = ios || android;
  var inapp = /FBAN|FBAV|FB_IAB|FBIOS|Instagram|Line\/|; wv\)/i.test(ua);
  var deferred = null;
  window.addEventListener("beforeinstallprompt", function (e) { e.preventDefault(); deferred = e; });
  window.addEventListener("appinstalled", function () { var b = document.getElementById("tg-app"); if (b) b.remove(); });
  var T = {
    si: { b: "📲 App එක ගන්න", h: "📲 TopGoviya App එක", ok: "හරි",
          ios: "Safari හි පහළ ඇති Share ⬆️ බොත්තම ඔබා “Add to Home Screen” තෝරන්න. එවිට TopGoviya ඔබේ phone එකේ app එකක් ලෙස පෙනේ.",
          menu: "Browser එකේ උඩ ඇති මෙනුව ⋮ ඔබා “Add to Home screen” හෝ “Install app” තෝරන්න.",
          qr: "ඔබේ phone එකේ camera එකෙන් මේ QR code එක scan කරන්න. ඉන්පසු “App එක ගන්න” ඔබන්න.", free: "නොමිලේ · ඉඩ අඩුයි · හැමදාම මිල එක tap එකකින්" },
    ta: { b: "📲 ஆப் பெறுக", h: "📲 TopGoviya ஆப்", ok: "சரி",
          ios: "Safari-யில் கீழே உள்ள Share ⬆️ அழுத்தி “Add to Home Screen” தேர்வு செய்யவும்.",
          menu: "Browser மெனு ⋮ அழுத்தி “Add to Home screen” அல்லது “Install app” தேர்வு செய்யவும்.",
          qr: "உங்கள் போன் கேமராவால் இந்த QR குறியீட்டை ஸ்கேன் செய்யவும்.", free: "இலவசம் · சிறியது · தினசரி விலை ஒரே தட்டலில்" },
    en: { b: "📲 Get the app", h: "📲 TopGoviya app", ok: "OK",
          ios: "In Safari, tap the Share ⬆️ button at the bottom, then “Add to Home Screen”. TopGoviya then opens like an app.",
          menu: "Open the browser menu ⋮ and choose “Add to Home screen” or “Install app”.",
          qr: "Scan this QR code with your phone camera, then tap “Get the app”.", free: "Free · tiny · today's prices in one tap" }
  };
  function L() { return T[(document.documentElement.lang || "si").slice(0, 2)] || T.si; }
  var QR = '<svg viewBox="0 0 33 33" width="200" height="200" shape-rendering="crispEdges" style="display:block;margin:6px auto;background:#fff"><path fill="#0e4f4a" d="M2 2h7v1h-7zM10 2h1v1h-1zM15 2h2v1h-2zM18 2h1v1h-1zM24 2h7v1h-7zM2 3h1v1h-1zM8 3h1v1h-1zM12 3h1v1h-1zM15 3h3v1h-3zM21 3h1v1h-1zM24 3h1v1h-1zM30 3h1v1h-1zM2 4h1v1h-1zM4 4h3v1h-3zM8 4h1v1h-1zM12 4h1v1h-1zM16 4h1v1h-1zM19 4h4v1h-4zM24 4h1v1h-1zM26 4h3v1h-3zM30 4h1v1h-1zM2 5h1v1h-1zM4 5h3v1h-3zM8 5h1v1h-1zM10 5h1v1h-1zM12 5h1v1h-1zM14 5h1v1h-1zM18 5h1v1h-1zM20 5h3v1h-3zM24 5h1v1h-1zM26 5h3v1h-3zM30 5h1v1h-1zM2 6h1v1h-1zM4 6h3v1h-3zM8 6h1v1h-1zM10 6h1v1h-1zM12 6h2v1h-2zM22 6h1v1h-1zM24 6h1v1h-1zM26 6h3v1h-3zM30 6h1v1h-1zM2 7h1v1h-1zM8 7h1v1h-1zM10 7h1v1h-1zM13 7h2v1h-2zM21 7h1v1h-1zM24 7h1v1h-1zM30 7h1v1h-1zM2 8h7v1h-7zM10 8h1v1h-1zM12 8h1v1h-1zM14 8h1v1h-1zM16 8h1v1h-1zM18 8h1v1h-1zM20 8h1v1h-1zM22 8h1v1h-1zM24 8h7v1h-7zM10 9h1v1h-1zM12 9h1v1h-1zM14 9h2v1h-2zM18 9h2v1h-2zM21 9h2v1h-2zM2 10h1v1h-1zM6 10h1v1h-1zM8 10h3v1h-3zM12 10h1v1h-1zM15 10h1v1h-1zM18 10h2v1h-2zM22 10h6v1h-6zM30 10h1v1h-1zM2 11h1v1h-1zM4 11h2v1h-2zM9 11h2v1h-2zM12 11h9v1h-9zM22 11h1v1h-1zM24 11h7v1h-7zM2 12h1v1h-1zM4 12h1v1h-1zM6 12h4v1h-4zM11 12h1v1h-1zM13 12h1v1h-1zM17 12h1v1h-1zM19 12h2v1h-2zM22 12h1v1h-1zM26 12h1v1h-1zM30 12h1v1h-1zM3 13h1v1h-1zM5 13h3v1h-3zM10 13h1v1h-1zM12 13h1v1h-1zM14 13h1v1h-1zM16 13h6v1h-6zM27 13h1v1h-1zM29 13h2v1h-2zM5 14h4v1h-4zM14 14h3v1h-3zM18 14h1v1h-1zM22 14h2v1h-2zM29 14h1v1h-1zM2 15h1v1h-1zM4 15h1v1h-1zM6 15h2v1h-2zM10 15h2v1h-2zM14 15h1v1h-1zM17 15h3v1h-3zM23 15h8v1h-8zM3 16h2v1h-2zM8 16h3v1h-3zM13 16h5v1h-5zM20 16h1v1h-1zM24 16h2v1h-2zM27 16h2v1h-2zM30 16h1v1h-1zM2 17h2v1h-2zM7 17h1v1h-1zM9 17h2v1h-2zM13 17h3v1h-3zM17 17h1v1h-1zM19 17h2v1h-2zM22 17h2v1h-2zM25 17h1v1h-1zM29 17h2v1h-2zM7 18h2v1h-2zM12 18h1v1h-1zM14 18h2v1h-2zM17 18h3v1h-3zM22 18h2v1h-2zM25 18h1v1h-1zM29 18h1v1h-1zM2 19h1v1h-1zM4 19h1v1h-1zM6 19h1v1h-1zM10 19h1v1h-1zM15 19h3v1h-3zM24 19h4v1h-4zM29 19h2v1h-2zM7 20h2v1h-2zM12 20h3v1h-3zM17 20h1v1h-1zM23 20h1v1h-1zM26 20h1v1h-1zM28 20h1v1h-1zM30 20h1v1h-1zM4 21h4v1h-4zM14 21h1v1h-1zM16 21h2v1h-2zM19 21h4v1h-4zM24 21h1v1h-1zM26 21h1v1h-1zM29 21h2v1h-2zM2 22h3v1h-3zM8 22h4v1h-4zM13 22h4v1h-4zM19 22h1v1h-1zM22 22h6v1h-6zM30 22h1v1h-1zM10 23h2v1h-2zM17 23h6v1h-6zM26 23h1v1h-1zM30 23h1v1h-1zM2 24h7v1h-7zM10 24h1v1h-1zM12 24h2v1h-2zM15 24h3v1h-3zM20 24h3v1h-3zM24 24h1v1h-1zM26 24h3v1h-3zM30 24h1v1h-1zM2 25h1v1h-1zM8 25h1v1h-1zM11 25h1v1h-1zM13 25h1v1h-1zM15 25h1v1h-1zM18 25h3v1h-3zM22 25h1v1h-1zM26 25h1v1h-1zM2 26h1v1h-1zM4 26h3v1h-3zM8 26h1v1h-1zM10 26h4v1h-4zM15 26h1v1h-1zM19 26h1v1h-1zM21 26h7v1h-7zM2 27h1v1h-1zM4 27h3v1h-3zM8 27h1v1h-1zM11 27h1v1h-1zM13 27h1v1h-1zM16 27h3v1h-3zM22 27h2v1h-2zM30 27h1v1h-1zM2 28h1v1h-1zM4 28h3v1h-3zM8 28h1v1h-1zM11 28h10v1h-10zM27 28h4v1h-4zM2 29h1v1h-1zM8 29h1v1h-1zM11 29h1v1h-1zM13 29h2v1h-2zM18 29h3v1h-3zM22 29h2v1h-2zM25 29h1v1h-1zM27 29h1v1h-1zM29 29h2v1h-2zM2 30h7v1h-7zM10 30h3v1h-3zM14 30h1v1h-1zM16 30h1v1h-1zM18 30h2v1h-2zM22 30h2v1h-2zM25 30h2v1h-2zM29 30h1v1h-1z"/></svg>';

  var css = document.createElement("style");
  css.textContent =
    "#tg-app{position:fixed;left:10px;bottom:calc(10px + env(safe-area-inset-bottom,0px));z-index:40;border:0;border-radius:999px;" +
    "background:#0e4f4a;color:#fff;font:inherit;font-weight:700;font-size:13.5px;padding:9px 14px;box-shadow:0 4px 14px rgba(0,0,0,.25);cursor:pointer;opacity:.95}" +
    "#tg-appbox{position:fixed;inset:0;z-index:100000;background:rgba(10,20,18,.55);display:flex;align-items:center;justify-content:center;padding:16px}" +
    "#tg-appbox>div{background:#fffdf7;border-radius:16px;max-width:360px;width:100%;padding:18px 18px 14px;text-align:center;color:#191d1a;font-family:inherit;line-height:1.5;box-shadow:0 10px 40px rgba(0,0,0,.3)}" +
    "#tg-appbox b{display:block;font-size:17px;color:#0e4f4a;margin-bottom:6px}#tg-appbox p{margin:6px 0;font-size:14.5px}#tg-appbox small{color:#6f685b}" +
    "#tg-appbox button{margin-top:10px;border:0;border-radius:10px;background:#0e4f4a;color:#fff;font:inherit;font-weight:700;font-size:15px;padding:10px 26px;cursor:pointer}";
  document.head.appendChild(css);

  function box(html) {
    var o = document.createElement("div"); o.id = "tg-appbox";
    o.innerHTML = '<div role="dialog"><b>' + L().h + '</b>' + html + '<p><small>' + L().free + '</small></p><button type="button">' + L().ok + '</button></div>';
    o.addEventListener("click", function (e) { if (e.target === o || e.target.tagName === "BUTTON") o.remove(); });
    document.body.appendChild(o);
  }
  var btn = document.createElement("button");
  btn.id = "tg-app"; btn.type = "button"; btn.textContent = L().b;
  document.body.appendChild(btn);
  document.addEventListener("click", function (e) { if (e.target.closest && e.target.closest(".lang button")) setTimeout(function () { btn.textContent = L().b; }, 50); });

  btn.onclick = function () {
    var method = !phone ? "qr" : ios ? "ios" : deferred ? "chrome" : inapp ? "inapp" : "menu";
    ev("app_button_click", { method: method });
    if (method === "chrome") {
      try { var pr = deferred.prompt(); if (pr && pr.catch) pr.catch(function () { box("<p>" + L().menu + "</p>"); }); deferred.userChoice.then(function (c) { ev("install_choice", { outcome: c.outcome, from: "app_button" }); }); deferred = null; return; }
      catch (x) { method = "menu"; }
    }
    if (method === "inapp") {
      location.href = "intent://" + location.host + location.pathname + location.search +
        "#Intent;scheme=https;package=com.android.chrome;S.browser_fallback_url=" + encodeURIComponent(location.href) + ";end";
      return;
    }
    if (method === "qr") box(QR + "<p>" + L().qr + "</p>");
    else box("<p>" + (method === "ios" ? L().ios : L().menu) + "</p>");
  };
})();
