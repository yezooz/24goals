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

            news = News.objects.all()
            if request.POST['filter_nid'] != "":
                news = news.filter(pk=request.POST['filter_nid'])
                filter = True
                top_filter = True

            if request.POST['filter_uid'] != "":
                news = news.filter(user__id=request.POST['filter_uid'])
                filter = True
                top_filter = True

            if request.POST['filter_date_start'] != "":
                news = news.filter(created_at__gte=request.POST['filter_date_start'])
                filter = True

            if request.POST['filter_date_end'] != "":
                news = news.filter(created_at__lte=request.POST['filter_date_end'])
                filter = True

            if request.POST['filter_accepted'] != "":
                news = news.filter(is_accepted=request.POST['filter_accepted'], is_deleted=0)
                filter = True

            elif request.POST['filter_deleted'] != "":
                news = news.filter(is_deleted=request.POST['filter_deleted'])
                filter = True

            if top_filter:
                news = news.order_by('created_at')
            elif filter:
                news = news.order_by('created_at')[:20]
            else:
                news = news.filter(is_accepted=0, is_deleted=0, is_temp=0).order_by('created_at')[:20]

            # # select elements to EDIT
            # elif request.POST.has_key('delete'):
            # 	ids = []
            # 	for id in request.POST.iterkeys():
            # 		if id.find('delete_') >= 0:
            # 			ids.append(id.replace('delete_', ''))
            #
            # 	if len(ids) > 0:
            # 		cs = News.objects.in_bulk(ids).values()
            # 		for c in cs:
            # 			c.mark_as_deleted()
            #
            # 		return HttpResponseRedirect(request.path)

    else:
        news = News.objects.filter(is_accepted=0, is_deleted=0, is_temp=0).order_by('created_at')

    return render_to_response(
        "admin/news/index.html",
        {'news': news},
        RequestContext(request, {}),
    )


@staff_member_required
def add(request):
    leagues = Leagues.objects.all().order_by('name_pl')
    teams = Teams.objects.all().order_by('name_pl')

    if request.POST:
        post = request.POST.copy()

        n = News()
        n.user = request.user
        n.caption = post["caption"]
        n.short_content = post["short_content"]
        n.content = post["content"]
        n.source = post["source"]
        if n.source.find('http://') == 0:
            n.source = "<a href='%s'>%s</a>" % (n.source, n.source)
        elif n.source.find('www.') == 0:
            n.source = "<a href='http://%s'>%s</a>" % (n.source, n.source)

        n.lang = post["lang"]
        if post["league_id"] != "":
            n.league_id = post["league_id"]
        if post["ass_league_id"]:
            n.assign_league_logo = Leagues.objects.get(pk=post["ass_league_id"])
        if post["ass_team_id"]:
            n.assign_team_logo = Teams.objects.get(pk=post["ass_team_id"])
        n.save()

        request.user.message_set.create(message="Dodano news o ID %s" % n.id)

        return HttpResponseRedirect("/admin/main/news/")

    return render_to_response("admin/news/add.html", {'leagues': leagues, 'teams': teams},
                              RequestContext(request, {}), )


@staff_member_required
def edit(request, news_id):
    leagues = Leagues.objects.all().order_by('name_pl')
    teams = Teams.objects.all().order_by('name_pl')

    news = News.objects.get(pk=news_id)

    if request.POST:
        post = request.POST.copy()

        if post["caption"] == '':
            request.user.message_set.create(message="Chyba zapomniałeś o tytule ?")
            return HttpResponseRedirect("/admin/main/news/%s/" % news.id)

        news.caption = post["caption"]
        news.short_content = post["short_content"]
        news.content = post["content"]
        news.source = post["source"]
        news.lang = post["lang"]
        news.view_count = post["view_count"]
        news.published_at = post["published_at"]

        if news.source.find('http://') == 0:
            news.source = "<a href='%s'>%s</a>" % (news.source, news.source)
        elif news.source.find('www.') == 0:
            news.source = "<a href='http://%s'>%s</a>" % (news.source, news.source)

        if post["league_id"] != "":
            news.league_id = post["league_id"]
        else:
            news.league_id = 0

        if post["ass_league_id"]:
            news.assign_league_logo = Leagues.objects.get(pk=post["ass_league_id"])
        else:
            news.assign_league_logo = 0

        if post["ass_team_id"]:
            news.assign_team_logo = Teams.objects.get(pk=post["ass_team_id"])
        else:
            news.assign_team_logo = 0

        if post.has_key("is_promoted") and post["is_promoted"] == 'on':
            news.is_promoted = 1
        else:
            news.is_promoted = 0

        news.save()

        request.user.message_set.create(message="Zmieniono news %s" % news)

        return HttpResponseRedirect("/admin/main/news/%s/" % news.id)

    return render_to_response("admin/news/edit.html", {'news': news, 'leagues': leagues, 'teams': teams},
                              RequestContext(request, {}), )


@staff_member_required
def accept(request, news_id):
    news = News.objects.get(pk=news_id).accept()
    request.user.message_set.create(message="Potwierdzono news")

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@staff_member_required
def refuse(request, news_id):
    news = News.objects.get(pk=news_id)
    reasons = AutoReplies.objects.filter(type='n')

    if request.POST and request.POST['reason_id'] != "":
        news = News.objects.get(pk=news_id).refuse(reason_id=request.POST['reason_id'])
        request.user.message_set.create(message="Odrzucono news")

        return HttpResponseRedirect("/admin/main/news/")

    return render_to_response("admin/news/refuse.html", {'news': news, 'reasons': reasons},
                              RequestContext(request, {}), )
