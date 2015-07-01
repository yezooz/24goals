#!/usr/bin/python

import os

from dateutil.relativedelta import *

import datetime
import sys
from time import strptime

# django settings
sys.path.append(os.path.dirname(__file__) + "../../../")
# os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_pl'
os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_production_pl'

from myscore.main.models import *


class TrophiesAdd:
    def __init__(self):
        self.start_year = 2007
        self.start_month = 9

    def calculate_points(self):
        day = datetime.datetime(*strptime("2007-09-01", "%Y-%m-%d")[0:5])

        while True:

            if day.date().month >= datetime.date.today().month and day.date().year >= datetime.date.today().year:
                break

            check = AccountsTrophies.objects.filter(date=day.date())

            if len(check) > 0:
                last_day = day + relativedelta(day=31)
                day = last_day + datetime.timedelta(days=1)
                continue

            # 'day' is always first day of month
            for trophy in Trophies.objects.all().order_by('priority', 'position'):
                at = UsersTable.objects.filter(table_type='m', date=day.date(), season_id=settings.CURRENT_SEASON_ID,
                                               league_id=trophy.league_id).order_by('position')[
                     int(trophy.position) - 1:int(trophy.position)]

                if len(at) == 1:
                    at = at[0]
                    AccountsActivity(user_id=at.user.id, username=str(at.username), dst_id=0, action_type='trophies',
                                     points=trophy.points, is_calculated=0, is_confirmed=1,
                                     created_at=day.date()).save()
                    AccountsTrophies(user_id=at.user.id, username=str(at.username), trophy_id=trophy.id,
                                     league_id=trophy.league_id, season_id=settings.CURRENT_SEASON_ID,
                                     priority=trophy.priority, date=day.date()).save()

            last_day = day + relativedelta(day=31)
            day = last_day + datetime.timedelta(days=1)


if __name__ == '__main__':
    t = TrophiesAdd()
    t.calculate_points()
