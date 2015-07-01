# coding=utf-8
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required

from myscore.main.models import *


@staff_member_required
def multi_edit(request):
    leagues = Leagues.objects.all()
    if request.POST:
        post = request.POST.copy()
        for league in leagues:
            lid = str(league.id)
            if league.name_espn != post["name_espn_" + lid] or league.name_en != post[
                        "name_en_" + lid] or league.name_pl != post["name_pl_" + lid]:
                league.name_espn = post["name_espn_" + lid]
                league.name_en = post["name_en_" + lid]
                league.name_pl = post["name_pl_" + lid]
                league.save()

        return HttpResponseRedirect("/admin/main/leagues/multi_edit/")

    return render_to_response("admin/leagues/multi_edit.html", {'leagues': leagues}, RequestContext(request, {}))
