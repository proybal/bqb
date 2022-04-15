from django.urls import path
from django.conf.urls import url

import affiliate.views

from . import views

urlpatterns = [
    path('affiliate/', views.index, name='affiliate'),
]
