/* events.js — TopGoviya.lk: counts the actions that matter in Google Analytics (GA4)
   share            WhatsApp / Share buttons
   price_download   PDF / image downloads (price lists, daily images, official reports)
   ask_question     price assistant (typed or voice) — sent from assistant.js
   calculator_use   first number typed into a calculator on a page
   language_change  Sinhala / Tamil / English switch
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
