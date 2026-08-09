import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bqb.settings")
django.setup()

from news.views import scrape_news

print("Starting scraper debug...")

news = scrape_news()

print(f"Finished. Articles: {len(news)}")