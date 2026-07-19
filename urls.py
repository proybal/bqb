"""bqb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from accounts.views import home_view, signup_view, activate
from django.conf import settings
from django.conf.urls.static import static
import news.views

urlpatterns = [
    path('', news.views.index, name="news"),
    path('home/', news.views.index, name="news"),
    path('', include('pages.urls')),
    path('', include('slideshow.urls')),
    path('', include('news.urls')),
    path('', include('KANW.urls')),
    path('admin/', admin.site.urls),
    path('signup/', signup_view, name="signup"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)