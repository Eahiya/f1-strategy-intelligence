/**
 * F1 Strategy Platform v4.0 - Service Worker
 * Provides offline support and caching strategies for PWA functionality
 */

const CACHE_NAME = 'f1-strategy-v4.0';
const STATIC_CACHE = `${CACHE_NAME}-static`;
const API_CACHE = `${CACHE_NAME}-api`;
const IMAGE_CACHE = `${CACHE_NAME}-images`;

// Assets to cache immediately on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/static/js/main.js',
  '/static/css/main.css',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// API endpoints that can be cached
const CACHEABLE_API_ROUTES = [
  '/circuits',
  '/tires'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[ServiceWorker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[ServiceWorker] Skip waiting');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[ServiceWorker] Install failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              return cacheName.startsWith(CACHE_NAME) && 
                     ![STATIC_CACHE, API_CACHE, IMAGE_CACHE].includes(cacheName);
            })
            .map((cacheName) => {
              console.log('[ServiceWorker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('[ServiceWorker] Claiming clients');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other non-http requests
  if (!url.protocol.includes('http')) {
    return;
  }
  
  // Handle API requests
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/auth/')) {
    event.respondWith(handleAPIRequest(request));
    return;
  }
  
  // Handle image requests
  if (request.destination === 'image') {
    event.respondWith(handleImageRequest(request));
    return;
  }
  
  // Handle static assets
  event.respondWith(handleStaticRequest(request));
});

// Cache strategies
async function handleStaticRequest(request) {
  const cache = await caches.open(STATIC_CACHE);
  
  // Try cache first
  const cached = await cache.match(request);
  if (cached) {
    // Return cached response and update in background
    fetch(request)
      .then((response) => {
        if (response.ok) {
          cache.put(request, response.clone());
        }
      })
      .catch(() => {}); // Ignore network errors for background update
    
    return cached;
  }
  
  // Fetch from network
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // Return offline fallback for HTML requests
    if (request.headers.get('accept').includes('text/html')) {
      return cache.match('/index.html');
    }
    throw error;
  }
}

async function handleAPIRequest(request) {
  const url = new URL(request.url);
  const isCacheableEndpoint = CACHEABLE_API_ROUTES.some(route => 
    url.pathname.includes(route)
  );
  
  if (!isCacheableEndpoint) {
    return fetch(request);
  }
  
  const cache = await caches.open(API_CACHE);
  
  try {
    // Try network first for API requests
    const response = await fetch(request);
    if (response.ok) {
      // Cache for 1 hour
      const responseToCache = response.clone();
      const headers = new Headers(responseToCache.headers);
      headers.set('sw-cached-at', Date.now().toString());
      
      const modifiedResponse = new Response(responseToCache.body, {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers: headers
      });
      
      cache.put(request, modifiedResponse);
    }
    return response;
  } catch (error) {
    // Fallback to cache if network fails
    const cached = await cache.match(request);
    if (cached) {
      // Check if cache is still valid (less than 1 hour old)
      const cachedAt = cached.headers.get('sw-cached-at');
      const isFresh = cachedAt && (Date.now() - parseInt(cachedAt)) < 3600000;
      
      if (isFresh) {
        return cached;
      }
    }
    
    // Return offline response for API
    return new Response(
      JSON.stringify({ 
        error: 'Offline',
        message: 'You are currently offline. Please check your connection.'
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

async function handleImageRequest(request) {
  const cache = await caches.open(IMAGE_CACHE);
  
  const cached = await cache.match(request);
  if (cached) {
    return cached;
  }
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // Return placeholder for failed image loads
    return new Response('', { status: 404 });
  }
}

// Background sync for offline form submissions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-simulations') {
    event.waitUntil(syncPendingSimulations());
  }
});

async function syncPendingSimulations() {
  // Retrieve pending simulations from IndexedDB and send them
  console.log('[ServiceWorker] Syncing pending simulations');
  // Implementation would use IndexedDB to queue offline requests
}

// Push notifications (optional)
self.addEventListener('push', (event) => {
  const options = {
    body: event.data.text(),
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      url: event.data.url || '/'
    }
  };
  
  event.waitUntil(
    self.registration.showNotification('F1 Strategy', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});

console.log('[ServiceWorker] Registered for F1 Strategy Platform v4.0');
