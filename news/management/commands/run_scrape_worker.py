import time
import traceback

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from news.models import ScrapeJob


class Command(BaseCommand):
    help = "Run the BurqueBro scrape-job worker outside Gunicorn."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Process at most one job and exit.")
        parser.add_argument("--poll", type=int, default=5, help="Seconds between queue checks.")

    def handle(self, *args, **options):
        while True:
            job = self.claim_job()
            if job is None:
                if options["once"]:
                    return
                time.sleep(max(options["poll"], 1))
                continue

            self.run_job(job)
            if options["once"]:
                return

    @staticmethod
    def claim_job():
        with transaction.atomic():
            job = (
                ScrapeJob.objects.select_for_update()
                .filter(status=ScrapeJob.STATUS_QUEUED)
                .order_by("created_at")
                .first()
            )
            if job is None:
                return None
            job.status = ScrapeJob.STATUS_RUNNING
            job.started_at = timezone.now()
            job.message = ""
            job.save(update_fields=("status", "started_at", "message"))
            return job

    def run_job(self, job):
        try:
            # Imported here so the worker—not Gunicorn—loads and executes scraper code.
            from news.views import scrape_news

            articles = scrape_news() or []
            job.status = ScrapeJob.STATUS_SUCCEEDED
            job.article_count = len(articles)
            job.message = f"Completed with {len(articles)} articles."
            self.stdout.write(self.style.SUCCESS(f"Job {job.pk}: {job.message}"))
        except Exception:
            job.status = ScrapeJob.STATUS_FAILED
            job.message = traceback.format_exc()[-8000:]
            self.stderr.write(self.style.ERROR(f"Job {job.pk} failed.\n{job.message}"))
        finally:
            job.finished_at = timezone.now()
            job.save(update_fields=("status", "article_count", "message", "finished_at"))
