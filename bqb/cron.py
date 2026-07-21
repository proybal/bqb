from news.models import ScrapeJob


def scrape():
    """Queue the hourly scrape; a separate worker executes it."""
    active = ScrapeJob.objects.filter(
        status__in=(ScrapeJob.STATUS_QUEUED, ScrapeJob.STATUS_RUNNING)
    ).exists()
    if not active:
        ScrapeJob.objects.create(source="cron")
