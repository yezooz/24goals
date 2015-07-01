# coding=utf-8
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required

from myscore.main.models import *


@staff_member_required
def multi_edit(request):
    seasons = Seasons.objects.all()
    if request.POST:
        post = request.POST.copy()
        for season in seasons:
            sid = str(season.id)
            if season.lead_year != post["lead_year_" + sid] or season.title != post["title_" + sid]:
                season.lead_year = post["lead_year_" + sid]
                season.title = post["title_" + sid]
                season.save()

        return HttpResponseRedirect("/admin/main/seasons/multi_edit/")

    return render_to_response("admin/seasons/multi_edit.html", {'seasons': seasons}, RequestContext(request, {}))
