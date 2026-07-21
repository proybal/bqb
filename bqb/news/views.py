# views.py -pr
import re
import sys
import time
import requests
from bs4 import BeautifulSoup
import json
from .models import News
from dateutil.parser import *
import datetime
from datetime import date, datetime, timedelta
from csv import writer
from django.conf import settings
import os
from dateutil import tz
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
import random
from django.contrib import messages

def parse_relative_time(relative_time_str):
    # Get the current time
    now = datetime.now()

    # Define regex to match expressions like '15 minutes ago', '3 hours ago', etc.
    match = re.match(r'(\d+)\s+(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\s+ago', relative_time_str,
                     re.IGNORECASE)
    if not match:
        return False

    # Extract the amount and the unit
    amount = int(match.group(1))
    unit = match.group(2).lower()

    # Convert to singular if plural
    if unit.endswith('s'):
        unit = unit[:-1]

    # Use relativedelta to calculate the past time
    delta_args = {unit: amount}
    past_time = now - relativedelta(**delta_args)

    return past_time

# def get_past_date(str_days_ago):
#     TODAY = datetime.now()
#     splitted = str_days_ago.split()
#     if len(splitted) == 1 and splitted[0].lower() == 'today':
#         return str(TODAY.isoformat())
#     elif len(splitted) == 1 and splitted[0].lower() == 'yesterday':
#         date = TODAY - relativedelta(days=1)
#         return str(date.isoformat())
#     elif splitted[1].lower() in ['hour', 'hours', 'hr', 'hrs', 'h']:
#         date = datetime.now() - relativedelta(hours=int(splitted[0]))
#         return str(date.date().isoformat())
#     elif splitted[1].lower() in ['day', 'days', 'd']:
#         date = TODAY - relativedelta(days=int(splitted[0]))
#         return str(date.isoformat())
#     elif splitted[1].lower() in ['wk', 'wks', 'week', 'weeks', 'w']:
#         date = TODAY - relativedelta(weeks=int(splitted[0]))
#         return str(date.isoformat())
#     elif splitted[1].lower() in ['mon', 'mons', 'month', 'months', 'm']:
#         date = TODAY - relativedelta(months=int(splitted[0]))
#         return str(date.isoformat())
#     elif splitted[1].lower() in ['yrs', 'yr', 'years', 'year', 'y']:
#         date = TODAY - relativedelta(years=int(splitted[0]))
#         return str(date.isoformat())
#     else:
#         # return False
#         return str(TODAY.isoformat())


# def adjust_string_length(input_string, max_length):
#     if len(input_string) <= max_length:
#         return input_string
#
#     truncated_string = input_string[:max_length]
#
#     last_space_index = truncated_string.rfind(' ')
#     last_period_index = truncated_string.rfind('.')
#
#     if last_space_index > last_period_index:
#         truncated_string = truncated_string[:last_space_index] + '...'
#     elif last_period_index != -1:  # Check if a period was found
#         truncated_string = truncated_string[:last_period_index]
#
#     return truncated_string.strip()


# def filter_max_articles(news):
#     if settings.MAX_ARTICLES < 99:
#         news = sorted(news, key=lambda x: (x['source'], x['last_update']), reverse=True)
#         last_article = ""
#         new_news = []
#         article_count = 1
#         for article in news:
#             if article['source'] == last_article:
#                 article_count += 1
#             else:
#                 article_count = 1
#                 last_article = article['source']
#             if article_count <= settings.MAX_ARTICLES:
#                 new_news.append(article)
#
#         news = sorted(new_news, key=lambda x: x['last_update'])[::-1]
#         # Group news randomly by day
#         daily_news = []
#         new_news = []
#         day = ""
#         for item in news:
#             if item['last_update'][:10] == day:
#                 daily_news.append(item)
#             else:
#                 day = item['last_update'][:10]
#                 random.shuffle(daily_news)
#                 new_news = new_news + daily_news
#                 daily_news.clear()
#                 daily_news.append(item)
#         new_news = new_news + daily_news
#
#         news = new_news
#
#     return news


def shuffle_news(news):
    # Group news randomly by day
    daily_news = []
    new_news = []
    day = ""
    for item in news:
        if item['last_update'][:10] == day:
            daily_news.append(item)
        else:
            day = item['last_update'][:10]
            random.shuffle(daily_news)
            new_news = new_news + daily_news
            daily_news.clear()
            daily_news.append(item)
    new_news = new_news + daily_news

    return new_news


def remove_duplicates(news):
    seen = set()
    unique_news = []

    for article in news:
        title_source_pair = (article['title'], article['source'])
        if title_source_pair not in seen:
            seen.add(title_source_pair)
            unique_news.append(article)

    return unique_news


def write_error_log(message):
    FILE_NAME = 'error_log'
    with open(FILE_NAME, 'a', newline='') as file:
        data = writer(file)
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/Denver')
        utc = datetime.utcnow()
        utc = utc.replace(tzinfo=from_zone)
        denver = utc.astimezone(to_zone)
        time_out = denver.strftime("%m-%d-%Y %H:%M:%S")
        list_data = [time_out, message]
        data.writerow(list_data)
        file.close()


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
        # location_data = get_location(ip)
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/Denver')
        utc = datetime.utcnow()
        utc = utc.replace(tzinfo=from_zone)
        denver = utc.astimezone(to_zone)
        time_out = denver.strftime("%m-%d-%Y %H:%M:%S")
        # list_data = [time_out, ip, location_data['city'], location_data['country'], category, hostname]
        list_data = [time_out, ip, category, hostname]
        data.writerow(list_data)
        file.close()


def truncate_news_body(news, max_words=50):
    """
    Truncate the 'body' field of each news item in the provided list to the specified maximum number of words.
    """
    for article in news:
        if article['body']:
            body_words = article['body'].split()
            truncated_body = ' '.join(body_words[:max_words])
            article['body'] = truncated_body
        else:
            article['body'] = ""
    return news


