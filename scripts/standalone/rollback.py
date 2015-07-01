#!/usr/bin/python

import os
import getopt

import sys
import datetime

sys.path.append(os.path.dirname(__file__) + "../../../")
# os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_pl'
os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_production_en'

from myscore.main.models import *
from django.db import connection


class Rollback:
    def __init__(self, match_id):
        match = Matches.objects.get(pk=match_id)

        self.match_id = match_id
        self.match_date = match.match_date

    def backup_tables(self):
        sql = "CREATE TABLE _picks SELECT * FROM picks"
        cursor = connection.cursor()
        print "start: %s" % str(datetime.datetime.now())
        print sql
        cursor.execute(sql)
        print "finish: %s" % str(datetime.datetime.now())

        sql = "CREATE TABLE _accounts_table SELECT * FROM accounts_table"
        cursor = connection.cursor()
        print "start: %s" % str(datetime.datetime.now())
        print sql
        cursor.execute(sql)
        print "finish: %s" % str(datetime.datetime.now())

    def rollback_users_points(self):
        sql = "UPDATE picks SET is_calculated = 0, points = 0 WHERE match_id = %s" % self.match_id
        cursor = connection.cursor()
        print "start: %s" % str(datetime.datetime.now())
        print sql
        cursor.execute(sql)
        print "finish: %s" % str(datetime.datetime.now())

    def remove_table_items(self):
        sql = "DELETE FROM accounts_table WHERE date >= '%s'" % self.match_date
        cursor = connection.cursor()
        print "start: %s" % str(datetime.datetime.now())
        print sql
        cursor.execute(sql)
        print "finish: %s" % str(datetime.datetime.now())


if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "clstu")

    try:
        mid = int(args[0])
        if mid <= 0:
            sys.exit()
    except:
        print "wrong ID"
        sys.exit()

    print "rollback %s" % mid
    r = Rollback(mid)
    r.backup_tables()
    r.rollback_users_points()
    r.remove_table_items()
