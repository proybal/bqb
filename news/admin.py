from django.contrib import admin

from .forms import NewsForm
from .models import Cities, Counties, News, Region, ScrapeJob


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
    list_display = ("id", "status", "source", "requested_by", "created_at", "started_at", "finished_at", "article_count")
    list_filter = ("status", "source")
    readonly_fields = ("created_at", "started_at", "finished_at", "article_count", "message")
