# coding=utf-8
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

import datetime
from time import strptime


def render(request, module, method, params={}, is_folded=False):
    menu_order = ('index', 'news', 'matches', 'teams', 'typer', 'users', 'user')

    if params.has_key('today'):
        if params['today'] != None:
            today = strptime(str(params['today']), "%Y-%m-%d")
            today = datetime.datetime(today.tm_year, today.tm_mon, today.tm_mday, 0, 0, 0)
            dates = get_dates_range(params['today'])
        else:
            today = datetime.date.today()
            dates = get_dates_range()
    else:
        today = datetime.date.today()
        dates = get_dates_range()

    if module == 'news':
        context = {}

        date = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        days_from_today = datetime.datetime.now() - date
        days_from_today = days_from_today.days

        context['today_minus_2'] = date + datetime.timedelta(days=-2)
        context['yesterday'] = date + datetime.timedelta(days=-1)
        context['today'] = date
        if days_from_today >= 1:
            context['tomorrow'] = date + datetime.timedelta(days=1)
        if days_from_today >= 2:
            context['today_plus_2'] = date + datetime.timedelta(days=2)
        if days_from_today >= 3:
            context['today_plus_3'] = date + datetime.timedelta(days=3)
        if days_from_today == 4:
            context['today_plus_4'] = date + datetime.timedelta(days=4)

        if int(context['today'].year) <= 2000:
            del context['yesterday']
            del context['today_minus_2']

        dates = context

    return render_to_string('modules/menu.html',
                            {'request': request, 'module': module, 'method': method, 'is_folded': is_folded,
                             'dates': dates, 'params': params})


def get_dates_range(today=datetime.date.today()):
    context = {}
    y, m, d = str(today).split("-")
    date = datetime.datetime(int(y), int(m), int(d), 0, 0, 0)

    context['today_minus_2'] = date + datetime.timedelta(days=-2)
    context['yesterday'] = date + datetime.timedelta(days=-1)
    context['today'] = date
    context['tomorrow'] = date + datetime.timedelta(days=1)
    context['today_plus_2'] = date + datetime.timedelta(days=2)
    context['today_plus_3'] = date + datetime.timedelta(days=3)
    context['today_plus_4'] = date + datetime.timedelta(days=4)

    if int(context['today_plus_4'].year) > (int(datetime.date.today().year) + 1):
        del context['tomorrow']
        del context['today_plus_2']
        del context['today_plus_3']
        del context['today_plus_4']
    if int(context['today'].year) <= 2000:
        del context['yesterday']
        del context['today_minus_2']
    else:
        print "less"

    return context
