self.addEventListener('push', function(event) {
    const options = {
        body: event.data.text(),
        icon: '/static/images/logo.png',
        badge: '/static/images/badge.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'View Details',
                icon: '/static/images/checkmark.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/images/xmark.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Anti-Doping Education', options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    if (event.action === 'explore') {
        // Open the app when notification is clicked
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open('anti-doping-v1').then(function(cache) {
            return cache.addAll([
                '/',
                '/static/css/style.css',
                '/static/js/main.js',
                '/static/images/logo.png',
                '/static/images/badge.png',
                '/static/images/checkmark.png',
                '/static/images/xmark.png'
            ]);
        })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
            return response || fetch(event.request);
        })
    );
});
