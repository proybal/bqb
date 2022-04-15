import shutil

from django.shortcuts import render
import requests
from bs4 import BeautifulSoup

# GEtting todo albuquerquetodo.com
def index(req):

    todo_r = requests.get("https://www.abqtodo.com")
    todo_soup = BeautifulSoup(todo_r.content, 'html5lib')
    children = todo_soup.findChildren()
    # print(children)

    # todo_headings = todo_soup.find_all('h2')
    #todo_headings = todo_soup.findAll("div", {"class": "blog-post"}, limit=1)
    todo_headings = todo_soup.findAll("div", {"class": "blog-post"})
    images = todo_soup.findAll('img', {'class': 'blog-thumb'})
    href = todo_soup.findAll("a")
    print(todo_headings)
    x = 0
    img = []
    for i in images:
    #    print(i.attrs['src'])
        if x > 0:
            url = i.attrs['src']
            img.append(i.attrs['src'])
    #        r = requests.get(url, stream=True)
     #        if r.status_code == 200:
     #            r.raw.decode_content = True
     # #           print(r)
        x+=1

    #print(todo_headings)
    #todo_headings = todo_soup.findAll("h2")
    #print(todo_headings)
    #print(todo_soup.prettify())
    #todo_headings = todo_headings[0:-13] # removing footers

    todo_news = []
    urls = []
    x = 0
    for th in todo_headings:
        i=images[x]
        url = i.attrs['src']
        urls.append(i.attrs['src'])
        try:
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                r.raw.decode_content = True
                # print(r)
                dict = {'text': th.text, 'url': urls, 'img': img[x]}
                todo_news.append(dict)
        except:
            print(url)
        x+=1



    #Getting todo from Hindustan times

    # ht_r = requests.get("https://www.abqjournal.com/")
    # ht_soup = BeautifulSoup(ht_r.content, 'html5lib')
    # ht_headings = ht_soup.findAll("div", {"class": "article-container"})
    # ht_headings = ht_headings[2:]
    #print(ht_soup.prettify())
    # ht_news = []
    #
    # for hth in ht_headings:
    #
    #     ht_news.append(hth.text)
     #   print(hth)


#   print(todo_news)
    return render(req, 'todo/index.html', {'todo_news':todo_news,'img': url })