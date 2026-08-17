# news/views.py
import json
import os
import datetime
import time

import feedparser
from django.conf import settings
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from collections import defaultdict
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .functions import *
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import PushSubscription
from .models import News, ScrapeJob
from .push import send_push_to_all


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

    return (redirect("state_news"))


@login_required
def push_public_key(request):
    return JsonResponse({
        "publicKey": settings.VAPID_PUBLIC_KEY_BROWSER,
    })


@login_required
@require_POST
def save_push_subscription(request):
    try:
        payload = json.loads(request.body)

        endpoint = payload["endpoint"]
        keys = payload["keys"]

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "user": request.user,
                "p256dh": keys["p256dh"],
                "auth": keys["auth"],
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "is_active": True,
            },
        )

        return JsonResponse({"success": True})

    except (KeyError, TypeError, json.JSONDecodeError):
        return JsonResponse(
            {"success": False, "error": "Invalid subscription data"},
            status=400,
        )


@login_required
@require_POST
def delete_push_subscription(request):
    try:
        payload = json.loads(request.body)
        endpoint = payload["endpoint"]

        PushSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint,
        ).delete()

        return JsonResponse({"success": True})

    except (KeyError, TypeError, json.JSONDecodeError):
        return JsonResponse(
            {"success": False, "error": "Invalid subscription data"},
            status=400,
        )


def offline_news(request):
    articles = (
        News.objects
        .all()
        .order_by("-published")[:150]
    )

    return render(
        request,
        "news/offline_news.html",
        {
            "articles": articles,
        },
    )


def manifest(request):
    content = render_to_string("news/manifest.json")

    return HttpResponse(
        content,
        content_type="application/manifest+json",
    )


def service_worker(request):
    content = render_to_string("news/service_worker.js")

    response = HttpResponse(
        content,
        content_type="application/javascript"
    )

    response["Service-Worker-Allowed"] = "/"
    return response


def offline(request):
    return render(request, "news/offline.html")


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


def sources(request):
    news_sources = (
        News.objects
        .filter(published=True)
        .select_related("city", "county", "region")
        .order_by("state", "title")
    )

    return render(
        request,
        "news/sources.html",
        {
            "news_sources": news_sources,
        },
    )


def by_source(request, code):
    news_source = get_object_or_404(
        News,
        code=code,
        published=True,
    )

    write_access_log(
        request,
        news_source.title,
    )

    with open("news.json", encoding="utf-8") as json_file:
        news = json.load(json_file)

    source_news = [
        article
        for article in news
        if article.get("code") == news_source.code
    ]

    # Do NOT diversify a single-source page.
    news = truncate_news_body(source_news)


    return render(
        request,
        "news/index.html",
        {
            "category": news_source.title,
            "news": news,
            "news_source": news_source,
        },
    )


from django.utils import timezone


def latest_news(request):
    write_access_log(request, "Latest News")

    with open("news.json", encoding="utf-8") as json_file:
        news = json.load(json_file)

    today = timezone.localdate().isoformat()

    latest = [
        article
        for article in news
        if str(article.get("last_update", "")).startswith(today)
    ]

    latest.sort(
        key=lambda article: article.get("last_update", ""),
        reverse=True,
    )

    latest = truncate_news_body(latest)

    return render(
        request,
        "news/index.html",
        {
            "category": "Latest",
            "news": latest,
        },
    )

