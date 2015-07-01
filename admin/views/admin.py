# coding=utf-8
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required

import datetime
from myscore.main.models import *


@staff_member_required
def index(request):
    comms_to_mod = Comments.objects.filter(created_at=datetime.date.today()).count()
    news_to_mod = News.objects.filter(is_accepted=0, is_deleted=0).count()
    vids_to_mod = Videos.objects.filter(is_accepted=0, is_deleted=0).count()
    imgs_to_mod = Images.objects.filter(is_accepted=0, is_deleted=0).count()

    user_count = Accounts.objects.all().count()
    today_users = Accounts.objects.filter(created_at__startswith=datetime.date.today()).count()

    return render_to_response("admin/index.html", {'comms_to_mod': comms_to_mod, 'news_to_mod': int(news_to_mod),
                                                   'vids_to_mod': int(vids_to_mod), 'imgs_to_mod': int(imgs_to_mod),
                                                   'user_count': user_count, 'today_users': int(today_users)},
                              RequestContext(request, {}))
