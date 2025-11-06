# slideshow/views.py
from django.shortcuts import render
from django.views.generic import ListView
from .models import Slideshow
from bqb import settings
import os


class SlideshowView(ListView):
    model = Slideshow
    template_name = 'slideshow/slideshow.html'


def showimages(request):
    path=settings.MEDIA_ROOT
    img_list = os.listdir(path + "/images/Downtown Albuquerque C19 Art/")
    # print(request)
    # print(img_list)
    return render(request, 'slideshow/showimages.html', {'object_list':img_list})