/* jshint esversion: 11, browser: true */
/* jshint -W097 */

(function () {
    const pushToggle = document.getElementById("pushToggle");

    if (!pushToggle) {
        return;
    }

    if (
        !("serviceWorker" in navigator) ||
        !("PushManager" in window) ||
        !("Notification" in window)
    ) {
        console.log("Push notifications are not supported.");
        return;
    }

    function getCookie(name) {
        const cookies = document.cookie ? document.cookie.split(";") : [];

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {
                return decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
            }
        }

        return null;
    }

    function urlBase64ToUint8Array(base64String) {
        const padding = "=".repeat(
            (4 - (base64String.length % 4)) % 4
        );

        const base64 = (
            base64String + padding
        )
            .replace(/-/g, "+")
            .replace(/_/g, "/");

        const rawData = window.atob(base64);

        return Uint8Array.from(
            [...rawData].map(character => {
                return character.charCodeAt(0);
            })
        );
    }

    async function saveSubscription(subscription) {
        const response = await fetch("/push/subscribe/", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify(subscription.toJSON())
        });

        if (!response.ok) {
            throw new Error(
                "Unable to save push subscription."
            );
        }
    }

    async function deleteSubscription(subscription) {
        const response = await fetch("/push/unsubscribe/", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
                endpoint: subscription.endpoint
            })
        });

        if (!response.ok) {
            throw new Error(
                "Unable to remove push subscription."
            );
        }
    }

    function setButtonState(subscription) {
        pushToggle.style.display = "inline-block";

        if (subscription) {
            pushToggle.title = "Disable Notifications";
            pushToggle.setAttribute("aria-label", "Disable Notifications");
            pushToggle.dataset.enabled = "true";
        } else {
            pushToggle.title = "Enable Notifications";
            pushToggle.setAttribute("aria-label", "Enable Notifications");
            pushToggle.dataset.enabled = "false";
        }
    }

    async function enablePush(registration) {
        const permission = await Notification.requestPermission();

        if (permission !== "granted") {
            throw new Error(
                "Notification permission was not granted."
            );
        }

        const keyResponse = await fetch(
            "/push/public-key/",
            {
                credentials: "same-origin"
            }
        );

        if (!keyResponse.ok) {
            throw new Error(
                "Unable to retrieve the push public key."
            );
        }

        const keyData = await keyResponse.json();

        const subscription =
            await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey:
                    urlBase64ToUint8Array(
                        keyData.publicKey
                    )
            });

        await saveSubscription(subscription);
        setButtonState(subscription);
    }

    async function disablePush(subscription) {
        await deleteSubscription(subscription);
        await subscription.unsubscribe();
        setButtonState(null);
    }

    async function initialize() {

        console.log("Initializing push notifications");


        const registration =
            await navigator.serviceWorker.ready;

        const subscription =
            await registration.pushManager.getSubscription();

        setButtonState(subscription);

        pushToggle.addEventListener(
            "click",
            async function () {
                console.log("Notification bell clicked");
                pushToggle.disabled = true;

                try {
                    const currentSubscription =
                        await registration.pushManager
                            .getSubscription();

                    if (currentSubscription) {
                        await disablePush(
                            currentSubscription
                        );
                    } else {
                        await enablePush(registration);
                    }
                } catch (error) {
                    console.error(
                        "Push notification error:",
                        error
                    );

                    window.alert(error.message);
                } finally {
                    pushToggle.disabled = false;
                }
            }
        );
    }

    initialize().catch(error => {
        console.error(
            "Push initialization failed:",
            error
        );
    });
}());