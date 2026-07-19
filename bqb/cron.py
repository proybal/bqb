import datetime
import time
import os
from dateutil.tz import gettz
from news.views import scrape_news

from django.utils import timezone


def scrape():
        now = datetime.datetime.now(gettz('United States/Denver'))
        print(now.strftime("%A %B %-d, %Y %T %Z"))
        scrape_news()
