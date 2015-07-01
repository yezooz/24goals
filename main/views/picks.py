# coding=utf-8
from django import newforms as forms
from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.core.cache import cache

from myscore.main.models import *
import myscore.libs.helpers as helpers
from myscore.main.modules import menu
import myscore.main.helpers.league_tables as league_tables


# dziala tylko dla obecnego sezonu
def index(request, league_name="", when_type="", when=""):
    def parse_input():
        # tutaj pelna walidacja
        weeks = helpers.get_weeks()
        try:
            if int(when) <= len(weeks) - 1:
                return weeks[int(when)][0].strftime("%Y-%m-%d")
            else:
                return -1
        except:
            return -1

    # CACHING HERE FRO 2-4 HOURS
    # key = "typer_table_league_%s_type_%s_when_%s_limit_0_lang_%s" % (league_id, when_type, when, settings.LANGUAGE_CODE)
    # c = cache.get(key)
    # if c:
    # 	return c


    if league_name != "":
        league_id = helpers.reveal_league_name(league_name)
    else:
        league_id = 0

    url = request.META['PATH_INFO']
    try:
        if request.POST['select_month'] != "":
            if url.find(request.POST['select_month']) < 0:
                if league_id != 0:
                    return HttpResponseRedirect(
                        "/" + _('Typer URL') + "/" + league_name + "/" + _('miesiac') + "/" + request.POST[
                            'select_month'] + "/")
                else:
                    return HttpResponseRedirect(
                        "/" + _('Typer URL') + "/" + _('miesiac') + "/" + request.POST['select_month'] + "/")
    except:
        pass

    try:
        if int(request.POST['select_week']) >= 0:
            if url.find(request.POST['select_week']) < 0:
                if league_id != 0:
                    return HttpResponseRedirect("/" + _('Typer URL') + "/" + league_name + "/ + _('tydzien') + /" + str(
                        request.POST['select_week']) + "/")
                else:
                    return HttpResponseRedirect(
                        "/" + _('Typer URL') + "/" + _('tydzien') + "/" + str(request.POST['select_week']) + "/")
    except:
        pass

    if when_type == "miesiac" or when_type == "month":
        year, month = helpers.reveal_month_name(when)
        month_name = when
    else:
        month = 0
        month_name = None

    if when_type == "tydzien" or when_type == "week":
        week = parse_input()
        print week
        try:
            int_when = int(when) + 1
        except:
            int_when = None
    else:
        int_when = None
        week = -1

    if month != 0:
        users = UsersTable.objects.select_related().filter(table_type='m', league_id=league_id,
                                                           date=datetime.date(year, month, 1)).order_by('position')
    elif week != -1:
        users = UsersTable.objects.select_related().filter(table_type='w', league_id=league_id, date=week).order_by(
            'position')
    else:
        users = UsersTable.objects.select_related().filter(table_type='o', league_id=league_id,
                                                           date=datetime.date.today() - datetime.timedelta(1)).order_by(
            'position')

    i = 1
    lines = []
    weeks = helpers.get_weeks()
    for days in weeks:
        if days[0] > datetime.datetime.now():
            break
        lines.append(
            str(i) + " " + _('tydz.') + " | " + days[0].strftime("%d-%m-%y") + " - " + days[1].strftime("%d-%m-%y"))
        i += 1

    return render_to_response('picks/index.html', {
        'users': users,
        'league_name': league_name,
        'month_name': month_name,
        'weeks': lines,
        'selected_week': int_when,
        'menu': menu.render(request, 'prediction', 'index', {'league_name': league_name}, False),
    }, context_instance=RequestContext(request))
