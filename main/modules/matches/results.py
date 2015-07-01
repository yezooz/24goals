# coding=utf-8
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache

from myscore.main.models import Matches


def render_results(league_id=0, team_id=0):
    # caching
    key = "render_results_lid_%s_tid_%s_lang_%s" % (league_id, team_id, settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c: return c

    if team_id == 0:
        matches = Matches().get_results_by_league(league_id=league_id)[:10]
    else:
        matches = Matches().get_results_by_team(team_id=team_id)[:10]
    ret = render_to_string('modules/matches/results.html', {'matches': matches})
    cache.set(key, ret)
    return ret


def render_fixtures(league_id=0, team_id=0):
    # caching
    key = "render_fixtures_lid_%s_tid_%s_lang_%s" % (league_id, team_id, settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c: return c

    if team_id == 0:
        matches = Matches().get_fixtures_by_league(league_id=league_id)[:10]
    else:
        matches = Matches().get_fixtures_by_team(team_id=team_id)[:10]

    ret = render_to_string('modules/matches/results.html', {'matches': matches})
    cache.set(key, ret)
    return ret


def render_live_fixtures(league_id=0, team_id=0):
    # caching
    key = "render_live_fixtures_lid_%s_tid_%s_lang_%s" % (league_id, team_id, settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c: return c

    if team_id == 0:
        matches = Matches().get_live_fixtures_by_league(league_id=league_id)[:10]
    else:
        matches = Matches().get_live_fixtures_by_team(team_id=team_id)[:10]

    ret = render_to_string('modules/matches/results.html', {'matches': matches})
    cache.set(key, ret)
    return ret
