# coding=utf-8
from django import oldforms, template
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache

from myscore.main.models import *


@staff_member_required
def index(request):
    if request.POST:
        # create FILTER
        if request.POST.has_key('filter'):
            filter = False
            top_filter = False

            comments = Comments.objects.all()
            if request.POST['filter_nid'] != "":
                comments = comments.filter(dst='m', dst_id=request.POST['filter_nid'])
                filter = True
                top_filter = True

            elif request.POST['filter_mid'] != "":
                comments = comments.filter(dst__in=['a', 'm'], dst_id=request.POST['filter_mid'])
                filter = True
                top_filter = True

            if request.POST['filter_uid'] != "":
                comments = comments.filter(user__id=request.POST['filter_uid'])
                filter = True
                top_filter = True

            if request.POST['filter_date_start'] != "":
                comments = comments.filter(created_at__gte=request.POST['filter_date_start'])
                filter = True

            if request.POST['filter_date_end'] != "":
                comments = comments.filter(created_at__lte=request.POST['filter_date_end'])
                filter = True

            if request.POST['filter_accepted'] != "0":
                comments = comments.filter(is_accepted=request.POST['filter_accepted'])
                filter = True

            if request.POST['filter_deleted'] != "":
                comments = comments.filter(is_deleted=request.POST['filter_deleted'])
                filter = True

            if top_filter:
                comments = comments.select_related().order_by('created_at')
            elif filter:
                comments = comments.select_related().order_by('created_at')[:50]
            else:
                comments = comments.filter(is_deleted=0, is_accepted=1).select_related().order_by('created_at')[:30]

        # select elements to EDIT
        elif request.POST.has_key('delete'):
            ids = []
            for id in request.POST.iterkeys():
                if id.find('delete_') >= 0:
                    ids.append(id.replace('delete_', ''))

            if len(ids) > 0:
                cs = Comments.objects.in_bulk(ids).values()
                for c in cs:
                    c.mark_as_deleted()

                return HttpResponseRedirect(request.path)

    else:
        comments = Comments.objects.filter(is_deleted=0, is_accepted=1, created_at__gte=datetime.date.today()).order_by(
            '-created_at')

    return render_to_response(
        "admin/comments/index.html",
        {'comments': comments},
        RequestContext(request, {}),
    )


def accept(request, comment_id):
    c = Comments.objects.get(pk=comment_id)
    if c.is_accepted:
        c.unaccept()
    else:
        c.accept()

    request.user.message_set.create(message="Zmieniono status komentarza")
    return HttpResponseRedirect(request.META["HTTP_REFERER"])
