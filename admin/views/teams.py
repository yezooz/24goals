# coding=utf-8
from django import oldforms, template
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache

from myscore.main.models import *


@staff_member_required
def multi_edit(request):
    teams = Teams.objects.all().order_by('name_espn')
    leagues = Leagues().get_season_leagues()

    if request.POST:
        post = request.POST.copy()
        for team in teams:
            tid = str(team.id)
            if team.name_espn != post["name_espn_" + tid] or team.name_live != post[
                        "name_live_" + tid] or team.name_en != post["name_en_" + tid] or team.name_pl != post[
                        "name_pl_" + tid] or team.current_league_id != post["curr_lid_" + tid]:
                team.name_espn = post["name_espn_" + tid]
                team.name_live = post["name_live_" + tid]
                team.name_en = post["name_en_" + tid]
                team.name_pl = post["name_pl_" + tid]
                team.current_league_id = post["curr_lid_" + tid]
                team.save()

        return HttpResponseRedirect("/admin/main/teams/multi_edit/")

    return render_to_response("admin/teams/multi_edit.html", {'teams': teams, 'leagues': leagues},
                              RequestContext(request, {}))


@staff_member_required
def multi_add(request):
    multi_count = range(1, 25)

    if request.POST:
        post = request.POST.copy()

        for i in multi_count:
            i = str(i)

            if post.has_key("name_en_" + i) and post["name_en_" + i] != "":
                t = Teams()
                t.name_en = post["name_en_" + i]
                t.name_pl = post["name_pl_" + i]
                t.country_id = 1
                t.save()
                request.user.message_set.create(message="Dodano drużynę o ID %s" % t.id)

        return HttpResponseRedirect("/admin/main/teams/multi_add/")

    return render_to_response("admin/teams/multi_add.html", {'multi_count': multi_count}, RequestContext(request, {}), )
