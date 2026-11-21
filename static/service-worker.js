const STATIC_CACHE_NAME = 'winstock-static-v5';
const PAGES_CACHE_NAME = 'winstock-pages-v1';
const OFFLINE_URL = '/static/pwa/offline.html';
const ALLOWED_PAGE_PATHS = new Set([
  '/',
  '/alimentos/',
  '/alimentos/stock/'
]);
const CURRENT_CACHE_NAMES = new Set([STATIC_CACHE_NAME, PAGES_CACHE_NAME]);
const STATIC_ASSETS = [
  OFFLINE_URL,
  '/static/style.css',
  '/static/alimentos/alimentos.css',
  '/static/pwa/icon-192.png',
  '/static/pwa/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => !CURRENT_CACHE_NAMES.has(key))
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', (event) => {
  if (!event.data || event.data.type !== 'CLEAR_PAGES') return;

  event.waitUntil(
    caches.delete(PAGES_CACHE_NAME).then(() => {
      if (event.ports[0]) {
        event.ports[0].postMessage({ type: 'PAGES_CLEARED' });
      }
    })
  );
});

function isAllowedPage(url) {
  return url.search === '' && ALLOWED_PAGE_PATHS.has(url.pathname);
}

function pageCacheKey(url) {
  return new Request(new URL(url.pathname, url.origin));
}

async function offlineFallback(url, allowedPage) {
  if (allowedPage) {
    const pages = await caches.open(PAGES_CACHE_NAME);
    const savedPage = await pages.match(pageCacheKey(url));
    if (savedPage) return savedPage;
  }

  const staticCache = await caches.open(STATIC_CACHE_NAME);
  const offlinePage = await staticCache.match(OFFLINE_URL);
  if (offlinePage) return offlinePage;

  return new Response('La página sin conexión no está disponible.', {
    status: 503,
    headers: { 'Content-Type': 'text/plain; charset=utf-8' }
  });
}

async function saveAllowedPage(request, response, url) {
  const pages = await caches.open(PAGES_CACHE_NAME);
  let pageToSave = response.clone();

  if (url.pathname === '/alimentos/') {
    const snapshotUrl = new URL(request.url);
    snapshotUrl.searchParams.set('offline_snapshot', '1');
    pageToSave = await fetch(snapshotUrl, { credentials: 'same-origin' });
    if (!pageToSave.ok || pageToSave.redirected) return;
  }

  await pages.put(pageCacheKey(url), pageToSave);
}

async function handleNavigation(request, event) {
  const url = new URL(request.url);
  const allowedPage = isAllowedPage(url);
  let response;

  try {
    response = await fetch(request);
  } catch (error) {
    return offlineFallback(url, allowedPage);
  }

  if (response.redirected) return response;
  if (!response.ok) {
    return allowedPage ? offlineFallback(url, true) : response;
  }

  if (allowedPage) {
    event.waitUntil(
      saveAllowedPage(request, response, url).catch((error) => {
        console.error('No se pudo guardar la página de consulta:', error);
      })
    );
  }

  return response;
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(handleNavigation(request, event));
    return;
  }

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.open(STATIC_CACHE_NAME).then((cache) =>
        cache.match(request).then((cached) => {
          if (cached) return cached;

          return fetch(request).then((response) => {
            if (response.ok) {
              event.waitUntil(cache.put(request, response.clone()));
            }
            return response;
          });
        })
      )
    );
  }
});
