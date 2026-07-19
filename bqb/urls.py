# bqb URL Configuration

from django.contrib import admin
from django.urls import include, path

import news.views
from accounts.views import signup_view, loginPage, activate
from django.conf import settings 
from django.urls import path, include 
from django.conf.urls.static import static 

urlpatterns = [
    path('', news.views.index, name="news"),
    path('home/', news.views.index, name="news"),
    path('', include('pages.urls')),
    path('', include('slideshow.urls')),
    path('login/', loginPage, name='login'),
    # path('home/', include('pages.urls'), name="home"),
    path('admin/', admin.site.urls),
    path('signup/', signup_view, name="signup"),
    path('activate/<slug:uidb64>/<slug:token>/', activate, name='activate'),
    path('', include('news.urls')),
]

if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)