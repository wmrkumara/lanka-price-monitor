/* ===== TopGoviya PWA Service Worker ===== */
/* Version: 1.0 | topgoviya.lk | Built in Gampola 🇱🇰 */

const CACHE_NAME = 'topgoviya-v2';
const DATA_CACHE = 'topgoviya-data-v2';

/* Static files to cache for offline use */
const STATIC_ASSETS = [
  '/lanka-price-monitor/',
  '/lanka-price-monitor/index.html',
  '/lanka-price-monitor/insights.html',
  '/lanka-price-monitor/blog.html',
  '/lanka-price-monitor/about.html',
  '/lanka-price-monitor/privacy.html',
  '/lanka-price-monitor/netherlands-sri-lanka-agriculture.html',
  '/lanka-price-monitor/manifest.json',
  '/lanka-price-monitor/icons/icon-192.png',
  '/lanka-price-monitor/icons/icon-512.png',
  /* Google Fonts — cache for offline */
  'https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+Sinhala:wght@400;500;600&family=Noto+Sans+Tamil:wght@400;500;600&display=swap'
];

/* Install — cache static assets */
self.addEventListener('install', event => {
  console.log('[TopGoviya SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[TopGoviya SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS).catch(err => {
        console.warn('[TopGoviya SW] Some assets failed to cache:', err);
      });
    })
  );
  self.skipWaiting();
});

/* Activate — clean old caches */
self.addEventListener('activate', event => {
  console.log('[TopGoviya SW] Activating...');
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

/* Fetch — Network first for data, cache first for static */
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  /* data.json — always try network first (fresh prices!) */
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

  /* Open-Meteo weather API — network only */
  if (url.hostname.includes('open-meteo.com')) {
    event.respondWith(fetch(event.request).catch(() => new Response('{}', {headers: {'Content-Type': 'application/json'}})));
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
        /* Offline fallback */
        if (event.request.destination === 'document') {
          return caches.match('/lanka-price-monitor/index.html');
        }
      });
    })
  );
});

/* Push notifications — price alerts */
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'TopGoviya.lk';
  const options = {
    body: data.body || 'නව මිල දැනුම්දීමක්!',
    icon: '/lanka-price-monitor/icons/icon-192.png',
    badge: '/lanka-price-monitor/icons/icon-72.png',
    tag: 'topgoviya-price-alert',
    data: { url: data.url || '/lanka-price-monitor/' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

/* Notification click — open app */
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/lanka-price-monitor/')
  );
});

console.log('[TopGoviya SW] Service Worker loaded ✅');
