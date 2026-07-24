from django.contrib import admin
from django.utils import timezone
import json
import os
from collections import Counter
from .forms import NewsForm
from .models import Cities, Counties, News, Region, ScrapeJob
from django.conf import settings
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path


# Django Admin branding
admin.site.site_header = "BurqueBro Administration"
admin.site.site_title = "BurqueBro Admin"
admin.site.index_title = "BurqueBro Site Management"

def article_counts_view(request):
    json_path = os.path.join(settings.BQB_URL, "news.json")

    source_counts = Counter()
    total_articles = 0
    error_message = ""

    try:
        with open(json_path, "r", encoding="utf-8") as json_file:
            articles = json.load(json_file)

        total_articles = len(articles)

        for article in articles:
            source = article.get("source") or "Unknown"
            source_counts[source] += 1

    except FileNotFoundError:
        error_message = f"news.json was not found at {json_path}"

    except json.JSONDecodeError as exc:
        error_message = f"news.json contains invalid JSON: {exc}"

    rows = [
        {
            "source": source,
            "count": count,
            "percentage": (
                round(count / total_articles * 100, 1)
                if total_articles
                else 0
            ),
        }
        for source, count in source_counts.most_common()
    ]

    context = {
        **admin.site.each_context(request),
        "title": "Article Counts by News Source",
        "rows": rows,
        "total_articles": total_articles,
        "total_sources": len(rows),
        "error_message": error_message,
    }

    return TemplateResponse(
        request,
        "news/article_counts.html",
        context,
    )

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    form = NewsForm
    list_display = ("title", "city", "county", "region", "function", "published")
    ordering = ("title",)
    actions = ("set_published_true", "set_published_false")

    @admin.action(description="Publish selected news")
    def set_published_true(self, request, queryset):
        queryset.update(published=True)

    @admin.action(description="Unpublish selected news")
    def set_published_false(self, request, queryset):
        queryset.update(published=False)


@admin.register(Cities)
class CitiesAdmin(admin.ModelAdmin):
    list_display = ("name", "county")
    ordering = ("name",)


@admin.register(Counties)
class CountiesAdmin(admin.ModelAdmin):
    list_display = ("name",)
    ordering = ("name",)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    ordering = ("name",)


@admin.register(ScrapeJob)
class ScrapeJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "source",
        "requested_by",
        "created_at",
        "started_at",
        "finished_at",
        "elapsed_time",
    )

    list_filter = (
        "status",
        "source",
        "created_at",
    )

    search_fields = (
        "source",
        "requested_by__username",
        "error_message",
    )

    ordering = ("-created_at",)

    @admin.display(description="Elapsed Time")
    def elapsed_time(self, obj):
        if not obj.started_at:
            return "Not started"

        end_time = obj.finished_at or timezone.now()
        elapsed = end_time - obj.started_at

        total_seconds = max(0, int(elapsed.total_seconds()))

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours:
            return f"{hours}h {minutes}m {seconds}s"

        if minutes:
            return f"{minutes}m {seconds}s"

        return f"{seconds}s"

