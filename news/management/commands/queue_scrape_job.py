from django.core.management.base import BaseCommand

from news.models import ScrapeJob


class Command(BaseCommand):
    help = "Queue a news scrape job unless one is already queued or running."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default="cron",
            help="Source recorded on the ScrapeJob.",
        )

    def handle(self, *args, **options):
        active_job = ScrapeJob.objects.filter(
            status__in=(
                ScrapeJob.STATUS_QUEUED,
                ScrapeJob.STATUS_RUNNING,
            )
        ).first()

        if active_job:
            self.stdout.write(
                f"Job {active_job.pk} is already {active_job.status}; no new job queued."
            )
            return

        job = ScrapeJob.objects.create(source=options["source"])

        self.stdout.write(
            self.style.SUCCESS(f"Queued scrape job {job.pk}.")
        )