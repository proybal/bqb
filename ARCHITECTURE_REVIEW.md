# BurqueBro Architecture Review and Phase 1 Refactor

## What Phase 1 changes

The web request no longer executes every scraper. The **Update News** link now creates a `ScrapeJob` database record and returns immediately. A separate systemd worker claims queued jobs and runs `scrape_news()` outside Gunicorn.

This directly fixes the Gunicorn timeout/worker-abort problem while preserving the existing scraper functions and `news.json` output.

## New execution flow

```text
Browser Update News link ──> Django creates ScrapeJob ──> immediate redirect
                                      │
Hourly cron ──────────────────────────┘
                                      │
                                      ▼
                       burquebro-scrape-worker.service
                                      │
                                      ▼
                              scrape_news()
                                      │
                                      ▼
                                 news.json
```

Only one worker should run while SQLite remains the database.

## Files added or changed

- `news/models.py`: adds `ScrapeJob`.
- `news/migrations/0004_scrapejob.py`: creates the queue table.
- `news/views.py`: `news_update` now queues a job; hard-coded Paramiko credentials and SFTP upload are removed.
- `news/management/commands/run_scrape_worker.py`: persistent queue worker.
- `news/management/commands/enqueue_news_update.py`: CLI/cron job submission.
- `bqb/cron.py`: queues instead of running the scraper in-process.
- `news/admin.py`: job visibility in Django admin.
- `deploy/burquebro-scrape-worker.service`: systemd unit template.

## Install Phase 1

From the project directory on the VPS:

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py check
```

As root:

```bash
cp deploy/burquebro-scrape-worker.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now burquebro-scrape-worker
systemctl status burquebro-scrape-worker --no-pager
```

Test the queue:

```bash
sudo -u burquebr bash -lc '
cd /home/burquebr/public_html/bqb
source .venv/bin/activate
python manage.py enqueue_news_update --source manual
'

journalctl -u burquebro-scrape-worker -f -l
```

The existing `django-crontab` entry can remain temporarily because `bqb.cron.scrape` now only creates a job. A normal OS cron entry is preferable long term:

```cron
0 * * * * cd /home/burquebr/public_html/bqb && /home/burquebr/public_html/bqb/.venv/bin/python manage.py enqueue_news_update --source cron
```

## Critical findings still to address

1. **Secrets are committed in `settings.py`.** Rotate the Django secret key and email password, then load them from environment variables. The ZIP contained live-looking credentials, so treat them as exposed.
2. **`DEBUG=True` in production.** Move this to an environment variable and use `False` on the VPS.
3. **Scrapers are nested inside `news/views.py`.** Move them into `news/scrapers/` in Phase 2. The worker currently imports `scrape_news` from views only to minimize risk during this first change.
4. **Dynamic dispatch uses `eval()`.** Replace it with an explicit function registry.
5. **`requirements.txt` contains desktop and packaging dependencies.** PyQt, pygame, pandas, PyInstaller-related packages, and Windows packages should not deploy to the VPS. It also pins versions that conflict with Celery.
6. **`news.json` is a shared mutable file.** Write to a temporary file and use `os.replace()` for an atomic swap so readers never see partial JSON.
7. **Relative file paths are used for logs and JSON.** Resolve paths from `settings.BASE_DIR`; systemd and cron can otherwise write into unexpected working directories.
8. **Error handling is inconsistent.** Every source should return a structured result and one source failure must never abort the whole run.
9. **HTTP behavior needs centralization.** Use one `requests.Session`, connect/read timeouts, retries for transient errors, and a current User-Agent.
10. **SQLite needs a single writer.** Keep worker concurrency at one. PostgreSQL becomes appropriate if jobs, articles, or editors grow.

## Recommended Phase 2 structure

```text
news/
  services/
    article_store.py
    scrape_runner.py
  scrapers/
    __init__.py
    abqjournal.py
    artesia.py
    koat.py
    ...
  management/commands/
    enqueue_news_update.py
    run_scrape_worker.py
```

Each scraper should expose a consistent callable:

```python
def scrape(source, client) -> list[dict]:
    ...
```

The runner should use a registry rather than `eval`:

```python
SCRAPERS = {
    "abqjournal": abqjournal.scrape,
    "artesia_news": artesia.scrape,
}
```

## Deployment note

The GitHub Action can deploy code and run migrations as `burquebr`, but the Bluehost jailed shell cannot restart root-owned services with `sudo`. Continue the manual root restart, or add a root-side deployment mechanism. The new scrape worker also needs restarting after worker-code changes.
