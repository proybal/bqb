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
    return render(req, 'news/index_old.html', {'news': news})


def news_update(req):
    def cleanup(s):
        s = re.sub('\n+', '', s)
        s = s.strip()
        return s

    def abqjournal():
        ########################################
        # Scrape "Albuquerque Journal" news
        ########################################
        feed_url = "https://www.abqjournal.com/category/abqnewsseeker"
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        news_tags = news_soup.find_all('article', class_='post-card')
        for tag in news_tags:
            div_tag = tag.findAll('div', attrs={'class': 'post-card__thumbnail__image'})
            updated = ""
            if div_tag:
                title_tag = tag.findAll('div', attrs={'class': 'post-card__excerpt', 'span': ''})
                date_tag = tag.findAll('time', attrs={'class': 'entry-date'})
                url_tag = tag.findAll('div', attrs={'class': 'post-card__thumbnail', 'a': ''})
                url = url_tag[0].contents[1].attrs['href']
                body = cleanup(tag.text)
                if date_tag:
                    published = date_tag[0].attrs['datetime']
                    if len(date_tag) > 1:  # look for date updated, if any
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
        return

    def thepaper():
        ########################################
        # Scrape "The Paper" news
        ########################################
        feed_url = "https://abq.news/category/news/albuquerque/"
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
        return

    def joemonahan():
        ###############################################
        # Scrape "New Mexico Politics with Joe Monahan
        ###############################################
        feed_url = "https://joemonahansnewmexico.blogspot.com/"
        url = "https://joemonahansnewmexico.blogspot.com/"
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        body_tags = news_soup.find_all('tbody')
        blog_tags = news_soup.find_all('div', class_="blogPost")
        tr_tag = news_soup.find_all('h2')
        t = 0
        for tag in blog_tags:
            date_published = ""
            td_tag = tag.findAll('td')
            title = tr_tag[t].text
            title = cleanup(title[:title.find(':')])
            body = tr_tag[t].text
            body = body[body.find(':') + 1:]
            # body = cleanup(tr_tag[t].text)
            if td_tag:
                img = td_tag[0].contents[0].attrs['href']
            else:
                img = ""
            published = parse(tag.parent.contents[1].text)
            published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = parse(tag.parent.contents[1].text)
            updated = updated.strftime("%Y-%m-%dT%H:%M:%S")
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body,
                         'published': published,
                         'updated': updated, 'url': url, 'img': img, 'thumbnail': thumbnail}
            if img != "":
                news.append(news_dict)
            t += 1
        return

    # def koat(req):
    # ###############################################
    # # Scrape "KOAT Action News 7"
    # ###############################################
    # feed_url = "https://www.koat.com/local-news"
    # source = News.objects.filter(feed_url=feed_url).values()[0]['title']
    # thumbnail = News.objects.filter(feed_url=feed_url).values()[0]['cover']
    # news_r = requests.get(feed_url)
    # news_soup = BeautifulSoup(news_r.text, 'html5lib')
    # body_tags = news_soup.find_all('div', class_="article")
    # blog_tags = news_soup.find_all('div', class_="feed-item-byline")
    # a_tags = news_soup.find_all('li', class_="news")
    # tr_tag = news_soup.find_all('h2')
    # t = 0
    # for tag in body_tags:
    #     url = tag.attrs['data-content-url']
    #     news_r = requests.get(url)
    #     news_soup = BeautifulSoup(news_r.text, 'html5lib')
    #     date_published = ""
    #     td_tag = tag.findAll('td')
    #     title = tag.attrs['data-content-title']
    #     # img = blog_tags[t].contents
    #     # img = img[1].attrs['data-style']
    #     # img = img[img.find('(')+1:img.find('?')]
    #     # title = cleanup(title[:title.find(':')])
    #     # body = tr_tag[t].text
    #     # body = body[body.find(':')+1:]
    #     # body = cleanup(tr_tag[t].text)
    #     if td_tag:
    #         img = td_tag[0].contents[0].attrs['href']
    #     else:
    #         img = ""
    #     # published = parse(tag.parent.contents[1].text)
    #     # published = published.strftime("%Y-%m-%dT%H:%M:%S")
    #     # updated = parse(tag.parent.contents[1].text)
    #     # updated = updated.strftime("%Y-%m-%dT%H:%M:%S")
    #     news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body,
    #                  'published': published,
    #                  'updated': updated, 'url': url, 'img': img, 'thumbnail': thumbnail}
    #     # if img != "":
    #     news.append(news_dict)
    #     t += 1
    #
    news = []
    news_list = News.objects.filter(published=True)
    for n in news_list:
        source = n.title
        source_url = n.source
        thumbnail = n.cover
        eval(n.function + "()")

    news = sorted(news, key=lambda d: d['published'])[::-1]
    with open("news.json", "w") as outfile:
        json.dump(news, outfile, indent=4)

    return render(req, 'news/index_old.html', {'news': news})
