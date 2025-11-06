from django.contrib import admin
from .models import News, Counties, Cities, Region
from .forms import NewsForm


class NewsAdmin(admin.ModelAdmin):
    form = NewsForm
    list_display = ('title', 'city', 'county', 'region', 'function', 'published')
    ordering = ['title']

    def set_published_true(self, request, queryset):
        queryset.update(published=True)

    def set_published_false(self, request, queryset):
        queryset.update(published=False)

    set_published_true.short_description = "Publish selected news"
    set_published_false.short_description = "Unpublish selected news"

    actions = [set_published_true, set_published_false]


class CitiesAdmin(admin.ModelAdmin):
    list_display = ('name', 'county')
    ordering = ['name']


class CountiesAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ['name']


class RegionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ['name']


admin.site.register(News, NewsAdmin)
admin.site.register(Counties, CountiesAdmin)
admin.site.register(Cities, CitiesAdmin)
admin.site.register(Region, RegionAdmin)
