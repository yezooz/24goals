# coding=utf-8
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required

from myscore.main.models import *


@staff_member_required
def multi_edit(request):
    countries = Countries.objects.all().order_by('name_en')
    if request.POST:
        post = request.POST.copy()
        for country in countries:
            cid = str(country.id)
            if country.name_en != post["name_en_" + cid] or country.name_pl != post["name_pl_" + cid]:
                country.name_en = post["name_en_" + cid]
                country.name_pl = post["name_pl_" + cid]
                country.save()

        request.user.message_set.create(message='Lista państw zauktualizowana')
        return HttpResponseRedirect("/admin/main/countries/multi_edit/")

    return render_to_response("admin/countries/multi_edit.html", {'countries': countries}, RequestContext(request, {}))
