# coding=utf-8
from django.http import HttpResponse
from django.conf import settings

from myscore.main.models import *


def index(request):
    # update accounts set activity_points = 0, news_count = 0, videos_count = 0, images_count = 0, analyses_count = 0

    # NEWS - 20
    # VIDEO - 5
    # IMAGE - 3
    # ANALYSIS - 10

    # -----
    # ANALYSIS
    # -----
    users_list = {}
    listing = Comments.objects.filter(is_accepted=1, is_deleted=0, dst='a')
    for news in listing:
        if not users_list.has_key(str(news.user)):
            users_list[str(news.user)] = 0

        users_list[str(news.user)] += 1

        AccountsActivity(user_id=news.user.id, username=str(news.user), dst_id=news.id, action_type='match_analysis',
                         points=10, is_calculated=0, is_confirmed=1, created_at=news.created_at).save()

    # -----
    # NEWS
    # -----
    users_list = {}
    listing = News.objects.filter(is_accepted=1, is_deleted=0, is_temp=0)
    for news in listing:
        if not users_list.has_key(str(news.user)):
            users_list[str(news.user)] = 0

        users_list[str(news.user)] += 1

        AccountsActivity(user_id=news.user.id, username=str(news.user), dst_id=news.id, action_type='news', points=20,
                         is_calculated=0, is_confirmed=1, created_at=news.published_at).save()


    # -----
    # NEWS_VIDEO
    # -----
    users_list = {}
    listing = Videos.objects.filter(is_accepted=1, is_deleted=0, dst='news')
    for news in listing:
        if not users_list.has_key(str(news.user)):
            users_list[str(news.user)] = 0

        users_list[str(news.user)] += 1

        AccountsActivity(user_id=news.user.id, username=str(news.user), dst_id=news.id, action_type='news_video',
                         points=5, is_calculated=0, is_confirmed=1, created_at=news.created_at).save()

    # -----
    # NEWS_IMAGES
    # -----
    users_list = {}
    listing = Images.objects.filter(is_accepted=1, is_deleted=0, dst='news')
    for news in listing:
        if not users_list.has_key(str(news.user)):
            users_list[str(news.user)] = 0

        users_list[str(news.user)] += 1

        AccountsActivity(user_id=news.user.id, username=str(news.user), dst_id=news.id, action_type='news_image',
                         points=3, is_calculated=0, is_confirmed=1, created_at=news.created_at).save()

    # -----
    # MATCH_VIDEO
    # -----
    users_list = {}
    listing = Videos.objects.filter(is_accepted=1, is_deleted=0, dst='match')
    for news in listing:
        if not users_list.has_key(str(news.user)):
            users_list[str(news.user)] = 0

        users_list[str(news.user)] += 1

        AccountsActivity(user_id=news.user.id, username=str(news.user), dst_id=news.id, action_type='match_video',
                         points=5, is_calculated=0, is_confirmed=1, created_at=news.created_at).save()

    # -----
    # MATCH_IMAGES
    # -----
    users_list = {}
    listing = Images.objects.filter(is_accepted=1, is_deleted=0, dst='match')
    for news in listing:
        if not users_list.has_key(str(news.user)):
            users_list[str(news.user)] = 0

        users_list[str(news.user)] += 1

        AccountsActivity(user_id=news.user.id, username=str(news.user), dst_id=news.id, action_type='match_image',
                         points=3, is_calculated=0, is_confirmed=1, created_at=news.created_at).save()

    # -----
    # PICKS
    # -----
    users_list = {}
    listing = Picks.objects.filter(is_calculated=1)
    for news in listing:
        if not users_list.has_key(str(news.user)):
            users_list[str(news.user)] = 0

        users_list[str(news.user)] += 1

        AccountsActivity(user_id=news.user.id, username=str(news.user), dst_id=news.id, action_type='match_points',
                         points=news.points, is_calculated=0, is_confirmed=1, created_at=news.created_at).save()

    return HttpResponse("done!")
