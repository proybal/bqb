# rss/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('rss/', views.rss, name='rss'),
]