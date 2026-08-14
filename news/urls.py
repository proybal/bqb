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
    path('news/search/<str:search>/', views.search, name="search"),
    path('news/update/', views.news_update, name="news-update"),
    path('news/signup/', signup_view, name="signup"),
    path('news/activate/<slug:uidb64>/<slug:token>/', activate, name='activate'),
    path(
        "news/sources/",
        views.sources,
        name="sources",
    ),
    path(
        "news/source/<str:code>/",
        views.by_source,
        name="by_source",
    ),
    path(
        "push/public-key/",
        views.push_public_key,
        name="push-public-key",
    ),

    path(
        "push/subscribe/",
        views.save_push_subscription,
        name="push-subscribe",
    ),

    path(
        "push/unsubscribe/",
        views.delete_push_subscription,
        name="push-unsubscribe",
    ),

]
