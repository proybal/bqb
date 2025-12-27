import re
from datetime import datetime
from urllib.parse import urljoin
import csv

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from dateutil.tz import tz
from urllib3.filepost import writer

#from news.views import parse_relative_time




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


    FILE_NAME = 'access_log'
    with open(FILE_NAME, 'a', newline='') as file:
        csv_writer = csv.writer(file)  # Use csv.writer() explicitly
        ip, hostname = get_client_ip(req)
        location_data = get_location(ip)
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/Denver')
        utc = datetime.utcnow()
        utc = utc.replace(tzinfo=from_zone)
        denver = utc.astimezone(to_zone)
        date_out = denver.strftime("%m-%d-%Y")
        time_out = denver.strftime("%H:%M:%S")
        list_data = [date_out, time_out, ip, category, location_data['city'], location_data['country']]
        csv_writer.writerow(list_data)




def parse_relative_time(relative_time_str):
    """
    Converts strings like '15 minutes ago' or '3 weeks ago'
    into an actual datetime object.
    """
    now = datetime.now()

    # Match e.g. "15 minutes ago", "3 hours ago"
    match = re.match(
        r'(\d+)\s+(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\s+ago',
        relative_time_str.strip(),
        re.IGNORECASE
    )

    if not match:
        return False

    amount = int(match.group(1))
    unit = match.group(2).lower()

    # Normalize plural (relativedelta wants plural keys)
    if not unit.endswith('s'):
        unit += 's'

    # relativedelta only supports these keys
    valid_units = {'years', 'months', 'days', 'hours', 'minutes', 'seconds', 'microseconds', 'weeks'}
    if unit not in valid_units:
        return False

    delta_args = {unit: amount}
    past_time = now - relativedelta(**delta_args)

    return past_time

def write_error_log(message):
    FILE_NAME = 'error_log'
    with open(FILE_NAME, 'a', newline='') as file:
        csv_writer = csv.writer(file)
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/Denver')
        utc = datetime.utcnow()
        utc = utc.replace(tzinfo=from_zone)
        denver = utc.astimezone(to_zone)
        time_out = denver.strftime("%m-%d-%Y %H:%M:%S")
        list_data = [time_out, message]
        csv_writer.writerow(list_data)
        file.close()

def get_value(tag, tag_to_find=None, class_name=None, attr=None, text=None):
    """
    Extract text or an attribute from a BeautifulSoup tag.
    - If attr is provided, returns that attribute's value.
    - Else returns text.
    - If class_name is None, no class filter is applied.
    """
    # Locate target tag
    if tag_to_find is None:
        t = tag
    else:
        t = tag.find(tag_to_find) if class_name is None else tag.find(tag_to_find, class_=class_name)

    if not t:
        return ""

    # If attr is specified, prefer attribute lookup
    if attr is not None:
        val = t.get(attr, "")
        return cleanup(val) if val else ""

    # Otherwise, return text
    txt = t.get_text(strip=True)
    return cleanup(txt) if txt else ""


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


def get_img(tag, class_name=None, prefer=None, base_url=None,
            ensure_http=True, strip_query=False, clean_extension=True,
            allow_relative=False, allow_data_uri=False):
    """
    Find a single <img> or <picture> and return a URL.
      prefer: one of {'data-style', 'ta-srcset','data-srcset','srcset','data-src','src'}
    """
    if tag is None:
        return ""

    # Try to find img first, then check for picture tag
    img = tag.find("picture", class_=class_name) if class_name is not None else tag.find("img")

    # If no img found, try picture > source or picture > img
    if not img:
        picture = tag.find("img", class_=class_name) if class_name is not None else tag.find("picture")
        if picture:
            # Try to get source tag first (usually has better quality)
            source = picture.find("source")
            if source:
                img = source  # Use source tag for attribute extraction
            else:
                # Fall back to img inside picture
                img = picture.find("img")

    if not img:
        return ""

    # Prefer site-specific srcset first (like 'ta-srcset'), then standard attrs
    order = [prefer] if prefer else ["data-style", "ta-srcset", "data-srcset", "srcset", "data-src", "src"]
    order = [a for a in order if a]

    def pick_from_srcset(s: str) -> str:
        # take the first candidate: "url 320w, url2 640w" -> "url"
        first = s.split(",", 1)[0].strip()
        return first.split()[0] if first else ""

    def normalize(u: str) -> str:
        if not u:
            return ""
        u = u.strip()

        # Drop data: unless explicitly allowed
        if u.startswith("data:"):
            return u if allow_data_uri else ""

        if u.startswith("//"):
            u = "https:" + u

        if base_url and not (u.startswith("http://") or u.startswith("https://")):
            u = urljoin(base_url, u)

        if not (u.startswith("http://") or u.startswith("https://")):
            if ensure_http and not allow_relative:
                return ""
            # else keep relative

        if strip_query and "?" in u:
            u = u.split("?", 1)[0]
        return u

    def trim_after_extension(u: str) -> str:
        m = re.search(r"(\.webp|\.jpe?g|\.png|\.gif|\.avif|\.bmp|\.tiff)", u, re.IGNORECASE)
        return u[:m.end()] if m else u

    for attr in order:
        val = img.get(attr)
        if not val:
            continue
        url = pick_from_srcset(val) if attr.endswith("srcset") else val
        url = normalize(url)
        if url:
            if clean_extension:
                url = trim_after_extension(url)
            return url

    return ""


def get_tags(url, tag, class_name=None, id_name=None, **kwargs):
    """
    Fetch all tags of a given type (with optional class, id, or other attributes) from a URL.
    Returns a list of BeautifulSoup tag objects or None on failure.

    Example:
        get_tags(url, 'article', **{'data-section': 'news'})
        get_tags(url, 'div', class_name='container', **{'data-id': '123'})
    """
    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/92.0.4515.131 Safari/537.36'
            )
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        write_error_log(e)
        return None

    soup = BeautifulSoup(response.text, 'html5lib')

    # --- filter logic ---------------------------------------------------------
    # Build attrs dictionary for additional attributes
    attrs = {}

    if class_name:
        attrs['class'] = class_name
    if id_name:
        attrs['id'] = id_name

    # Merge any additional keyword arguments (like data-section)
    attrs.update(kwargs)

    # Use attrs if we have any filters, otherwise just find by tag
    if attrs:
        tags = soup.find_all(tag, attrs=attrs)
    else:
        tags = soup.find_all(tag)
    # -------------------------------------------------------------------------

    if not tags:
        write_error_log(f"No results found for tag '{tag}' on {url}")
        return None

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


def add_article(news_source, title, body, author, published, updated, url, img):
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
    #news.append(news_dict)
    return


def cleanup(str):
    return re.sub(r'[\n\t]+', ' ', str).strip()