def index(request):
    write_access_log(request, 'Home')
    category = 'New Mexico'
    with open('news.json') as json_file:
        news = json.load(json_file)
    news = truncate_news_body(news)
    news = shuffle_news(news)
    return render(request, 'news/index.html', {'category': category, 'news': news})


def search(request, search):
    write_access_log(request, 'Home')
    category = 'New Mexico'
    with open('news.json') as json_file:
        news = json.load(json_file)
    news = truncate_news_body(news)
    matched_items = []

    for item in news:
        title = item['title'].lower()  # Convert title to lowercase for case-insensitive comparison
        body = item['body'].lower()  # Convert body to lowercase for case-insensitive comparison

        # Check if search term is present in either title or body
        if search in title or search in body:
            matched_items.append(item)

    news = shuffle_news(matched_items)

    # random.shuffle(news)
    return render(request, 'news/index.html', {'category': category, 'news': news})


def state_news(req):
    state = 'New Mexico'
    write_access_log(req, state)
    with open('news.json') as json_file:
        news = json.load(json_file)
    news = shuffle_news(news)
    news = truncate_news_body(news)
    return render(req, 'news/index.html', {'category': state, 'news': news})


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
    news = shuffle_news(new_news)
    news = truncate_news_body(news)
    return render(req, 'news/index.html', {'category': region, 'news': news})


def by_city(req, city):
    write_access_log(req, city)
    with open('news.json') as json_file:
        news = json.load(json_file)
    new_news = []
    for news_item in news:
        if news_item['city'] == city:
            new_news.append(news_item)
    city = city.replace("_", " ")
    news = shuffle_news(new_news)
    news = truncate_news_body(news)
    return render(req, 'news/index.html', {'category': city, 'news': news})


