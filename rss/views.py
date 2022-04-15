# rss\views.py
from django.shortcuts import render


import feedparser

def rss(request):
    feed = feedparser.parse("https://www.abqjournal.com/feed")
    feed2 = feedparser.parse("https://www.news.yahoo.com/rss")
    # feed.update(feed2)

    print(feed.values())
    return render(request, 'rss/index.html', {'feed': feed})
