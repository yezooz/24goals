# coding=utf-8
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required

from myscore.main.models import *


@staff_member_required
def multi_edit(request):
    languages = Languages.objects.all().order_by('name_en')
    if request.POST:
        post = request.POST.copy()
        for lang in languages:
            lid = str(lang.id)
            if lang.name_en != post["name_en_" + lid] or lang.name_pl != post["name_pl_" + lid]:
                lang.name_en = post["name_en_" + lid]
                lang.name_pl = post["name_pl_" + lid]
                lang.save()

        request.user.message_set.create(message='Lista języków została zaktualizowana')
        return HttpResponseRedirect("/admin/main/languages/multi_edit/")

    return render_to_response("admin/languages/multi_edit.html", {'languages': languages}, RequestContext(request, {}))
