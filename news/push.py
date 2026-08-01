import json
import logging

from django.conf import settings
from pywebpush import WebPushException, webpush

from .models import PushSubscription


logger = logging.getLogger(__name__)


def send_push_notification(
    subscription,
    title,
    body,
    url="/news/",
):
    payload = {
        "title": title,
        "body": body,
        "url": url,
    }

    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth,
        },
    }

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": settings.VAPID_ADMIN_EMAIL,
            },
        )

        return True

    except WebPushException as exc:
        logger.exception(
            "Push notification failed for subscription %s",
            subscription.pk,
        )

        response = getattr(exc, "response", None)

        if response is not None and response.status_code in (404, 410):
            subscription.is_active = False
            subscription.save(update_fields=["is_active"])

        return False


def send_push_to_all(title, body, url="/news/"):
    subscriptions = PushSubscription.objects.filter(
        is_active=True,
    )

    sent = 0
    failed = 0

    for subscription in subscriptions:
        if send_push_notification(
            subscription=subscription,
            title=title,
            body=body,
            url=url,
        ):
            sent += 1
        else:
            failed += 1

    return sent, failed