// Service Worker for TRADEX PWA
self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
    // Network-first policy to ensure live real-time pricing
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});