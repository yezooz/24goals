# coding=utf-8
import datetime
from myscore.main.models import *
import myscore.libs.helpers as helpers


class UsersTables:
    def get_overall(date=datetime.date.today(), league_id=0):
        return 0

    def get_for_month(dt=datetime.datetime.now(), league_id=0):
        first_of_month = datetime.date(int(dt.year), int(dt.month), 1)
        lom = helpers.mkLastOfMonth(dt)
        last_of_month = datetime.date(int(lom.year), int(lom.month), int(lom.day))

        return 0

    def get_for_week(monday, league_id=0):
        # datetime.date.today().weekday() == 1
        return 0
