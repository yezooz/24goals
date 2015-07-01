# coding=utf-8
from django import oldforms, template
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.core.cache import cache

import datetime
from myscore.main.models import *


@staff_member_required
def moderate(request):
    comms_to_mod = Comments.objects.filter(created_at__gte=datetime.date.today(), is_accepted=1, is_deleted=0).count()
    news_to_mod = News.objects.filter(is_accepted=0, is_deleted=0, is_temp=0).count()
    vids_to_mod = Videos.objects.filter(is_accepted=0, is_deleted=0).count()
    imgs_to_mod = Images.objects.filter(is_accepted=0, is_deleted=0).count()

    u09 = cache.get('users_count_09')
    if u09 is None:
        u09 = int(Accounts.objects.filter(
            created_at__range=[datetime.datetime(2007, 9, 1, 0, 0), datetime.datetime(2007, 9, 30, 23, 59)]).count())
    cache.set('users_count_09', u09, 3600 * 24 * 365)

    u10 = cache.get('users_count_10')
    if u10 is None:
        u10 = int(Accounts.objects.filter(
            created_at__range=[datetime.datetime(2007, 10, 1, 0, 0), datetime.datetime(2007, 10, 31, 23, 59)]).count())
    cache.set('users_count_10', u10, 3600 * 24 * 365)

    u11 = cache.get('users_count_11')
    if u11 is None:
        u11 = int(Accounts.objects.filter(
            created_at__range=[datetime.datetime(2007, 11, 1, 0, 0), datetime.datetime(2007, 11, 30, 23, 59)]).count())
    cache.set('users_count_11', u11, 3600 * 24 * 365)

    u12 = cache.get('users_count_12')
    if u12 is None:
        u12 = int(Accounts.objects.filter(
            created_at__range=[datetime.datetime(2007, 12, 1, 0, 0), datetime.datetime(2007, 12, 31, 23, 59)]).count())
    cache.set('users_count_12', u12, 3600 * 24 * 365)

    u01 = cache.get('users_count_01')
    if u01 is None:
        u01 = int(Accounts.objects.filter(
            created_at__range=[datetime.datetime(2008, 1, 1, 0, 0), datetime.datetime(2008, 1, 30, 23, 59)]).count())
    cache.set('users_count_01', u01, 3600 * 24 * 365)

    u02 = int(Accounts.objects.filter(
        created_at__range=[datetime.datetime(2008, 2, 1, 0, 0), datetime.datetime(2008, 2, 29, 23, 59)]).count())

    user_count = Accounts.objects.all().count()
    week_users = Accounts.objects.filter(
        created_at__range=[datetime.datetime.now() + datetime.timedelta(days=-7), datetime.datetime.now()]).count()
    today_users = Accounts.objects.filter(created_at__startswith=datetime.date.today())

    return render_to_response("admin/stats/moderate.html",
                              {'comms_to_mod': comms_to_mod, 'news_to_mod': int(news_to_mod),
                               'vids_to_mod': int(vids_to_mod), 'imgs_to_mod': int(imgs_to_mod),
                               'user_count': user_count, 'today_users': today_users, 'week_users': week_users,
                               'u09': u09, 'u10': u10, 'u11': u11, 'u12': u12, 'u01': u01, 'u02': u02,
                               'online': cache.get("who_online")}, RequestContext(request, {}))
