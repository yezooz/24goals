# coding=utf-8
from django import oldforms, template
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache

import datetime
from myscore.main.models import *


@staff_member_required
def index(request):
    if request.POST:
        # create FILTER
        if request.POST.has_key('filter'):
            filter = False
            top_filter = False

            videos = Videos.objects.all()
            if request.POST['filter_nid'] != "":
                videos = videos.filter(dst_id=request.POST['filter_nid'], dst="news")
                filter = True
                top_filter = True

            elif request.POST['filter_mid'] != "":
                videos = videos.filter(dst_id=request.POST['filter_mid'], dst="match")
                filter = True
                top_filter = True

            if request.POST['filter_uid'] != "":
                videos = videos.filter(user__id=request.POST['filter_uid'])
                filter = True
                top_filter = True

            if request.POST['filter_date_start'] != "":
                videos = videos.filter(created_at__gte=request.POST['filter_date_start'])
                filter = True

            if request.POST['filter_date_end'] != "":
                videos = videos.filter(created_at__lte=request.POST['filter_date_end'])
                filter = True

            if request.POST['filter_accepted'] != "":
                videos = videos.filter(is_accepted=request.POST['filter_accepted'], is_deleted=0)
                filter = True

            elif request.POST['filter_deleted'] != "":
                videos = videos.filter(is_deleted=request.POST['filter_deleted'])
                filter = True

            if top_filter:
                videos = videos.select_related().order_by('created_at')
            elif filter:
                videos = videos.select_related().order_by('created_at')[:10]
            else:
                videos = videos.filter(is_accepted=0, is_deleted=0).select_related().order_by('created_at')[:10]

        # select elements to EDIT
        elif request.POST.has_key('delete'):
            ids = []
            for id in request.POST.iterkeys():
                if id.find('delete_') >= 0:
                    ids.append(id.replace('delete_', ''))

            if len(ids) > 0:
                cs = Videos.objects.in_bulk(ids).values()
                for c in cs:
                    c.mark_as_deleted()

                return HttpResponseRedirect(request.path)

    else:
        videos = Videos.objects.filter(is_accepted=0, is_deleted=0).order_by('created_at')[:10]

    return render_to_response("admin/videos/index.html", {
        'videos': videos,
        'vid_cats': VideoCategories.objects.all().order_by('name_pl')
    }, RequestContext(request, {}))


def preview(request, video_id):
    video = Videos.objects.get(pk=video_id)
    return render_to_response("admin/videos/preview.html", {'video': video})


def edit(request, video_id):
    video = Videos.objects.get(pk=video_id)
    vid_cats = VideoCategories.objects.all().order_by('name_pl')

    if request.POST:
        post = request.POST.copy()

        if post["name"] == '':
            request.user.message_set.create(message="Chyba zapomniałeś o tytule ?")
            return HttpResponseRedirect("/admin/main/news/%s/" % video.id)

        video.content = post["content"]
        video.lang = post["lang"]
        video.view_count = post["view_count"]
        video.cat_id = post["cat_id"]
        video.published_at = post["published_at"]

        video.save()
        request.user.message_set.create(message="Zmieniono film %s" % video.id)

        return HttpResponseRedirect("/admin/main/videos/%s/" % video.id)

    return render_to_response("admin/videos/edit.html", {'video': video, 'vid_cats': vid_cats})


def accept(request, video_id):
    try:
        video = Videos.objects.get(pk=video_id).accept()
        request.user.message_set.create(message="Film został zaakceptowany")
    except:
        request.user.message_set.create(message="Nie udało się zaakceptować filmu")

    return HttpResponseRedirect(request.META["HTTP_REFERER"])
