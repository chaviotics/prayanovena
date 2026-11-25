/* "Add to home screen" (built into every site page by tools/build.py, install_kit()).
   Every [data-install] button opens it: the browser's own install box where the browser offers one (Chrome, Edge,
   Samsung Internet), otherwise short steps in #instSheet: iPhone and iPad (Share > Add to Home Screen), Mac Safari
   (File > Add to Dock), and in-app browsers like Messenger, which can't add anything (open in Chrome or Safari first).
   [data-inst] elements show only when this browser has a way to add the site and it isn't already opened from its icon;
   data-inst="offer" also needs data-on="1" (set by the novena page) and no earlier "Not now". */
(function(){
  var d = document, ua = navigator.userAgent, mm = function(q){ return !!window.matchMedia && matchMedia(q).matches; };
  var installed = mm("(display-mode: standalone)") || mm("(display-mode: window-controls-overlay)") || navigator.standalone === true;
  var ios = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
  var android = /Android/i.test(ua), touch = mm("(pointer: coarse)");
  var inApp = /FBAN|FBAV|FB_IAB|FBIOS|Messenger|Instagram|Line\/|MicroMessenger|; wv\)/i.test(ua);
  var macSafari = !ios && /Macintosh/.test(ua) && /Version\/(1[7-9]|[2-9]\d)\./.test(ua) && !/Chrome|Chromium|CriOS|Edg|Firefox|OPR/.test(ua);
  var OFFER = "novenas-install";   /* "no" after "Not now" on the offer; cleared with everything else on the Privacy page */
  var deferred = null, kind = null, opener = null;
  if (!installed){
    if (ios) kind = inApp ? "ios-app" : "ios";
    else if (android && inApp) kind = "android-app";
    else if (macSafari) kind = "mac";
  }
  /* Chrome, Edge and Samsung Internet say when the site can be installed; keep that, so our button can open their box
     (this also stops Chrome's own bar from popping up on a first visit) */
  window.addEventListener("beforeinstallprompt", function(e){ e.preventDefault(); deferred = e; if (!installed){ kind = "prompt"; paint(); } });
  window.addEventListener("appinstalled", function(){ deferred = null; kind = null; paint(); });

  function offerOff(){ try{ return localStorage.getItem(OFFER) === "no"; }catch(e){ return false; } }
  var pc = function(){ return (kind === "prompt" || kind === "menu") && !touch; };
  function label(){ return kind === "mac" ? "Add to Dock" : pc() ? "Install on this computer" : "Add to home screen"; }
  function paint(){
    [].forEach.call(d.querySelectorAll("[data-inst]"), function(el){
      var show = !!kind;
      if (el.getAttribute("data-inst") === "offer") show = show && el.getAttribute("data-on") === "1" && !offerOff();
      el.hidden = !show;
    });
    [].forEach.call(d.querySelectorAll("[data-inst-label]"), function(el){ el.textContent = label(); });
    [].forEach.call(d.querySelectorAll("[data-inst-title]"), function(el){
      el.textContent = kind === "mac" ? "Keep it in your Dock" : pc() ? "Keep it on this computer" : "Keep it on your home screen"; });
    [].forEach.call(d.querySelectorAll("[data-inst-sub]"), function(el){
      el.textContent = kind === "mac" || pc() ? "Tomorrow’s prayer will be one click away, even offline." : "Tomorrow’s prayer will be one tap away, even without signal."; });
  }

  /* the steps for each case: [icon html or "", text html] */
  function key(name){ return '<span class="is-key" aria-hidden="true"><svg focusable="false"><use href="#i-' + name + '"/></svg></span>'; }
  function begun(){ try{ for (var i = 0; i < localStorage.length; i++) if (/^novena-/.test(localStorage.key(i))) return true; }catch(e){} return false; }
  function guide(){
    var t = "Add to your home screen", sub = "", steps = [], note = "", open = false;
    var share = /CriOS/.test(ua) ? "Tap <b>Share</b> " + key("export") + " in the address bar."
      : /FxiOS|EdgiOS|OPiOS/.test(ua) ? "Open the browser’s menu, then tap <b>Share</b> " + key("export") + "."
      : "Tap <b>Share</b> " + key("export") + ". On newer iPhones it’s in the <b>•••</b> menu beside the address.";
    var add = "Tap <b>Add to Home Screen</b> " + key("plus-square") + ". If you don’t see it, scroll down or tap <b>View More</b>.";
    var ipad = /iPad/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
    if (kind === "ios"){
      sub = "It opens from its own icon like an app, even without signal.";
      steps = [share, add, "Tap <b>Add</b>. The 9 days icon appears on your home screen."];
      if (begun()) note = (ipad ? "Your iPad" : "Your iPhone") + " keeps the home screen copy separate from the browser, so a novena you’ve begun starts fresh there. Open it, set its start date and tick the days you’ve prayed.";
    } else if (kind === "ios-app"){
      sub = "Messenger and Facebook open pages in their own browser, which can’t do this. Open the page in Safari first.";
      steps = ["Tap <b>•••</b> " + key("dots-three") + " or the menu, then <b>Open in Safari</b> (or Open in browser).",
               "In Safari, tap <b>Share</b> " + key("export") + ", then <b>Add to Home Screen</b>.", "Tap <b>Add</b>."];
    } else if (kind === "android-app"){
      sub = "Messenger and Facebook open pages in their own browser, which can’t do this. Open the page in Chrome first.";
      steps = ["Tap <b>Open in Chrome</b> below.", "In Chrome, tap the menu " + key("dots-three-vertical") + ", then <b>Add to home screen</b>."];
      open = true;
    } else if (kind === "mac"){
      t = "Add to your Dock"; sub = "It opens in its own window, even offline.";
      steps = ["In the menu bar, choose <b>File</b>, then <b>Add to Dock</b>.", "Click <b>Add</b>."];
    } else {   /* the browser's box was closed earlier: its menu still has it */
      t = pc() ? "Install on this computer" : t; sub = "It opens from its own icon like an app, even offline.";
      steps = ["Open your browser’s menu " + key("dots-three-vertical") + ".", "Look for <b>" + (pc() ? "Install" : "Add to home screen") + "</b>, then confirm."];
    }
    var $ = function(id){ return d.getElementById(id); };
    $("instTitle").textContent = t; $("instSub").textContent = sub;
    $("instSteps").innerHTML = steps.map(function(s, i){ return '<li><span class="is-n" aria-hidden="true">' + (i + 1) + '</span><span>' + s + '</span></li>'; }).join("");
    $("instNote").textContent = note; $("instNote").hidden = !note;
    var o = $("instOpen"); o.hidden = !open;
    if (open) o.href = "intent://" + location.host + location.pathname + "#Intent;scheme=https;package=com.android.chrome;S.browser_fallback_url=" + encodeURIComponent(location.origin + location.pathname) + ";end";
    var sh = $("instSheet");
    if (sh.showModal) sh.showModal(); else sh.setAttribute("open", "");
  }
  function start(btn){
    opener = btn;
    if (kind === "prompt" && deferred){
      var e = deferred; deferred = null;
      e.prompt();
      e.userChoice.then(function(c){ kind = c && c.outcome === "accepted" ? null : "menu"; paint(); }, function(){ kind = "menu"; paint(); });
      return;
    }
    if (kind) guide();
  }
  d.addEventListener("click", function(e){ var b = e.target.closest && e.target.closest("[data-install]"); if (b){ e.preventDefault(); start(b); } });
  var sheet = d.getElementById("instSheet");
  if (sheet){
    d.getElementById("instDone").addEventListener("click", function(){ sheet.close ? sheet.close() : sheet.removeAttribute("open"); });
    sheet.addEventListener("click", function(e){ if (e.target === sheet && sheet.close) sheet.close(); });
    sheet.addEventListener("close", function(){ if (opener && d.contains(opener) && !opener.closest("[hidden]")) opener.focus(); });
  }
  window.novenaInstall = {
    paint: paint,
    later: function(){ try{ localStorage.setItem(OFFER, "no"); }catch(e){} paint(); }
  };
  paint();
})();
