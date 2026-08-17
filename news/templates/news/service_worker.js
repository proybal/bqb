/* jshint esversion: 11, worker: true */
/* jshint -W097 */
/* global caches, clients, Promise */

const STATIC_CACHE = "burquebro-static-v6";
const CONTENT_CACHE = "burquebro-content-v7";

const OFFLINE_URL = "/offline/";
const OFFLINE_NEWS_URL = "/offline-news/";

const STATIC_FILES = [
    OFFLINE_URL,
    "/static/news/pwa/icon-192.png",
    "/static/news/pwa/icon-512.png",
    "/static/news/pwa/maskable-icon-512.png",
    "/static/news/pwa/apple-touch-icon.png",
    "/static/news/pwa/favicon-32.png",
    "/static/news/pwa/favicon-16.png"
];


/*
 * Download the latest compact offline-news page and cache it.
 *
 * If the request fails, the previous cached copy remains available.
 */
function refreshOfflineNews() {
    return fetch(OFFLINE_NEWS_URL, {
        cache: "no-store",
        credentials: "same-origin"
    }).then(response => {
        if (!response.ok) {
            throw new Error(
                "Offline news request failed: " + response.status
            );
        }

        return caches.open(CONTENT_CACHE).then(cache => {
            return cache.put(
                OFFLINE_NEWS_URL,
                response.clone()
            );
        });
    });
}


/*
 * Install
 *
 * Cache core PWA files and attempt to cache the latest compact
 * offline-news page.
 */
self.addEventListener("install", event => {
    event.waitUntil(
        caches
            .open(STATIC_CACHE)
            .then(cache => cache.addAll(STATIC_FILES))
            .then(() => {
                return refreshOfflineNews().catch(error => {
                    console.warn(
                        "Initial offline-news download failed:",
                        error
                    );
                });
            })
            .then(() => self.skipWaiting())
    );
});


/*
 * Activate
 *
 * Remove older BurqueBro caches and immediately take control
 * of open pages.
 */
self.addEventListener("activate", event => {
    const currentCaches = [
        STATIC_CACHE,
        CONTENT_CACHE
    ];

    event.waitUntil(
        caches
            .keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(cacheName => {
                            return (
                                cacheName.startsWith("burquebro-") &&
                                !currentCaches.includes(cacheName)
                            );
                        })
                        .map(cacheName => caches.delete(cacheName))
                );
            })
            .then(() => self.clients.claim())
    );
});


/*
 * Fetch
 *
 * Navigation requests:
 * - Try the network first.
 * - Refresh the compact offline-news page in the background.
 * - If offline, show the cached compact news page.
 * - If unavailable, show the basic offline page.
 *
 * Local static assets:
 * - Use the cache first.
 * - Fall back to the network.
 *
 * External article images are not cached.
 */
self.addEventListener("fetch", event => {
    const request = event.request;

    if (request.method !== "GET") {
        return;
    }

    if (request.mode === "navigate") {
        event.waitUntil(
            refreshOfflineNews().catch(error => {
                console.warn(
                    "Offline-news refresh failed:",
                    error
                );
            })
        );

        event.respondWith(
            fetch(request).catch(() => {
                return caches
                    .match(OFFLINE_NEWS_URL)
                    .then(cachedNews => {
                        if (cachedNews) {
                            return cachedNews;
                        }

                        return caches.match(OFFLINE_URL);
                    });
            })
        );

        return;
    }

    const requestUrl = new URL(request.url);

    if (
        requestUrl.origin === self.location.origin &&
        requestUrl.pathname.startsWith("/static/")
    ) {
        event.respondWith(
            caches.match(request).then(cachedResponse => {
                return cachedResponse || fetch(request);
            })
        );
    }
});


/*
 * Push notifications
 */
self.addEventListener("push", event => {
    const notificationData = {
        title: "BurqueBro",
        body: "You have a new notification.",
        url: "/news/",
        icon: "/static/news/pwa/icon-192.png",
        badge: "/static/news/pwa/icon-192.png"
    };

    if (event.data) {
        try {
            const incomingData = event.data.json();

            Object.assign(
                notificationData,
                incomingData
            );
        } catch (error) {
            notificationData.body = event.data.text();
        }
    }

    event.waitUntil(
        self.registration.showNotification(
            notificationData.title,
            {
                body: notificationData.body,
                icon: notificationData.icon,
                badge: notificationData.badge,
                data: {
                    url: notificationData.url
                }
            }
        )
    );
});


/*
 * Notification clicks
 *
 * Focus an existing BurqueBro window when possible.
 * Otherwise, open a new window.
 */
self.addEventListener("notificationclick", event => {
    event.notification.close();

    let targetUrl = "/news/";

    if (
        event.notification.data &&
        event.notification.data.url
    ) {
        targetUrl = event.notification.data.url;
    }

    event.waitUntil(
        clients
            .matchAll({
                type: "window",
                includeUncontrolled: true
            })
            .then(clientList => {
                for (const client of clientList) {
                    if (
                        client.url === targetUrl &&
                        "focus" in client
                    ) {
                        return client.focus();
                    }
                }

                if (clients.openWindow) {
                    return clients.openWindow(targetUrl);
                }

                return null;
            })
    );
});