# coding=utf-8
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings

from myscore.main.models import *


class API:
    """
    get_news:
    - limit [max. 25]
    - strona
    - data
    - liga [id, nazwa]

    get_matches:
    - status
    - data
    - liga

    get_predictions:
    - username
    - match_id
    - limit
    - strona
    - data [match_date]
    - liga
    - no_scores [bool]

    get_rankings:
    - username
    - month_no
    - week_no
    - limit
    - strona
    - liga

    get_user_rankings:
    - username
    - month_stats [bool]
    - week_stats [bool]
    - start *
    - end *

    POST!

    send_predictions (all req.):
    - username + password (?)
    - match_id
    - home_score
    - away_score

    ...

    """
    pass


def request_parser(request, rep):
    """
    Sprawdza typ zapytania, uwierzytelnienie (jezeli jest potrzebne) oraz inne zabezpieczenia
    """

    if request.method == "GET":
        pass

    elif request.method == "POST":
        pass

    elif request.method == "PUT":
        pass

    elif request.method == "DELETE":
        pass

    host = "127.0.0.1"
    url = ""

    conn = Connection(host)
    rep = conn.request(url, 'GET', {"Accept": "application/json", "X-Blip-api": "0.02"})

    rep = request_parser(rep)

    print str(resp.read())

    return rep


def params_parser(list, check_list=('lang', 'limit')):
    pass


def get_leagues(request):
    if request.GET.has_key('lang'):
        if request.GET['lang'] in ('pl', 'en'):
            lang = reques.GET['lang']
        else:
            lang = 'en'
    else:
        lang = 'en'

    leagues_list = []
    for league in Leagues().get_leagues_list():
        if lang == 'pl':
            leagues_list.append(league.name_pl)
        # league_name = league.name_pl
        else:
            leagues_list.append(league.name_en)
        # league_name = league.name_en

    return leagues_list


def get_news(request):
    if request.GET.has_key('limit'):
        limit = int(request.GET['limit'])
    else:
        limit = 20

    if request.GET.has_key('page'):
        page = int(request.GET['page'])
        if page < 0 or page > 50:
            page = 1
        elif page == 0:
            page = 1
    else:
        page = 1

    if request.GET.has_key('league'):
        league = int(request.GET['league'])
    else:
        league = 0

    if request.GET.has_key('date'):
        date = int(request.GET['date'])
    else:
        date = 0

    if request.GET.has_key('lang'):
        if request.GET['lang'] in ('pl', 'en'):
            lang = reques.GET['lang']
        else:
            lang = 'en'
    else:
        lang = 'en'

    # query
    news = News().get_news(page_no=page, news_date=date, lang=lang)

    return HttpResponse(str())
