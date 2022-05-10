import shutil

from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
import datetime

from dateutil.parser import parse


# todo albuquerquetodo.com

def index(req):
    def get_date(str):

        def get_datetime(str, index):
            event_str = str
            i = index
            i = event_str.find(':',i)+2
            d = event_str.find(',', i)
            # dow = event_str[i:d]
            M = event_str.find(',', d + 2)
            mon = event_str[d + 2:M]
            t = event_str[M + 2:event_str.find(' ', M + 2)]
            d = parse(mon + ' ' + t)
            return (d, t)

        event_date = ""
        event_str = str
        event_str = event_str.replace("\n", "")
        event_str = " ".join(event_str.split())
        event_str = event_str[event_str.find('TIMES') + 6:event_str.find('WEBSITE') - 1]
        event_date = datetime.datetime(2099, 12, 31)
        event_dates = []
        event_end_dates = []
        i = event_str.find('Event Date :')
        if i != -1:
            event_found = True
            while event_found:
                k = event_str.find('Event Date :', i+12)  # lookahead
                if k == -1:
                    event_found = False
                else:
                    i = k
                d, t = get_datetime(event_str, i)
                current_time = datetime.datetime.now()
                if current_time <= d <= event_date:
                    event_date = d
                else:
                    if event_date != datetime.datetime(2099, 12, 31):
                        event_date = d
                event_dates.append(d)
                event_end_dates.append("")
        else:
            i = event_str.find('Event Start Date :')
            if i != -1:
                k = event_str.find('Event End Date:')
                if k != -1:
                    j = k
                    d, t = get_datetime(event_str, i)
                    event_date = d
                    event_dates.append(d)
                    i = j
                    d, t = get_datetime(event_str, k)
                    event_end_dates.append(d)

        return event_date, event_dates, event_end_dates

    todo_r = requests.get("https://www.abqtodo.com")
    todo_soup = BeautifulSoup(todo_r.content, 'html5lib')
    href = todo_soup.select('.blog-post .blog-thumb a[href]')
    title_tags = todo_soup.select(".blog-post .blog-title")
    thumb_tags = todo_soup.select(".blog-post .blog-thumb img")
    meta_tags = todo_soup.select(".blog-post .blog-post-meta")
    meta = [mt.get_text() for mt in meta_tags]
    text = [t.get_text() for t in title_tags]
    thumbs = [t.attrs['src'] for t in thumb_tags]
    todo_news = []
    for x in range(0, len(meta)):
        todo_r = requests.get(href[x]['href'])
        todo_soup = BeautifulSoup(todo_r.content, 'html5lib')
        url = todo_soup.select(".row p a")
        url = url[0]['href']
        title = todo_soup.select(".row H1")
        title = title[0].get_text()
        event_str = todo_soup.select(".row")
        event_str = event_str[0].get_text().strip()
        event_str = event_str.replace("\n", "")
        event_date = False
        event_dates = []
        event_end_dates = []
        event_date, event_dates, event_end_dates = get_date(event_str)
        google_map = todo_soup.select("iframe")
        google_map = google_map[0]['src']
        todo_dates = []
        for y in range(0, len(event_dates)):
            d = event_dates[y].strftime("%m/%d/%Y %I:%M%p")
            if event_end_dates[y]:
                e = event_end_dates[y].strftime("%m/%d/%Y %I:%M%p")
            else:
                e = ""
            todo_date = {'date': d, 'enddate': e}
            todo_dates.append(todo_date)
        todo_dict = {'title': title,'dates': todo_dates, 'text': text[x], 'url': url, 'img': thumbs[x]}
        todo_news.append(todo_dict)

    return render(req, 'todo/index.html', {'todo_news': todo_news})
