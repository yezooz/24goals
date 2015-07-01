# coding=utf-8
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache

from myscore.main.models import News


def render(league_name, team_id, limit=10):
    try:
        limit = int(limit)
    except:
        limit = 10

    # caching
    key = "other_news_league_%s_team_%s_lang_%s_limit_%s" % (league_name, team_id, settings.LANGUAGE_CODE, limit)
    c = cache.get(key)
    if c: return c

    news = News().get_not_related_to_league(league_name=league_name, team_id=team_id)[:10]

    ret = render_to_string('modules/news/related_news.html', {'news': news})
    cache.set(key, ret, 3600)
    return ret
