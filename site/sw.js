/* Pray a Novena service worker: keeps the whole library on this device so it opens without signal.
   Pages: network first (corrections arrive right away), the saved copy when offline or after 4000 ms.
   Everything else (images, fonts, icons): saved once and reused. Built by tools/build.py; do not edit site/sw.js. */
var VERSION = "9eb010672be8";
var CACHE = "novenas-" + VERSION;
var FILES = ["apple-touch-icon.png", "favicon.ico", "favicon.svg", "icon-192.png", "icon-512.png", "icon-maskable-512.png", "index.html", "./", "manifest.webmanifest", "about/index.html", "about/", "about/img/acutis.jpg", "about/img/angelus.jpg", "about/img/aquinas.jpg", "about/img/augustine.jpg", "about/img/bosco.jpg", "about/img/camillus.jpg", "about/img/cupertino.jpg", "about/img/ignatius.jpg", "about/img/lamb.jpg", "about/img/longo.jpg", "about/img/mary.jpg", "about/img/paul.jpg", "about/img/pentecost.jpg", "about/img/peter.jpg", "about/img/savio.jpg", "expectant-parents/index.html", "expectant-parents/", "expectant-parents/img/elizabeth.jpg", "expectant-parents/img/elizabeth_face.jpg", "expectant-parents/img/gerard.jpg", "expectant-parents/img/gerard_face.jpg", "expectant-parents/img/joseph.jpg", "expectant-parents/img/joseph_face.jpg", "expectant-parents/img/mary_face.jpg", "fonts/cormorant-garamond-italic.woff2", "fonts/cormorant-garamond.woff2", "fonts/eb-garamond-italic.woff2", "fonts/eb-garamond.woff2", "fonts/fonts.css", "gift-of-knowledge/index.html", "gift-of-knowledge/", "gift-of-knowledge/img/albert.jpg", "gift-of-knowledge/img/albert_face.jpg", "gift-of-knowledge/img/augustine.jpg", "gift-of-knowledge/img/augustine_face.jpg", "gift-of-knowledge/img/hildegard.jpg", "gift-of-knowledge/img/hildegard_face.jpg", "gift-of-knowledge/img/mary_face.jpg", "healing/index.html", "healing/", "healing/img/bernadette.jpg", "healing/img/bernadette_face.jpg", "healing/img/camillus.jpg", "healing/img/camillus_face.jpg", "healing/img/mary_face.jpg", "healing/img/raphael.jpg", "healing/img/raphael_face.jpg", "impossible-cases/index.html", "impossible-cases/", "impossible-cases/img/jude.jpg", "impossible-cases/img/jude_face.jpg", "impossible-cases/img/rita.jpg", "impossible-cases/img/rita_face.jpg", "passing-an-exam/index.html", "passing-an-exam/", "passing-an-exam/img/aquinas.jpg", "passing-an-exam/img/aquinas_face.jpg", "passing-an-exam/img/cupertino.jpg", "passing-an-exam/img/cupertino_face.jpg", "passing-an-exam/img/mary_face.jpg", "privacy/index.html", "privacy/", "relief-from-debt/index.html", "relief-from-debt/", "relief-from-debt/img/joseph.jpg", "relief-from-debt/img/joseph_face.jpg", "relief-from-debt/img/jude.jpg", "relief-from-debt/img/jude_face.jpg", "relief-from-debt/img/mary_face.jpg", "relief-from-debt/img/rita.jpg", "relief-from-debt/img/rita_face.jpg", "work-and-livelihood/index.html", "work-and-livelihood/", "work-and-livelihood/img/cajetan.jpg", "work-and-livelihood/img/cajetan_face.jpg", "work-and-livelihood/img/homobonus.jpg", "work-and-livelihood/img/homobonus_face.jpg", "work-and-livelihood/img/joseph.jpg", "work-and-livelihood/img/joseph_face.jpg", "work-and-livelihood/img/mary_face.jpg"];
var TIMEOUT = 4000;

function url(p){ return new URL(p, self.registration.scope).href; }
/* a redirected response can't answer a page request, so keep only its body */
function clean(r){
  if (!r || !r.redirected) return Promise.resolve(r);
  return r.blob().then(function(b){ return new Response(b, {status: r.status, statusText: r.statusText, headers: r.headers}); });
}
function isPage(req){ return req.mode === "navigate" || (req.headers.get("accept") || "").indexOf("text/html") >= 0; }

self.addEventListener("install", function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){
    return Promise.all(FILES.map(function(p){
      return fetch(url(p), {cache: "no-cache"}).then(function(r){
        if (!r.ok) throw new Error(p + " " + r.status);
        return clean(r).then(function(cr){ return c.put(url(p), cr); });
      });
    }));
  }).then(function(){ return self.skipWaiting(); }));
});

self.addEventListener("activate", function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){ return k.indexOf("novenas-") === 0 && k !== CACHE; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});

self.addEventListener("fetch", function(e){
  var req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  if (isPage(req)){
    e.respondWith(caches.open(CACHE).then(function(c){
      var u = new URL(req.url), key = u.origin + u.pathname;
      var net = fetch(req).then(clean).then(function(r){ if (r && r.ok) c.put(key, r.clone()); return r; });
      var saved = c.match(key).then(function(m){
        if (m) return m;
        var dir = /\/$/.test(u.pathname) ? u.pathname : (/\.html$/.test(u.pathname) ? null : u.pathname + "/");
        return dir ? c.match(u.origin + dir + "index.html") : null;
      }).then(function(m){ return m || c.match(url("index.html")); });
      return new Promise(function(resolve){
        var done = false;
        function give(r){ if (!done && r){ done = true; resolve(r); } }
        var t = setTimeout(function(){ saved.then(give); }, TIMEOUT);
        net.then(function(r){ clearTimeout(t); give(r); }, function(){ clearTimeout(t); saved.then(function(m){ give(m || Response.error()); }); });
      });
    }));
    return;
  }
  e.respondWith(caches.open(CACHE).then(function(c){
    return c.match(req, {ignoreSearch: true}).then(function(m){
      return m || fetch(req).then(function(r){ if (r && r.ok && r.type === "basic") c.put(req, r.clone()); return r; });
    });
  }));
});
