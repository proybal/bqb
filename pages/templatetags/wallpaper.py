from random import choice
from django import template

from pages.models import Wallpaper

register = template.Library()


@register.simple_tag(takes_context=True)
def get_wallpapers(context):
    return Wallpaper.published_objects.all()


@register.simple_tag(takes_context=True)
def get_wallpaper(context, pk):
    try:
        return Wallpaper.published_objects.get(pk=pk)
    except Wallpaper.DoesNotExist:
        return None


@register.simple_tag(takes_context=True)
def random_wallpaper(context):
    wallpapers = Wallpaper.published_objects.all()
    try:
        return choice(wallpapers)
    except IndexError:
        return None
