# coding=utf-8
import os

from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache

import sys
import datetime
from myscore.main.models import News


def render_league(league_id, limit=10, start_from=0):
    try:
        limit = int(limit)
    except:
        limit = 10

    # caching
    key = "related_render_league_%s_lang_%s_limit_%s_start_from_%s" % (
    league_id, settings.LANGUAGE_CODE, limit, start_from)
    c = cache.get(key)
    if c: return c

    news = News().get_related_to_league(league_id=league_id)[start_from:start_from + limit]

    ret = render_to_string('modules/news/related_news.html', {'news': news})
    cache.set(key, ret)
    return ret


def render_team(team_id, limit=10):
    try:
        limit = int(limit)
    except:
        limit = 10

    # caching
    key = "related_render_team_%s_lang_%s_limit_%s" % (team_id, settings.LANGUAGE_CODE, limit)
    c = cache.get(key)
    if c: return c

    news = News().get_related_to_team(team_id=team_id)[:limit]

    ret = render_to_string('modules/news/related_news.html', {'news': news})
    cache.set(key, ret)
    return ret


def most_popular(limit=10):
    try:
        limit = int(limit)
    except:
        limit = 10

    # caching
    key = "most_popular_news_lang_%s_limit_%s" % (settings.LANGUAGE_CODE, limit)
    c = cache.get(key)
    if c: return c

    news = News().get_news(news_date=datetime.date.today().strftime("%Y-%m-%d"), order_by='-view_count')[:limit]

    ret = render_to_string('modules/news/most_popular_news.html', {'news': news})
    cache.set(key, ret, 3600)
    return ret


def most_popular_league(league_id, limit=10):
    try:
        limit = int(limit)
    except:
        limit = 10

    # caching
    key = "most_popular_news_league_%s_lang_%s_limit_%s" % (league_id, settings.LANGUAGE_CODE, limit)
    c = cache.get(key)
    if c: return c

    news = News().get_related_to_league(league_id=league_id, news_date=(
    datetime.datetime.now() + datetime.timedelta(days=-7), datetime.datetime.now()), order_by='-view_count')[:limit]

    ret = render_to_string('modules/news/most_popular_news.html', {'news': news})
    cache.set(key, ret, 3600)
    return ret


def most_popular_team(team_id, limit=10):
    try:
        limit = int(limit)
    except:
        limit = 10

    # caching
    key = "most_popular_news_team_%s_lang_%s_limit_%s" % (team_id, settings.LANGUAGE_CODE, limit)
    c = cache.get(key, 3600)
    if c: return c

    news = News().get_related_to_team(team_id=team_id, news_date=(
    datetime.datetime.now() + datetime.timedelta(days=-7), datetime.datetime.now()), order_by='-view_count')[:limit]

    ret = render_to_string('modules/news/most_popular_news.html', {'news': news})
    cache.set(key, ret)
    return ret
