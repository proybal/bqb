from django.core.management.base import BaseCommand

from news.push import send_push_to_all


class Command(BaseCommand):
    help = "Send a test push notification to active subscribers."

    def handle(self, *args, **options):
        sent, failed = send_push_to_all(
            title="BurqueBro",
            body="This is a test notification.",
            url="/news/",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Push test completed: {sent} sent, {failed} failed."
            )
        )