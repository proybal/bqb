# news/urls.py
from django.contrib import admin
from accounts.views import signup_view, loginPage, activate

from django.urls import path
from news import views, scripts

urlpatterns = [
    path('news/', views.state_news, name="state_news"),
    path('test/', scripts.scrape, name="test"),
    path('news/state_news/', views.state_news, name="state_news"),
    path('news/by_region/<str:region>/', views.by_region, name="by_region"),
    # path('news/by_city/<str:city>/', views.by_city, name="by_city"),
    # path('news/by_county/<str:county>/', views.by_county, name="by_county"),
    # path('news/Southern/', views.index, name="Southern"),
    # path('news/Eastern/', views.index, name="Eastern"),
    # path('news/Western/', views.index, name="Western"),
    path('news/search/<str:search>/', views.search, name="search"),
    path('news/update/', views.news_update, name="news-update"),
    path('news/signup/', signup_view, name="signup"),
    path('news/activate/<slug:uidb64>/<slug:token>/', activate, name='activate'),
]
