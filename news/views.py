# views.py
import json
from .models import News, ScrapeJob
import datetime
from django.conf import settings
import os
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
import time, random
from django.views.decorators.http import require_POST
from collections import defaultdict



try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except Exception:
    SELENIUM_AVAILABLE = False

from .functions import *


def diversify_news(news, top_limit=20, max_per_source=2):
    """
    Diversify the first part of the feed.

    - Max 2 stories per source in the first 15.
    - Never show the same source twice in a row if possible.
    - Preserve the original (date) order as much as possible.
    """

    remaining = list(news)
    selected = []

    counts = defaultdict(int)
    last_source = None

    while remaining and len(selected) < top_limit:
        chosen = None

        for i, article in enumerate(remaining):
            source = article["source"]

            if counts[source] >= max_per_source:
                continue

            if source == last_source:
                continue

            chosen = i
            break

        if chosen is None:
            for i, article in enumerate(remaining):
                source = article["source"]

                if counts[source] < max_per_source:
                    chosen = i
                    break

        if chosen is None:
            break

        article = remaining.pop(chosen)

        selected.append(article)
        counts[article["source"]] += 1
        last_source = article["source"]

    selected.extend(remaining)

    return selected

def remove_duplicates(news):
    seen = set()
    unique_news = []

    for article in news:
        title_source_pair = (article['title'], article['source'])
        if title_source_pair not in seen:
            seen.add(title_source_pair)
            unique_news.append(article)

    return unique_news


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
    news = diversify_news(news)
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

    news = diversify_news(news)(matched_items)

    # random.shuffle(news)
    return render(request, 'news/index.html', {'category': category, 'news': news})


def state_news(req):
    state = 'New Mexico'
    write_access_log(req, state)
    with open('news.json') as json_file:
        news = json.load(json_file)
    news = diversify_news(news)
    news = truncate_news_body(news)
    return render(req, 'news/index.html', {'category': state, 'news': news})


def by_region(req, region):
    write_access_log(req, region)
    reg = region

    with open("news.json") as json_file:
        news = json.load(json_file)

    if region.find("ern"):
        cat = region[:region.find("ern")]

    new_news = []

    for article in news:
        news_cat = article["region"]

        if news_cat.find(reg) != -1:
            new_news.append(article)

    news = diversify_news(new_news)
    news = truncate_news_body(news)

    return render(
        req,
        "news/index.html",
        {
            "category": region,
            "news": news,
        },
    )

def by_city(req, city):
    write_access_log(req, city)
    with open('news.json') as json_file:
        news = json.load(json_file)
    new_news = []
    for news_item in news:
        if news_item['city'] == city:
            new_news.append(news_item)
    city = city.replace("_", " ")
    news = diversify_news(new_news)
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
    news = diversify_news(new_news)
    news = truncate_news_body(news)
    return render(req, 'news/index.html', {'category': county, 'news': news})


