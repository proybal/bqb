# todo/urls.py
from django.contrib import admin
from django.urls import path
from news import views

urlpatterns = [
    path('news', views.index, name="news"),
]
