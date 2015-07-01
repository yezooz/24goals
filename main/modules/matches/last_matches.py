# coding=utf-8
import os

from django.db.models import Q
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache

import sys
from myscore.main.models import Matches


def render_team(team_id, limit=10, short=False):
    try:
        limit = int(limit)
    except:
        limit = 10

    if not short:
        width = 396
    else:
        width = 300

    # caching
    key = "last_render_results_tid_%s_limit_%s_width_%s_lang_%s" % (team_id, limit, width, settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c: return c

    home10_1 = Matches.objects.filter(Q(home_team__id=team_id) | Q(away_team__id=team_id)).filter(
        season__id=settings.CURRENT_SEASON_ID, status='f').order_by('-match_date', '-match_time')[:limit]
    away10_1 = Matches.objects.filter(Q(home_team__id=team_id) | Q(away_team__id=team_id)).filter(
        season__id=settings.CURRENT_SEASON_ID, status='f').order_by('-match_date', '-match_time')[:limit]
    home10_2 = Matches.objects.filter(season__id=settings.CURRENT_SEASON_ID, home_team__id=team_id,
                                      status='f').order_by('-match_date', '-match_time')[:limit]
    away10_2 = Matches.objects.filter(season__id=settings.CURRENT_SEASON_ID, home_team__id=team_id,
                                      status='f').order_by('-match_date', '-match_time')[:limit]
    home10_3 = Matches.objects.filter(season__id=settings.CURRENT_SEASON_ID, away_team__id=team_id,
                                      status='f').order_by('-match_date', '-match_time')[:limit]
    away10_3 = Matches.objects.filter(season__id=settings.CURRENT_SEASON_ID, away_team__id=team_id,
                                      status='f').order_by('-match_date', '-match_time')[:limit]

    ret = render_to_string("modules/matches/last_team_matches_%s.html" % width,
                           {'limit': limit, 'team_id': team_id, 'home10_1': home10_1, 'away10_1': away10_1,
                            'home10_2': home10_2, 'away10_2': away10_2, 'home10_3': home10_3, 'away10_3': away10_3})
    cache.set(key, ret)
    return ret


def render(match, limit=5):
    try:
        limit = int(limit)
    except:
        limit = 5

    # caching
    key = "last_render_tid_%s_limit_%s_lang_%s" % (team_id, limit, settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c: return c

    home5_1 = Matches.objects.filter(Q(home_team__id=match.home_team.id) | Q(away_team__id=match.home_team.id)).filter(
        season__id=settings.CURRENT_SEASON_ID, status='f').order_by('-match_date', '-match_time')[:limit]
    away5_1 = Matches.objects.filter(Q(home_team__id=match.away_team.id) | Q(away_team__id=match.away_team.id)).filter(
        season__id=settings.CURRENT_SEASON_ID, status='f').order_by('-match_date', '-match_time')[:limit]
    home5_2 = Matches.objects.filter(season__id=settings.CURRENT_SEASON_ID, home_team__id=match.home_team.id,
                                     status='f').order_by('-match_date', '-match_time')[:limit]
    away5_2 = Matches.objects.filter(season__id=settings.CURRENT_SEASON_ID, home_team__id=match.away_team.id,
                                     status='f').order_by('-match_date', '-match_time')[:limit]
    home5_3 = Matches.objects.filter(season__id=settings.CURRENT_SEASON_ID, away_team__id=match.home_team.id,
                                     status='f').order_by('-match_date', '-match_time')[:limit]
    away5_3 = Matches.objects.filter(season__id=settings.CURRENT_SEASON_ID, away_team__id=match.away_team.id,
                                     status='f').order_by('-match_date', '-match_time')[:limit]

    res = render_to_string('modules/matches/last_matches.html',
                           {'limit': limit, 'home5_1': home5_1, 'away5_1': away5_1, 'home5_2': home5_2,
                            'away5_2': away5_2, 'home5_3': home5_3, 'away5_3': away5_3})
    cache.set(key, ret)
    return ret
