import re
import sys

import requests
from bs4 import BeautifulSoup
import json
from .models import News
from dateutil.parser import *
import datetime
from datetime import date, datetime
from csv import writer
from django.conf import settings
import os
from dateutil import tz
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect

MAX_ARTICLES = 99


def get_past_date(str_days_ago):
    TODAY = datetime.now()
    splitted = str_days_ago.split()
    if len(splitted) == 1 and splitted[0].lower() == 'today':
        return str(TODAY.isoformat())
    elif len(splitted) == 1 and splitted[0].lower() == 'yesterday':
        date = TODAY - relativedelta(days=1)
        return str(date.isoformat())
    elif splitted[1].lower() in ['hour', 'hours', 'hr', 'hrs', 'h']:
        date = datetime.now() - relativedelta(hours=int(splitted[0]))
        return str(date.date().isoformat())
    elif splitted[1].lower() in ['day', 'days', 'd']:
        date = TODAY - relativedelta(days=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ['wk', 'wks', 'week', 'weeks', 'w']:
        date = TODAY - relativedelta(weeks=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ['mon', 'mons', 'month', 'months', 'm']:
        date = TODAY - relativedelta(months=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ['yrs', 'yr', 'years', 'year', 'y']:
        date = TODAY - relativedelta(years=int(splitted[0]))
        return str(date.isoformat())
    else:
        # return False
        return str(TODAY.isoformat())


def adjust_string_length(input_string, max_length):
    if len(input_string) <= max_length:
        return input_string

    truncated_string = input_string[:max_length]

    last_space_index = truncated_string.rfind(' ')
    last_period_index = truncated_string.rfind('.')

    if last_space_index > last_period_index:
        truncated_string = truncated_string[:last_space_index] + '...'
    elif last_period_index != -1:  # Check if a period was found
        truncated_string = truncated_string[:last_period_index]

    return truncated_string.strip()


def filter_max_articles(news):
    if MAX_ARTICLES < 99:
        news = sorted(news, key=lambda x: x['source'])
        last_article = ""
        new_news = []
        article_count = 1
        for article in news:
            if article['source'] == last_article:
                article_count += 1
            else:
                article_count = 1
                last_article = article['source']
            if article_count <= MAX_ARTICLES:
                new_news.append(article)
        news = sorted(new_news, key=lambda x: x['last_update'])[::-1]
    return news


def write_access_log(req, category):
    """
        ##  write out access log for visits to home page
        ##  getting the hostname by socket.gethostname() method
        # hostname = socket.gethostname()
        ## getting the IP address using socket.gethostbyname() method
        # ip_address = socket.gethostbyname(hostname)
    """

    def get_location(ip_address):
        # ip_address = '98.60.223.30'
        response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
        location_data = {
            "ip": ip_address,
            "city": response.get("city"),
            "region": response.get("region"),
            "country": response.get("country_name")
        }
        return location_data

    def get_client_ip(req):
        x_forwarded_for = req.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = req.META.get('REMOTE_ADDR')
            host = req.META.get('REMOTE_HOST')
        return ip, host

    # messages.info(req, 'Welcome to burquebro.com the place to go for the latest New Mexico news!')
    FILE_NAME = 'access_log'
    with open(FILE_NAME, 'a', newline='') as file:
        data = writer(file)
        ip, hostname = get_client_ip(req)
        location_data = get_location(ip)
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/Denver')
        utc = datetime.utcnow()
        utc = utc.replace(tzinfo=from_zone)
        denver = utc.astimezone(to_zone)
        time_out = denver.strftime("%m-%d-%Y %H:%M:%S")
        list_data = [time_out, ip, location_data['city'], location_data['country'], category, hostname]
        data.writerow(list_data)
        file.close()


def index(request):
    write_access_log(request, 'Home')
    category = 'New Mexico'
    with open('news.json') as json_file:
        news = json.load(json_file)
    news = filter_max_articles(news)
    return render(request, 'news/index_old.html', {'category': category, 'news': news})


def state_news(req):
    state = 'New Mexico'
    write_access_log(req, state)
    with open('news.json') as json_file:
        news = json.load(json_file)
    news = filter_max_articles(news)
    return render(req, 'news/index_old.html', {'category': state, 'news': news})


def by_region(req, region):
    write_access_log(req, region)
    reg = region
    with open('news.json') as json_file:
        news = json.load(json_file)
    if region.find('ern'):
        cat = region[:region.find('ern')]
    new_news = []
    for r in news:
        news_cat = r['region']
        if news_cat.find(reg) != -1:
            new_news.append(r)
    news = filter_max_articles(new_news)
    return render(req, 'news/index_old.html', {'category': region, 'news': news})


def by_city(req, city):
    write_access_log(req, city)
    with open('news.json') as json_file:
        news = json.load(json_file)
    new_news = []
    for news_item in news:
        if news_item['city'] == city:
            new_news.append(news_item)
    city = city.replace("_", " ")
    news = filter_max_articles(new_news)
    return render(req, 'news/index_old.html', {'category': city, 'news': news})


def by_county(req, county):
    write_access_log(req, county + ' County')
    with open('news.json') as json_file:
        news = json.load(json_file)
    new_news = []
    for news_item in news:
        if news_item['county'] == county:
            new_news.append(news_item)
    county = county.replace("_", " ")
    news = filter_max_articles(new_news)
    return render(req, 'news/index_old.html', {'category': county, 'news': news})


def scrape_news():
    def get_class_text(tag, tag_to_find, class_name):
        t = tag.find(tag_to_find, class_=class_name)
        if t and t.text:
            return cleanup(t.text)
        else:
            return ""

    def get_class_attr(tag, tag_to_find, class_name, attr):
        t = tag.find(tag_to_find, class_=class_name)
        if t and t.has_attr(attr):
            return cleanup(t.attrs[attr])
        else:
            return ""

    def get_class_date(tag, tag_to_find, class_name):
        t = tag.find(tag_to_find, class_=class_name)
        if t:
            class_date = parse(t.text)
            class_date = class_date.strftime("%Y-%m-%dT%H:%M:%S")
            return class_date
        else:
            return ""

    def get_attr(tag, tag_to_find, attr):
        if not tag_to_find:
            if tag.has_attr(attr):
                return tag.attrs[attr]
            else:
                return ""
        t = tag.find(tag_to_find)
        if t and t.has_attr(attr):
            return cleanup(t.attrs[attr])
        else:
            return ""

    def get_attr_date(tag, tag_to_find, attr):
        t = tag.find(tag_to_find)
        if t and t.has_attr(attr):
            attr_date = parse(t.attrs[attr])
            attr_date = attr_date.strftime("%Y-%m-%dT%H:%M:%S")
            return attr_date
        else:
            return ""

    def get_text(tag, tag_to_find):
        t = tag.find(tag_to_find)
        if t and t.text:
            return cleanup(t.text)
        else:
            return ""

    def get_source(feed):
        feed_url = feed
        news_object = News.objects.filter(feed_url=feed_url).first()
        if news_object:
            region = str(news_object.region)
            source = str(news_object.title)
            source_url = str(news_object.source)
            thumbnail = str(news_object.cover)
            city = str(news_object.city)
            county = str(news_object.county)
            return source, source_url, thumbnail, region, city, county,
        else:
            return False

    def get_news_source(url):
        news_object = News.objects.filter(feed_url=url).first()
        news_source = {}
        if news_object:
            news_source['feed_url'] = str(url)
            news_source['region'] = str(news_source.region)
            news_source['source'] = str(news_source.title)
            news_source['source_url'] = str(news_source.source)
            news_source['thumbnail'] = str(news_source.cover)
            news_source['city'] = str(news_source.city)
            news_source['county'] = str(news_source.county)
            return news_source
        else:
            return False

    def get_soup(url):
        news_request = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
        return BeautifulSoup(news_request.text, 'html5lib')

    def add_article(title, body, author, published, updated, url, img):
        last_update = published
        if updated:
            last_update = updated
        news_dict = {'source': str(news_source.source), 'source_url': str(news_source.feed_url), 'title': title,
                     'body': body, 'author': author,
                     'published': published, 'region': str(news_source.region), 'city': str(news_source.city),
                     'county': str(news_source.county),
                     'updated': updated, 'last_update': last_update, 'url': url, 'img': img,
                     'thumbnail': str(news_source.cover)}
        news.append(news_dict)

    def cleanup(str):
        return re.sub(r'[\n\t]+', ' ', str).strip()

    # def find_tag(tag, class_, attr):

    def abqjournal():
        """
        ########################################
        # Scrape "Albuquerque Journal" news
        ########################################
        """
        news_soup = get_soup(news_source.feed_url)
        news_tags = news_soup.find_all('article', class_='tnt-asset-type-article')
        for tag in news_tags:

            title = get_class_text(tag, 'h3', 'tnt-headline')

            body = get_class_text(tag, 'p', 'tnt-summary')

            url = news_source.source + get_class_attr(tag, 'a', 'tnt-asset-link', 'href')

            img_tags = tag.find('img', class_='img-responsive')
            if img_tags:
                img = img_tags.attrs['data-srcset']
                img = img[0: img.find('?')]
            else:
                img = ""

            news_soup = get_soup(news_source.feed_url + url)

            meta_tag = news_soup.find('meta', attrs={'name': 'author'})
            if meta_tag:
                author = meta_tag.attrs['content']
            else:
                author = ""

            date_tag = news_soup.find('time', class_='tnt-date')
            if date_tag:
                published = date_tag.attrs['datetime']
            else:
                published = ""

            date_tag = news_soup.find('time', class_='tnt-update-recent')
            if date_tag:
                updated = date_tag.attrs['datetime']
            else:
                updated = ""

            add_article(title, body, author, published, updated, url, img)

    def citydesk():
        """
        ########################################
        # Scrape "City Desk" news
        ########################################
        """
        news_soup = get_soup(news_source.feed_url)
        news_tags = news_soup.find_all('article', class_='type-post')
        for tag in news_tags:

            title = get_text(tag, 'h3')

            body = get_text(tag, 'p')

            url = get_attr(tag, 'a', 'href')

            img = get_class_attr(tag, 'img', 'wp-post-image', 'src')

            author = get_class_text(tag, 'span', 'author')

            published = parse(get_class_text(tag, 'time', 'published'))
            published = published.strftime("%Y-%m-%dT%H:%M:%S")

            updated = get_class_text(tag, 'time', 'updated')
            if updated:
                updated = parse(updated)
                updated = updated.strftime("%Y-%m-%dT%H:%M:%S")

            add_article(title, body, author, published, updated, url, img)

    def thepaper():
        """
        ########################################
        # Scrape "The Paper" news
        ########################################
        """
        news_soup = get_soup(news_source.feed_url)

        news_tags = news_soup.find_all('article', class_='post')
        for tag in news_tags:
            title = get_class_text(tag, 'h2', 'entry-title')

            body = cleanup(tag.text)

            url = get_attr(tag, 'a', 'href')

            img = get_class_attr(tag, 'img', 'wp-post-image', 'src')

            author = get_class_text(tag, 'span', 'author')

            published = get_class_date(tag, 'time', 'published')

            updated = get_class_date(tag, 'time', 'updated')

            add_article(title, body, author, published, updated, url, img)

    def joemonahan():
        """
        ###############################################
        # Scrape "New Mexico Politics with Joe Monahan
        ###############################################
        """
        news_soup = get_soup(news_source.feed_url)
        blog_tags = news_soup.find_all('div', class_="blogPost")
        for tag in blog_tags:

            # title = tag.previous_sibling.previous_sibling.text
            title_tag = tag.previous_sibling.previous_sibling
            if title_tag and title_tag.text:
                title = title_tag.text
            else:
                title = ""

            if tag.text:
                body = tag.text
                body = cleanup(body)
            else:
                body = ""

            author = 'Joe Monahan'

            img_tag = tag.find('img')
            if img_tag and img_tag.has_attr('src'):
                img = img_tag.attrs['src']
                if img.find('facebook') != -1:
                    img = ""
            else:
                img = ""

            published = tag.find('div', class_='byline')
            if published:
                published = published.text
                published = parse(published[published.find('/') + 2:])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""
            updated = ""

            add_article(title, body, author, published, updated, news_source.feed_url, img)

    def newmexican():
        """
        ###############################################
        # Scrape "Santa Fe New Mexican"
        ###############################################
        """
        news_soup = get_soup(news_source.feed_url)

        article_tags = news_soup.find_all('article')
        for tag in article_tags:

            title = get_attr(tag, 'a', 'aria-label')
            if not title:
                title = get_text(tag, 'a')

            body = get_class_text(tag, 'p', 'tnt-summary')
            if len(body) <= 20 or title == body:
                body = ""

            url = news_source.source + get_attr(tag, 'a', 'href')

            img = get_attr(tag, 'img', 'data-srcset')

            author_tag = tag.find('div', class_='card-meta')
            if author_tag:
                author = author_tag.text
            else:
                author = ""

            news_r = requests.get(url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            time_tag = news_soup.find('meta', itemprop='dateCreated')

            if time_tag:
                published = parse(time_tag.attrs['content'])
                published = published.strftime("%Y-%m-%d %H:%M:%S")
            else:
                published = ""

            time_tag = news_soup.find('meta', itemprop='dateModified')
            if time_tag:
                updated = parse(time_tag.attrs['content'])
                updated = updated.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def riograndesun():
        """
        ###############################################
        # Scrape "Rio Grande Sun"
        ###############################################
        """
        feed_url = "http://www.riograndesun.com/news/"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        a_tags = news_soup.find_all('article', class_='tnt-asset-type-article')
        for tag in a_tags:

            url_tag = tag.find('a', class_="tnt-asset-link")
            if url_tag:
                title = cleanup(url_tag.attrs['aria-label'])
                url = source_url + url_tag.attrs['href']
            else:
                url = ""
                title = ""

            p_tag = tag.find('p')
            if p_tag:
                body = p_tag.text
            else:
                body = ""

            img_tag = tag.find('img')
            img_attributes = ['data-src', 'data-srcset', 'srcset', 'src']

            if img_tag:
                for attr in img_attributes:
                    if img_tag.has_attr(attr):
                        img = img_tag.attrs[attr]
                        img = img[0: img.find('?')]
                        break
                else:
                    img = ""
            else:
                img = ""

            time_tag = tag.find('time')
            if time_tag:
                published = time_tag.attrs['datetime']
            else:
                published = ""

            news_r = requests.get(url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')

            author_tag = news_soup.find('span', itemprop='author')
            if author_tag:
                author = cleanup(author_tag.text)
            else:
                author = ""

            time_tag = news_soup.find('time', class_='tnt-update-recent')
            if time_tag:
                updated = parse(time_tag.attrs['datetime'])
                updated = updated.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                updated = ""

            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def lascrucessun():
        """
        ###############################################
        # Scrape "Las Cruces Sun"
        ###############################################
        """
        feed_url = "https://www.lcsun-news.com/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('a', class_='gnt_m_he')
        tags = tags + news_soup.find_all('a', class_='gnt_m_flm_a')
        for tag in tags:
            # Skip if not a valid tag
            if tag.has_attr('rel'):
                continue

            if tag.text:
                title = tag.text
            else:
                title = ""

            body = get_attr(tag, None, 'data-c-br')

            url = source_url + get_attr(tag, None, 'href')

            img_tag = tag.find('img')
            img_attributes = ['src', 'srcset', 'data-gl-src']

            img = ""
            if img_tag:
                for attr in img_attributes:
                    if img_tag.has_attr(attr):
                        img = img_tag.attrs[attr]
                        img = img[0: img.find('?')]
                        img = source_url + img
                        break

            news_r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            date_tag = news_soup.find('div', class_="gnt_ar_dt")
            if date_tag and date_tag.has_attr('aria-label'):
                aria_label = date_tag.attrs['aria-label']
                if aria_label.find('Updated') != -1:
                    published = parse(aria_label[11:aria_label.find('Updated')])
                    updated = parse(aria_label[aria_label.find('Updated') + 8:len(aria_label)])
                    updated = updated.strftime("%Y-%m-%dT%H:%M:%S")
                else:
                    published = parse(aria_label.replace('Published', ''))
                    updated = ""
            else:
                # no date found / extract it  from the image url using regex
                # Define the search pattern using a regular expression
                pattern = r'/(\d{4}/\d{2}/\d{2})/'

                # Search for the pattern in the string
                match = re.search(pattern, url)

                # Extract the date based on the search pattern
                if match:
                    extracted_date = match.group(1)
                    published = parse(extracted_date)
                updated = ""
            published = published.strftime("%Y-%m-%dT%H:%M:%S")
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def hobbssun():
        """
        ###############################################
        # Scrape "Hobbs Sun"
        ###############################################
        """
        feed_url = "https://www.hobbsnews.com/category/local-news/"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        page_url = feed_url
        PAGES = 12
        # loop through PAGES of news
        for page in range(1, PAGES):
            if page > 1:
                page_url = feed_url + '/page/' + str(page) + '/'
            news_r = requests.get(page_url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            article_tags = news_soup.find_all('article', class_="")
            for tag in article_tags:
                h2_tag = tag.find('h2')
                if h2_tag:
                    title = h2_tag.text
                else:
                    title = ""

                body_tag = tag.find('p')
                if body_tag and body_tag.text:
                    body = body_tag.text
                else:
                    body = ""

                url_tag = tag.find('a')
                if url_tag and url_tag.has_attr('href'):
                    url = url_tag.attrs['href']
                else:
                    url = ""

                img_tag = tag.find('img')
                if img_tag and img_tag.has_attr('data-src'):
                    img = img_tag.attrs['data-src']
                else:
                    img = ""

                a_tag = tag.find('a', rel='author')
                if a_tag and a_tag.text:
                    author = a_tag.text
                else:
                    author = ""

                published = ""
                date_tag = tag.find('span', class_='bdayh-date')
                if date_tag:
                    published = date_tag.text
                published = parse(published)
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
                updated = ""
                last_update = published
                if updated:
                    last_update = updated
                news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                             'published': published, 'region': region, 'city': city, 'county': county,
                             'updated': updated, 'last_update': last_update, 'url': url, 'img': img,
                             'thumbnail': thumbnail}
                news.append(news_dict)
        return

    def taosnews():
        """
        ###############################################
        # Scrape "Taos News"
        ###############################################
        """
        feed_url = "https://www.taosnews.com/news/"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        article_tags = news_soup.find_all('article', class_='tnt-asset-type-article')
        for tag in article_tags:
            title = get_attr(tag, 'a', 'aria-label')
            url = source_url + get_attr(tag, 'a', 'href')
            img = get_attr(tag, 'img', 'data-srcset')
            body_tag = tag.find('div', class_='card-lead')
            if body_tag and body_tag.text:
                body = body_tag.text
            else:
                body = ""
            news_r = requests.get(url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            if body == "":
                d_tag = news_soup.find('meta', property='og:description')
                if d_tag and d_tag.has_attr('content'):
                    body = d_tag.attrs['content']
                else:
                    body = ""
            meta_tags = news_soup.find_all('meta')
            author = ""
            for meta_tag in meta_tags:
                if meta_tag.has_attr('name') and meta_tag.attrs['name'] == 'author':
                    author = meta_tag.attrs['content']
            published = ""
            time_tag = news_soup.find('time', class_='tnt-date')
            published = time_tag.attrs['datetime']
            time_tag = news_soup.find('time', class_='tnt-update-recent')
            if time_tag:
                updated = time_tag.attrs['datetime']
            else:
                updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def gallupsun():
        """
        ###############################################
        # Scrape "Gallup Sun News"
        ###############################################
        """
        #
        # def has_title(tag):
        #     return tag.name == 'p' and tag.text and not tag.has_attr('id')
        #
        # def has_image(tag):
        #     return tag.name == 'img' and tag.has_attr('title')
        PAGES = 10
        feed_url = "https://www.gallupsun.com/index.php?option=com_content&view=category&layout=blog&id=150&Itemid=600"
        page_url = feed_url
        limitstart = 0
        # loop through PAGES of news
        for page in range(1, PAGES):
            if page > 1:
                limitstart += 5
                page_url = feed_url + '&limitstart=' + str(limitstart)
            source, source_url, thumbnail, region, city, county, = get_source(feed_url)
            news_r = requests.get(page_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
            news_soup = BeautifulSoup(news_r.text, 'html5lib')

            source, source_url, thumbnail, region, city, county, = get_source(feed_url)
            # news_r = requests.get(feed_url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            tags = news_soup.find_all('div', class_='contentpaneopen')
            for tag in tags:
                body = cleanup(tag.text)

                h2_tag = tag.find('h2', class_='contentheading')
                title = h2_tag.text

                a_tag = tag.find('a')
                url = source_url + a_tag.attrs['href']

                c_tags = tag.find('span', class_='createby')
                author = c_tags.text

                news_r = requests.get(url)
                news_soup = BeautifulSoup(news_r.text, 'html5lib')
                img_tag = news_soup.find('img', class_='caption')
                if img_tag:
                    img = source_url + img_tag.attrs['src']
                else:
                    img = ""
                d_tag = tag.find('span', class_='createdate')
                published = parse(d_tag.text)
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
                updated = ""
                last_update = published
                if updated:
                    last_update = updated
                news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                             'published': published, 'region': region, 'city': city, 'county': county,
                             'updated': updated, 'last_update': last_update, 'url': url, 'img': img,
                             'thumbnail': thumbnail}
                news.append(news_dict)
        return

    def artesia_news():
        """
        ###############################################
        # Scrape "Artesian News"
        ###############################################
        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('name') and tag.attrs['name'] == 'author'

        feed_url = "http://www.artesianews.com/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('div', class_="td-cpt-post")
        for tag in tags:
            a_tag = tag.find('a')
            url = a_tag.attrs['href']
            title = cleanup(a_tag.attrs['title'])
            img_tag = tag.find('span')
            img = img_tag.attrs['data-img-url']
            img_tag = tag.find('img')
            p_tag = tag.find('p')
            if p_tag:
                body = p_tag.text
            else:
                body = ""
            news_r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            meta_tag = news_soup.find(has_author)
            if meta_tag:
                author = meta_tag.attrs['content']
            else:
                author = ""

            d_tag = news_soup.find('meta', property='og:description')
            if d_tag:
                body = d_tag.attrs['content']
            else:
                body = ""

            d_tag = news_soup.find('time')
            published = parse(d_tag.attrs['datetime'])
            published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def newmexicosun():
        """
        ###############################################
        # Scrape "New Mexico Sun"
        ###############################################

        Note: "More News" could be added
        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('name') and tag.attrs['name'] == 'author'

        feed_url = "https://newmexicosun.com"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('div', class_="news")
        for tag in tags:
            a_tag = tag.find('a')
            if a_tag:
                url = source_url + a_tag.attrs['href']
            else:
                url = ""

            h_tag = tag.find(re.compile('^h'))
            if h_tag:
                title = cleanup(h_tag.text)
            else:
                title = ""

            img_tag = tag.find('div', class_='bg-img')
            if img_tag:
                img = img_tag.attrs['style']
                pattern = re.compile(r'https://[^\s\)]+')
                # Use the findall method to extract all matches of the pattern in the input string
                matches = pattern.findall(img)
                # Display the extracted URLs
                img = matches[0]
            else:
                img = ""

            a_tag = tag.find('a', class_='d-block')
            body_tag = tag.find('div', class_='content')
            if body_tag:
                body = body_tag.text
            elif a_tag and a_tag.text:
                body = cleanup(a_tag.text)
            else:
                body = ""

            news_r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            author_tag = news_soup.find(has_author)
            if author_tag:
                author = author_tag.attrs['content']
            else:
                author = ""

            date_tag = news_soup.find('meta', itemprop='datePublished')
            if date_tag:
                published = parse(date_tag.attrs['content'])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""
            date_tag = news_soup.find('meta', itemprop='dateModified')
            if date_tag:
                updated = parse(date_tag.attrs['content'])
                updated = updated.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def pinonpost():
        """
        ###############################################
        # Scrape "Pinon Post"
        ###############################################
        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('name') and tag.attrs['name'] == 'author'

        feed_url = "https://pinonpost.com/politics/"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all("article", class_='jeg_post')
        img_tags = news_soup.find_all('div', class_="thumbnail-container")
        for t, tag in enumerate(tags):
            title = tag.text
            if title.find('by Piñon') != -1:
                title = title[:title.find('by Piñon')]
            if title.find('by Renato') != -1:
                title = title[:title.find('by Renato')]

            a_tag = tag.find('a')
            if a_tag:
                url = a_tag.attrs['href']
            else:
                url = ""

            news_r = requests.get(url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            p_tag = news_soup.find('p')
            if p_tag:
                body = cleanup(p_tag.text)
                if body.find('by John'):
                    body = body[:body.find('by John')]
            else:
                body = ""

            author_tag = news_soup.find(has_author)
            if author_tag:
                author = author_tag.attrs['content']
            else:
                author = ""

            img_tag = news_soup.find('img', class_='wp-post-image')
            date_tag = tag.find('div', class_='jeg_meta_date')
            if img_tag:
                if img_tag.has_attr('data-src'):
                    img = img_tag.attrs['data-src']
                elif img_tag.has_attr('srcset'):
                    img = img_tag.attrs['srcset']
            else:
                img = ""

            updated = ""
            published = parse(date_tag.text)
            published = published.strftime("%Y-%m-%dT%H:%M:%S")
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
            if t == 20:
                break
        return

    def lasvegasoptic():
        """
        ###############################################
        # Scrape "Las Vegas Optic
        ###############################################
        """

        def has_date(tag):
            return tag.name == 'time' and tag.has_attr('datetime')

        def has_title(tag):
            return tag.name == 'a' and tag.has_attr('href') and tag.has_attr('aria-label')

        feed_url = "https://www.lasvegasoptic.com/news/"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        article_tags = news_soup.find_all('article', class_='tnt-section-news')
        for tag in article_tags:
            a_tag = tag.find(has_title)
            if a_tag:
                url = source_url + a_tag.attrs['href']
                title = cleanup(a_tag.attrs['aria-label'])
            else:
                title = ""

            p_tag = tag.find('p')
            if p_tag:
                body = cleanup(p_tag.text)
            else:
                body = ""

            img_tag = tag.find('img')
            if img_tag:
                if img_tag.has_attr('data-srcset'):
                    img = img_tag.attrs['data-srcset']
                elif img_tag.has_attr('srcset'):
                    img = img_tag.attrs['srcset']
                img = img[0: img.find('?')]
            else:
                img = ""

            news_r = requests.get(url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            span_tag = news_soup.find('span', class_='tnt-user-name')
            if span_tag and span_tag.text:
                author = cleanup(span_tag.text)
            else:
                author = ""

            time_tag = tag.find(has_date)
            if time_tag:
                published = parse(time_tag.attrs['datetime'])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                time_tag = news_soup.find(has_date)
                if time_tag:
                    published = parse(time_tag.attrs['datetime'])
                    published = published.strftime("%Y-%m-%dT%H:%M:%S")
                else:
                    published = ""
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def roswelldaily():
        """
        ###############################################
        # Scrape "Roswell Daily Record
        ###############################################
        """
        feed_url = "https://www.rdrnews.com/news/"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        article_tags = news_soup.find_all('article', class_='tnt-section-news')
        for tag in article_tags:
            a_tag = tag.find('a')
            url = source_url + a_tag.attrs['href']
            if a_tag.has_attr('aria-label'):
                title = cleanup(a_tag.attrs['aria-label'])
            else:
                title = ""
            p_tag = tag.find('p')
            if p_tag:
                body = cleanup(p_tag.text)
            else:
                body = ""
            time_tag = tag.find('time')
            if time_tag:
                published = parse(time_tag.attrs['datetime'])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""
            span_tags = tag.findAll('span', class_='tnt-byline')
            if span_tags:
                author = span_tags[0].text
            else:
                author = ""
            img = ""
            img_tag = tag.find('img')
            if img_tag:
                if img_tag.has_attr('data-srcset'):
                    img = img_tag.attrs['data-srcset']
                elif img_tag.has_attr('srcset'):
                    img = img_tag.attrs['srcset']
                img = img[0: img.find('?')]
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def farmingtondaily():
        """
        ###############################################
        # Scrape "Farmington Daily News"
        ###############################################
        """

        def has_href(tag):
            return tag.name == 'a' and tag.has_attr('href')

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('content') and tag.has_attr('property') \
                   and tag.attrs['property'] == 'article:author'

        feed_url = "https://www.daily-times.com/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all(has_href, class_='gnt_m_he')
        tags = tags + news_soup.find_all(has_href, class_='gnt_m_flm_a')

        for tag in tags:
            url = source_url + tag.attrs['href']
            img = settings.MEDIA_URL + thumbnail
            img_tag = tag.find('img')
            if img_tag:
                if img_tag.has_attr('src'):
                    img = img_tag.attrs['src']
                elif img_tag.has_attr('srcset'):
                    img = img_tag.attrs['srcset']
                elif img_tag.has_attr('data-gl-src'):
                    img = img_tag.attrs['data-gl-src']
                if img.find('?'):
                    img = img[0: img.find('?')]
                img = source_url + img
            title = tag.text
            body = ""
            news_r = requests.get(url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            a_tag = news_soup.find('a', class_='gnt_ar_by_a')
            meta_tag = news_soup.find(has_author)
            author = ""
            if meta_tag:
                author = meta_tag.attrs['content']
            elif not author:
                slide_tag = news_soup.find('slide')
                if slide_tag:
                    author = slide_tag.attrs['author']
            if not author:
                a_tag = news_soup.find('a', class_='gnt_ar_by_a')
                if a_tag:
                    author = a_tag.text
            if not author:
                author = 'The Farmington Daily-Times'
            if tag.has_attr('data-c-br'):
                body = tag.attrs['data-c-br']
            dt_tag = tag.find('div')
            if dt_tag.has_attr('data-c-dt'):
                published = parse(dt_tag.attrs['data-c-dt'])
            else:
                published = date.today()
            published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def eastern_nm_news():
        """
        ###############################################
        # Scrape "Eastern New Mexico News" (clovis)
        ###############################################
        """

        def has_author(tag):
            return tag.name == 'a' and tag.has_attr('href') and tag.has_attr('aria-label') and tag.attrs[
                'aria-label'] == title

        feed_url = "https://www.easternnewmexiconews.com/section/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('div', class_='hmfunction_sectioncontainer')
        for tag in tags:
            h3_tag = tag.find('h3')
            if h3_tag:
                title = h3_tag.text
            else:
                title = ""
            p_tag = tag.find('p')
            if p_tag:
                body = p_tag.text
            else:
                body = ""
            a_tag = tag.find(has_author)
            if a_tag:
                author = a_tag.text
                url = a_tag.attrs['href']
            else:
                author = ""
                url = ""
            news_r = requests.get(url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            img_tag = news_soup.find('div', class_='top_image_left')
            img = ""
            if img_tag:
                img_tag = img_tag.find('img')
                if img_tag:
                    img = source_url + img_tag.attrs['src']
            dt_tag = tag.find('span')
            if dt_tag:
                published = dt_tag.text
                published = parse(published[published.find('/') - 2:])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def defensor_chieftain():
        """
        ###############################################
        # Scrape "El Defensor Cheiftain" (socorro)
        ###############################################
        """
        feed_url = "https://dchieftain.com/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('article')
        for tag in tags:
            body = ""
            body_tag = tag.find('div', class_='entry-summary')
            if body_tag:
                body_tag = body_tag.find('p')
                if body_tag:
                    body = body_tag.text
            author_tag = tag.find('p')
            author = ""
            if author_tag:
                author_tag = author_tag.find('a')
                if author_tag:
                    author = author_tag.attrs['title']
            title_tag = tag.find('a')
            if title_tag:
                title = title_tag.text
            else:
                title = ""
            url_tag = tag.find('a')
            if url_tag and url_tag.has_attr('href'):
                url = url_tag.attrs['href']
            else:
                url = ""
            news_r = requests.get(url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            img_tag = news_soup.find('img', class_='size-medium')
            if img_tag:
                img = img_tag.attrs['data-lazy-src']
            else:
                img = ""
            dt_tag = tag.findAll('span', class_='updated')
            published = parse(dt_tag[0].text)
            published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def la_daily_post():
        """
        ###############################################
        # Scrape "Los Alamos Daily Post"
        ###############################################
        """

        def has_img(tag):
            return tag.name and tag.name == 'img' and tag.has_attr('data-lazy-src')

        feed_url = "https://ladailypost.com"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('article', class_='elementor-post')
        for tag in tags:
            b_tags = tag.findAll('p')
            if b_tags:
                body = ""
                for b in b_tags:
                    if b.text:
                        body = body + b.text
            else:
                body = ""

            author = ""
            author_tag = tag.find('span', class_='elementor-post-author')
            if author_tag:
                author = cleanup(author_tag.text)
            a_tag = tag.find('a')
            title = a_tag.text
            url = a_tag.attrs['href']
            img = ""
            img_tag = tag.find(has_img)
            if img_tag:
                img = img_tag.attrs['data-lazy-src']
            d_tag = tag.find('span', class_='elementor-post-date')
            published = ""
            if d_tag:
                published = parse(d_tag.text)
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def sc_daily_press():
        """
        ###############################################
        # Scrape "Silver City Daily Press"
        ###############################################
        """

        def has_article(tag):
            if tag.name == 'div' and tag.has_attr('class'):
                if tag.attrs['class'] == 'item-container' or tag.attrs['class'] == 'post-content':
                    return True
            else:
                return False

        def has_title(tag):
            return tag.name == 'a' and tag.has_attr('title')

        feed_url = "https://www.scdailypress.com"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.select('div.item-container, div.post-content')

        for tag in tags:
            p_tags = tag.findAll('p')
            if p_tags:
                body = p_tags[0].text
            else:
                body = ""

            title_tag = tag.find(has_title)
            title = title_tag.attrs['title']
            url = title_tag.attrs['href']

            img = ""
            img_tag = tag.select_one('div.entry-bg, div.post-image-small')
            pattern = re.compile(r'https://[^\s\)]+')
            if img_tag:
                if img_tag.has_attr('style'):
                    img = img_tag.attrs['style']
                    # Use the findall method to extract all matches of the pattern in the input string
                    matches = pattern.findall(img)
                    # Display the extracted URLs
                    img = matches[0]
            news_r = requests.get(url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            b_tag = news_soup.find('div', class_='ls-post-content')
            if b_tag:
                p_tag = b_tag.find('p')
                if p_tag and body == "":
                    body = p_tag.text
                img_tag = b_tag.find('img')
                if img_tag and img_tag.has_attr('srcset') and img == "":
                    img = img_tag.attrs['srcset']
                    matches = pattern.findall(img)
                    # Display the extracted URLs
                    img = matches[0]
            if body == "":
                pass
            author = ""
            a_tag = news_soup.find('a', rel='author')
            if a_tag:
                author = a_tag.text
            published = ""
            d_tags = tag.findAll('time', class_='entry-date')
            if d_tags:
                published = parse(d_tags[0].attrs['datetime'])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def nm_political_report():
        """
        ###############################################
        # Scrape "New Mexico Political Report"
        ###############################################
        """
        feed_url = "https://nmpoliticalreport.com/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={'User-Agent': 'Mozilla/5.0'})  ## IMPORTANT wont work w/o!!
        news_soup = BeautifulSoup(news_r.text, 'html.parser')
        tags = news_soup.find_all('div', class_="sp-thumbnail")
        for tag in tags:
            a_tag = tag.find('a')
            img_tag = tag.find('img')
            title = img_tag.attrs['alt']
            url = a_tag.attrs['href']
            img = img_tag.attrs['src']
            news_r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            meta_tag = news_soup.find("meta", property='article:modified_time')
            if meta_tag:
                updated = parse(meta_tag.attrs['content'])
                updated = updated.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                updated = ""
            meta_tag = news_soup.find("meta", property='article:published_time')
            if meta_tag:
                published = parse(meta_tag.attrs['content'])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""
            if updated == published:
                updated = ""
            meta_tag = news_soup.find("meta", property='og:description')
            if meta_tag:
                body = meta_tag.attrs['content']
            else:
                body = ""
            meta_tag = news_soup.find("span", class_="sp-postinfo-author-name")
            if meta_tag:
                author = meta_tag.text
            else:
                author = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def alamagordo_daily():
        """
        ###############################################
        # Scrape "Alamagordo Daily Press"
        ###############################################
        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('content') and tag.has_attr('property') \
                   and tag.attrs['property'] == 'article:author'

        feed_url = "https://www.alamogordonews.com/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('a', class_='gnt_m_flm_a')
        for tag in tags:
            if tag.has_attr('data-c-br'):
                title = tag.text
                body = tag.attrs['data-c-br']
                url = source_url + tag.attrs['href']
                img_tag = tag.find('img')
                if img_tag:
                    img = source_url + img_tag.attrs['data-gl-src']
                    img = img[0: img.find('?')]
                else:
                    img = ""

                dt_tag = tag.find('div', class_='gnt_m_flm_sbt')
                if dt_tag.has_attr('data-c-dt'):
                    published = parse(dt_tag.attrs['data-c-dt'])
                    published = published.strftime("%Y-%m-%dT%H:%M:%S")
                else:
                    published = ""

                updated = ""
                news_r = requests.get(url)
                news_soup = BeautifulSoup(news_r.text, 'html5lib')
                meta_tag = news_soup.find(has_author)
                if meta_tag:
                    author = meta_tag.attrs['content']
                else:
                    author = ""
                last_update = published
                if updated:
                    last_update = updated
                news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                             'published': published, 'region': region, 'city': city, 'county': county,
                             'updated': updated, 'last_update': last_update, 'url': url, 'img': img,
                             'thumbnail': thumbnail}
                news.append(news_dict)
        return

    def abq_raw():
        """
        ###############################################
        # Scrape "Abq Raw"
        ###############################################
        """

        def has_href(tag):
            return tag.name == 'a' and tag.has_attr('href')

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('property') and tag.attrs['property'] == 'article:author'

        def has_published(tag):
            return tag.name == 'meta' and tag.has_attr('property') and tag.attrs['property'] == 'article:published_time'

        def has_update(tag):
            return tag.name == 'meta' and tag.has_attr('property') and tag.attrs['property'] == 'article:modified_time'

        def has_img(tag):
            return tag.name == 'meta' and tag.has_attr('property') and tag.attrs['property'] == 'og:image'

        feed_url = "https://www.abqraw.com/all-news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('div', class_='gallery-item-container')
        for tag in tags:
            body = tag.text
            title = tag.attrs['aria-label']

            img_tag = tag.find('img')
            if img_tag:
                img = img_tag.attrs['src']
            else:
                img = ""

            a_tag = tag.find(has_href)
            if a_tag:
                url = a_tag.attrs['href']
            else:
                url = ""

            if body.find('By:') != -1 and body.find('Posted:') != -1:
                author = body[body.find('By:') + 4:body.find('Posted:') - 1]
            else:
                author = ""

            news_r = requests.get(url)
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            meta_tag = news_soup.find(has_author)
            if meta_tag:
                author = meta_tag['content']
            else:
                author = ""

            meta_tag = news_soup.find(has_published)
            if meta_tag:
                published = parse(meta_tag['content'])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""

            meta_tag = news_soup.find(has_update)
            if meta_tag:
                updated = meta_tag['content']
            else:
                updated = ""

            meta_tag = news_soup.find(has_img)
            if meta_tag:
                img = meta_tag['content']
            else:
                img = ""

            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def valencia_county():
        """
        ###############################################
        # Scrape "Valencia County News"
        ###############################################
        """
        feed_url = "https://news-bulletin.com/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('article')
        for tag in tags:
            b_tag = tag.find('div', class_='entry-summary')
            if b_tag:
                body = cleanup(b_tag.text)
            else:
                body = ""

            img_tag = tag.find('img')
            if img_tag:
                if img_tag.has_attr('data-src'):
                    img = img_tag.attrs['data-src']
                elif img_tag.has_attr('data-lazy-src'):
                    img = img_tag.attrs['data-lazy-src']
                title = img_tag.attrs['alt']
            else:
                img = ""
                title = ""

            a_tag = tag.find('a')
            if a_tag:
                url = a_tag.attrs['href']
            else:
                url = ""

            p_tag = tag.find('span', class_='updated')
            if p_tag:
                published = parse(p_tag.text)
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""

            a_tag = tag.find('a', rel="author")
            if a_tag:
                if a_tag.has_attr('title'):
                    author = a_tag.attrs['title']
            else:
                author = ""

            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def the_independent():
        """
        ###############################################
        # Scrape "Edgewood News"
        ###############################################
        """
        feed_url = "https://edgewood.news/category/_newspack_news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url)
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('article')
        for tag in tags:

            t_tag = tag.find('h2', class_="entry-title")
            if t_tag:
                title = t_tag.text
            else:
                title = ""

            b_tag = tag.find('div', class_='entry-summary')
            if b_tag:
                body = cleanup(b_tag.text)
            else:
                body = ""

            img_tag = tag.find('img')
            if img_tag:
                img = img_tag.attrs['data-lazy-src']
            else:
                img = ""

            a_tag = tag.find('a')
            if a_tag:
                url = a_tag.attrs['href']
            else:
                url = ""

            a_tag = tag.find('a', class_='url')
            if a_tag:
                author = cleanup(a_tag.text)
            else:
                author = ""

            time_tag = tag.find('time', class_='published')
            if time_tag and time_tag.has_attr('datetime'):
                published = parse(time_tag.attrs['datetime'])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""

            time_tag = tag.find('time', class_='updated')
            if time_tag and time_tag.has_attr('datetime'):
                updated = parse(time_tag.attrs['datetime'])
                updated = updated.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                updated = ""

            if not published:
                news_r = requests.get(url)
                news_soup = BeautifulSoup(news_r.text, 'html5lib')
                time_tag = news_soup.find('meta', property='article:published_time')
                if time_tag and time_tag.has_attr('content'):
                    published = time_tag.attrs['content']
                time_tag = news_soup.find('meta', property='article:modified_time')
                if time_tag and time_tag.has_attr('content'):
                    updated = time_tag.attrs['content']

            if updated:
                last_update = updated
            else:
                last_update = published

            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def cebola_citizen():
        """
        ###############################################
        # Scrape "Cebola Citizen (Grants)"
        ###############################################
        """
        feed_url = "https://www.cibolacitizen.com"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('div', class_='views-row')
        for tag in tags:
            # ---------- title ---------- #
            title_tag = tag.find('div', class_='views-field-title')
            if title_tag:
                title = title_tag.text
            else:
                title = ""

            # ---------- author ---------- #
            author_tag = tag.find('div', class_='views-field-uid')
            if author_tag:
                author = author_tag.text
            else:
                author = ""

            # ---------- body ---------- #
            body_tag = tag.find('div', class_='views-field-body')
            if body_tag:
                body = body_tag.text
            else:
                body = ""

            # ---------- url ---------- #
            a_tag = tag.find('a')
            if a_tag:
                url = source_url + a_tag.attrs['href']
            else:
                url = ""

            # ---------- img ---------- #
            img_tag = tag.find('img')
            if img_tag:
                img = source_url + img_tag.attrs['src']
            else:
                img = ""

            # ---------- published ---------- #
            d_tag = tag.find('div', class_='views-field-created')
            if d_tag:
                published = parse(d_tag.text)
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def roosevelt_review():
        """
        ###############################################
        # Scrape "Roosevelt Review (Portales)"
        ###############################################
        """
        feed_url = "https://www.therooseveltreview.com/category/community-news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('article', class_='category-community-news')
        for tag in tags:
            a_tag = tag.find('a')
            if a_tag.has_attr('title'):
                title = cleanup(a_tag.attrs['title'])
            else:
                title = ""
            p_tag = tag.find('div', class_='entry-summary')
            if p_tag:
                body = cleanup(p_tag.text)
            else:
                body = ""
            author_tag = tag.find('a', class_='url')
            if author_tag:
                author = author_tag.text
            else:
                author = ""
            url = a_tag.attrs['href']
            img_tags = tag.findAll('img')
            if img_tags:
                img = img_tags[0].attrs['src']
            else:
                img = ""
                title = ''
            d_tags = tag.findAll('span', class_='updated')
            published = parse(d_tags[0].text)
            published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def current_argus():
        """
        ###############################################
        # Scrape "Carlsbad Current Argus"
        ###############################################
        """
        feed_url = "https://www.currentargus.com/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('a', class_=re.compile(r'^(gnt_m_he|gnt_m_flm_a)'), href=True)
        for tag in tags:
            if tag.has_attr('href'):
                title = cleanup(tag.text)

                if tag.has_attr('data-c-br'):
                    body = cleanup(tag.attrs['data-c-br'])
                else:
                    body = ""

                url = source_url + tag.attrs['href']

                news_r = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
                news_soup = BeautifulSoup(news_r.text, 'html5lib')
                meta_tag = news_soup.find('div', class_='gnt_ar_by')

                if meta_tag and meta_tag.text:
                    author = meta_tag.text
                else:
                    author = ""  # Get article author if present

                img_tag = tag.find('img')
                if img_tag:
                    if img_tag.has_attr('data-gl-src'):
                        img = img_tag.attrs['data-gl-src']
                    elif img_tag.has_attr('srcset'):
                        img = img_tag.attrs['srcset']
                    elif img_tag.has_attr('src'):
                        img = img_tag.attrs['src']
                    img = source_url + img[0: img.find('?')]
                else:
                    img = ""

                dt_tag = tag.find('div', class_='gnt_sbt')
                if dt_tag:
                    if dt_tag.has_attr('data-c-dt'):
                        published = parse(dt_tag.attrs['data-c-dt'])
                        published = published.strftime("%Y-%m-%dT%H:%M:%S")
                else:
                    published = ""
                updated = ""
                last_update = published
                if updated:
                    last_update = updated
                news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                             'published': published, 'region': region, 'city': city, 'county': county,
                             'updated': updated, 'last_update': last_update, 'url': url, 'img': img,
                             'thumbnail': thumbnail}
                news.append(news_dict)
        return

    def deming_headlight():
        """
        ###############################################
        # Scrape "Deming Headlight"
        ###############################################
        """
        feed_url = "https://www.demingheadlight.com/category/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('article', class_='article')
        for tag in tags:
            url = tag.attrs['ta_permalink']
            author_tags = tag.find('div', class_='author')
            if author_tags:
                author = author_tags.text
            else:
                author = ""

            title_tag = tag.find('div', class_='title')
            if title_tag:
                title = title_tag.text
            else:
                title = ""

            body_tag = tag.find('div', class_='body')
            if body_tag:
                body = body_tag.text
            else:
                body = ""

            img_tag = tag.find('img')
            img = ""
            if img_tag:
                attributes_to_check = ['src', 'srcset', 'data-gl-src']
                # find image
                for attr in attributes_to_check:
                    if img_tag.has_attr(attr):
                        img = img_tag[attr]
                        break
                # trim past file extension
                file_extensions = ['.jpg', '.JPG', '.jpeg', '.png']
                for ext in file_extensions:
                    index = img.find(ext)
                    if index != -1:
                        img = img[:index + len(ext)]
                        break

            date_tag = tag.find('div', class_='date')
            if date_tag:
                published = parse(date_tag.text)
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img,
                         'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def rio_rancho_observer():
        """
        ###############################################
        # Scrape "Rio Rancho Observer"
        ###############################################
        """
        feed_url = "https://rrobserver.com/news"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('article', class_='post')
        for tag in tags:

            title = get_text(tag, 'h2')

            a_tag = tag.find('a')

            url = get_attr(tag, 'a', 'href')

            author = get_class_text(tag, 'a', 'url')

            p_tags = tag.findAll('p', class_=False)
            if p_tags and len(p_tags) > 1:
                body = cleanup(p_tags[1].text)
            else:
                body = ""

            img = ""
            img_tag = tag.find('img')
            if img_tag:
                attributes_to_check = ['data-src', 'src', 'srcset', 'data-gl-src']
                # find image
                for attr in attributes_to_check:
                    if img_tag.has_attr(attr):
                        img = img_tag[attr]
                        break

            published = parse(get_class_text(tag, 'span', 'updated'))
            published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def source_nm():
        """
         ###############################################
         # Scrape "Source NM News"
         ###############################################
         """
        feed_url = "https://sourcenm.com/news"
        page_url = feed_url
        PAGES = 5
        # loop through PAGES of news
        for page in range(1, PAGES):
            if page > 1:
                page_url = feed_url + '/page/' + str(page) + '/'
            source, source_url, thumbnail, region, city, county, = get_source(feed_url)
            news_r = requests.get(page_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            tags = news_soup.find_all('div', class_='archiveCard')
            for tag in tags:
                title = get_text(tag, 'h3')
                url = get_attr(tag, 'a', 'href')
                body = get_text(tag, 'p')

                a_tag = tag.find('a', rel='author')
                if a_tag and a_tag.has_attr('title'):
                    author = a_tag.attrs['title']
                else:
                    author = ""

                img = get_attr(tag, 'img', 'src')

                dt_tag = tag.find_all('span', class_='archiveByline')[-1]
                published = parse(dt_tag.text)
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
                updated = ""
                last_update = published
                if updated:
                    last_update = updated
                news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                             'published': published, 'region': region, 'city': city, 'county': county,
                             'updated': updated, 'last_update': last_update, 'url': url, 'img': img,
                             'thumbnail': thumbnail}
                news.append(news_dict)
        return

    def koat():
        """
          ###############################################
          # Scrape "KOAT Action News"
          ###############################################
          """
        feed_url = "https://koat.com/local-news/"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('div', class_="article")
        for tag in tags:
            title = get_attr(tag, 'a', 'aria-label')
            url = source_url + get_attr(tag, 'a', 'href')

            img_tag = tag.find('div', class_='image')
            if img_tag and img_tag.has_attr('data-style'):
                img = img_tag.attrs['data-style']
                # Define a regular expression pattern to extract the URL
                pattern = re.compile(r'background-image:url\((https://[^?]+)')
                # Use the pattern to find the URL in the string
                img = pattern.search(img)
                img = img.group(1)

            author = get_class_text(tag, 'div', 'author-name')

            try:
                news_r = requests.get(url)
            except:
                continue
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            body = get_class_text(news_soup, 'div', 'article-content--body-text')

            dt_tag = news_soup.find('meta', property="datepublished")
            published = parse(dt_tag.attrs['content'])
            published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def krqe():
        """
          ###############################################
          # Scrape "KRQE Local Reporting you can Trust"
          ###############################################
          """
        feed_url = "https://www.krqe.com/news/top-stories/"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all("article", class_="article-list__article", attrs={'data-collection': 'article-list3'})

        for tag in tags:
            title = get_attr(tag, 'a', 'data-link-label')
            url = get_attr(tag, 'a', 'href')
            img = get_attr(tag, 'img', 'src')

            news_r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
            news_soup = BeautifulSoup(news_r.text, 'html5lib')

            body = get_class_text(news_soup, 'div', 'article-body')
            author = get_class_text(news_soup, 'p', 'article-authors')
            published = get_attr_date(tag, 'time', 'datetime')
            updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    def kob():
        """
          ###############################################
          # Scrape "KOB 4"
          ###############################################
          """
        feed_url = "https://www.kob.com/new-mexico/albuquerque-metro/"
        source, source_url, thumbnail, region, city, county, = get_source(feed_url)
        news_r = requests.get(feed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
        news_soup = BeautifulSoup(news_r.text, 'html5lib')
        tags = news_soup.find_all('div', class_='embed-responsive-item')
        for tag in tags:
            h_tag = tag.find_next(re.compile("^h"))
            if h_tag:
                title = h_tag.text
            else:
                title = ""

            a_tag = tag.findParent('a')
            if a_tag:
                url = a_tag.attrs['href']
            else:
                url = ""

            img = get_attr(tag, 'img', 'data-src')

            news_r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
            news_soup = BeautifulSoup(news_r.text, 'html5lib')
            meta_tag = news_soup.find('meta', attrs={'name': 'author'})
            if meta_tag:
                author = meta_tag.attrs['content']
            else:
                author = ""

            bd_tag = news_soup.find('meta', property="og:description")
            if bd_tag:
                body = bd_tag.attrs['content']
            else:
                body = ""

            dt_tag = news_soup.find('meta', property="article:published_time")
            if dt_tag:
                published = parse(dt_tag.attrs['content'])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                dt_tag = ""

            dt_tag = news_soup.find('meta', property="article:modified_time")
            if dt_tag:
                updated = parse(dt_tag.attrs['content'])
                updated = updated.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                updated = ""
            last_update = published
            if updated:
                last_update = updated
            news_dict = {'source': source, 'source_url': source_url, 'title': title, 'body': body, 'author': author,
                         'published': published, 'region': region, 'city': city, 'county': county,
                         'updated': updated, 'last_update': last_update, 'url': url, 'img': img, 'thumbnail': thumbnail}
            news.append(news_dict)
        return

    """ 
    Main loop. Scrape news from model of published sources and execute function to scrape. Sort dictionary containing 
    news articles and output to json file. This function runs using http://burquebro.com/news/update or by cron 
    job that runs every hour.
    """

    # messages.info(req, 'Welcome to burquebro.com the place to go for the latest New Mexico news!')
    filename = 'access_log'
    with open(filename, 'a', newline='') as file:
        data = writer(file)
        list_data = ['Python', sys.version, sys.version_info]
        data.writerow(list_data)
        file.close()

    news = []
    news_list = News.objects.filter(published=True)
    for news_source in news_list:
        function = news_source.function
        eval(function + "()")

    # Sort list by title and remove duplicate key values.

    news = sorted(news, key=lambda x: x['title'])
    last_title = ""
    new_news = []
    for article in news:
        if article['title'] == last_title:
            continue
        else:
            new_news.append(article)
            last_title = article['title']
    news = new_news

    # sort dictionary by date in reverse chrono and write to json file
    news = sorted(news, key=lambda d: d['published'])[::-1]
    """
    Clean up data in news dictionary prior to committing to json file.
    """
    for article in news:
        max_len = 256
        if len(article['body']) > max_len:
            article['body'] = adjust_string_length(article['body'], max_len)

        base_name, extension = os.path.splitext(article['img'])
        match = re.match(r'^(.*-)(\d+)x\d+$', base_name)
        if match:
            article['img'] = match.group(1)[:len(match.group(1)) - 1] + extension
        else:
            article['img'] = base_name + extension

        article['city'] = article['city'].replace(" ", "_")
        article['county'] = article['county'].replace(" ", "_")
        if article['published']:
            if article['published'].find('T') != -1:
                date_time_obj = datetime.strptime(article['published'][:19], '%Y-%m-%dT%H:%M:%S')
            else:
                date_time_obj = datetime.strptime(article['published'][:19], '%Y-%m-%d %H:%M:%S')
            pub_time = date_time_obj.strftime("%H:%M")
            if pub_time == "00:00":  # if time wasnt given dont display
                article['published'] = date_time_obj.strftime("%A %B %d %Y")
            else:
                article['published'] = date_time_obj.strftime("%A %B %d %Y %H:%M%p")
        if article['updated']:
            date_time_obj = datetime.strptime(article['updated'][:19], '%Y-%m-%dT%H:%M:%S')
            pub_time = date_time_obj.strftime("%H:%M")
            if pub_time == "00:00":  # if time wasnt given dont display
                article['updated'] = date_time_obj.strftime("%A %B %d %Y")
            else:
                article['updated'] = date_time_obj.strftime("%A %B %d %Y %H:%M%p")

    with open(settings.BQB_URL + "news.json", "w") as outfile:
        json.dump(news, outfile, indent=4)
    return news


def news_update(req):
    write_access_log(req, 'Update Started')
    region = 'New Mexico'
    news = scrape_news()
    news = filter_max_articles(scrape_news())
    write_access_log(req, 'Update Completed')
    return render(req, 'news/index_old.html', {'category': region, 'news': news})
