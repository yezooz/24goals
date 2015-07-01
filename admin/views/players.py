# coding=utf-8
from django import oldforms, template
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache

from myscore.main.models import *


@staff_member_required
def multi_add(request):
    multi_count = range(1, 25)
    teams = list(Teams.objects.filter(name_pl__gt="").order_by('name_pl'))

    if request.POST:
        post = request.POST.copy()

        global_team_id = False
        if post["team_id"] != "":
            global_team_id = post["team_id"]

        for i in multi_count:
            i = str(i)
            if post["last_name_" + i] != "":
                if not global_team_id:
                    if post["team_id_" + i] != "":
                        team_id = post["team_id_" + i]
                    else:
                        team_id = ""
                else:
                    team_id = global_team_id

                p = Players()
                p.first_name = post["first_name_" + i]
                p.last_name = post["last_name_" + i]
                p.current_team_id = team_id
                p.position = post["position_" + i]

                if p.current_team_id != "":
                    p.current_team_name = Teams.objects.get(pk=p.current_team_id).name_espn

                p.save()
                request.user.message_set.create(message="Dodano gracza o ID %s" % p.id)

        return HttpResponseRedirect("/admin/main/players/multi_add/")

    return render_to_response("admin/players/multi_add.html", {'teams': teams, 'multi_count': multi_count},
                              RequestContext(request, {}), )


@staff_member_required
def multi_edit(request, team_id):
    teams = Teams.objects.all().order_by('name_espn')
    players = Players.objects.filter(current_team_id=team_id)
    if request.POST:
        post = request.POST.copy()
        for player in players:
            pid = str(player.id)
            if player.first_name != post["first_name_" + pid] or player.last_name != post[
                        "last_name_" + pid] or player.current_team_id != team_id:
                player.first_name = post["first_name_" + pid]
                player.last_name = post["last_name_" + pid]
                player.position = post["position_" + pid]

                player.save()

        return HttpResponseRedirect("/admin/main/players/multi_edit/" + team_id)

    return render_to_response("admin/players/multi_edit.html", {'players': players, 'teams': teams},
                              RequestContext(request, {}))


@staff_member_required
def transfers(request, team_id):
    teams = Teams.objects.all().order_by('name_espn')
    players = Players.objects.filter(current_team_id=team_id)

    return render_to_response("admin/players/transfers.html", {'players': players, 'teams': teams},
                              RequestContext(request, {}))
