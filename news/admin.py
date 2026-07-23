from django.contrib import admin
from django.utils import timezone

from .forms import NewsForm
from .models import Cities, Counties, News, Region, ScrapeJob


# Django Admin branding
admin.site.site_header = "BurqueBro Administration"
admin.site.site_title = "BurqueBro Admin"
admin.site.index_title = "BurqueBro Site Management"

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