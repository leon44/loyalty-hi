// Service Worker for PWA with offline loyalty card support
const CACHE_NAME = 'loyalty-hi-v2';
const STATIC_CACHE = 'loyalty-static-v2';
const DYNAMIC_CACHE = 'loyalty-dynamic-v2';

const staticAssets = [
  '/',
  '/static/style.css',
  '/static/images/logo.png'
];

// Install event - cache static resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(staticAssets))
  );
  self.skipWaiting();
});

// Fetch event - network first for dashboard, cache for static assets
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // For dashboard/main pages - network first, cache as fallback
  if (url.pathname === '/' || url.pathname === '/dashboard') {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Clone the response
          const responseClone = response.clone();
          
          // Cache the fresh response for offline use
          caches.open(DYNAMIC_CACHE)
            .then(cache => cache.put(request, responseClone));
          
          return response;
        })
        .catch(() => {
          // If network fails, try cache
          return caches.match(request)
            .then(cachedResponse => {
              if (cachedResponse) {
                return cachedResponse;
              }
              // If no cache, return offline page or error
              return new Response('Offline - Please check your connection', {
                status: 503,
                statusText: 'Service Unavailable'
              });
            });
        })
    );
  }
  // For static assets - cache first
  else if (request.url.includes('/static/')) {
    event.respondWith(
      caches.match(request)
        .then(cachedResponse => {
          if (cachedResponse) {
            return cachedResponse;
          }
          return fetch(request)
            .then(response => {
              const responseClone = response.clone();
              caches.open(STATIC_CACHE)
                .then(cache => cache.put(request, responseClone));
              return response;
            });
        })
    );
  }
  // For everything else - network first
  else {
    event.respondWith(
      fetch(request)
        .catch(() => caches.match(request))
    );
  }
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== STATIC_CACHE && 
              cacheName !== DYNAMIC_CACHE) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});
