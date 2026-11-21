//Donde se guarda la cache:
const CACHE_NAME = 'winstock-static-v4';
//Direcion de pagina sin conexion
const OFFLINE_URL = '/static/pwa/offline.html';
//Lista de cosas que se guardan en la cache antes de quedar sin conexion
const STATIC_ASSETS = [
  OFFLINE_URL,
  '/static/style.css',
  '/static/pwa/icon-192.png',
  '/static/pwa/icon-512.png'
];

//Evento que se dispara una sola vez abre el cache--> guarda datos 
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

//Empieza a trabajar --> Revisa cache --> Elimina cache desactualizada(basura)
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

//Trabajo diario 
// if metho != get  (ignorar) ejem-->(post,formularios)
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  //Va a internet a buscar la pagina --> si falla(no internet) --> (busca en cache)--> se muestra
  // Las páginas dinámicas y los datos privados nunca se guardan en caché.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  // Solo recursos estáticos: caché primero y red como alternativa.
  //Mira lo guardado en la cache--> lo entrega de inmediatio sin internet
  //Si no lo tiene--> va  a internet --> realiza una copia
  //Entrega archivo original de la app

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return response;
        });
      })
    );
  }
});