def scrape_news():
    def scrape_rss(news_source):
        """
        Generic RSS scraper.
        Expects news_source.feed_url to point to a valid RSS feed.
        """

        try:
            response = requests.get(
                news_source.feed_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )

            response.raise_for_status()

        except requests.RequestException as e:
            write_error_log(
                f"{news_source.title} RSS request failed: {e}"
            )
            return

        feed = feedparser.parse(response.content)

        MAX_RSS_ENTRIES = 30
        for entry_num, entry in enumerate(feed.entries[:MAX_RSS_ENTRIES], start=1):

            title = getattr(entry, "title", "").strip()
            url = getattr(entry, "link", "").strip()
            author = getattr(entry, "author", "")

            # Body
            body = ""

            if hasattr(entry, "summary"):
                body = BeautifulSoup(
                    entry.summary,
                    "html.parser"
                ).get_text(
                    " ",
                    strip=True
                )

            # Published
            published = ""

            if hasattr(entry, "published"):
                try:
                    published = parse(
                        entry.published
                    ).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )
                except Exception as e:
                    write_error_log(
                        f"{news_source.title} date error "
                        f"{entry.published!r}: {e}"
                    )

            if not published:
                continue

            # Updated
            updated = ""

            if hasattr(entry, "updated"):
                try:
                    updated = parse(
                        entry.updated
                    ).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )
                except Exception:
                    updated = ""

            # Image
            # Image
            img = ""

            # 1. Prefer full-size image embedded in content
            if hasattr(entry, "content"):
                for content_item in entry.content:
                    content_html = content_item.get("value", "")

                    content_soup = BeautifulSoup(
                        content_html,
                        "html.parser"
                    )

                    img_tag = content_soup.find("img")

                    if img_tag:
                        img = (
                                img_tag.get("src")
                                or img_tag.get("data-src")
                                or ""
                        )

                    if img:
                        break

            # 2. Then try summary HTML
            if not img and hasattr(entry, "summary"):
                summary_soup = BeautifulSoup(
                    entry.summary,
                    "html.parser"
                )

                img_tag = summary_soup.find("img")

                if img_tag:
                    img = (
                            img_tag.get("src")
                            or img_tag.get("data-src")
                            or img_tag.get("data-lazy-src")
                            or ""
                    )

            # 3. Then media_content
            if not img and hasattr(entry, "media_content"):
                for media in entry.media_content:
                    candidate = media.get("url", "")
                    if candidate:
                        img = candidate
                        break

            # 4. Then enclosure
            if not img and hasattr(entry, "enclosures"):
                for enclosure in entry.enclosures:
                    candidate = (
                            enclosure.get("href")
                            or enclosure.get("url")
                            or ""
                    )

                    media_type = enclosure.get("type", "")

                    if (
                            candidate
                            and (
                            media_type.startswith("image/")
                            or candidate.lower().endswith(
                        (".jpg", ".jpeg", ".png", ".webp")
                    )
                    )
                    ):
                        img = candidate
                        break

            # 5. Thumbnail is last resort
            if not img and hasattr(entry, "media_thumbnail"):
                for media in entry.media_thumbnail:
                    candidate = media.get("url", "")
                    if candidate:
                        img = candidate
                        break
            if not img and hasattr(entry, "summary"):
                summary_soup = BeautifulSoup(
                    entry.summary,
                    "html.parser"
                )

                img_tag = summary_soup.find("img")

                if img_tag:
                    img = (
                            img_tag.get("src")
                            or img_tag.get("data-src")
                            or img_tag.get("data-lazy-src")
                            or ""
                    )

            if not img and hasattr(entry, "content"):
                for content_item in entry.content:
                    content_html = content_item.get("value", "")

                    content_soup = BeautifulSoup(
                        content_html,
                        "html.parser"
                    )

                    img_tag = content_soup.find("img")

                    if img_tag:
                        img = (
                                img_tag.get("src")
                                or img_tag.get("data-src")
                                or ""
                        )

                    if img:
                        break

            img = improve_feed_image(img)

            if not img and url:
                news_soup = get_soup(url)

                if news_soup:
                    img = get_meta(
                        news_soup,
                        {"property": "og:image"}
                    )

            if not isinstance(img, str):
                img = ""

            add_article(
                title,
                body,
                author,
                published,
                updated,
                url,
                img,
            )

    def scrape_wordpress_api(news_source, api_url=None):
        if api_url is None:
            api_url = news_source.feed_url

        try:
            response = requests.get(
                api_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type",
                ""
            ).lower()

            if "application/json" not in content_type:
                message = (
                    f"{news_source.title} API expected JSON but received "
                    f"{content_type or 'unknown content type'} "
                    f"from {response.url}"
                )

                print(message)
                write_error_log(message)
                return

            posts = response.json()

        except requests.RequestException as e:
            message = (
                f"{news_source.title} API request error: {e}"
            )

            print(message)
            write_error_log(message)
            return

        except ValueError as e:
            message = (
                f"{news_source.title} API JSON parse error: {e}"
            )

            print(message)
            write_error_log(message)
            return

        if not isinstance(posts, list):
            message = (
                f"{news_source.title} API returned unexpected "
                f"JSON type: {type(posts).__name__}"
            )

            print(message)
            write_error_log(message)
            return

        print(
            f"{news_source.title} API returned "
            f"{len(posts)} posts"
        )

        for post in posts:

            title_html = (
                post.get("title", {})
                .get("rendered", "")
            )

            title = BeautifulSoup(
                title_html,
                "html.parser"
            ).get_text(
                " ",
                strip=True
            )

            url = post.get(
                "link",
                ""
            )

            excerpt_html = (
                post.get("excerpt", {})
                .get("rendered", "")
            )

            body = BeautifulSoup(
                excerpt_html,
                "html.parser"
            ).get_text(
                " ",
                strip=True
            )

            published = post.get(
                "date",
                ""
            )

            if published:
                published = published[:19]

            updated = post.get(
                "modified",
                ""
            )

            if updated:
                updated = updated[:19]

            author = ""

            embedded = post.get(
                "_embedded",
                {}
            )

            author_data = embedded.get(
                "author",
                []
            )

            if author_data:
                author = author_data[0].get(
                    "name",
                    ""
                )

            img = ""

            media_data = embedded.get(
                "wp:featuredmedia",
                []
            )

            if media_data:
                img = media_data[0].get(
                    "source_url",
                    ""
                )

            if not title or not url or not published:
                continue

            add_article(
                title,
                body,
                author,
                published,
                updated,
                url,
                img,
            )

    def improve_feed_image(img):
        if not img:
            return ""

        # Blogger / Blogspot images often contain a forced thumbnail size.
        if (
                "blogspot.com" in img
                or "googleusercontent.com" in img
                or "bp.blogspot.com" in img
        ):
            # Old Blogger style:
            # /s72-c/
            # /s320/
            img = re.sub(
                r"/s\d+(?:-c)?/",
                "/s1600/",
                img
            )

            # Newer Google image style:
            # =s72-c
            # =w300-h200
            img = re.sub(
                r"=s\d+(?:-c)?$",
                "=s1600",
                img
            )

            img = re.sub(
                r"=w\d+-h\d+[^?]*$",
                "=s1600",
                img
            )

        return img

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

        if updated:
            last_update = updated
        last_update = published

        news_dict = {
            'source': str(news_source.title),
            'source_url': str(news_source.source),
            'title': title,
            'body': body,
            'author': author,
            'published': published,
            'region': str(news_source.region),
            'city': str(news_source.city),
            'county': str(news_source.county),
            'updated': updated,
            'last_update': last_update,
            'url': url,
            'img': img,
            'thumbnail': str(news_source.cover),
            'code': news_source.code, }
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

    def lascrucessun(news_source):
        """
        ###############################################
        # Scrape "Las Cruces Sun-News"
        # Gannett listing-page version
        ###############################################
        """

        try:
            response = requests.get(
                news_source.feed_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )

            response.raise_for_status()

        except requests.RequestException as e:
            write_error_log(
                f"Las Cruces Sun request failed: {e}"
            )
            return

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        story_urls = set()
        article_count = 0

        for a in soup.find_all("a", href=True):

            href = a.get("href", "")

            # Only actual news stories.
            if not href.startswith("/story/news/"):
                continue

            url = urljoin(
                news_source.feed_url,
                href
            )

            if url in story_urls:
                continue

            story_urls.add(url)

            title = a.get_text(
                " ",
                strip=True
            )

            if not title:
                continue

            # --------------------------------
            # Published date from URL
            #
            # Example:
            # /story/news/local/2026/08/11/...
            # --------------------------------
            date_match = re.search(
                r"/(\d{4})/(\d{2})/(\d{2})/",
                href
            )

            if not date_match:
                print(
                    f"Las Cruces Sun could not find date "
                    f"in URL: {url}"
                )
                continue

            year, month, day = date_match.groups()

            published = (
                f"{year}-{month}-{day}T00:00:00"
            )

            # --------------------------------
            # Try to extract description from
            # surrounding listing markup
            # --------------------------------
            body = ""

            parent = a.parent

            if parent:
                # Look for nearby text that isn't
                # simply the headline.
                container = parent.parent

                if container:
                    text = container.get_text(
                        " ",
                        strip=True
                    )

                    if text and text != title:
                        body = text

                        if body.startswith(title):
                            body = body[len(title):].strip()

            # --------------------------------
            # Image
            # --------------------------------
            img = ""

            container = a

            for _ in range(6):
                if not container:
                    break

                img_tag = container.find("img")

                if img_tag:
                    img = (
                            img_tag.get("data-gl-src")
                            or img_tag.get("src")
                            or img_tag.get("data-src")
                            or ""
                    )

                    if not img:
                        srcset = (
                                img_tag.get("data-gl-srcset")
                                or img_tag.get("srcset")
                                or ""
                        )

                        if srcset:
                            img = (
                                srcset
                                .split(",")[0]
                                .strip()
                                .split(" ")[0]
                            )

                    if img:
                        img = urljoin(
                            news_source.feed_url,
                            img
                        )

                        img = re.sub(
                            r'width=\d+',
                            'width=600',
                            img
                        )

                        img = re.sub(
                            r'height=\d+',
                            'height=400',
                            img
                        )

                        break

                container = container.parent

            # Listing doesn't consistently provide
            # an author, so leave blank.
            author = ""

            updated = ""

            add_article(
                title,
                body,
                author,
                published,
                updated,
                url,
                img,
            )

            article_count += 1

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

    def newmexicosun(news_source):
        """
        ###############################################
        # Scrape "New Mexico Sun"
        # HTML /stories page
        ###############################################
        """

        try:
            response = requests.get(
                news_source.feed_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            response.raise_for_status()

        except requests.RequestException as e:
            write_error_log(
                f"New Mexico Sun request failed: {e}"
            )
            return

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        story_links = []

        for h3 in soup.find_all("h3"):
            a_tag = h3.find("a", href=True)

            if not a_tag:
                continue

            title = a_tag.get_text(
                " ",
                strip=True
            )

            url = urljoin(
                news_source.feed_url,
                a_tag["href"]
            )

            if not title or not url:
                continue

            story_links.append(
                {
                    "title": title,
                    "url": url,
                    "tag": h3,
                }
            )

        print(
            f"New Mexico Sun found "
            f"{len(story_links)} stories"
        )

        for story in story_links:

            title = story["title"]
            url = story["url"]
            h3 = story["tag"]

            # Excerpt is typically immediately after the heading.
            body = ""

            next_tag = h3.find_next_sibling()

            if next_tag:
                body = next_tag.get_text(
                    " ",
                    strip=True
                )

            try:
                article_response = requests.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=20,
                )

                article_response.raise_for_status()

            except requests.RequestException:
                continue

            article_soup = BeautifulSoup(
                article_response.text,
                "html.parser"
            )

            # Image
            img = ""

            img_tag = article_soup.find(
                "meta",
                property="og:image"
            )

            if img_tag:
                img = img_tag.get(
                    "content",
                    ""
                )

            # Body fallback
            if not body:
                desc_tag = article_soup.find(
                    "meta",
                    property="og:description"
                )

                if desc_tag:
                    body = desc_tag.get(
                        "content",
                        ""
                    )

            # Author
            author = ""

            author_tag = article_soup.find(
                "meta",
                attrs={"name": "author"}
            )

            if author_tag:
                author = author_tag.get(
                    "content",
                    ""
                )

            # Published
            published = ""

            date_candidates = [
                article_soup.find(
                    "meta",
                    property="article:published_time"
                ),
                article_soup.find(
                    "meta",
                    itemprop="datePublished"
                ),
                article_soup.find(
                    "time",
                    attrs={"datetime": True}
                ),
            ]

            for dt_tag in date_candidates:
                if not dt_tag:
                    continue

                if dt_tag.name == "meta":
                    raw_date = dt_tag.get(
                        "content",
                        ""
                    )
                else:
                    raw_date = dt_tag.get(
                        "datetime",
                        ""
                    )

                if raw_date:
                    try:
                        published = parse(
                            raw_date
                        ).strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        )
                        break
                    except Exception:
                        pass

            if not published:
                print(
                    f"New Mexico Sun skipping "
                    f"article with no date: {title}"
                )
                continue

            updated = ""

            add_article(
                title,
                body,
                author,
                published,
                updated,
                url,
                img,
            )

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
            title = get_value(tag, 'a', attr='aria-label')

            url = news_source.source + get_value(tag, 'a', attr='href')

            body = get_body_text(tag)

            published = get_date(tag, 'time', attr='datetime')

            author = get_value(tag, 'span', 'tnt-byline')

            img = get_img(tag)

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

        tags = get_tags(
            news_source.feed_url,
            'article',
            class_name='elementor-post'
        )

        if not tags:
            return

        for tag in tags:

            # Title and URL
            title_tag = tag.find(
                ['h2', 'span'],
                class_='elementor-post__title'
            )

            if not title_tag:
                continue

            link_tag = title_tag.find(
                'a',
                href=True
            )

            if not link_tag:
                continue

            title = link_tag.get_text(
                " ",
                strip=True
            )

            url = link_tag['href']

            # Author
            author_tag = tag.find(
                'span',
                class_='elementor-post-author'
            )

            if author_tag:
                author = author_tag.get_text(
                    " ",
                    strip=True
                )
            else:
                author = ""

            # Body / excerpt
            body_tag = tag.find(
                'div',
                class_='elementor-post__excerpt'
            )

            if body_tag:
                body = body_tag.get_text(
                    " ",
                    strip=True
                )
            else:
                body = ""

            # Image
            img = ""

            img_tag = tag.find('img')

            if img_tag:
                img = (
                        img_tag.get('src')
                        or img_tag.get('data-src')
                        or ""
                )

            # Date
            date_tag = tag.find(
                'span',
                class_='elementor-post-date'
            )

            time_tag = tag.find(
                'span',
                class_='elementor-post-time'
            )

            published = ""

            if date_tag:
                date_text = date_tag.get_text(
                    " ",
                    strip=True
                )

                if time_tag:
                    date_text += " " + time_tag.get_text(
                        " ",
                        strip=True
                    )

                date_text = (
                    date_text
                    .replace("on ", "")
                    .replace(" - ", " ")
                    .strip()
                )

                try:
                    published_dt = parse(date_text)

                    published = published_dt.strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )

                except Exception as e:
                    print(
                        f"Los Alamos Daily Post "
                        f"date error {date_text!r}: {e}"
                    )

            if not published:
                continue

            updated = ""

            add_article(
                title,
                body,
                author,
                published,
                updated,
                url,
                img,
            )

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
        # Labrador CMS HTML version
        ###############################################
        """

        try:
            response = requests.get(
                news_source.feed_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            response.raise_for_status()

        except requests.RequestException as e:
            write_error_log(
                f"Rio Rancho Observer request failed: {e}"
            )
            return

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        story_links = []

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            title = a.get_text(" ", strip=True)

            if not title:
                continue

            if not (
                    "/news/" in href
                    or "/business/" in href
            ):
                continue

            if not re.search(r"/\d+$", href):
                continue

            url = urljoin(
                news_source.feed_url,
                href
            )

            if any(
                    item["url"] == url
                    for item in story_links
            ):
                continue

            story_links.append({
                "title": title,
                "url": url,
            })

        print(
            f"Rio Rancho Observer found "
            f"{len(story_links)} story links"
        )

        for item in story_links:

            title = item["title"]
            url = item["url"]

            try:
                article_response = requests.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=20,
                )

                article_response.raise_for_status()

            except requests.RequestException as e:
                print(
                    f"Rio Rancho Observer article request failed: "
                    f"{url}: {e}"
                )
                continue

            article_soup = BeautifulSoup(
                article_response.text,
                "html.parser"
            )

            # Title
            og_title = article_soup.find(
                "meta",
                property="og:title"
            )

            if og_title and og_title.get("content"):
                title = og_title["content"].strip()

            # Body / description
            body = ""

            description = article_soup.find(
                "meta",
                property="og:description"
            )

            if description:
                body = description.get(
                    "content",
                    ""
                ).strip()

            # Image
            img = ""

            image_tag = article_soup.find(
                "meta",
                property="og:image"
            )

            if image_tag:
                img = image_tag.get(
                    "content",
                    ""
                )

            # Author
            author = ""

            author_tag = article_soup.find(
                "meta",
                attrs={"name": "author"}
            )

            if author_tag:
                author = author_tag.get(
                    "content",
                    ""
                )

            # Published
            published = ""

            date_candidates = [
                article_soup.find(
                    "meta",
                    property="article:published_time"
                ),
                article_soup.find(
                    "meta",
                    itemprop="datePublished"
                ),
                article_soup.find(
                    "time",
                    attrs={"datetime": True}
                ),
            ]

            for dt_tag in date_candidates:
                if not dt_tag:
                    continue

                if dt_tag.name == "meta":
                    raw_date = dt_tag.get(
                        "content",
                        ""
                    )
                else:
                    raw_date = dt_tag.get(
                        "datetime",
                        ""
                    )

                if raw_date:
                    try:
                        published = parse(
                            raw_date
                        ).strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        )
                        break

                    except Exception:
                        pass

            if not published:
                print(
                    f"Rio Rancho Observer skipping article "
                    f"with no date: {title}"
                )
                continue

            # Updated
            updated = ""

            modified_tag = article_soup.find(
                "meta",
                property="article:modified_time"
            )

            if modified_tag:
                raw_updated = modified_tag.get(
                    "content",
                    ""
                )

                if raw_updated:
                    try:
                        updated = parse(
                            raw_updated
                        ).strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        )
                    except Exception:
                        updated = ""

            add_article(
                title,
                body,
                author,
                published,
                updated,
                url,
                img,
            )

        return

    def koat(news_source):
        """
        ###############################################
        # Scrape "KOAT Action News"
        ###############################################
        """

        try:
            response = requests.get(
                news_source.feed_url,
                timeout=20,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/142.0 Safari/537.36"
                    )
                },
            )

            response.raise_for_status()

        except requests.RequestException as e:
            print(f"KOAT request failed: {e}")
            return

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # KOAT story links now use /article/...
        story_links = []

        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            title = link.get_text(" ", strip=True)

            if not href.startswith("/article/"):
                continue

            if not title:
                continue

            # Avoid duplicate links to the same article
            url = "https://www.koat.com" + href

            if any(item["url"] == url for item in story_links):
                continue

            story_links.append({
                "title": title,
                "url": url,
            })

        # Keep this reasonable -- homepage can contain old/promotional links
        story_links = story_links[:30]

        for item in story_links:

            title = item["title"]
            url = item["url"]

            try:
                article_response = requests.get(
                    url,
                    timeout=20,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/142.0 Safari/537.36"
                        )
                    },
                )

                article_response.raise_for_status()

            except requests.RequestException as e:
                print(
                    f"KOAT article request failed "
                    f"{url}: {e}"
                )
                continue

            article_soup = BeautifulSoup(
                article_response.text,
                "html.parser"
            )

            #
            # Title
            #
            og_title = article_soup.find(
                "meta",
                property="og:title"
            )

            if og_title and og_title.get("content"):
                title = og_title["content"].strip()

            #
            # Body / description
            #
            body = ""

            description = article_soup.find(
                "meta",
                property="og:description"
            )

            if description:
                body = description.get(
                    "content",
                    ""
                ).strip()

            if not body:
                description = article_soup.find(
                    "meta",
                    attrs={"name": "description"}
                )

                if description:
                    body = description.get(
                        "content",
                        ""
                    ).strip()

            #
            # Image
            #
            img = ""

            image_tag = article_soup.find(
                "meta",
                property="og:image"
            )

            if image_tag:
                img = image_tag.get(
                    "content",
                    ""
                )

            #
            # Author
            #
            author = ""

            author_tag = article_soup.find(
                "meta",
                attrs={"name": "author"}
            )

            if author_tag:
                author = author_tag.get(
                    "content",
                    ""
                )

            #
            # Published date
            #
            published = ""

            published_tag = article_soup.find(
                "meta",
                property="article:published_time"
            )

            if published_tag:
                published = published_tag.get(
                    "content",
                    ""
                )

            # Try alternate Hearst metadata
            if not published:
                published_tag = article_soup.find(
                    "meta",
                    attrs={"name": "pubdate"}
                )

                if published_tag:
                    published = published_tag.get(
                        "content",
                        ""
                    )

            if published:
                try:
                    published = parse(
                        published
                    ).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )

                except Exception as e:
                    print(
                        f"KOAT date parse error "
                        f"{url}: {e}"
                    )

                    published = ""

            if not published:
                print(
                    f"KOAT skipping article with no date: "
                    f"{title}"
                )
                continue

            #
            # Updated date
            #
            updated = ""

            updated_tag = article_soup.find(
                "meta",
                property="article:modified_time"
            )

            if updated_tag:
                updated = updated_tag.get(
                    "content",
                    ""
                )

                if updated:
                    try:
                        updated = parse(
                            updated
                        ).strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        )
                    except Exception:
                        updated = ""

            add_article(
                title,
                body,
                author,
                published,
                updated,
                url,
                img,
            )

        return

    def joemonahan(news_source):
        """
        Joe Monahan:
        Blogger RSS for article discovery.
        Article HTML for high-quality images.
        """

        feed_url = (
            "https://joemonahansnewmexico.blogspot.com/"
            "feeds/posts/default?alt=rss&max-results=30"
        )

        try:
            response = requests.get(
                feed_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            response.raise_for_status()

        except requests.RequestException as e:
            write_error_log(
                f"Joe Monahan feed request failed: {e}"
            )
            return

        feed = feedparser.parse(response.content)

        print(
            f"Joe Monahan feed returned "
            f"{len(feed.entries)} entries"
        )

        for entry in feed.entries:

            title = getattr(entry, "title", "").strip()
            url = getattr(entry, "link", "").strip()

            if not title or not url:
                continue

            # Body
            body = ""

            if hasattr(entry, "summary"):
                body = BeautifulSoup(
                    entry.summary,
                    "html.parser"
                ).get_text(
                    " ",
                    strip=True
                )

            author = "Joe Monahan"

            # Published date
            published = ""

            if hasattr(entry, "published"):
                try:
                    published = parse(
                        entry.published
                    ).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )
                except Exception:
                    published = ""

            if not published:
                continue

            updated = ""

            # Get higher-quality image from article page
            img = ""

            news_soup = get_soup(url)

            if news_soup:

                # Prefer image inside Joe's actual post
                post = news_soup.find(
                    "div",
                    class_="blogPost"
                )

                if post:
                    img = get_img(post)

                # Fallback to OpenGraph
                if not img:
                    img = get_meta(
                        news_soup,
                        {"property": "og:image"}
                    )

            add_article(
                title,
                body,
                author,
                published,
                updated,
                url,
                img,
            )

        return

    """ 
    =================================================================================================================
    Main loop. Scrape news from model of published sources and execute function to scrape. Sort dictionary containing 
    news articles and output to json file. This function runs using http://burquebro.com/news/update or by cron 
    job that runs every hour.
    =================================================================================================================
    """
    SCRAPERS = {
        "abqjournal": abqjournal,
        "defensor_chieftain": defensor_chieftain,
        "deming_headlight": deming_headlight,
        "joemonahan": joemonahan,
        "koat": koat,
        "ladailypost": la_daily_post,
        "lascrucessun": lascrucessun,
        "lasvegasoptic": lasvegasoptic,
        "newmexican": newmexican,
        "newmexicosun": newmexicosun,
        "rio_rancho_observer": rio_rancho_observer,
        "roosevelt_review": roosevelt_review,
        "roswelldaily": roswelldaily,
        "taosnews": taosnews,
        "valencia_county": valencia_county,
    }

    news = []
    news_list = News.objects.filter(published=True)

    for news_source in news_list:

        article_count_before = len(news)
        source_start = time.time()

        try:
            if news_source.scrape_type == News.SCRAPE_RSS:
                scrape_rss(news_source)

            elif news_source.scrape_type == News.SCRAPE_WORDPRESS:
                scrape_wordpress_api(news_source)

            elif news_source.scrape_type == News.SCRAPE_HTML:

                scraper = SCRAPERS.get(news_source.code)

                if scraper is None:
                    write_error_log(
                        f"No HTML scraper registered for "
                        f"source='{news_source.title}', "
                        f"code={news_source.code}"
                    )
                    continue

                scraper(news_source)

            else:
                write_error_log(
                    f"Unknown scrape_type "
                    f"{news_source.scrape_type!r} "
                    f"for {news_source.title}"
                )
                continue

        except Exception as e:
            elapsed = time.time() - source_start

            print(
                f"{news_source.title:<32} "
                f"{'ERROR':>14} "
                f"{elapsed:>7.1f}s "
                f"{type(e).__name__}: {e}"
            )

            write_error_log(
                f"Error processing source='{news_source.title}', "
                f"type='{news_source.scrape_type}': "
                f"{type(e).__name__}: {e}"
            )

            continue

        articles_added = len(news) - article_count_before
        elapsed = time.time() - source_start

        if articles_added == 0:
            status = "NO ARTICLES"

            write_error_log(
                f"Scraper completed but added no articles: "
                f"source='{news_source.title}', "
                f"type='{news_source.scrape_type}'"
            )
        else:
            status = f"{articles_added} articles"

        print(
            f"{news_source.title:<32} "
            f"{status:>14} "
            f"{elapsed:>7.1f}s"
        )
    # Remove duplicate entries
    news = remove_duplicates(news)

    # news = sorted(news, key=lambda d: d['published'])[::-1]
    news = sorted(news, key=lambda d: d['published'][:13], reverse=True)
    """
    Clean up data in news dictionary prior to committing to json file.
    """
    for article in news:
        base_name, extension = os.path.splitext(article['img'])
        match = re.match(r'^(.*-)(\d+)x\d+$', base_name)
        if match:
            article['img'] = match.group(1)[:len(match.group(1)) - 1] + extension
        else:
            article['img'] = base_name + extension

        # replace blanks in city and county name with underscore so links work
        article['city'] = article['city'].replace(" ", "_")
        article['county'] = article['county'].replace(" ", "_")

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

    news_json_path = os.path.join(
        settings.BQB_URL,
        "news.json",
    )

    breaking_news_path = os.path.join(
        settings.BQB_URL,
        "breaking_news.json",
    )

    notified_urls = set()

    breaking_news_file_exists = os.path.exists(
        breaking_news_path
    )

    if breaking_news_file_exists:
        try:
            with open(
                    breaking_news_path,
                    "r",
                    encoding="utf-8",
            ) as infile:
                saved_urls = json.load(infile)

            if isinstance(saved_urls, list):
                notified_urls = {
                    url
                    for url in saved_urls
                    if isinstance(url, str) and url
                }
            else:
                print(
                    "breaking_news.json did not contain "
                    "a list. Rebuilding its baseline."
                )
                breaking_news_file_exists = False

        except (
                json.JSONDecodeError,
                OSError,
                TypeError,
        ) as error:
            print(
                "Could not read breaking_news.json: "
                f"{error}"
            )

            breaking_news_file_exists = False
            notified_urls = set()

    current_urls = {
        article.get("url")
        for article in news
        if article.get("url")
    }

    if breaking_news_file_exists:
        breaking_news = [
            article
            for article in news
            if article.get("url")
               and article["url"] not in notified_urls
        ]
    else:
        # The first run establishes a baseline.
        # It must not notify about every current article.
        breaking_news = []

        print(
            "Created breaking-news baseline; "
            "no push notification sent."
        )

    if news:
        with open(
                news_json_path,
                "w",
                encoding="utf-8",
        ) as outfile:
            json.dump(
                news,
                outfile,
                indent=4,
            )

        if breaking_news:
            max_push_articles = 5
            articles_to_notify = breaking_news[:max_push_articles]

            total_sent = 0
            total_failed = 0

            for article in articles_to_notify:
                source_name = article.get(
                    "source",
                    "New Mexico News",
                )

                article_title = article.get(
                    "title",
                    "A new story is available.",
                )

                article_url = article.get(
                    "url",
                    "/news/",
                )

                sent, failed = send_push_to_all(
                    title=f"BurqueBro • {source_name}",
                    body=article_title,
                    url=article_url,
                )

                total_sent += sent
                total_failed += failed

            print(
                "Breaking-news pushes complete: "
                f"{len(articles_to_notify)} articles, "
                f"{total_sent} deliveries sent, "
                f"{total_failed} deliveries failed."
            )
        # Remember all URLs in the current feed.
        notified_urls.update(current_urls)

        with open(
                breaking_news_path,
                "w",
                encoding="utf-8",
        ) as outfile:
            json.dump(
                sorted(notified_urls),
                outfile,
                indent=4,
            )

    return news
