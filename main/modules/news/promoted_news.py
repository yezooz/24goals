# coding=utf-8
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache

from myscore.main.models import News


def render():
    # caching
    key = "promoted_news_lang_%s" % (settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c: return c

    news = News.objects.filter(is_promoted=1, lang=settings.LANGUAGE_CODE).order_by('-published_at')
    if news.count() == 0: return ''

    ret = render_to_string('modules/news/promoted_news.html', {'news': news})
    cache.set(key, ret)
    return ret
