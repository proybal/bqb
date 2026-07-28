/* jshint esversion: 11, worker: true */
/* jshint -W097 */
/* global caches, Promise */

const STATIC_CACHE = "burquebro-static-v3";
const CONTENT_CACHE = "burquebro-content-v3";

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
 * Download a current compact headline list and save it.
 *
 * A failed refresh does not remove the previously cached copy.
 */
function refreshOfflineNews() {
    return fetch(
        OFFLINE_NEWS_URL,
        {
            cache: "no-store",
            credentials: "same-origin"
        }
    ).then(response => {
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


self.addEventListener("fetch", event => {
    const request = event.request;

    if (request.method !== "GET") {
        return;
    }

    /*
     * Every online page visit refreshes the compact headline list
     * in the background.
     */
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

    /*
     * Serve local static assets from the cache when available.
     * External article images are not cached.
     */
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