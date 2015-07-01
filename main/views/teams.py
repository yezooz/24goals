# coding=utf-8
# from django import newforms as forms
from myscore.main.models import *
# from django.db.models import Q
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
import myscore.libs.helpers as helpers
from myscore.main.modules import menu
from myscore.main.modules.matches import league_table, last_matches
from myscore.main.modules.matches.results import render_results, render_live_fixtures
from myscore.main.modules.news import related_news


def leagues_list(request, country_name=0):
    country_id = helpers.reveal_country_name(country_name)
    if country_id == 0:
        return HttpResponseRedirect("/")
    else:
        league = Leagues.objects.get(country__id=country_id)
        if settings.LANGUAGE_CODE == 'pl':
            return HttpResponseRedirect("/%s/%s/" % (_('Druzyny URL'), league.name_pl_url))
        else:
            return HttpResponseRedirect("/%s/%s/" % (_('Druzyny URL'), league.name_en_url))

        # return render_to_response("teams/leagues_list.html", {'leagues' : leagues}, RequestContext(request, {}))


def teams_list(request, country_name, league_name, season="2007-2008"):
    league_id = helpers.reveal_league_name(league_name)
    league = Leagues.objects.get(pk=league_id)
    teams = Teams.objects.filter(current_league_id=league_id).order_by('name_en')

    return render_to_response("teams/teams_list.html", {
        'league': league,
        'teams': teams,
        'league_table': league_table.render(league_id),
        'league_news': related_news.render_league(league_id),
        'league_news_most_popular': related_news.most_popular_league(league_id),
        'results': render_results(league_id=league_id),
        'live_fixtures': render_live_fixtures(league_id=league_id),
        'menu': menu.render(request, 'index', 'index', {}, True)}, RequestContext(request, {}))


def details(request, team_name, season="2007-2008"):
    team = get_object_or_404(Teams, name_en_url=team_name)
    # season = get_object_or_404(Seasons, url=season)

    return render_to_response("teams/details.html", {
        'team': team,
        'teams_news': related_news.render_team(team.id),
        'team_news_most_popular': related_news.most_popular_team(team.id),
        'league_table': league_table.render(team.current_league_id, team.id),
        'results': last_matches.render_team(team.id),
        'live_fixtures': render_live_fixtures(team_id=team.id),
        'menu': menu.render(request, 'index', 'index', {}, True)}, RequestContext(request, {}))


# fixtures, results, news, info

def fixtures(request, team_name, season="2007-2008"):
    team = get_object_or_404(Teams, name_en_url=team_name)
    return render_to_response('teams/fixtures.html', {'team': team}, RequestContext(request, {}))


def results(request, team_name, season="2007-2008"):
    team = get_object_or_404(Teams, name_en_url=team_name)
    return render_to_response('teams/results.html', {})


def news(request, team_name, season="2007-2008"):
    team = get_object_or_404(Teams, name_en_url=team_name)
    return render_to_response('teams/news.html', {})


def info(request, team_name, season="2007-2008"):
    team = get_object_or_404(Teams, name_en_url=team_name)
    return render_to_response('teams/info.html', {})


def tables(request, team_name, season="2007-2008"):
    team = get_object_or_404(Teams, name_en_url=team_name)

    if not season:
        season_id = Seasons.objects.get(is_current=1).id
    else:
        season_id = Seasons.objects.get(lead_year=season).id

    return render_to_response('teams/tables.html', {'team': team, 'league_table': league_table.render(league.id),
                                                    'last5': last_matches.render(match)})
