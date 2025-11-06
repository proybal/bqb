import textwrap

from django import template
from news.models import Counties, Cities
from datetime import datetime
from dateutil import tz
import time
import json
import timeago
from django.utils.safestring import mark_safe
import os

register = template.Library()


@register.simple_tag(takes_context=True)
def get_counties(context):
    counties = Counties.objects.all().order_by('name')
    c_list = []
    for c in counties:
        s = str(c).replace(" ", "_")
        c_dict = {'location': c, 'slug': s}
        c_list.append(c_dict)
    return c_list


@register.simple_tag(takes_context=True)
def get_cities(context):
    cities = Cities.objects.all().order_by('name')
    c_list = []
    for c in cities:
        s = str(c).replace(" ", "_")
        c_dict = {'location': c, 'slug': s}
        c_list.append(c_dict)
    return c_list


@register.simple_tag
def time_ago(date_time):
    to_zone = tz.gettz('America/Denver')
    d = date_time[0:19]
    d = datetime.strptime(d, "%Y-%m-%dT%H:%M:%S")
    d = d.astimezone(to_zone)
    n = datetime.now()
    n = n.astimezone(to_zone)
    how_long_ago = timeago.format(d, n)
    return how_long_ago


@register.simple_tag
def current_time(format_string):
    return datetime.now().strftime(format_string)


@register.simple_tag(takes_context=True)
def get_last_update(context):
    filename = 'news.json'
    dt_utc = os.path.getmtime(filename)
    local_time = time.ctime(dt_utc)
    return local_time


@register.simple_tag()
def get_news(filter_by=None, filter_value=None, search=None):
    with open('news.json') as json_file:
        news = json.load(json_file)
    if filter_by:
        new_news = []
        for r in news:
            news_cat = r[filter_by]
            if news_cat.find(filter_value) != -1:
                new_news.append(r)
        return new_news
    return news


@register.simple_tag
def get_about_message():
    filename = 'news.json'
    to_zone = tz.gettz('America/Denver')
    utc = datetime.fromtimestamp(os.path.getmtime(filename))
    date_time = utc.astimezone(to_zone)
    with open('news.json') as json_file:
        news = json.load(json_file)

        message = mark_safe(f"""\
        <p>New Mexico News is a comprehensive news aggregator that sources articles from
        over 30 online newspapers spanning across the state. We aim to provide you with
        the latest news and updates from various sources in one convenient location.</p>

        <p>We encourage you to visit us frequently to stay informed about the latest
        happenings in New Mexico. Your feedback is valuable to us, so please feel free
        to reach out to us at proybal@yahoo.com with any comments or suggestions you may
        have.</p>

        <p>Thank you for visiting New Mexico News. We appreciate your support!</p>

        <small><p>Last Updated on {date_time.strftime("%A, %B %d, %Y %I:%M%p")} with {len(news)} articles.</p></small>""")
    return message
