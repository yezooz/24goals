#!/usr/bin/python

import os

import sys
# django settings
sys.path.append(os.path.dirname(__file__) + "../../../")
# os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_pl'
os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_production_pl'

from myscore.main.models import *


class ActivityPoints:
    def calculate_points(self):

        for activ in AccountsActivity.objects.filter(is_calculated=0, is_confirmed=1):

            acc = Accounts.objects.get(username=activ.username)

            if activ.action_type == 'news':
                acc.news_count += 1
            elif activ.action_type == 'news_video' or activ.action_type == 'match_video':
                acc.videos_count += 1
            elif activ.action_type == 'news_image' or activ.action_type == 'match_image':
                acc.images_count += 1
            elif activ.action_type == 'match_analysis':
                acc.analyses_count += 1

            acc.activity_points += activ.points
            acc.save()

            activ.is_calculated = 1
            activ.save()

        # delete user's data cache


if __name__ == '__main__':
    ap = ActivityPoints()
    ap.calculate_points()
