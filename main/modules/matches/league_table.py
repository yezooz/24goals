# coding=utf-8
from myscore.main.models import LeagueTable
# from django.db.models import Q
from django.template.loader import render_to_string
from django.conf import settings
# from myscore.libs.cache import TemplatesCache as tcache
from django.core.cache import cache
# import myscore.libs.helpers as helpers
# import myscore.main.helpers.league_tables as league_tables

def render(league_id, team_id=0, team_id_2=0):
    # caching
    key = "league_table_lid_%s_tid_%s_tid2_%s" % (league_id, team_id, team_id_2)
    c = cache.get(key)
    if c: return c

    table_1 = LeagueTable.objects.filter(league__id=league_id, season__id=settings.CURRENT_SEASON_ID,
                                         table_type=1).select_related().order_by('position')
    table_2 = LeagueTable.objects.filter(league__id=league_id, season__id=settings.CURRENT_SEASON_ID,
                                         table_type=2).select_related().order_by('position')
    table_3 = LeagueTable.objects.filter(league__id=league_id, season__id=settings.CURRENT_SEASON_ID,
                                         table_type=3).select_related().order_by('position')

    ret = render_to_string('modules/matches/league_table.html',
                           {'table_1': table_1, 'table_2': table_2, 'table_3': table_3, 'team_id': team_id,
                            'team_id_2': team_id_2})
    cache.set(key, ret)
    return ret
