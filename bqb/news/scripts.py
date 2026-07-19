import requests
from django.conf import settings
from .models import News
from django.http import HttpResponse


def scrape(e):
    news_list = News.objects.filter(published=True)
    print(e)
    response_html = "<html><body><h1>News Feed Processing Results</h1><ul>"

    for news_source in news_list:
        print(news_source.feed_url)
        try:
            news_request = requests.get(news_source.feed_url, timeout=10)  # Set a timeout for the request
            response_html += f"<li>{news_request.status_code} - {news_request.url}</li>"
        except requests.exceptions.RequestException as ex:
            print(f"Error occurred processing: {news_source.feed_url} Error: {ex}")
            response_html += f"<li>Error processing {news_source.feed_url}: {ex}</li>"

    response_html += "</ul></body></html>"

    return HttpResponse(response_html, content_type="text/html")
