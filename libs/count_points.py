#!/usr/bin/python

import urllib
import re
import os

import sys
import datetime
# django settings
sys.path.append(os.path.dirname(__file__) + "../../")
# os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_pl'
os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_production_en'

from django.db import models
from myscore.main.models import *
from django.core.cache import cache


class CountPoints:
    def calculate_picks(self):
        from myscore.main.models import Picks, Accounts

        picks_to_count = Picks.objects.filter(match__status='f', is_calculated=False)
        print len(picks_to_count)

        for pick in picks_to_count:
            home_score = pick.match.home_score
            away_score = pick.match.away_score

            pick.points = self.count_points(home_score, away_score, pick.home_score, pick.away_score)
            pick.is_calculated = True
            pick.save()

            user = Accounts.objects.get(user=pick.user)
            user.live_points = int(user.live_points) + int(pick.points)
            user.save()

            AccountsActivity(user_id=user.user.id, username=str(user.username), dst_id=pick.id,
                             action_type='match_points', points=pick.points, is_calculated=0, is_confirmed=1,
                             created_at=datetime.datetime.now()).save()

    def recalculate_picks_by_match(self, match_id):
        from myscore.main.models import Picks

        picks_to_recount = Picks.objects.filter(match__id=match_id)
        match = Matches.objects.get(pk=int(match_id))

        for pick in picks_to_recount:
            home_score = match.home_score
            away_score = match.away_score

            pick.is_calculated = False
            removed_points = pick.points
            pick.points = 0
            pick.save()

            user = Accounts.objects.get(pk=int(pick.user.id))
            user.points -= removed_points
            user.save()

        # recount
        self.calculate_picks()

    # count points
    # 1 - za poprawny wynik dowolnej strony
    # 3 - poprawny wygrany
    # 4 - za poprawna druzyne wygrana i liczbe jej bramek
    # 6 - poprawny wynik
    def count_points(self, ha, aa, hb, ab):
        ha = int(ha)
        aa = int(aa)
        hb = int(hb)
        ab = int(ab)

        if ha < aa:
            won = -1
        elif ha == aa:
            won = 0
        elif ha > aa:
            won = 1

        if hb < ab:
            pred_won = -1
        elif hb == ab:
            pred_won = 0
        elif hb > ab:
            pred_won = 1


        # poprawny wynik
        if (ha == hb and aa == ab):
            return 6
        # poprawa wygrana druzyna i jej wynik
        elif (won == pred_won):
            if ((won == 1 and ha == hb) or (won == -1 and aa == ab)):
                return 4
            else:
                return 3
        elif (ha == hb or aa == ab):
            return 1
        else:
            return -1


if __name__ == '__main__':
    cp = CountPoints()
    cp.calculate_picks()

## test suite
# print str(6) + " = " + str(cp.count_points(0,0,0,0))
# print str(4) + " = " + str(cp.count_points(2,1,2,0))
# print str(3) + " = " + str(cp.count_points(2,1,3,1))
# print str(1) + " = " + str(cp.count_points(4,1,0,1))
# print str(0) + " = " + str(cp.count_points(4,1,1,2))
#
# cp.recalculate_picks_by_match(13070)
