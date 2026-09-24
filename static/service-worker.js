/**
 * Service Worker - نظام إدارة وتتبع الأعطال التقنية
 * White Nile University IT Fault Management System
 */

const CACHE_NAME = 'it-fault-system-v2';
const STATIC_ASSETS = [
    '/',
    '/static/manifest.json',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/static/icons/apple-touch-icon.png',
    '/static/icons/favicon.png',
    '/static/images/logo.png',
    '/offline',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js'
];

// 1. تثبيت Service Worker وحفظ الأصول الأساسية في الكاش
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[PWA Service Worker] Caching core static assets');
            return cache.addAll(STATIC_ASSETS).catch((err) => {
                console.warn('[PWA Service Worker] Non-critical asset cache skip:', err);
            });
        })
    );
    self.skipWaiting();
});

// 2. تفعيل وتنظيف الكاش القديم عند التحديث
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('[PWA Service Worker] Removing old cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    return self.clients.claim();
});

// 3. اعتراض واستجابة الطلبات (Fetch Handler)
self.addEventListener('fetch', (event) => {
    // تجاهل الطلبات غير الـ GET أو طلبات الـ API الحساسة
    if (event.request.method !== 'GET') return;
    
    const url = new URL(event.request.url);

    // استراتيجية 1: Cache-First للصور والخطوط والأصول الثابتة
    if (
        url.pathname.startsWith('/static/') ||
        url.hostname.includes('fonts.googleapis.com') ||
        url.hostname.includes('fonts.gstatic.com') ||
        url.hostname.includes('cdn.jsdelivr.net')
    ) {
        event.respondWith(
            caches.match(event.request).then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(event.request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const responseToCache = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, responseToCache);
                        });
                    }
                    return networkResponse;
                });
            })
        );
        return;
    }

    // استراتيجية 2: Network-First للصفحات والمحتوى المتغير مع Fallback لصفحة Offline
    event.respondWith(
        fetch(event.request)
            .then((networkResponse) => {
                // إذا تم بنجاح وكان استجابة عادية، نحفظ نسخة بالكاش
                if (networkResponse && networkResponse.status === 200 && event.request.url.startsWith(self.location.origin)) {
                    // لا نخزن مسارات التحميل أو العمليات الديناميكية الحساسة
                    if (!url.pathname.includes('/logout') && !url.pathname.includes('/api/')) {
                        const responseToCache = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, responseToCache);
                        });
                    }
                }
                return networkResponse;
            })
            .catch(() => {
                // عند فقدان الاتصال بالإنترنت
                return caches.match(event.request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // إذا كان الطلب صفحة HTML نعرض صفحة Offline المخصصة
                    if (event.request.headers.get('accept') && event.request.headers.get('accept').includes('text/html')) {
                        return caches.match('/offline');
                    }
                });
            })
    );
});
