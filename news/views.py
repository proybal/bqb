import re

from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
import json
from .models import News
from dateutil.parser import *


def index(req):
    with open('news.json') as json_file:
        news = json.load(json_file)
    return render(req, 'news/index.html', {'news': news})


def news_update(req):
    def cleanup(s):
        s = re.sub('\n+', '', s)
        s = s.strip()
        return s

    ########################################
    # Scrape "Albuquerque Journal" news
    ########################################
    feed_url = "https://www.abqjournal.com/category/abqnewsseeker"
    source = News.objects.filter(feed_url=feed_url).values()[0]['title']
    source_url = News.objects.filter(feed_url=feed_url).values()[0]['source']
    thumbnail = News.objects.filter(feed_url=feed_url).values()[0]['cover']
    news_r = requests.get(feed_url)
    news_soup = BeautifulSoup(news_r.text, 'html5lib')
    news_tags = news_soup.find_all('article', class_='post-card')
    news = []
    for tag in news_tags:
        div_tag = tag.findAll('div', attrs={'class': 'post-card__thumbnail__image'})
        date_updated = ""
        if div_tag:
            title_tag = tag.findAll('div', attrs={'class': 'post-card__excerpt', 'span': ''})
            date_tag = tag.findAll('time', attrs={'class': 'entry-date'})
            url_tag = tag.findAll('div', attrs={'class': 'post-card__thumbnail', 'a': ''})
            url = url_tag[0].contents[1].attrs['href']
            body = cleanup(tag.text)
            if date_tag:
                published = date_tag[0].attrs['datetime']
                # date_published = date_published['datetime']
                if len(date_tag) > 1: # look for date updated, if any
                    updated = date_tag[1].attrs['datetime']
                    # updated = updated[updated.find(':') + 1:len(updated)]
                    # date_updated = parse(updated)
                    # date_updated = date_updated['datetime']
            try:
                title = cleanup(title_tag[0].text)

            except Exception:
                continue
            img = div_tag[0].attrs
            img = img['data-bg']
            img = img[4:len(img) - 1]
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body,
                         'published': published,
                         'updated': updated, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)

    ########################################
    # Scrape "The Paper" news
    ########################################
    feed_url = "https://abq.news/category/news/albuquerque/"
    source = News.objects.filter(feed_url=feed_url).values()[0]['title']
    thumbnail = News.objects.filter(feed_url=feed_url).values()[0]['cover']
    news_r = requests.get(feed_url)
    news_soup = BeautifulSoup(news_r.text, 'html5lib')
    news_tags = news_soup.find_all('article', class_='post')
    for tag in news_tags:
        date_published = ""
        date_updated = ""
        img = ""
        div_tag = tag.findAll('h2', attrs={'class': 'entry-title'})
        title = cleanup(div_tag[0].text)
        div_tag = tag.findAll('a', attrs={'class': 'post-thumbnail-inner'})
        url = div_tag[0].attrs['href']
        img = tag.findAll('amp-img')
        img = img[0].attrs['src']
        img = img[0: img.find('?')]
        date_tag = tag.findAll('time')
        body = cleanup(tag.text)
        if date_tag:
            published = date_tag[0].attrs['datetime']
            if len(date_tag) > 1:
                updated = date_tag[1].attrs['datetime']
        news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body,
                     'published': published,
                     'updated': updated, 'url': url, 'img': img, 'thumbnail': thumbnail}
        news.append(news_dict)

    ###############################################
    # Scrape "New Mexico Politics with Joe Monahan
    ###############################################
    feed_url = "http://joemonahansnewmexico.blogspot.com"
    source = News.objects.filter(feed_url=feed_url).values()[0]['title']
    thumbnail = News.objects.filter(feed_url=feed_url).values()[0]['cover']
    news_r = requests.get(feed_url)
    news_soup = BeautifulSoup(news_r.text, 'html5lib')
    news_tags = news_soup.find_all('tbody')
    blog_tags = news_soup.find_all('div', class_="blogPost")
    for tag in blog_tags:
        date_published = ""
        date_updated = ""
        td_tag = tag.findAll('td')
        h2_tag = tag.findAll('h2')
        a_tag = tag.findAll('img')
        div_tag = tag.findAll('table', attrs={'class': 'tr-caption-container'})
        title = 'New Mexico Politics with Joe Monahan'
        body = cleanup(tag.text)
        body = tag.parent.contents[3].contents[0]
        div_tag = tag.findAll('a', )
        # for d in a_tag:
        #     url = d.attrs['href']
        if td_tag:
            img = td_tag[0].contents[0].attrs['href']
        else:
            img = ""
        date_tag = tag.parent.contents[1].text
        # body = tag.parent.text
        # body = body.strip()
        if date_tag:
            date_published = parse(date_tag)
            # date_published = date_published['datetime']
            # if len(date_tag) > 1:
        date_updated = parse(date_tag)
        # date_updated = date_updated['datetime']
        news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body,
                     'published': date_published,
                     'updated': date_updated, 'url': url, 'img': img, 'thumbnail': thumbnail}
        news.append(news_dict)
    # news = sorted(news, key=lambda d: d['published'])[::-1]
    # news = news.sort(key=lambda x: x[0]['published'], reverse=False)
    # news = sorted(news.items(), key=lambda kv: (kv[1], kv[0]))
    # news = sorted(news, key=lambda d: d['date_published'])
    with open("news.json", "w") as outfile:
        json.dump(news, outfile, indent=4)
    return render(req, 'news/index.html', {'news': news})
