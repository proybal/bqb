# bqb/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from accounts.views import activate, loginPage, registerPage
from news import views
from news.admin import article_counts_view


urlpatterns = [
    path(
        "",
        RedirectView.as_view(
            pattern_name="state_news",
            permanent=False,
        ),
        name="home",
    ),

    path(
        "home/",
        RedirectView.as_view(
            pattern_name="state_news",
            permanent=False,
        ),
        name="home-redirect",
    ),

    path(
        "admin/article-counts/",
        admin.site.admin_view(article_counts_view),
        name="article-counts",
    ),

    path("admin/", admin.site.urls),

    path("manifest.json", views.manifest, name="manifest"),
    path("service_worker.js", views.service_worker, name="service_worker"),
    path("offline/", views.offline, name="offline"),
    path(
        "offline-news/",
        views.offline_news,
        name="offline-news",
    ),

    path("login/", loginPage, name="login"),
    path("signup/", registerPage, name="signup"),
    path(
        "activate/<slug:uidb64>/<slug:token>/",
        activate,
        name="activate",
    ),

    path("", include("pages.urls")),
    path("", include("slideshow.urls")),
    path("", include("news.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )