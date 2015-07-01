# coding=utf-8
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from myscore.main.models import *
from myscore.main.modules import menu


def show_supporters(request, team_name):
    fav_team = get_object_or_404(Teams, name_en_url=team_name)
    supps = Accounts.objects.filter(favourite_team_id=fav_team.id).order_by('-points')

    return render_to_response('fans/show_supporters.html', {
        'menu': menu.render(request, 'users', 'index', {}, True),
        'team': fav_team,
        'supps': supps, }, context_instance=RequestContext(request))


def show_tables(request, table_type='punkty'):
    tt = 'p'
    if table_type == 'liczba-kibicow':
        tt = 'f'
    elif table_type == 'srednia':
        tt = 'a'
    teams = FansTable.objects.filter(table_type=tt).order_by('position')

    return render_to_response('fans/show_tables.html', {
        'menu': menu.render(request, 'users', 'index', {}, True),
        'teams': teams, }, context_instance=RequestContext(request))
