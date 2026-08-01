/* jshint esversion: 11, browser: true */
/* global Notification, navigator, fetch, document, console */

function getCookie(name) {
    const cookieValue = document.cookie
        .split(";")
        .map(cookie => cookie.trim())
        .find(cookie => cookie.startsWith(name + "="));

    if (!cookieValue) {
        return null;
    }

    return decodeURIComponent(
        cookieValue.substring(name.length + 1)
    );
}


function urlBase64ToUint8Array(base64String) {
    const padding =
        "=".repeat((4 - base64String.length % 4) % 4);

    const base64 = (
        base64String + padding
    )
        .replace(/-/g, "+")
        .replace(/_/g, "/");

    const rawData = window.atob(base64);

    return Uint8Array.from(
        Array.from(rawData).map(character => {
            return character.charCodeAt(0);
        })
    );
}


async function getVapidPublicKey() {
    const response = await fetch(
        "/news/push/vapid-key/",
        {
            credentials: "same-origin"
        }
    );

    if (!response.ok) {
        throw new Error(
            "Could not retrieve VAPID key: " +
            response.status
        );
    }

    const data = await response.json();

    return data.publicKey;
}


async function saveSubscription(subscription) {
    const response = await fetch(
        "/news/push/subscribe/",
        {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify(
                subscription.toJSON()
            )
        }
    );

    if (!response.ok) {
        throw new Error(
            "Could not save push subscription: " +
            response.status
        );
    }

    return response.json();
}


async function subscribeToPush() {
    if (!("serviceWorker" in navigator)) {
        throw new Error(
            "Service workers are not supported."
        );
    }

    if (!("PushManager" in window)) {
        throw new Error(
            "Push notifications are not supported."
        );
    }

    const permission =
        await Notification.requestPermission();

    if (permission !== "granted") {
        throw new Error(
            "Notification permission was not granted."
        );
    }

    const registration =
        await navigator.serviceWorker.ready;

    let subscription =
        await registration.pushManager.getSubscription();

    if (!subscription) {
        const publicKey =
            await getVapidPublicKey();

        subscription =
            await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey:
                    urlBase64ToUint8Array(publicKey)
            });
    }

    await saveSubscription(subscription);

    return subscription;
}


document.addEventListener("DOMContentLoaded", async () => {
    const pushButton =
        document.getElementById("pushToggle");

    if (!pushButton) {
        return;
    }

    if (
        !("serviceWorker" in navigator) ||
        !("PushManager" in window) ||
        !("Notification" in window)
    ) {
        return;
    }

    pushButton.style.display = "inline-block";

    try {
        const registration =
            await navigator.serviceWorker.ready;

        const existingSubscription =
            await registration.pushManager.getSubscription();

        if (existingSubscription) {
            pushButton.textContent =
                "🔔 Notifications Enabled";

            pushButton.disabled = true;
        }
    } catch (error) {
        console.error(
            "Could not check push subscription:",
            error
        );
    }

    pushButton.addEventListener("click", async () => {
        pushButton.disabled = true;

        try {
            await subscribeToPush();

            pushButton.textContent =
                "🔔 Notifications Enabled";
        } catch (error) {
            console.error(error);

            pushButton.textContent =
                "⚠ Could Not Enable Notifications";

            pushButton.disabled = false;
        }
    });
});