def scrape_news():

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

    def abqjournal(news_source):
        """
        ########################################
        # Scrape "Albuquerque Journal" news
        ########################################
        """
        tags = get_tags(news_source.feed_url, 'article')
        if not tags:
            return
        for tag in tags:

            title = get_value(tag, 'h2')

            body = get_value(tag, 'p', 'subtitle')

            url = get_value(tag, 'a', attr='href')

            img = get_img(tag, clean_extension=False)

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

    def citydesk(news_source):
        """

        Getting a 403 error..... blocking the request...

        ########################################
        # Scrape "City Desk" news
        ########################################
        """
        tags = get_tags(news_source.feed_url, 'article')
        if not tags:
            return
        for tag in tags:
            title = get_text(tag, 'h3')
            url = get_value(tag, 'a', attr='href')
            if not title:
                title = get_text(tag, 'h2')
                utag = tag.find('h2')
                url = get_value(utag, 'a', attr='href')

            body = get_value(tag, 'div', 'newspack-post-subtitle')

            # img = get_value(tag, 'img', 'wp-post-image', 'src')
            img = get_img(tag, 'img', 'wp-post-image')
            if not img:
                news_soup = get_soup(url)
                # img = get_value(news_soup, 'img', 'attachment-newspack-featured-image', 'src')
                img = get_img(news_soup, 'attachment-newspack-featured-image')
                if not img:
                    img = get_img(news_soup, 'wp-post-image')

            news_soup = get_soup(url)
            if not news_soup:
                continue
            author = get_meta(news_soup, {'name': 'author'})

            published = get_meta(news_soup, {'property': 'article:published_time'})[:19]

            updated = get_meta(news_soup, {'property': 'article:modified_time'})[:19]

            add_article(title, body, author, published, updated, url, img)

        return

    def thepaper(news_source):
        """
        ########################################
        # Scrape "The Paper" news
        ########################################
        """
        tags = get_tags(news_source.feed_url, 'article', 'post')
        if not tags:
            return
        for tag in tags:
            title = get_value(tag, 'h2', 'entry-title')

            body = cleanup(tag.text)

            url = get_value(tag, 'a', attr='href', text=False)

            img = get_img(tag, 'wp-post-image')

            author = get_value(tag, 'span', 'author')

            published = get_date(tag, 'time', 'published', 'datetime')

            updated = get_date(tag, 'time', 'updated', 'datetime')

            add_article(title, body, author, published, updated, url, img)

    def joemonahan(news_source):
        """
        ###############################################
        # Scrape "New Mexico Politics with Joe Monahan
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', class_name="blogPost")
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

            img = get_img(tag)

            published = tag.find('div', class_='byline')
            if published:
                published = published.text
                published = parse(published[published.find('/') + 2:])
                published = published.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                published = ""
            updated = ""

            add_article(title, body, author, published, updated, news_source.feed_url, img)

    def newmexican(news_source):
        """
        ###############################################
        # Scrape "Santa Fe New Mexican"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_name='tnt-asset-type-article')
        if not tags:
            return
        for tag in tags:

            title = get_value(tag, 'a', attr='aria-label')
            if not title:
                title = get_text(tag, 'a')

            body = get_value(tag, 'p', 'tnt-summary')
            if len(body) <= 20 or title == body:
                body = ""

            url = news_source.source + get_value(tag, 'a', attr='href')

            img = get_value(tag, 'img', attr='data-srcset')

            author = get_value(tag, 'div', 'card-meta')

            news_soup = get_soup(url)
            if not news_soup:
                continue
            published = get_date(news_soup, 'meta', itemprop='dateCreated')
            updated = get_date(news_soup, 'meta', itemprop='dateModified')

            add_article(title, body, author, published, updated, url, img)

        return

    def riograndesun(news_source):
        """
        ###############################################
        # Scrape "Rio Grande Sun"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', 'tnt-asset-type-article')
        if not tags:
            return
        for tag in tags:

            title = get_value(tag, 'a', 'tnt-asset-link', 'aria-label', text=False)

            url = news_source.source + get_value(tag, 'a', 'tnt-asset-link', 'href', text=False)

            body = get_body_text(tag)

            img = get_img(tag)

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

    def lascrucessun(news_source):
        """

        Another candidate for selenium....

        ###############################################
        # Scrape "Las Cruces Sun"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'a', 'p1-container')
        if not tags:
            return

        for tag in tags:
            # # Skip if not a valid tag
            # if tag.has_attr('rel'):
            #     continue

            title = get_value(tag, 'div', 'p1-title-spacer', text=True)

            body = get_value(tag, attr='data-c-br')

            author = ""

            url = news_source.source + get_value(tag, attr='href')

            img = get_img(tag)

            news_soup = get_soup(url)
            if not news_soup:
                continue

            author = get_value(news_soup, "div", "gnt_ar_by")

            published = get_date(tag, 'lit-timestamp', attr='publishdate')

            updated = get_date(tag, 'lit-timestamp', attr='update-date')

            add_article(title, body, author, published, updated, url, img)
        return

    def hobbssun(news_source):
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

            tags = get_tags(news_source, 'article')
            if not tags:
                return
            for tag in tags:

                title = get_text(tag, 'h2')

                body = get_body_text(tag)

                url = get_value(tag, 'a', attr='href')

                img = get_value(tag, 'img', attr='data-src')

                a_tag = tag.find('a', rel='author')
                if a_tag and a_tag.text:
                    author = a_tag.text
                else:
                    author = ""

                published = get_date(tag, 'span', 'bdayh-date')
                updated = ""

                add_article(title, body, author, published, updated, url, img)

        return

    def taosnews(news_source):
        """
        ###############################################
        # Scrape "Taos News"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_name='tnt-asset-type-article')
        if not tags:
            return
        for tag in tags:

            title = get_value(tag, 'a', attr='aria-label')

            url = news_source.source + get_value(tag, 'a', attr='href')

            img = get_value(tag, 'img', attr='data-srcset')

            body = get_value(tag, 'div', 'card-lead')

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

    def gallupsun(news_source):
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
        PAGES = 3
        page_url = news_source.feed_url
        limitstart = 0
        # loop through PAGES of news
        page_url = news_source.feed_url
        for page in range(1, PAGES):

            tags = get_tags(page_url, 'div', class_name='contentpaneopen')
            if not tags:
                return
            for tag in tags:
                body = cleanup(tag.text)

                title = get_value(tag, 'h2', 'contentheading', text=True)

                url = news_source.source + get_value(tag, 'a', attr='href')

                author = get_value(tag, 'span', 'createby', text=True)

                # news_soup = get_soup(url)

                img = news_source.source + remove_suffix(get_img(tag.find(class_="article-content")))

                published = get_date(tag, 'span', 'createdate')

                updated = ""

                add_article(title, body, author, published, updated, url, img)

                limitstart += 5
                page_url = news_source.feed_url + '&limitstart=' + str(limitstart)

        return

    def artesia_news(news_source):
        """
        ###############################################
        # Scrape "Artesian News"
        ###############################################
        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('name') and tag.attrs['name'] == 'author'

        tags = get_tags(news_source.feed_url, 'div', class_name="td-cpt-post")
        if not tags:
            return
        for tag in tags:
            url = get_value(tag, 'a', attr='href')

            title = get_value(tag, 'a', attr='title')

            img = get_value(tag, 'span', attr='data-img-url')

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

    def newmexicosun(news_source):
        """
        ###############################################
        # Scrape "New Mexico Sun"
        ###############################################

        Note: "More News" could be added
        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('name') and tag.attrs['name'] == 'author'

        tags = get_tags(news_source, 'div', class_name="news")
        if not tags:
            return
        for tag in tags:
            url = news_source.source + get_value(tag, 'a', attr='href')

            title = get_text(tag, re.compile('^h'))

            img = get_img(tag)

            body = get_value(tag, 'div', 'content')

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

    def pinonpost(news_source):
        """
        ###############################################
        # Scrape "Pinon Post"
        ###############################################
        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('name') and tag.attrs['name'] == 'author'

        tags = get_tags(news_source.feed_url, "article", class_name='jeg_post')
        if not tags:
            return
        for t, tag in enumerate(tags):
            title = tag.text
            if title.find('by Piñon') != -1:
                title = title[:title.find('by Piñon')]
            if title.find('by Renato') != -1:
                title = title[:title.find('by Renato')]

            url = get_value(tag, 'a', attr='href')

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

            img = get_img(news_soup, 'wp-post-image', prefer='src')

            published = get_date(news_soup, 'span', 'published')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

            if t == 20:
                break
        return

    def lasvegasoptic(news_source):
        """
        ###############################################
        # Scrape "Las Vegas Optic
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_name='tnt-section-news')
        if not tags:
            return
        for tag in tags:

            title = get_value(tag, 'a', attr='aria-label')

            url = news_source.source + get_value(tag, 'a', attr='href')

            body = get_body_text(tag)

            img = get_img(tag.find(class_="image")) if tag.find(class_="image") else ""



            news_soup = get_soup(url)
            if not news_soup:
                continue

            # if not body:
            #     body = get_body_text(news_soup)
            body = get_body_text(news_soup)
            author = get_value(news_soup, 'span', 'tnt-user-name')


            published = get_date(news_soup, 'time', 'tnt-date', 'datetime')
            updated = ""
            add_article(title, body, author, published, updated, url, img)

        return

    def roswelldaily(news_source):
        """
        ###############################################
        # Scrape "Roswell Daily Record
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_name='tnt-section-news')
        if not tags:
            return
        for tag in tags:

            title = get_value(tag, 'a',attr='aria-label')

            url = news_source.source + get_value(tag, 'a', attr='href')

            body = get_body_text(tag)

            published = get_date(tag, 'time', attr='datetime')

            author = get_value(tag, 'span', 'tnt-byline')

            img = get_img(tag)

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def farmingtondaily(news_source):
        """
        ###############################################
        # Scrape "Farmington Daily Times"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', class_name="frontpage-headlines-title")

        for tag in tags:

            title = cleanup(tag.text)

            url = get_value(tag, 'a', attr='href')

            news_soup = get_soup(url)

            img = get_img(news_soup, class_name='image')

            body = get_body_text(news_soup)

            author = get_meta(news_soup, {'name': 'author'})

            published = get_meta(news_soup, {'name': 'pubdate'})

            updated = ''

            add_article(title, body, author, published, updated, url, img)

        return

    def eastern_nm_news(news_source):
        """

        Another candidate for selenium....

        ###############################################
        # Scrape "Eastern New Mexico News" (clovis)
        ###############################################
        """

        def has_author(tag):
            return tag.name == 'a' and tag.has_attr('href') and tag.has_attr('aria-label') and tag.attrs[
                'aria-label'] == title

        #tags = get_tags(news_source, 'div', class_name='hmfunction_sectioncontainer')
        tags = get_tags(news_source, 'div')
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

    def defensor_chieftain(news_source):
        """
        ###############################################
        # Scrape "El Defensor Cheiftain" (socorro)
        ###############################################
        """

        tags = get_tags(news_source.feed_url, 'article')
        for tag in tags:

            title = get_value(tag, 'a', attr='aria-label')

            url = news_source.feed_url + get_value(tag, 'a', attr='href')

            news_soup = get_soup(url)
            if not news_soup:
                continue

            body = get_body_text(tag)

            img = get_meta(news_soup, {'property': 'og:image'})

            author = get_meta(news_soup, {'name': 'author'})

            published = get_date(tag, 'span', 'updated')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def la_daily_post(news_source):
        """
        ###############################################
        # Scrape "Los Alamos Daily Post"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_name='post')
        if not tags:
            return
        for tag in tags:

            author = get_value(tag, 'span', 'elementor-post-author')

            title = get_text(tag, 'a')

            body = get_body_text(tag)

            url = get_value(tag, 'a', attr='href')

            img = get_value(tag, 'img', re.compile('^wp-image'), 'src', False)

            published = get_date(tag, 'span', 'elementor-post-date')

            updated = ""

            # added the conditional because articles are duplicated w/o img
            if img:
                add_article(title, body, author, published, updated, url, img)

        return

    def sc_daily_press(news_source):
        """
        ###############################################
        # Scrape "Silver City Daily Press"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', ['item-container', 'post-content'])
        if not tags:
            return

        for tag in tags:

            title = get_text(tag, 'h2')

            h2_tag = tag.find('h2')

            url = get_value(h2_tag, 'a', attr='href')

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

            body = get_meta(news_soup, {'property': "og:description"})

            if not img:
                img = get_meta(news_soup, {'property': 'og:image'})

            author = get_meta(news_soup, {'name': "author"})

            published = get_date(tag, 'span', 'date')
            if not published:
                published = get_date(tag, 'time', 'published', 'datetime')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return


    def nm_political_report(news_source):
        """
        ###############################################
        # Scrape "New Mexico Political Report"
        ###############################################
        """
        url = news_source.feed_url
        if not SELENIUM_AVAILABLE:
            return
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
            # from selenium import webdriver
            # from selenium.webdriver.chrome.options import Options
        except Exception as e:
            print("Selenium not available:", e)
            return None
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = ctx.new_page()

            # Load and wait just enough so articles are in the DOM
            page.set_default_timeout(10000)
            page.set_default_navigation_timeout(15000)
            page.goto(url, wait_until="load")
            try:
                page.wait_for_selector("article", timeout=5000)
            except PWTimeout:
                pass  # continue; some pages render immediately

            html = page.content()
            browser.close()  # Playwright is done; parse locally below

        soup = BeautifulSoup(html, "html.parser")
        print(soup.title.string if soup.title else "No title found")

        # Find article blocks
        tags = soup.find_all("article")
        if not tags:
            # Optional: drop a quick debug snapshot if nothing matched
            # Path is relative to where this runs
            with open("nmpr_dump.html", "w", encoding="utf-8") as f:
                f.write(html)
            return

        for tag in tags:
            # Uses your helpers; keep them if they already work across sources
            title = get_value(tag, "h2", "entry-title") or get_value(tag, "h3", "entry-title")
            url = get_value(tag, "a", attr="href")

            # Images on WP often sit on .wp-post-image; also try data-src
            img = get_img(tag, "wp-post-image")
            if not img:
                imgel = tag.find("img")
                if imgel:
                    img = imgel.get("src") or imgel.get("data-src") or imgel.get("data-lazy-src")

            # Dates: pass the tag name AND the class (most themes use <time class="published">)
            published = get_date(tag, "time", "published") or get_date(tag, "time", "entry-date")
            updated = get_date(tag, "time", "updated")

            author = ""
            body = ""  # populate later if you fetch article pages

            add_article(title, body, author, published, updated, url, img)

        return

    def alamagordo_daily(news_source):
        """

        Problems with site, in the middle of rewrite, site errors out.... not 403
        Check on sites sanity regularly 10/30/25

        ###############################################
        # Scrape "Alamagordo Daily Press"
        ###############################################
        """

        ####################################
        return
        ####################################


        tags = get_tags(news_source.feed_url, 'a', class_name='gnt_m_flm_a')
        tags = get_tags(news_source.feed_url, 'article')
        if not tags:
            return
        for tag in tags:
            title = tag.text
            body = tag.text
            url = news_source.source + tag.attrs['href']
            img_tag = tag.find('img')
            if img_tag:
                img = news_source.source + img_tag.attrs['data-gl-src']
                img = img[0: img.find('?')]
            else:
                img = ""
            img = get_img(tag)
            published = get_date(tag, 'div', 'gnt_m_flm_sbt', 'data-c-dt')
            if not published:
                published = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""

            news_soup = get_soup(url)
            if not news_soup:
                continue


            author = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def ruidoso_news(news_source):
        """
        ###############################################
        # Scrape "Ruidoso Daily News"
        ###############################################


        Problems with site, in the middle of rewrite, site errors out.... not 403. Modal says "Issue Detected" when
        accessed from browser session.
        Check on sites sanity regularly 10/30/25


        """

        def has_author(tag):
            return tag.name == 'meta' and tag.has_attr('content') and tag.has_attr('property') \
                   and tag.attrs['property'] == 'article:author'

        ####################################
        return
        ####################################



        tags = get_tags(news_source.feed_url, 'a', class_name='gnt_m_flm_a')
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
                dt = get_value(news_soup, 'div', 'gnt_ar_dt', 'aria-label', False)
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

    def abq_raw(news_source):
        """
        ###############################################
        # Scrape "Abq Raw"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', class_name='mg-blog-post')
        if not tags:
            return
        for tag in tags:

            title = get_value(tag, 'h4', 'title')

            url = get_value(tag, 'a', attr='href')

            news_soup = get_soup(url)
            if not news_soup:
                continue
            img = get_value(news_soup, 'img', 'wp-post-image', 'src', False)
            body = get_meta(news_soup, {'property': 'og:description'})
            published = get_date(news_soup, 'meta', property='article:published_time')
            updated = get_date(news_soup, 'meta', property= 'article:modified_time')
            author = get_meta(news_soup, {'name': 'author'})

            add_article(title, body, author, published, updated, url, img)

        return

    def valencia_county(news_source):
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

            title = get_value(tag, 'img', attr='alt')

            body = get_value(tag, 'div', 'entry-summary')

            img = get_img(
                tag,
                base_url=news_source.feed_url,
                clean_extension=False,
            )

            url = urljoin(
                news_source.feed_url,
                get_value(tag, "a", attr="href")
            )

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

    def the_independent(news_source):
        """
        ###############################################
        # Scrape "Edgewood News"
        ###############################################


        Changed site to: https://www.edgewood-nm.gov/

        Site not working, candidate for selenium

        """

        return


        news_soup = get_soup(news_source.feed_url)
        if not news_soup:
            return
        tags = news_soup.find_all('article')
        tags = get_tags(news_soup.find_all('article'))
        if not tags:
            write_error_log(f"News source {news_source.feed_url} returned no results.")
            return
        for tag in tags:

            title = get_value(tag, 'h2', 'entry-title')

            body = get_value(tag, 'div', 'entry-summary')

            img = get_img(tag, 'wp-post-image')

            url = get_value(tag, 'a', attr='href')

            news_soup = get_soup(url)
            if not news_soup:
                continue

            if not img:
                img = get_img(news_soup, 'wp-post-image')
            if not body:
                body = get_body_text(news_soup)

            author = get_value(tag, 'a', 'url')

            published = get_date(news_soup, 'time', 'published')
            updated = get_date(news_soup, 'time', 'updated')
            if published:
                add_article(title, body, author, published, updated, url, img)
        return

    def cebola_citizen(news_source):
        """
        ###############################################
        # Scrape "Cebola Citizen (Grants)"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', class_name='views-row')
        if not tags:
            return
        for tag in tags:

            title = get_value(tag, 'div', 'views-field-title')

            author = get_value(tag, 'div', 'views-field-uid')

            body = get_value(tag, 'div', 'views-field-body')

            url = news_source.source + get_value(tag, 'a', attr='href')

            img = news_source.source + get_value(tag, 'img', attr='src')

            # Dont display Site logo
            if img.find(
                    'https://www.cibolacitizen.com/sites/cibolacitizen.com/files/styles/article_420/public/default_images/Cibola%20Default.jpg?itok=wS5C-KQf') != -1:
                img = ""

            published = get_date(tag, 'div', 'views-field-created')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def roosevelt_review(news_source):
        """
        ###############################################
        # Scrape "Roosevelt Review (Portales)"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_name='category-community-news')
        if not tags:
            return
        for tag in tags:
            title = get_value(tag, 'a', attr='title')

            body = get_value(tag, 'div', 'entry-summary')

            author = get_value(tag, 'a', 'url')

            url = get_value(tag, 'a', attr='href')

            img = get_value(tag, 'img', attr='src')

            published = get_date(tag, 'span', 'updated')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def current_argus(news_source):
        """
        ###############################################
        # Scrape "Carlsbad Current Argus"
        ###############################################


        Same problem with "Issue Detected".


        """

        return

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

                body = get_value(tag, attr='data-c-br')

                url = news_source.source + tag.attrs['href']

                news_soup = get_soup(url)
                if not news_soup:
                    continue

                meta_tag = news_soup.find('div', class_='gnt_ar_by')

                if meta_tag and meta_tag.text:
                    author = meta_tag.text
                else:
                    author = ""  # Get article author if present

                img = get_img(tag)

                published = get_date(tag, 'div', attr='data-c-dt')

                updated = ""

                add_article(title, body, author, published, updated, url, img)
        return

    def deming_headlight(news_source):
        """
        ###############################################
        # Scrape "Deming Headlight"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'article', class_name='article')
        if not tags:
            return
        for tag in tags:

            title = get_value(tag, 'div', 'title')

            url = get_value(tag, attr='ta_permalink')

            body = get_value(tag, 'div', 'body')

            img = get_img(tag, prefer="ta-srcset", base_url="https://www.demingheadlight.com")

            author = get_value(tag, 'div', 'author')

            published = get_date(tag, 'div', 'date')

            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def rio_rancho_observer(news_source):
        """
        ###############################################
        # Scrape "Rio Rancho Observer"
        ###############################################
        """
        tags = get_tags(news_source.feed_url, 'div', class_name='card-container')
        if not tags:
            return
        for tag in tags:

            title = get_value(tag, 'a', attr='aria-label')

            url = news_source.feed_url + get_value(tag, 'a', attr='href')

            author = get_value(tag, 'a', 'url')

            body = get_text(tag, 'p')

            news_soup = get_soup(url)
            if not news_soup:
                continue
            img = get_meta(news_soup, {'property': 'og:image'})

            published = get_date(news_soup, 'time', 'tnt-date', 'datetime')
            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def source_nm(news_source):
        """
         ###############################################
         # Scrape "Source NM News"
         ###############################################
         """

        page_url = news_source.feed_url
        PAGES = 5
        # loop through PAGES of news
        for page in range(1, PAGES):
            tags = get_tags(news_source.feed_url, 'div', class_name='archiveCard')
            if not tags:
                return
            for tag in tags:
                title = get_text(tag, 'h3')

                url = get_value(tag, 'a', attr='href')

                body = get_body_text(tag)

                author = get_value(tag, 'a', 'author')

                img = get_value(tag, 'img', attr='src')

                dt_tag = tag.find_all('span', class_='archiveByline')[-1]
                published = parse(dt_tag.text)
                published = published.strftime("%Y-%m-%dT%H:%M:%S")

                updated = ""

                add_article(title, body, author, published, updated, url, img)

            page_url = news_source.source + '/page/' + str(page) + '/'

        return

    def koat(news_source):
        """
          ###############################################
          # Scrape "KOAT Action News"
          ###############################################
          """

        tags = get_tags(news_source.feed_url, 'div', class_name="article")
        if not tags:
            return
        for tag in tags:
            title = get_value(tag, 'a', attr='aria-label')

            url = news_source.source + get_value(tag, 'a', attr='href')

            img_tag = tag.find('div', class_='image')
            if img_tag and img_tag.has_attr('data-style'):
                img = img_tag.attrs['data-style']
                # Define a regular expression pattern to extract the URL
                pattern = re.compile(r'background-image:url\((https://[^?]+)')
                # Use the pattern to find the URL in the string
                img = pattern.search(img)
                img = img.group(1)
#            img = get_img(tag, class_name='image')
            author = get_value(tag, 'div', 'author-name')

            news_soup = get_soup(url)
            if not news_soup:
                continue

            body = get_value(news_soup, 'div', 'article-content--body-text')

            dt_tag = news_soup.find('div', class_='article-headline--publish-date')
            if dt_tag.text.find('Updated') != -1:
                published = parse(dt_tag.text[dt_tag.text.find('Updated:') + 9:])
            else:
                published = parse(dt_tag.text)
            published = published.strftime("%Y-%m-%dT%H:%M:%S")
            updated = ""

            add_article(title, body, author, published, updated, url, img)

        return

    def krqe(news_source):
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
            title = get_value(tag, 'a', attr='data-link-label')

            url = get_value(tag, 'a', attr='href')

            news_soup = get_soup(url)
            if not news_soup:
                continue

            img = get_meta(news_soup, {'property': 'og:image'})

            body = get_value(news_soup, 'div', 'article-body')

            author = get_value(news_soup, 'p', 'article-authors')

            published = get_date(tag, 'time', attr='datetime')

            updated = ""

            add_article(title, body, author, published, updated, url, img)
        return

    def kob(news_source):
        """
          ###############################################
          # Scrape "KOB 4"
          ###############################################
          """
        tags = get_tags(news_source.feed_url, 'div', class_name=re.compile("^hbi2020"))
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

            img = get_value(tag, 'img', attr='data-src')

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

    def searchlightnm(news_source):
        """
          ###############################################
          # Scrape "Searchlight NM"
          ###############################################
          """
        tags = get_tags(news_source.feed_url, 'article', class_name=re.compile("type-post"))
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
            title = get_value(tag, re.compile('^h'), 'entry-title')

            url = get_value(tag, 'a', attr='href')

            img = get_value(tag, 'img', re.compile('^wp-post'), 'src', False)

            # news_soup = get_soup(url)

            author = get_value(tag, 'span', 'author')

            body = ""

            # news_soup = get_soup(url)
            published = get_date(tag, 'time', 'published')

            updated = get_date(tag, 'time', 'updated')

            add_article(title, body, author, published, updated, url, img)

        return

    def corrales_comment(news_source):
        """
          ###############################################
          # Scrape "Corrales Comment"
          ###############################################
          """
        tags = get_tags(news_source.feed_url, 'article', class_name=re.compile("type-post"))
        if not tags:
            return
        for tag in tags:
            title = get_text(tag, 'h2')

            url = get_value(tag, 'a', attr='href')

            img = get_value(tag, 'img', re.compile('^wp-post'), 'src', False)

            author = get_value(tag, 'span', 'author')

            body = get_text(tag, 'p')

            news_soup = get_soup(url)

            published = get_date(news_soup, 'meta', property="article:published_time")

            updated = get_date(news_soup, 'meta', property="article:modified_time")

            add_article(title, body, author, published, updated, url, img)

        return

    """ 
    Main loop. Scrape news from model of published sources and execute function to scrape. Sort dictionary containing 
    news articles and output to json file. This function runs using http://burquebro.com/news/update or by cron 
    job that runs every hour.
    """
    SCRAPERS = {
        "abqjournal": abqjournal,
        "citydesk": citydesk,
        "thepaper": thepaper,
        "joemonahan": joemonahan,
        "newmexican": newmexican,
        "riograndesun": riograndesun,
        "lascrucessun": lascrucessun,
        "hobbssun": hobbssun,
        "taosnews": taosnews,
        "gallupsun": gallupsun,
        "artesia_news": artesia_news,
        "newmexicosun": newmexicosun,
        "pinonpost": pinonpost,
        "lasvegasoptic": lasvegasoptic,
        "roswelldaily": roswelldaily,
        "farmingtondaily": farmingtondaily,
        "eastern_nm_news": eastern_nm_news,
        "defensor_chieftain": defensor_chieftain,
        "la_daily_post": la_daily_post,
        "sc_daily_press": sc_daily_press,
        "nm_political_report": nm_political_report,
        "alamagordo_daily": alamagordo_daily,
        "ruidoso_news": ruidoso_news,
        "abq_raw": abq_raw,
        "valencia_county": valencia_county,
        "the_independent": the_independent,
        "cebola_citizen": cebola_citizen,
        "roosevelt_review": roosevelt_review,
        "current_argus": current_argus,
        "deming_headlight": deming_headlight,
        "rio_rancho_observer": rio_rancho_observer,
        "source_nm": source_nm,
        "koat": koat,
        "krqe": krqe,
        "kob": kob,
        "searchlightnm": searchlightnm,
        "corrales_comment": corrales_comment,
    }

    news = []
    news_list = News.objects.filter(published=True)

    for news_source in news_list:
        function_name = (news_source.function or "").strip()

        # Support old database values such as "abqjournal()".
        if function_name.endswith("()"):
            function_name = function_name[:-2].strip()

        scraper = SCRAPERS.get(function_name)

        if scraper is None:
            write_error_log(
                f"No scraper registered for source='{news_source.title}', "
                f"function={news_source.function!r}, "
                f"normalized={function_name!r}"
            )
            continue

        article_count_before = len(news)

        try:
            scraper(news_source)
        except Exception as e:
            write_error_log(
                f"Error processing source='{news_source.title}', "
                f"function='{function_name}': "
                f"{type(e).__name__}: {e}"
            )
            continue

        articles_added = len(news) - article_count_before

        if articles_added == 0:
            write_error_log(
                f"Scraper completed but added no articles: "
                f"source='{news_source.title}', "
                f"function='{function_name}'"
            )

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

    # Output news.json if dictionary entries exist

    if len(news) > 0:
        with open(settings.BQB_URL + "news.json", "w") as outfile:
            json.dump(news, outfile, indent=4)
    return news




@require_POST
@user_passes_test(lambda user: user.is_superuser)
def news_update(req):
    active_job = ScrapeJob.objects.filter(
        status__in=(
            ScrapeJob.STATUS_QUEUED,
            ScrapeJob.STATUS_RUNNING,
        )
    ).first()

    if active_job:
        messages.info(
            req,
            f"News update job {active_job.pk} is already {active_job.status}.",
        )
    else:
        job = ScrapeJob.objects.create(
            requested_by=req.user,
            source="web",
        )
        messages.success(
            req,
            f"News update job {job.pk} was queued.",
        )

    return redirect("state_news")