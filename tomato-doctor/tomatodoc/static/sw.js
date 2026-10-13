/* Service worker: makes the app installable and keeps the shell, styles,
   reference photos and fonts available on weak rural connections.
   Diagnosis itself (/api/*) always goes to the network. */
const VERSION = "tomatodoc-v2.3.0";
const SHELL = ["/", "/static/css/app.css?v=2.3.0", "/static/js/i18n.js?v=2.3.0", "/static/js/i18n_field.js?v=2.3.0", "/static/js/i18n_soil.js?v=2.3.0", "/static/js/i18n_myfield.js?v=2.3.0", "/static/js/app.js?v=2.3.0", "/static/img/icon.svg", "/manifest.webmanifest"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/expert")) return;

  if (req.mode === "navigate") {
    e.respondWith(fetch(req).then((res) => {
      const copy = res.clone();
      caches.open(VERSION).then((c) => c.put("/", copy));
      return res;
    }).catch(() => caches.match("/")));
    return;
  }
  const cacheable = url.origin === location.origin ? url.pathname.startsWith("/static/")
    : /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
  if (!cacheable) return;
  e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((res) => {
    if (res.ok || res.type === "opaque") { const copy = res.clone(); caches.open(VERSION).then((c) => c.put(req, copy)); }
    return res;
  })));
});