def by_county(req, county):
    write_access_log(req, county + ' County')
    with open('news.json') as json_file:
        news = json.load(json_file)
    new_news = []
    for news_item in news:
        if news_item['county'] == county:
            new_news.append(news_item)
    county = county.replace("_", " ")
    news = shuffle_news(new_news)
    news = truncate_news_body(news)
    return render(req, 'news/index.html', {'category': county, 'news': news})


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

    def get_date(tag, tag_to_find, class_=None, attr=None, itemprop=None, property=None):
        def has_date(tag):
            if attr and not class_:
                return tag.name == tag_to_find and tag.has_attr(attr)
            elif class_:
                return tag.name == tag_to_find and class_ in tag.attrs.get('class', [])
            if itemprop:
                return tag.name == tag_to_find and itemprop in tag.attrs.get('itemprop', [])
            if property:
                return tag.name == tag_to_find and property in tag.attrs.get('property', [])

        t = tag.find(has_date)
        if not t:
            return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        if itemprop or property:
            tag_date = t.attrs['content']
        elif t.has_attr(attr):
            tag_date = t.attrs[attr]
        else:
            tag_date = t.text
        try:
            return parse(tag_date).strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError as e:
            if tag_date and parse_relative_time(tag_date):
                return parse_relative_time(tag_date).strftime("%Y-%m-%dT%H:%M:%S")
        return ""

    def get_text(tag, tag_to_find):
        t = tag.find(tag_to_find)
        if t and t.text:
            return cleanup(t.text)
        else:
            return ""

    def get_body_text(tag):
        t = tag.findAll('p')
        body = ""
        for tx in t:
            body += cleanup(tx.text) + " "
        return body

    def get_meta(soup, value):
        tag = soup.find('meta', value)
        if tag:
            return tag.get('content')
        return False

    def get_img(tag):
        img = ""
        img_tag = tag.find('img')
        if img_tag:
            if img_tag.has_attr('src'):
                img = img_tag.attrs['src']
            elif img_tag.has_attr('srcset'):
                img = img_tag.attrs['srcset']
            elif img_tag.has_attr('data-srcset'):
                img = img_tag.attrs['data-srcset']
            img = img[0: img.find('?')]
        return img

    def get_tags(url, tag, class_):
        try:
            news_request = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
            # news_request = requests.get(url)
        except Exception as e:
            write_error_log(e)
            return False
        tags = BeautifulSoup(news_request.text, 'html5lib').find_all(tag, class_=class_)
        if not tags:
            write_error_log(f"News source {news_source.feed_url} returned no results.")
            return
        return tags

    def get_soup(url):
        try:
            news_request = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'})
            # news_request = requests.get(url)
        except Exception as e:
            write_error_log(e)
            return False
        return BeautifulSoup(news_request.text, 'html5lib')

    def add_article(title, body, author, published, updated, url, img):
        if not published:
            write_error_log(f"News source {news_source.feed_url} has no published date.")
            return
        # Use regular expression to extract date and time components
        match = re.search(r'(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})', published)
        if match:
            extracted_datetime = match.group(1)
            # Replace 'T' with space for consistent format
            extracted_datetime = extracted_datetime.replace(' ', 'T')

            published = datetime.strptime(extracted_datetime, "%Y-%m-%dT%H:%M:%S")

        else:
            published = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # Check if the published date is in the future
        if published > datetime.now():
            # Reset the date and time to today at 00:00 hours
            published = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        published = published.strftime("%Y-%m-%dT%H:%M:%S")

        last_update = published
        if updated:
            last_update = updated
        news_dict = {'source': str(news_source.title), 'source_url': str(news_source.source), 'title': title,
                     'body': body, 'author': author,
                     'published': published, 'region': str(news_source.region), 'city': str(news_source.city),
                     'county': str(news_source.county),
                     'updated': updated, 'last_update': last_update, 'url': url, 'img': img,
                     'thumbnail': str(news_source.cover)}
        news.append(news_dict)
        return

    def cleanup(str):
        return re.sub(r'[\n\t]+', ' ', str).strip()

    # def find_tag(tag, class_, attr):

    def abqjournal():
        """
        ########################################
        # Scrape "Albuquerque Journal" news
        ########################################
        """
        tags = get_tags(news_source.feed_url, 'article', 'tnt-asset-type-article')
        if not tags:
            return
        for tag in tags:

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
            if not news_soup:
                continue
            meta_tag = news_soup.find('meta', attrs={'name': 'author'})
            if meta_tag:
                author = meta_tag.attrs['content']
            else:
                author = ""

            published = get_date(news_soup, 'time', 'tnt-date', 'datetime')

            updated = get_date(news_soup, 'time', 'tnt-update-recent', 'datetime')

            add_article(title, body, author, published, updated, url, img)

    def citydesk():
        """
        ########################################
        # Scrape "City Desk" news
        ########################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_='type-post')
        if not tags:
            return
        for tag in tags:
            title = get_text(tag, 'h3')
            url = get_attr(tag, 'a', 'href')
            if not title:
                title = get_text(tag, 'h2')
                utag = tag.find('h2')
                url = get_attr(utag, 'a', 'href')

            body = get_class_text(tag, 'div', 'newspack-post-subtitle')

            img = get_class_attr(tag, 'img', 'wp-post-image', 'src')
            if not img:
                news_soup = get_soup(url)
                img = get_class_attr(news_soup, 'img', 'attachment-newspack-featured-image', 'src')
                if not img:
                    img = get_class_attr(news_soup, 'img', 'wp-post-image', 'src')

            news_soup = get_soup(url)
            if not news_soup:
                continue
            author = get_meta(news_soup, {'name': 'author'})

            published = get_meta(news_soup, {'property': 'article:published_time'})[:19]

            updated = get_meta(news_soup, {'property': 'article:modified_time'})[:19]

            add_article(title, body, author, published, updated, url, img)

        return

    def thepaper():
        """
        ########################################
        # Scrape "The Paper" news
        ########################################
        """
        tags = get_tags(news_source.feed_url, 'article', 'post')
        if not tags:
            return
        for tag in tags:
            title = get_class_text(tag, 'h2', 'entry-title')

            body = cleanup(tag.text)

            url = get_attr(tag, 'a', 'href')

            img = get_class_attr(tag, 'img', 'wp-post-image', 'src')

            author = get_class_text(tag, 'span', 'author')

            published = get_date(tag, 'time', 'published', 'datetime')

            updated = get_date(tag, 'time', 'updated', 'datetime')

            add_article(title, body, author, published, updated, url, img)

    def joemonahan():
        """
        ###############################################
        # Scrape "New Mexico Politics with Joe Monahan
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', class_="blogPost")
        if not tags:
            return
        for tag in tags:
            title_tag = tag.previous_sibling.previous_sibling
            if title_tag and title_tag.text:
                title = title_tag.text
            else:
                title = ""

            body = cleanup(tag.text)

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
        tags = get_tags(news_source.feed_url, 'article', class_='tnt-asset-type-article')
        if not tags:
            return
        for tag in tags:

            title = get_attr(tag, 'a', 'aria-label')
            if not title:
                title = get_text(tag, 'a')

            body = get_class_text(tag, 'p', 'tnt-summary')
            if len(body) <= 20 or title == body:
                body = ""

            url = news_source.source + get_attr(tag, 'a', 'href')

            img = get_attr(tag, 'img', 'data-srcset')

            author = get_class_text(tag, 'div', 'card-meta')

            news_soup = get_soup(url)
            if not news_soup:
                continue
            published = get_date(news_soup, 'meta', itemprop='dateCreated')
            updated = get_date(news_soup, 'meta', itemprop='dateModified')

            add_article(title, body, author, published, updated, url, img)

        return

    def riograndesun():
        """
        ###############################################
        # Scrape "Rio Grande Sun"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', 'tnt-asset-type-article')
        if not tags:
            return
        for tag in tags:

            title = get_class_attr(tag, 'a', 'tnt-asset-link', 'aria-label')

            url = news_source.source + get_class_attr(tag, 'a', 'tnt-asset-link', 'href')

            body = get_body_text(tag)

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

            published = get_date(tag, 'time', attr='datetime')

            updated = get_date(tag, 'time', 'tnt-update-recent', 'datetime')

            news_soup = get_soup(url)
            if not news_soup:
                continue
            author_tag = news_soup.find('span', itemprop='author')
            if author_tag:
                author = cleanup(author_tag.text)
            else:
                author = ""

            add_article(title, body, author, published, updated, url, img)
        return

    def lascrucessun():
        """
        ###############################################
        # Scrape "Las Cruces Sun"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'a', class_=['gnt_m_he', 'gnt_m_flm_a'])
        if not tags:
            return

        for tag in tags:
            # Skip if not a valid tag
            if tag.has_attr('rel'):
                continue

            if tag.text:
                title = tag.text
            else:
                title = ""

            body = get_attr(tag, None, 'data-c-br')
            author = ""
            url = news_source.source + get_attr(tag, None, 'href')

            img_tag = tag.find('img')
            img_attributes = ['src', 'srcset', 'data-gl-src']

            img = ""
            if img_tag:
                for attr in img_attributes:
                    if img_tag.has_attr(attr):
                        img = img_tag.attrs[attr]
                        img = img[0: img.find('?')]
                        img = news_source.source + img
                        break
            news_soup = get_soup(url)
            if not news_soup:
                continue
            author = get_class_text(news_soup, "div", "gnt_ar_by")
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

            add_article(title, body, author, published, updated, url, img)

        return

    def hobbssun():
        """
        ###############################################
        # Scrape "Hobbs Sun"
        ###############################################
        """
        page_url = news_source.feed_url
        PAGES = 12
        # loop through PAGES of news
        for page in range(1, PAGES):
            if page > 1:
                page_url = news_source.feed_url + '/page/' + str(page) + '/'

            tags = get_tags(news_source.feed_url, 'article', class_="")
            if not tags:
                return
            for tag in tags:

                title = get_text(tag, 'h2')

                body = get_body_text(tag)

                url = get_attr(tag, 'a', 'href')

                img = get_attr(tag, 'img', 'data-src')

                a_tag = tag.find('a', rel='author')
                if a_tag and a_tag.text:
                    author = a_tag.text
                else:
                    author = ""

                published = get_date(tag, 'span', 'bdayh-date')
                updated = ""

                add_article(title, body, author, published, updated, url, img)

        return

    def taosnews():
        """
        ###############################################
        # Scrape "Taos News"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_='tnt-asset-type-article')
        if not tags:
            return
        for tag in tags:

            title = get_attr(tag, 'a', 'aria-label')

            url = news_source.source + get_attr(tag, 'a', 'href')

            img = get_attr(tag, 'img', 'data-srcset')

            body = get_class_text(tag, 'div', 'card-lead')

            news_soup = get_soup(url)
            if not news_soup:
                continue
            if body == "":
                body = get_meta(news_soup, {'property': 'og:description'})

            meta_tags = news_soup.find_all('meta')
            author = ""
            for meta_tag in meta_tags:
                if meta_tag.has_attr('name') and meta_tag.attrs['name'] == 'author':
                    author = meta_tag.attrs['content']

            published = get_date(news_soup, 'time', 'tnt-date', 'datetime')

            updated = get_date(news_soup, 'time', 'tnt-update-recent', 'datetime')

            add_article(title, body, author, published, updated, url, img)

        return

    def gallupsun():
        """
        ###############################################
        # Scrape "Gallup Sun News"
        ###############################################
        """

        def remove_suffix(input_string):
            # Use regular expression to match "resized/" and underscore followed by one or more digits
            pattern = re.compile(r'(images/resized/|_\d+)')
            match = pattern.search(input_string)

            # If the pattern is found, remove it
            while match:
                input_string = input_string[:match.start()] + input_string[match.end():]
                match = pattern.search(input_string)

            return input_string

        # Example usage
        input_string = "resized/some_text_before_2_3_second_last_underscore_to_remove.jpg"
        result = remove_suffix(input_string)
        PAGES = 10
        page_url = news_source.feed_url
        limitstart = 0
        # loop through PAGES of news
        for page in range(1, PAGES):

            tags = get_tags(news_source.feed_url, 'div', class_='contentpaneopen')
            if not tags:
                return
            for tag in tags:
                body = cleanup(tag.text)

                title = get_class_text(tag, 'h2', 'contentheading')

                url = news_source.source + get_attr(tag, 'a', 'href')

                author = get_class_text(tag, 'span', 'createby')

                # news_soup = get_soup(url)

                img = news_source.source + remove_suffix(get_class_attr(tag, 'img', 'caption', 'src'))

                published = get_date(tag, 'span', 'createdate')

                updated = ""

                add_article(title, body, author, published, updated, url, img)

                limitstart += 5
                page_url = news_source.feed_url + '&limitstart=' + str(limitstart)

        return

    def artesia_news():
        """
        ###############################################
        # Scrape "Artesian News"
        ###############################################
        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('name') and tag.attrs['name'] == 'author'

        tags = get_tags(news_source.feed_url, 'div', class_="td-cpt-post")
        if not tags:
            return
        for tag in tags:
            url = get_attr(tag, 'a', 'href')

            title = get_attr(tag, 'a', 'title')

            img = get_attr(tag, 'span', 'data-img-url')

            # body = get_body_text(tag)

            news_soup = get_soup(url)
            if not news_soup:
                continue
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

            published = get_date(news_soup, 'time', attr='datetime')

            updated = ""

            add_article(title, body, author, published, updated, url, img)
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

        tags = get_tags(news_source.feed_url, 'div', class_="news")
        if not tags:
            return
        for tag in tags:
            url = news_source.source + get_attr(tag, 'a', 'href')

            title = get_text(tag, re.compile('^h'))
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

            body = get_class_text(tag, 'div', 'content')

            news_soup = get_soup(url)
            if not news_soup:
                continue

            author_tag = news_soup.find(has_author)
            if author_tag:
                author = author_tag.attrs['content']
            else:
                author = ""

            published = get_date(news_soup, 'meta', itemprop='datePublished')

            updated = get_date(news_soup, 'meta', itemprop='dateModified')

            add_article(title, body, author, published, updated, url, img)

        return

    def pinonpost():
        """
        ###############################################
        # Scrape "Pinon Post"
        ###############################################
        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('name') and tag.attrs['name'] == 'author'

        tags = get_tags(news_source.feed_url, "article", class_='jeg_post')
        if not tags:
            return
        for t, tag in enumerate(tags):
            title = tag.text
            if title.find('by Piñon') != -1:
                title = title[:title.find('by Piñon')]
            if title.find('by Renato') != -1:
                title = title[:title.find('by Renato')]

            url = get_attr(tag, 'a', 'href')

            news_soup = get_soup(url)
            if not news_soup:
                continue

            body = get_body_text(news_soup)
            if body.find('by John'):
                body = body[:body.find('by John')]

            author_tag = news_soup.find(has_author)
            if author_tag:
                author = author_tag.attrs['content']
            else:
                author = ""

            img_tag = news_soup.find('img', class_='wp-post-image')
            if img_tag:
                if img_tag.has_attr('src'):
                    img = img_tag.attrs['src']
                elif img_tag.has_attr('srcset'):
                    img = img_tag.attrs['srcset']
                elif img_tag.has_attr('data-src'):
                    img = img_tag.attrs['data-src']
            else:
                img = ""

            published = get_date(news_soup, 'span', 'published')
            updated = ""

            add_article(title, body, author, published, updated, url, img)

            if t == 20:
                break
        return

    def lasvegasoptic():
        """
        ###############################################
        # Scrape "Las Vegas Optic
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_='tnt-section-news')
        if not tags:
            return
        for tag in tags:

            title = get_attr(tag, 'a', 'aria-label')

            url = news_source.source + get_attr(tag, 'a', 'href')

            body = get_body_text(tag)

            img_tag = tag.find('img')
            if img_tag:
                if img_tag.has_attr('data-srcset'):
                    img = img_tag.attrs['data-srcset']
                elif img_tag.has_attr('srcset'):
                    img = img_tag.attrs['srcset']
                img = img[0: img.find('?')]
            else:
                img = ""

            news_soup = get_soup(url)
            if not news_soup:
                continue

            if not body:
                body = get_body_text(news_soup)
            author = get_class_text(news_soup, 'span', 'tnt-user-name')

            published = get_date(tag, 'time', 'tnt-date', 'datetime')
            if not published:
                published = get_date(news_soup, 'time', 'tnt-date', 'datetime')
            updated = ""
            add_article(title, body, author, published, updated, url, img)

        return

    def roswelldaily():
        """
        ###############################################
        # Scrape "Roswell Daily Record
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_='tnt-section-news')
        if not tags:
            return
        for tag in tags:

            title = get_attr(tag, 'a', 'aria-label')

            url = news_source.source + get_attr(tag, 'a', 'href')

            body = get_body_text(tag)

            published = get_date(tag, 'time', attr='datetime')

            author = get_class_text(tag, 'span', 'tnt-byline')

            img = ""
            img_tag = tag.find('img')
            if img_tag:
                if img_tag.has_attr('data-srcset'):
                    img = img_tag.attrs['data-srcset']
                elif img_tag.has_attr('srcset'):
                    img = img_tag.attrs['srcset']
                img = img[0: img.find('?')]
            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def farmingtondaily():
        """
        ###############################################
        # Scrape "Farmington Daily Times"
        ###############################################
        """

        news_soup = get_soup(news_source.feed_url)
        if not news_soup:
            return
        tags = news_soup.find('div', id='headlines-articles')
        if not tags:
            write_error_log(f"News source {news_source.feed_url} returned no results.")
            return
        tags = tags.find_all('div', class_="frontpage-headlines-title")
        for tag in tags:

            title = cleanup(tag.text)

            url = get_attr(tag, 'a', 'href')


            news_soup = get_soup(url)
            img = ""
            img_tag = news_soup.find('img', class_='image')
            if img_tag and img_tag.has_attr('src'):
                img = img_tag.attrs['src']

            body = get_body_text(news_soup)
            author = get_meta(news_soup, {'name': 'author'})
            published = get_meta(news_soup, {'name': 'pubdate'})
            updated = ''

            add_article(title, body, author, published, updated, url, img)

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

        tags = get_tags(news_source.feed_url, 'div', class_='hmfunction_sectioncontainer')
        if not tags:
            return
        for tag in tags:

            title = get_text(tag, 'h3')

            body = get_body_text(tag)

            author = get_text(tag, 'a')

            a_tag = tag.find(has_author)
            if a_tag:
                url = a_tag.attrs['href']
            else:
                url = ""

            news_soup = get_soup(url)
            if not news_soup:
                continue

            img_tag = news_soup.find('div', class_='top_image_left')
            img = ""
            if img_tag:
                img_tag = img_tag.find('img')
                if img_tag:
                    img = news_source.source + img_tag.attrs['src']

            dt_tag = tag.find('span')
            if dt_tag:
                published = dt_tag.text
                published = parse(published[published.find('/') - 2:])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""
            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def defensor_chieftain():
        """
        ###############################################
        # Scrape "El Defensor Cheiftain" (socorro)
        ###############################################
        """
        news_soup = get_soup(news_source.feed_url)
        if not news_soup:
            return
        tags = news_soup.find_all('article')
        if not tags:
            write_error_log(f"News source {news_source.feed_url} returned no results.")
            return
        for tag in tags:
            body = ""
            body_tag = tag.find('div', class_='entry-summary')
            if body_tag:
                body = get_body_text(body_tag)

            author_tag = tag.find('p')
            author = ""
            if author_tag:
                author_tag = author_tag.find('a')
                if author_tag:
                    author = author_tag.attrs['title']

            title = get_text(tag, 'h2')

            url = get_attr(tag, 'a', 'href')

            news_soup = get_soup(url)
            if not news_soup:
                continue

            img = get_class_attr(news_soup, 'img', 'size-medium', 'data-lazy-src')

            published = get_date(tag, 'span', 'updated')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def la_daily_post():
        """
        ###############################################
        # Scrape "Los Alamos Daily Post"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_='post')
        if not tags:
            return
        for tag in tags:

            author = get_class_text(tag, 'span', 'elementor-post-author')

            title = get_text(tag, 'a')

            body = get_body_text(tag)

            url = get_attr(tag, 'a', 'href')

            img = get_class_attr(tag, 'img', re.compile('^wp-image'), 'src')

            published = get_date(tag, 'span', 'elementor-post-date')

            updated = ""

            # added the conditional because articles are duplicated w/o img
            if img:
                add_article(title, body, author, published, updated, url, img)

        return

    def sc_daily_press():
        """
        ###############################################
        # Scrape "Silver City Daily Press"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', ['div.item-container, div.post-content'])
        if not tags:
            return

        for tag in tags:

            title = get_text(tag, 'h2')

            body = get_body_text(tag)

            url = get_attr(tag, 'a', 'href')

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

            news_soup = get_soup(url)
            if not news_soup:
                continue

            b_tag = news_soup.find('div', class_='ls-post-content')
            if b_tag:
                p_tag = b_tag.find('p')
                body = get_body_text(p_tag)

                img_tag = b_tag.find('img')
                if img_tag and img_tag.has_attr('srcset') and img == "":
                    img = img_tag.attrs['srcset']
                    matches = pattern.findall(img)
                    # Display the extracted URLs
                    img = matches[0]

            author = ""
            a_tag = news_soup.find('a', rel='author')
            if a_tag:
                author = a_tag.text

            published = get_date(tag, 'span', 'date')
            if not published:
                published = get_date(tag, 'time', 'published', 'datetime')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def nm_political_report():
        """
        ###############################################
        # Scrape "New Mexico Political Report"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', class_="sp-thumbnail")
        if not tags:
            return
        for tag in tags:

            title = get_attr(tag, 'img', 'alt')

            url = get_attr(tag, 'a', 'href')

            img = get_attr(tag, 'img', 'src')

            news_soup = get_soup(url)
            if not news_soup:
                continue

            # published = get_date(news_soup, 'meta', property='article:published_time')
            # updated = get_date(news_soup, 'meta', property='article:modified_time')
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
            author = get_class_text(news_soup, 'span', 'sp-postinfo-author-name')

            add_article(title, body, author, published, updated, url, img)

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

        tags = get_tags(news_source.feed_url, 'a', class_='gnt_m_flm_a')
        if not tags:
            return
        for tag in tags:
            if tag.has_attr('data-c-br'):
                title = tag.text
                body = tag.attrs['data-c-br']
                url = news_source.source + tag.attrs['href']
                img_tag = tag.find('img')
                if img_tag:
                    img = news_source.source + img_tag.attrs['data-gl-src']
                    img = img[0: img.find('?')]
                else:
                    img = ""

                published = get_date(tag, 'div', 'gnt_m_flm_sbt', 'data-c-dt')

                updated = ""

                news_soup = get_soup(url)
                if not news_soup:
                    continue

                meta_tag = news_soup.find(has_author)
                if meta_tag:
                    author = meta_tag.attrs['content']
                else:
                    author = ""

                add_article(title, body, author, published, updated, url, img)

        return

    def ruidoso_news():
        """
        ###############################################
        # Scrape "Ruidoso Daily News"
        ###############################################
        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('content') and tag.has_attr('property') \
                   and tag.attrs['property'] == 'article:author'

        tags = get_tags(news_source.feed_url, 'a', class_='gnt_m_flm_a')
        if not tags:
            return
        for tag in tags:
            # if tag.has_attr('data-c-br'):
            title = tag.text
            if tag.has_attr('data-c-br'):
                body = tag.attrs['data-c-br']
            else:
                body = ""
            url = ""
            if tag.has_attr('href'):
                url = news_source.source + tag.attrs['href']
            if not url and tag.has_attr('data-gl-src'):
                url = tag.attrs['data-gl-src']
            if not url:
                continue
            updated = ""
            news_soup = get_soup(url)
            if not news_soup:
                continue

            img = get_meta(news_soup, {'property': 'og:image'})
            published = get_date(tag, 'div', 'gnt_m_flm_sbt', 'data-c-dt')
            if not published:
                dt = get_class_attr(news_soup, 'div', 'gnt_ar_dt', 'aria-label')
                if dt:
                    published = parse(dt[dt.find('Published') + 10:dt.find('Updated')]).strftime("%Y-%m-%dT%H:%M:%S")
                    if dt.find('Updated') != -1:
                        updated = parse(dt[dt.find('Updated') + 8:]).strftime("%Y-%m-%dT%H:%M:%S")

            meta_tag = news_soup.find(has_author)
            if meta_tag:
                author = meta_tag.attrs['content']
            else:
                author = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def abq_raw():
        """
        ###############################################
        # Scrape "Abq Raw"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', class_='mg-blog-post')
        if not tags:
            return
        for tag in tags:

            title = get_class_text(tag, 'h4', 'title')

            url = get_attr(tag, 'a', 'href')

            news_soup = get_soup(url)
            if not news_soup:
                continue
            img = get_class_attr(news_soup, 'img', 'wp-post-image', 'src')
            body = get_meta(news_soup, {'property': 'og:description'})
            published = get_date(news_soup, 'meta', property='article:published_time')
            updated = get_date(news_soup, 'meta', property= 'article:modified_time')
            author = get_meta(news_soup, {'name': 'author'})

            add_article(title, body, author, published, updated, url, img)

        return

    def valencia_county():
        """
        ###############################################
        # Scrape "Valencia County News"
        ###############################################
        """
        news_soup = get_soup(news_source.feed_url)
        if not news_soup:
            return
        tags = news_soup.find_all('article')
        if not tags:
            write_error_log(f"News source {news_source.feed_url} returned no results.")
            return
        for tag in tags:

            title = get_attr(tag, 'img', 'alt')

            body = get_class_text(tag, 'div', 'entry-summary')

            img_tag = tag.find('img')
            if img_tag:
                if img_tag.has_attr('data-src'):
                    img = img_tag.attrs['data-src']
                elif img_tag.has_attr('data-lazy-src'):
                    img = img_tag.attrs['data-lazy-src']
            else:
                img = ""

            url = get_attr(tag, 'a', 'href')

            published = get_date(tag, 'span', 'updated')

            a_tag = tag.find('a', rel="author")
            if a_tag:
                if a_tag.has_attr('title'):
                    author = a_tag.attrs['title']
            else:
                author = ""

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def the_independent():
        """
        ###############################################
        # Scrape "Edgewood News"
        ###############################################
        """

        news_soup = get_soup(news_source.feed_url)
        if not news_soup:
            return
        tags = news_soup.find_all('article')
        if not tags:
            write_error_log(f"News source {news_source.feed_url} returned no results.")
            return
        for tag in tags:

            title = get_class_text(tag, 'h2', 'entry-title')

            body = get_class_text(tag, 'div', 'entry-summary')

            img = get_class_attr(tag, 'img', 'wp-post-image', 'src')

            url = get_attr(tag, 'a', 'href')
            news_soup = get_soup(url)
            if not news_soup:
                continue

            if not img:
                img = get_class_attr(news_soup, 'img', 'wp-post-image', 'src')
            if not body:
                body = get_body_text(news_soup)

            author = get_class_text(tag, 'a', 'url')

            news_soup = get_soup(url)
            published = get_date(news_soup, 'time', 'published')
            updated = get_date(news_soup, 'time', 'updated')
            if published:
                add_article(title, body, author, published, updated, url, img)
        return

    def cebola_citizen():
        """
        ###############################################
        # Scrape "Cebola Citizen (Grants)"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', class_='views-row')
        if not tags:
            return
        for tag in tags:

            title = get_class_text(tag, 'div', 'views-field-title')

            author = get_class_text(tag, 'div', 'views-field-uid')

            body = get_class_text(tag, 'div', 'views-field-body')

            url = get_attr(tag, 'a', 'href')

            img = news_source.source + get_attr(tag, 'img', 'src')

            if img.find(
                    'https://www.cibolacitizen.com/sites/cibolacitizen.com/files/styles/article_420/public/default_images/Cibola%20Default.jpg?itok=wS5C-KQf') != -1:
                img = ""

            published = get_date(tag, 'div', 'views-field-created')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def roosevelt_review():
        """
        ###############################################
        # Scrape "Roosevelt Review (Portales)"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_='category-community-news')
        if not tags:
            return
        for tag in tags:
            title = get_attr(tag, 'a', 'title')

            body = get_class_text(tag, 'div', 'entry-summary')

            author = get_class_text(tag, 'a', 'url')

            url = get_attr(tag, 'a', 'href')

            img = get_attr(tag, 'img', 'src')

            published = get_date(tag, 'span', 'updated')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def current_argus():
        """
        ###############################################
        # Scrape "Carlsbad Current Argus"
        ###############################################
        """
        news_soup = get_soup(news_source.feed_url)
        if not news_soup:
            return
        tags = news_soup.find_all('a', class_=['gnt_m_he', 'gnt_m_flm_a'], href=True)
        if not tags:
            write_error_log(f"News source {news_source.feed_url} returned no results.")
            return
        for tag in tags:
            if tag.has_attr('href'):
                title = cleanup(tag.text)

                body = get_attr(tag, None, 'data-c-br')

                url = news_source.source + tag.attrs['href']

                news_soup = get_soup(url)
                if not news_soup:
                    continue

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
                    img = news_source.source + img[0: img.find('?')]
                else:
                    img = ""

                published = get_date(tag, 'div', attr='data-c-dt')

                updated = ""

                add_article(title, body, author, published, updated, url, img)
        return

    def deming_headlight():
        """
        ###############################################
        # Scrape "Deming Headlight"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_='article')
        if not tags:
            return
        for tag in tags:

            title = get_class_text(tag, 'div', 'title')

            url = get_attr(tag, None, 'ta_permalink')

            body = get_class_text(tag, 'div', 'body')

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

            author = get_class_text(tag, 'div', 'author')

            published = get_date(tag, 'div', 'date')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def rio_rancho_observer():
        """
        ###############################################
        # Scrape "Rio Rancho Observer"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_='post')
        if not tags:
            return
        for tag in tags:

            title = get_text(tag, 'h2')

            url = get_attr(tag, 'a', 'href')

            author = get_class_text(tag, 'a', 'url')

            p_tag = tag.findAll('p', class_=False)[-1]
            if p_tag:
                body = cleanup(p_tag.text)
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

            published = get_date(tag, 'span', 'updated')
            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def source_nm():
        """
         ###############################################
         # Scrape "Source NM News"
         ###############################################
         """

        page_url = news_source.feed_url
        PAGES = 5
        # loop through PAGES of news
        for page in range(1, PAGES):
            tags = get_tags(news_source.feed_url, 'div', class_='archiveCard')
            if not tags:
                return
            for tag in tags:
                title = get_text(tag, 'h3')

                url = get_attr(tag, 'a', 'href')

                body = get_body_text(tag)

                author = get_class_text(tag, 'a', 'author')

                img = get_attr(tag, 'img', 'src')

                dt_tag = tag.find_all('span', class_='archiveByline')[-1]
                published = parse(dt_tag.text)
                published = published.strftime("%Y-%m-%dT%H:%M:%S")

                updated = ""

                add_article(title, body, author, published, updated, url, img)

            page_url = news_source.source + '/page/' + str(page) + '/'

        return

    def koat():
        """
          ###############################################
          # Scrape "KOAT Action News"
          ###############################################
          """

        tags = get_tags(news_source.feed_url, 'div', class_="article")
        if not tags:
            return
        for tag in tags:
            title = get_attr(tag, 'a', 'aria-label')

            url = news_source.source + get_attr(tag, 'a', 'href')

            img_tag = tag.find('div', class_='image')
            if img_tag and img_tag.has_attr('data-style'):
                img = img_tag.attrs['data-style']
                # Define a regular expression pattern to extract the URL
                pattern = re.compile(r'background-image:url\((https://[^?]+)')
                # Use the pattern to find the URL in the string
                img = pattern.search(img)
                img = img.group(1)

            author = get_class_text(tag, 'div', 'author-name')

            news_soup = get_soup(url)
            if not news_soup:
                continue

            body = get_class_text(news_soup, 'div', 'article-content--body-text')

            published = get_date(news_soup, None,'meta', property='datepublished')
            if not published:
                dt_tag = news_soup.find('div', class_='article-headline--publish-date')
                if dt_tag.text.find('Updated') != -1:
                    published = parse(dt_tag.text[:dt_tag.text.find('Updated:')])
                else:
                    published = parse(dt_tag.text)
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def krqe():
        """
          ###############################################
          # Scrape "KRQE Local Reporting you can Trust"
          ###############################################
          """
        news_soup = get_soup(news_source.feed_url)
        if not news_soup:
            return
        tags = news_soup.find_all("div", class_="article-list__article-text",
                                  attrs={'data-article-list-id': "article-list4"})
        if not tags:
            write_error_log(f"News source {news_source.feed_url} returned no results.")
            return
        for tag in tags:
            title = get_attr(tag, 'a', 'data-link-label')

            url = get_attr(tag, 'a', 'href')

            news_soup = get_soup(url)
            if not news_soup:
                continue

            img = get_meta(news_soup, {'property': 'og:image'})

            body = get_class_text(news_soup, 'div', 'article-body')

            author = get_class_text(news_soup, 'p', 'article-authors')

            published = get_date(tag, 'time', attr='datetime')

            updated = ""

            add_article(title, body, author, published, updated, url, img)
        return

    def kob():
        """
          ###############################################
          # Scrape "KOB 4"
          ###############################################
          """
        tags = get_tags(news_source.feed_url, 'div', class_=re.compile("^hbi2020"))
        if not tags:
            return
        for tag in tags:
            h_tag = tag.find_next(re.compile("^h"))
            if h_tag:
                title = h_tag.text
            else:
                title = ""

            a_tag = tag.find('a')
            if a_tag:
                url = a_tag.attrs['href']
            else:
                url = ""

            img = get_attr(tag, 'img', 'data-src')

            news_soup = get_soup(url)
            if not news_soup:
                continue

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
                published = ""

            dt_tag = news_soup.find('meta', property="article:modified_time")
            if dt_tag:
                updated = parse(dt_tag.attrs['content'])
                updated = updated.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def searchlightnm():
        """
          ###############################################
          # Scrape "Searchlight NM"
          ###############################################
          """
        tags = get_tags(news_source.feed_url, 'article', class_=re.compile("type-post"))
        if not tags:
            return
        # news_soup = get_soup(news_source.feed_url)
        # if not news_soup:
        #     return
        # tags = news_soup.find_all('article', class_='type-post')
        # if not tags:
        #     write_error_log(f"News source {news_source.feed_url} returned no results.")
        #     return
        for tag in tags:
            title = get_class_text(tag, re.compile('^h'), 'entry-title')

            url = get_attr(tag, 'a', 'href')

            img = get_class_attr(tag, 'img', re.compile('^wp-post'), 'src')

            # news_soup = get_soup(url)

            author = get_class_text(tag, 'span', 'author')

            body = ""

            published = get_date(tag, 'time', 'published')

            updated = get_date(tag, 'time', 'updated')

            add_article(title, body, author, published, updated, url, img)

        return

    def corrales_comment():
        """
          ###############################################
          # Scrape "Corrales Comment"
          ###############################################
          """
        tags = get_tags(news_source.feed_url, 'article', class_=re.compile("type-post"))
        if not tags:
            return
        for tag in tags:
            title = get_text(tag, 'h2')

            url = get_attr(tag, 'a', 'href')

            img = get_class_attr(tag, 'img', re.compile('^wp-post'), 'src')

            # news_soup = get_soup(url)

            author = get_class_text(tag, 'span', 'author')

            body = get_text(tag, 'p')

            published = get_date(tag, 'time', 'published')

            updated = get_date(tag, 'time', 'updated')

            add_article(title, body, author, published, updated, url, img)

        return

    """ 
    Main loop. Scrape news from model of published sources and execute function to scrape. Sort dictionary containing 
    news articles and output to json file. This function runs using http://burquebro.com/news/update or by cron 
    job that runs every hour.
    """
    news = []
    news_list = News.objects.filter(published=True)
    for news_source in news_list:
        function = news_source.function
        if settings.DEBUG:
            eval(function + "()")
        else:
            try:
                eval(function + "()")
            except Exception as e:
                write_error_log(f"Error occured processing: {news_source.function} Error: {e} ")


    # Remove duplicate entries
    news = remove_duplicates(news)

    # news = sorted(news, key=lambda d: d['published'])[::-1]
    news = sorted(news, key=lambda d: d['published'][:13], reverse=True)
    """
    Clean up data in news dictionary prior to committing to json file.
    """
    for article in news:
        # max_len = 256
        # if len(article['body']) > max_len:
        #     article['body'] = adjust_string_length(article['body'], max_len)

        base_name, extension = os.path.splitext(article['img'])
        match = re.match(r'^(.*-)(\d+)x\d+$', base_name)
        if match:
            article['img'] = match.group(1)[:len(match.group(1)) - 1] + extension
        else:
            article['img'] = base_name + extension

        # replace blanks in city and county name with underscore so links work
        article['city'] = article['city'].replace(" ", "_")
        article['county'] = article['county'].replace(" ", "_")

    """
    Compare old and new dictionaries and send notification of additions.
    with open(settings.BQB_URL + "news.json", "r") as old_file:
        old_news = json.load(old_file)
    breaking_news = []
    for key in news:
        match = False
        for key2 in old_news:
            if key['url'] == key2['url']:
                match = True
                break
        if not match:
            breaking_news.append(key)
    with open(settings.BQB_URL + "breaking_news.json", "w") as outfile:
        json.dump(breaking_news, outfile, indent=4)
    """

    # Format datetime objects as strings in the desired format
    for item in news:
        original_date_string = item['published']
        original_date = datetime.strptime(original_date_string, "%Y-%m-%dT%H:%M:%S")
        new_date_string = original_date.strftime("%A, %B %d, %Y %I:%M%p")
        item['published'] = new_date_string
        if item['updated']:
            original_date_string = item['updated']
            original_date = datetime.strptime(original_date_string, "%Y-%m-%dT%H:%M:%S")
            new_date_string = original_date.strftime("%A, %B %d, %Y %I:%M%p")
            item['updated'] = new_date_string
    # random.shuffle(news)
    if len(news) > 0:
        with open(settings.BQB_URL + "news.json", "w") as outfile:
            json.dump(news, outfile, indent=4)
    return news


def news_update(req):
    start_time = time.time()
    news = scrape_news()
    end_time = time.time()
    elapsed_time = end_time - start_time
    # Calculate hours, minutes, and seconds
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours > 0:
        parts.append(f"{int(hours)} hours")
    if minutes > 0:
        parts.append(f"{int(minutes)} minutes")
    if seconds > 0:
        parts.append(f"{int(seconds)} seconds")

    messages.info(req, f"Updated in {','.join(parts)}")
    return render(req, 'news/index.html', {'category': 'New Mexico', 'news': news})
