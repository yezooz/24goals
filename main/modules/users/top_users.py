# coding=utf-8
from myscore.main.models import Accounts
# from django.db.models import Q
from django.template.loader import render_to_string
from django.conf import settings
import os, sys, urlparse, re, datetime
from myscore.libs.cache import TemplatesCache as tcache
from django.core.cache import cache
# import myscore.libs.helpers as helpers

def render(league_id=0, team_id=0, limit=10):
    try:
        limit = int(limit)
    except:
        limit = 10

    # caching
    key = "supporters_lid_%s_tid_%s_lang_%s_limit_%s" % (league_id, team_id, settings.LANGUAGE_CODE, limit)
    c = cache.get(key)
    if c: return c

    if team_id != 0:
        users = Accounts().get_supporters_by_team(team_id=team_id)[:limit]
        ret = render_to_string('modules/users/finest_supporters_team.html', {'users': users})
        cache.set(key, ret)
        return ret

    elif league_id != 0:
        users = Accounts().get_supporters_by_league(league_id=league_id)[:limit]
        ret = render_to_string('modules/users/finest_supporters_league.html', {'users': users})
        cache.set(key, ret)
        return ret

    else:
        users = Accounts().get_supporters()[:limit]
        ret = render_to_string('modules/users/finest_supporters.html', {'users': users})
        cache.set(key, ret)
        return ret


def top_overall(limit=10):
    try:
        limit = int(limit)
    except:
        limit = 10

    # caching
    key = "top_users_overall_limit_%s_lang_%s" % (limit, settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c:
        return c

    users = Accounts().get_top_overall_supporters()[:limit]
    ret = render_to_string('modules/users/top_users.html', {'users': users})
    cache.set(key, ret)
    return ret


def top_month(year_no=0, month_no=0, limit=10):
    try:
        limit = int(limit)
    except:
        limit = 10

    users = Accounts().get_top_month_supporters(year_no=year_no, month_no=month_no)[:limit]
    ret = render_to_string('modules/users/top_users.html', {'users': users})
    return ret


def top_week(week_no):
    pass


def top_league(league_id=0):
    pass


def top_countries():
    pass
