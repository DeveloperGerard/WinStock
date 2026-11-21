const STATIC_CACHE_NAME = 'winstock-static-v8';
const PAGES_CACHE_NAME = 'winstock-pages-v4';
const OFFLINE_URL = '/static/pwa/offline.html';
const SNAPSHOT_PAGES = [
  ['/', '/alimentos/?offline_snapshot=1'],
  ['/alimentos/', '/alimentos/?offline_snapshot=1'],
  ['/alimentos/stock/', '/alimentos/stock/?offline_snapshot=1'],
  ['/cuentas/', '/cuentas/?offline_snapshot=1'],
  ['/insumos/', '/insumos/?offline_snapshot=1'],
  ['/ganado/lotes/', '/ganado/lotes/?offline_snapshot=1'],
  ['/raciones/', '/raciones/?offline_snapshot=1'],
  ['/reportes/', '/reportes/?offline_snapshot=1']
];
const ALLOWED_PAGE_PATHS = new Set(SNAPSHOT_PAGES.map(([path]) => path));
const CURRENT_CACHE_NAMES = new Set([STATIC_CACHE_NAME, PAGES_CACHE_NAME]);
const STATIC_ASSETS = [
  OFFLINE_URL,
  '/static/style.css',
  '/static/alimentos/alimentos.css',
  '/static/cuentas.css',
  '/static/insumos.css',
  '/static/crear_insumo.css',
  '/static/raciones/style.css',
  '/static/reportes/reportes.css',
  '/static/pwa/icon-192.png',
  '/static/pwa/icon-512.png'
];

// ---------------------------------------------------------------------------
// Instalación / activación
// ---------------------------------------------------------------------------

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      // addAll() es "todo o nada": si un solo archivo daba 404 el SW no se
      // instalaba. Con allSettled un archivo que falla no tumba todo.
      .then((cache) => Promise.allSettled(
        STATIC_ASSETS.map((asset) => cache.add(asset))
      ))
      .then((results) => {
        results.forEach((result, index) => {
          if (result.status === 'rejected') {
            console.warn('No se pudo precargar', STATIC_ASSETS[index], result.reason);
          }
        });
      })
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

// ---------------------------------------------------------------------------
// Mensajes desde las páginas
// ---------------------------------------------------------------------------

self.addEventListener('message', (event) => {
  if (!event.data) return;

  if (event.data.type === 'CLEAR_PAGES') {
    event.waitUntil(
      caches.delete(PAGES_CACHE_NAME).then(() => {
        if (event.ports[0]) {
          event.ports[0].postMessage({ type: 'PAGES_CLEARED' });
        }
      })
    );
    return;
  }

  // La página (con sesión iniciada) pide guardar las páginas de consulta,
  // así no hace falta haberlas visitado una por una antes de quedar offline.
  if (event.data.type === 'WARM_PAGES') {
    event.waitUntil(
      warmPages().catch((error) => {
        console.warn('No se pudieron precalentar las páginas:', error);
      })
    );
  }
});

// ---------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------

function isAllowedPage(url) {
  return url.search === '' && ALLOWED_PAGE_PATHS.has(canonicalPagePath(url.pathname));
}

function canonicalPagePath(path) {
  const withSlash = path.endsWith('/') ? path : `${path}/`;
  return ALLOWED_PAGE_PATHS.has(withSlash) ? withSlash : path;
}

function pageCacheKey(url) {
  return new Request(new URL(canonicalPagePath(url.pathname), url.origin));
}

// Una redirección en una navegación llega como "opaqueredirect" (status 0,
// ok=false, redirected=false). No es un error de red: hay que devolverla tal
// cual para que el navegador la siga (por ejemplo, hacia el login).
function isRedirect(response) {
  return response.type === 'opaqueredirect' || response.redirected;
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

// Cada ruta se guarda con su variante de lectura, sin formularios ni tokens CSRF.
async function fetchPageToStore(url) {
  const snapshotPage = SNAPSHOT_PAGES.find(
    ([path]) => path === canonicalPagePath(url.pathname)
  );
  if (!snapshotPage) return null;
  const snapshot = await fetch(new URL(snapshotPage[1], url.origin), {
    credentials: 'same-origin'
  });
  if (!snapshot.ok || isRedirect(snapshot)) return null;
  return snapshot;
}

async function saveAllowedPage(response, url) {
  const toStore = await fetchPageToStore(url);
  if (!toStore) return;
  const pages = await caches.open(PAGES_CACHE_NAME);
  await pages.put(pageCacheKey(url), toStore);
}

async function warmPages() {
  const pages = await caches.open(PAGES_CACHE_NAME);
  for (const [key, source] of SNAPSHOT_PAGES) {
    try {
      const response = await fetch(new URL(source, self.location.origin), {
        credentials: 'same-origin'
      });
      // Si redirige (sin sesión) o falla, no se guarda nada.
      if (!response.ok || isRedirect(response)) continue;
      await pages.put(
        new Request(new URL(key, self.location.origin)),
        response
      );
    } catch (error) {
      console.warn(`No se pudo precalentar ${key}:`, error);
    }
  }
}

// ---------------------------------------------------------------------------
// Navegaciones (páginas HTML)
// ---------------------------------------------------------------------------

async function handleNavigation(request, event) {
  const url = new URL(request.url);
  const allowedPage = isAllowedPage(url);
  let response;

  try {
    response = await fetch(request);
  } catch (error) {
    // Sin red de verdad: copia guardada u offline.html.
    return offlineFallback(url, allowedPage);
  }

  // Redirección (p. ej. sin sesión -> login): NO es "sin conexión".
  if (isRedirect(response)) return response;

  if (!response.ok) {
    // Solo los errores del servidor (5xx) caen a la copia guardada.
    // 403/404 se muestran tal cual.
    return (allowedPage && response.status >= 500)
      ? offlineFallback(url, true)
      : response;
  }

  if (allowedPage) {
    event.waitUntil(
      saveAllowedPage(response, url).catch((error) => {
        console.error('No se pudo guardar la página de consulta:', error);
      })
    );
  }

  return response;
}

// ---------------------------------------------------------------------------
// Archivos estáticos: stale-while-revalidate
// Sirve la copia guardada al instante y la actualiza en segundo plano, así un
// cambio de CSS llega en la visita siguiente sin tener que subir la versión.
// ---------------------------------------------------------------------------

async function handleStatic(request, event) {
  const cache = await caches.open(STATIC_CACHE_NAME);
  const cached = await cache.match(request);

  const network = fetch(request).then((response) => {
    if (response.ok && response.status === 200) {
      cache.put(request, response.clone()).catch(() => {});
    }
    return response;
  });

  if (cached) {
    event.waitUntil(network.catch(() => {}));
    return cached;
  }

  try {
    return await network;
  } catch (error) {
    return new Response('', { status: 503, statusText: 'Sin conexión' });
  }
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  // /ping/ (y cualquier otra ruta que no sea navegación ni /static/) pasa
  // directo a la red, sin que el SW la toque.
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigation(request, event));
    return;
  }

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(handleStatic(request, event));
  }
});