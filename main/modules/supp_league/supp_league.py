# coding=utf-8
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache

from myscore.main.models import FansTable


def render(team_id=0, limit=10):
    try:
        limit = int(limit)
    except:
        limit = 10

    # caching
    key = "supporters_table_tid_%s_lang_%s_limit_%s" % (team_id, settings.LANGUAGE_CODE, limit)
    c = cache.get(key)
    if c: return c

    nteams = []
    has_team = False
    for t in FansTable().get_current_by_points(limit=limit):
        if team_id != 0 and t.team.id == team_id: has_team = True
        if team_id != 0 and len(nteams) == 9 and has_team == False:    break

        nteams.append((t.position, t.team, t.points))

    if team_id != 0 and len(nteams) == 9:
        t = FansTable().get_current_by_points(team_id=team_id)
        nteams.append((t.position, t.team, t.points))

    ret = render_to_string('modules/supp_league/supp_league.html', {'teams': nteams})
    cache.set(key, ret)
    return ret
