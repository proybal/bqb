# todo/urls.py
from django.contrib import admin
from django.urls import path
from todo import views

urlpatterns = [
    path('todo', views.index, name = "todo"),
]