import re

from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
import json
from .models import News


def index(req):
    with open('news.json') as json_file:
        news = json.load(json_file)
    return render(req, 'news/index.html', {'news': news})


def news_update(req):
    ########################################
    # Scrape "Albuquerque Journal" news
    ########################################
    source_url = "https://www.abqjournal.com/category/abqnewsseeker"
    source = News.objects.filter(source=source_url).values()[0]['title']
    thumbnail = News.objects.filter(source=source_url).values()[0]['cover']
    news_r = requests.get(source_url)
    news_soup = BeautifulSoup(news_r.text, 'html5lib')
    news_tags = news_soup.find_all('article', class_='post-card')
    news = []
    for tag in news_tags:
        div_tag = tag.findAll('div', attrs={'class': 'post-card__thumbnail__image'})
        img = ""
        #        url = ""
        date_updated = ""
        if div_tag:
            title_tag = tag.findAll('div', attrs={'class': 'post-card__excerpt', 'span': ''})
            date_tag = tag.findAll('time', attrs={'class': 'entry-date'})
            url_tag = tag.findAll('div', attrs={'class': 'post-card__thumbnail', 'a': ''})
            url = url_tag[0].contents[1].attrs['href']
            body = tag.text
            if date_tag:
                date_published = date_tag[0].attrs
                date_published = date_published['datetime']
                if len(date_tag) > 1:
                    date_updated = date_tag[1].attrs
                    date_updated = date_updated['datetime']
            try:
                title = title_tag[0].text
            except Exception:
                continue
            img = div_tag[0].attrs
            img = img['data-bg']
            img = img[4:len(img) - 1]
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'published': date_published,
                         'updated': date_updated, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)

    ########################################
    # Scrape "The Paper" news
    ########################################
    source = "https://abq.news/category/news/albuquerque/"
    news_r = requests.get(source)
    news_soup = BeautifulSoup(news_r.text, 'html5lib')
    news_tags = news_soup.find_all('article', class_='post')
    for tag in news_tags:
        date_published = ""
        date_updated = ""
        img = ""
        div_tag = tag.findAll('h2', attrs={'class': 'entry-title'})
        title = div_tag[0].text
        title = title.strip()
        div_tag = tag.findAll('a', attrs={'class': 'post-thumbnail-inner'})
        url = div_tag[0].attrs['href']
        img = tag.findAll('amp-img')
        img = img[0].attrs['src']
        img = img[0: img.find('?')]
        date_tag = tag.findAll('time')
        body = tag.text
        body = body.strip()
        if date_tag:
            date_published = date_tag[0].attrs
            date_published = date_published['datetime']
            if len(date_tag) > 1:
                date_updated = date_tag[1].attrs
                date_updated = date_updated['datetime']
        news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body,
                     'published': date_published,
                     'updated': date_updated, 'url': url, 'img': img, 'thumbnail': thumbnail}
        news.append(news_dict)
    news = sorted(news, key=lambda d: d['published'])[::-1]
    with open("news.json", "w") as outfile:
        json.dump(news, outfile, indent=4)
    return render(req, 'news/index.html', {'news': news})
