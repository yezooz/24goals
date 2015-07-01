# coding=utf-8
import re
import logging

from django import http
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, HttpResponsePermanentRedirect

import datetime
import time
from time import strptime
from myscore.main.models import *

# from django.utils.translation import ugettext as _
from django.conf import settings
import myscore.libs.helpers as helpers
from myscore.libs.slughifi import slughifi
from django.core.cache import cache


def match_old_url_redirector(request, league_name, status_name=None, match_date=None):
    if league_name == 'angielska':
        nln = '/mecze/anglia/premiership/'
    elif league_name == 'francuska':
        nln = '/mecze/francja/ligue-1/'
    elif league_name == 'hiszpanska':
        nln = '/mecze/hiszpania/primera-division/'
    elif league_name == 'niemiecka':
        nln = '/mecze/niemcy/bundesliga/'
    elif league_name == 'polska':
        nln = '/mecze/polska/orange-ekstraklasa/'
    elif league_name == 'wloska':
        nln = '/mecze/wlochy/serie-a/'
    elif league_name == 'liga-mistrzow':
        nln = '/mecze/europa/liga-mistrzow/'
    elif league_name == 'puchar-uefa':
        nln = '/mecze/europa/puchar-uefa/'
    else:
        nln = '/'

    # return HttpResponsePermanentRedirect(request.META['PATH_INFO'].replace(league_name, nln))
    return HttpResponsePermanentRedirect(nln)


def news_old_url_redirector(request, league_name, news_date=None):
    if league_name == 'angielska':
        nln = '/news/anglia/premiership/'
    elif league_name == 'francuska':
        nln = '/news/francja/ligue-1/'
    elif league_name == 'hiszpanska':
        nln = '/news/hiszpania/primera-division/'
    elif league_name == 'niemiecka':
        nln = '/news/niemcy/bundesliga/'
    elif league_name == 'polska':
        nln = '/news/polska/orange-ekstraklasa/'
    elif league_name == 'wloska':
        nln = '/news/wlochy/serie-a/'
    elif league_name == 'liga-mistrzow':
        nln = '/news/europa/liga-mistrzow/'
    elif league_name == 'puchar-uefa':
        nln = '/news/europa/puchar-uefa/'
    else:
        nln = '/'

    if news_date:
        nln += news_date + '/'

    # return HttpResponsePermanentRedirect(request.META['PATH_INFO'].replace(league_name, nln))
    return HttpResponsePermanentRedirect(nln)


def match_detail_old_url_redirector(request, home_team, away_team, match_id):
    return HttpResponsePermanentRedirect("/rejestracja/")


# ---


def regenerate_fans_table(request):
    def regenerate(teams, table_type='p', today=datetime.date.today()):
        order = ""
        if table_type == 'p':
            order = '-points'
        elif table_type == 'a':
            order = '-avg'
        elif table_type == 'f':
            order = '-fans'

        for team_id, points in teams.iteritems():
            try:
                ft = FansTable.objects.get_or_create(team=Teams.objects.get(pk=int(team_id)), table_type=table_type,
                                                     league_id=10)[0]
                ft.fans = count[team_id]
                ft.points = points
                ft.avg = int(ft.points) / int(ft.fans)
                ft.save()
            except:
                pass

        i = 1
        for team in FansTable.objects.filter(table_type=table_type).order_by(order):
            team.position = i
            # team.date = today
            team.save()
            i += 1

    teams = {}
    count = {}
    for user in Accounts.objects.filter(favourite_team_id__gt=0):
        if user.favourite_team_id in teams:
            teams[user.favourite_team_id] += user.points
            count[user.favourite_team_id] += 1
        else:
            teams[user.favourite_team_id] = user.points
            count[user.favourite_team_id] = 1

    # TODO: dodac jeszcze licznik, zeby sprawdzic ile jest fanow w sumie

    regenerate(teams)
    regenerate(teams, table_type='a')
    regenerate(teams, table_type='f')

    return HttpResponse("done!")


def refresh_player_names(request):
    if not (request.user.is_authenticated() and request.user.is_staff):
        raise http.Http404

    dets = MatchDetails.objects.all()
    for d in dets:
        try:
            pid = d.player_id
            player = Players.objects.get(pk=pid)

            d.player_name = player.espn_name
            d.save()
        except:
            print "error in %s" % d.id

    return HttpResponse("done!")


def refresh_who_online(request):
    who_online = cache.get("who_online")
    new_dict = who_online.copy()

    if who_online is not None:
        for user, time in who_online.iteritems():
            if (datetime.datetime.now() + datetime.timedelta(minutes=-15)) > time:
                del new_dict[str(user)]

    cache.set("who_online", new_dict, 3600 * 24)

    return HttpResponse("done!")
