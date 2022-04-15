# slideshow/urls.py
from django.urls import path

from .views import SlideshowView, showimages

urlpatterns = [
    path('slideshow/', SlideshowView.as_view(), name='slideshow'),
    path('show-images/', showimages, name='show-images'),
]