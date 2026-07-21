from django.core.management.base import BaseCommand
from news.models import ScrapeJob


class Command(BaseCommand):
    help = "Queue a BurqueBro news scrape job."

    def add_arguments(self, parser):
        parser.add_argument("--source", default="cron", choices=("cron", "manual", "web"))

    def handle(self, *args, **options):
        if ScrapeJob.objects.filter(status__in=(ScrapeJob.STATUS_QUEUED, ScrapeJob.STATUS_RUNNING)).exists():
            self.stdout.write(self.style.WARNING("A scrape job is already queued or running."))
            return
        job = ScrapeJob.objects.create(source=options["source"])
        self.stdout.write(self.style.SUCCESS(f"Queued scrape job {job.pk}."))
