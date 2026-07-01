/* ===== TopGoviya PWA Service Worker ===== */
/* Version: 2.2 | topgoviya.lk | Built in Gampola 🇱🇰 */
/* Updated: July 2026 — Google Analytics added site-wide; netherlands-sri-lanka-agriculture.html precached */

const CACHE_NAME = 'topgoviya-v7';
const DATA_CACHE = 'topgoviya-data-v7';

/* ── Static files to cache for offline use ── */
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/wholesale.html',
  '/weather.html',
  '/breakeven.html',
  '/insights.html',
  '/blog.html',
  '/about.html',
  '/privacy.html',
  '/farmers-guide-topgoviya.html',
  '/bulletin.html',
  '/netherlands-sri-lanka-agriculture.html',
  '/manifest.json',
  '/icon-72x72.png',
  '/icon-96x96.png',
  '/icon-128x128.png',
  '/icon-192x192.png',
  '/icon-512x512.png',
  /* Google Fonts — cache for offline */
  'https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+Sinhala:wght@400;500;600&family=Noto+Sans+Tamil:wght@400;500;600&display=swap'
];

/* ── Install — cache all static assets ── */
self.addEventListener('install', event => {
  console.log('[TopGoviya SW v2.2] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[TopGoviya SW] Caching all pages + assets');
      return cache.addAll(STATIC_ASSETS).catch(err => {
        console.warn('[TopGoviya SW] Some assets failed to cache:', err);
      });
    })
  );
  self.skipWaiting();
});

/* ── Activate — remove old caches ── */
self.addEventListener('activate', event => {
  console.log('[TopGoviya SW v2.2] Activating...');
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME && k !== DATA_CACHE)
            .map(k => {
              console.log('[TopGoviya SW] Removing old cache:', k);
              return caches.delete(k);
            })
      )
    )
  );
  self.clients.claim();
});

/* ── Fetch strategy ── */
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  /* data.json — always network first (fresh prices!) */
  if (url.pathname.includes('data.json') || url.href.includes('data.json')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const clone = response.clone();
          caches.open(DATA_CACHE).then(cache => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  /* HARTI PDF data — network only, no cache */
  if (url.hostname.includes('harti.gov.lk')) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response('{}', { headers: { 'Content-Type': 'application/json' } })
      )
    );
    return;
  }

  /* Open-Meteo weather API — network only */
  if (url.hostname.includes('open-meteo.com')) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response('{}', { headers: { 'Content-Type': 'application/json' } })
      )
    );
    return;
  }

  /* OSRM routing API — network only */
  if (url.hostname.includes('router.project-osrm.org')) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response('{}', { headers: { 'Content-Type': 'application/json' } })
      )
    );
    return;
  }

  /* Everything else — cache first, network fallback */
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (response.ok && event.request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => {
        /* Offline fallback — show main page */
        if (event.request.destination === 'document') {
          return caches.match('/index.html');
        }
      });
    })
  );
});

/* ── Push notifications — price alerts ── */
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'TopGoviya.lk';
  const options = {
    body: data.body || 'නව මිල දැනුම්දීමක් | New price alert!',
    icon: '/icon-192x192.png',
    badge: '/icon-96x96.png',
    tag: 'topgoviya-price-alert',
    vibrate: [200, 100, 200],
    data: { url: data.url || '/' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

/* ── Notification click — open app ── */
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});

console.log('[TopGoviya SW v2.2] Service Worker loaded ✅ | topgoviya.lk');
