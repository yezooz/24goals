# coding=utf-8
import logging
import re

from dateutil.relativedelta import *
from django import http
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, HttpResponsePermanentRedirect

import datetime
import time
from time import strptime
from myscore.main.models import *

# from django.utils.translation import ugettext as _
from django.conf import settings
import myscore.libs.helpers as helpers
from myscore.libs.slughifi import slughifi
from django.db import connection


def parseDate(date_str):
    """Returns datetime"""
    return datetime.datetime(*strptime(date_str, "%Y-%m-%d")[0:5])


def getDate(date):
    """Returns string"""
    return strftime("%Y-%m-%d", date.timetuple())


# ---

def regenerate_users_table(request):
    has_points = {}
    has_points_users = Accounts.objects.filter(live_points__gt=0)
    for user in has_points_users:
        has_points[user.user_id] = 0

    def generate(first_day, last_day, table_type, league_id=0):

        d = first_day.date()

        for user in User.objects.filter(is_active=1, date_joined__lte=last_day):
            if not has_points.has_key(user.id):
                continue

            query = "SELECT \
						p.points \
					 FROM \
						picks as p \
					 LEFT JOIN matches as m ON (m.id = p.match_id) \
					 WHERE \
						p.is_calculated = 1 AND \
						p.user_id = %s AND \
						m.status = 'f' AND \
						m.match_date BETWEEN '%s 00:00:00' AND '%s 23:59:59' \
					 " % (user.id, first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"))

            if league_id is not 0:
                query += " AND m.league_id = %s" % league_id

            db = connection.cursor()
            db.execute(query)
            rep = db.fetchall()

            if rep is None:
                continue

            picks = {'minus_five': 0, 'minus_one': 0, 'zero': 0, 'one': 0, 'three': 0, 'four': 0, 'six': 0, 'count': 0,
                     'points': 0}
            for row in rep:
                if row[0] == -5:
                    picks['minus_five'] += 1
                elif row[0] == -1:
                    picks['minus_one'] += 1
                elif row[0] == 0:
                    picks['zero'] += 1
                elif row[0] == 1:
                    picks['one'] += 1
                elif row[0] == 3:
                    picks['three'] += 1
                elif row[0] == 4:
                    picks['four'] += 1
                elif row[0] == 6:
                    picks['six'] += 1

                picks['points'] += int(row[0])
                picks['count'] += 1

            try:
                picks['avg'] = float(picks['points']) / float(picks['count'])
            except ZeroDivisionError:
                picks['avg'] = 0

            # previous positions check!
            if table_type == 'm':
                d = first_day.date()

                try:
                    prev_month = UsersTable.objects.get(user=user, league_id=league_id, table_type=table_type,
                                                        date=first_day + datetime.timedelta(days=-1) + relativedelta(
                                                            day=1))
                    prev_month_pos = prev_month.position
                    prev_month_picks = prev_month.picked
                    prev_month_points = prev_month.points
                    prev_month_avg = prev_month.avg
                except:
                    prev_month_pos = 0
                    prev_month_picks = 0
                    prev_month_points = 0
                    prev_month_avg = 0

            elif table_type == 'w':
                d = first_day.date()

                try:
                    prev_week = UsersTable.objects.get(user=user, league_id=league_id, table_type=table_type,
                                                       date=first_day + datetime.timedelta(days=-7))
                    prev_week_pos = prev_week.position
                    prev_week_picks = prev_week.picked
                    prev_week_points = prev_week.points
                    prev_week_avg = prev_week.avg
                except:
                    prev_week_pos = 0
                    prev_week_picks = 0
                    prev_week_points = 0
                    prev_week_avg = 0

                try:
                    prev_month = UsersTable.objects.get(user=user, league_id=league_id, table_type=table_type,
                                                        date=first_day + datetime.timedelta(days=-28)).position
                except:
                    prev_month = 0

            else:
                d = last_day

                try:
                    prev_week = UsersTable.objects.get(user=user, league_id=league_id, table_type=table_type,
                                                       date=last_day + datetime.timedelta(days=-7))
                    prev_week_pos = prev_week.position
                    prev_week_picks = prev_week.picked
                    prev_week_points = prev_week.points
                    prev_week_avg = prev_week.avg
                except:
                    prev_week_pos = 0
                    prev_week_picks = 0
                    prev_week_points = 0
                    prev_week_avg = 0

                try:
                    prev_month = UsersTable.objects.get(user=user, league_id=league_id, table_type=table_type,
                                                        date=last_day + datetime.timedelta(days=-30))
                    prev_month_pos = prev_month.position
                    prev_month_picks = prev_month.picked
                    prev_month_points = prev_month.points
                    prev_month_avg = prev_month.avg
                except:
                    prev_month_pos = 0
                    prev_month_picks = 0
                    prev_month_points = 0
                    prev_month_avg = 0

            # avoid stupid errors
            try:
                t = prev_month_pos
            except UnboundLocalError:
                prev_month_pos = -1
            try:
                t = prev_month_picks
            except UnboundLocalError:
                prev_month_picks = -1
            try:
                t = prev_month_points
            except UnboundLocalError:
                prev_month_points = -1
            try:
                t = prev_month_avg
            except UnboundLocalError:
                prev_month_avg = -1

            try:
                t = prev_week_pos
            except UnboundLocalError:
                prev_week_pos = -1
            try:
                t = prev_week_picks
            except UnboundLocalError:
                prev_week_picks = -1
            try:
                t = prev_week_points
            except UnboundLocalError:
                prev_week_points = -1
            try:
                t = prev_week_avg
            except UnboundLocalError:
                prev_week_avg = -1

            ut = UsersTable.objects.get_or_create(date=d, table_type=table_type, user=user, league_id=league_id,
                                                  season_id=settings.CURRENT_SEASON_ID,
                                                  defaults={'username': str(user), 'six': picks['six'],
                                                            'four': picks['four'], 'three': picks['three'],
                                                            'one': picks['one'], 'zero': picks['zero'],
                                                            'minus_one': picks['minus_one'],
                                                            'minus_five': picks['minus_five'],
                                                            'points': picks['points'], 'picked': picks['count'],
                                                            'avg': picks['avg'], 'prev_week': prev_week_pos,
                                                            'prev_month': prev_month_pos,
                                                            'prev_week_picks': prev_week_picks,
                                                            'prev_month_picks': prev_month_picks,
                                                            'prev_week_points': prev_week_points,
                                                            'prev_month_points': prev_month_points,
                                                            'prev_week_avg': prev_week_avg,
                                                            'prev_month_avg': prev_month_avg})

            if league_id == 0 and table_type == 'o':
                acc = Accounts.objects.get(user=user)
                acc.points = picks['points']
                acc.save()

        i = 1
        for user in UsersTable.objects.filter(league_id=league_id, table_type=table_type, date=d).order_by('-points',
                                                                                                           '-avg',
                                                                                                           '-six',
                                                                                                           'minus_one',
                                                                                                           '-four',
                                                                                                           '-three',
                                                                                                           '-one'):
            user.position = i
            user.save()
            i += 1

        i = 1
        for user in UsersTable.objects.filter(league_id=league_id, table_type=table_type, date=d).order_by('-avg',
                                                                                                           '-points',
                                                                                                           '-six',
                                                                                                           'minus_one',
                                                                                                           '-four',
                                                                                                           '-three',
                                                                                                           '-one'):
            user.avg_position = i
            user.save()
            i += 1

    def generate_month(days=(), league_id=0):

        if len(days) != 2:
            check = UsersTable.objects.filter(table_type='m', league_id=league_id,
                                              season_id=settings.CURRENT_SEASON_ID).order_by('-date')[:1]
            if len(check) == 1:
                first_day = parseDate(str(check[0].date))
            else:
                first_day = parseDate('2007-08-01')
        else:
            first_day = parseDate("%s-%s-01" % (days[0], days[1]))

        while True:
            last_day = first_day + relativedelta(day=31)

            # check if further entries are not already there
            check = UsersTable.objects.filter(table_type='m', league_id=league_id, season_id=settings.CURRENT_SEASON_ID,
                                              date=first_day.date())

            if len(check) > 0 and last_day < datetime.datetime.now():
                first_day = last_day + datetime.timedelta(days=1)
                continue

            # break
            if first_day > datetime.datetime.today():
                break

            if len(check) > 0 and first_day.date().month == datetime.date.today().month:
                check.delete()

            generate(first_day, last_day, 'm', league_id)

            first_day = last_day + datetime.timedelta(days=1)

    def generate_week(days=(), league_id=0):

        if len(days) != 3:
            check = UsersTable.objects.filter(table_type='w', league_id=league_id,
                                              season_id=settings.CURRENT_SEASON_ID).order_by('-date')[:1]
            if len(check) == 1:
                first_day = parseDate(str(check[0].date))
            else:
                first_day = parseDate('2007-07-30')
        else:
            first_day = parseDate("%s-%s-%s" % (days[0], days[1], days[2]))

        while True:
            last_day = first_day + datetime.timedelta(days=6)

            # check if further entries are not already there
            check = UsersTable.objects.filter(table_type='w', league_id=league_id, season_id=settings.CURRENT_SEASON_ID,
                                              date=first_day.date())

            if len(check) > 0 and last_day < datetime.datetime.now():
                first_day = last_day + datetime.timedelta(days=1)
                continue

            if last_day > datetime.datetime.now():
                break

            if len(check) > 0 and datetime.date.today() > first_day.date() and datetime.date.today() <= last_day.date():
                check.delete()

            generate(first_day, last_day, 'w', league_id)

            first_day = last_day + datetime.timedelta(days=1)

    def generate_overall(days=(), league_id=0):

        first_day = parseDate('2007-07-30')
        last_day = parseDate('2007-07-30')

        if len(days) != 3:
            check = UsersTable.objects.filter(table_type='o', league_id=league_id,
                                              season_id=settings.CURRENT_SEASON_ID).order_by('-date')[:1]
            if len(check) == 1:
                last_day = check[0].date

        while True:

            try:
                if last_day.date() >= datetime.date.today():
                    break
            except AttributeError:
                if last_day >= datetime.date.today():
                    break
            except:
                break

            generate(first_day, last_day, 'o', league_id)
            last_day = last_day + datetime.timedelta(days=1)

    # by month
    year = 2007
    month = 7
    day = 30

    generate_month()
    for league in Leagues().get_leagues_list():
        generate_month(league_id=league.id)

    # by week
    generate_week()
    for league in Leagues().get_leagues_list():
        generate_week(league_id=league.id)

    # overall
    generate_overall()
    for league in Leagues().get_leagues_list():
        generate_overall(league_id=league.id)

    return HttpResponse("done!")
