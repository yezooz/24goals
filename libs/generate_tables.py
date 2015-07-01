#!/usr/bin/python

import urllib
import re
import os

import sys
import datetime
# django settings
sys.path.append(os.path.dirname(__file__) + "../../")
os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_production_en'

from django.db import models
from myscore.main.models import *
from django.core.cache import cache


class GenerateTables:
    """Creates league tables for regular season"""

    def __init__(self, league_id, season_id):
        self.league_id = Leagues.objects.get(pk=league_id).id
        self.season_id = season_id
        self.ms = Matches.objects.filter(league__id=league_id, season__id=season_id, status="f")
        self.lt = LeagueTable()

    def init_data(self, teams, match_id):
        # append
        match_id = int(match_id)

        # fill in
        teams[match_id] = {}
        teams[match_id]["points"] = 0
        teams[match_id]["gp"] = 0
        teams[match_id]["w"] = 0
        teams[match_id]["d"] = 0
        teams[match_id]["l"] = 0
        teams[match_id]["gs"] = 0
        teams[match_id]["ga"] = 0

        return teams

    def gt(self, table_type=1):

        teams = {}
        for m in self.ms:
            if not teams.has_key(int(m.home_team_id)):
                teams = self.init_data(teams, m.home_team_id)

            if not teams.has_key(int(m.away_team_id)):
                teams = self.init_data(teams, m.away_team_id)

            won = 0
            if m.home_score > m.away_score:
                won = 1
            elif m.home_score < m.away_score:
                won = 2

            teams[m.home_team_id]["gp"] += 1
            teams[m.away_team_id]["gp"] += 1
            teams[m.home_team_id]["gs"] += m.home_score
            teams[m.home_team_id]["ga"] += m.away_score
            teams[m.away_team_id]["gs"] += m.away_score
            teams[m.away_team_id]["ga"] += m.home_score

            if won == 1:
                teams[m.home_team_id]["w"] += 1
                teams[m.away_team_id]["l"] += 1
                teams[m.home_team_id]["points"] += 3
            if won == 2:
                teams[m.home_team_id]["l"] += 1
                teams[m.away_team_id]["w"] += 1
                teams[m.away_team_id]["points"] += 3
            if won == 0:
                teams[m.home_team_id]["d"] += 1
                teams[m.away_team_id]["d"] += 1
                teams[m.home_team_id]["points"] += 1
                teams[m.away_team_id]["points"] += 1

        self.save(teams, table_type)
        self.update_positions(table_type)

    def g_home(self, table_type=2):

        teams = {}
        for m in self.ms:
            if not teams.has_key(int(m.home_team_id)):
                teams = self.init_data(teams, m.home_team_id)

            if not teams.has_key(int(m.away_team_id)):
                teams = self.init_data(teams, m.away_team_id)

            won = 0
            if m.home_score > m.away_score:
                won = 1
            elif m.home_score < m.away_score:
                won = 2

            teams[m.home_team_id]["gp"] += 1
            teams[m.home_team_id]["gs"] += m.home_score
            teams[m.home_team_id]["ga"] += m.away_score

            if won == 1:
                teams[m.home_team_id]["w"] += 1
                teams[m.home_team_id]["points"] += 3
            if won == 2:
                teams[m.home_team_id]["l"] += 1
            if won == 0:
                teams[m.home_team_id]["d"] += 1
                teams[m.home_team_id]["points"] += 1

        self.save(teams, table_type)
        self.update_positions(table_type)

    def g_away(self, table_type=3):

        teams = {}
        for m in self.ms:
            if not teams.has_key(int(m.home_team_id)):
                teams = self.init_data(teams, m.home_team_id)

            if not teams.has_key(int(m.away_team_id)):
                teams = self.init_data(teams, m.away_team_id)

            won = 0
            if m.home_score > m.away_score:
                won = 1
            elif m.home_score < m.away_score:
                won = 2

            teams[m.away_team_id]["gp"] += 1
            teams[m.away_team_id]["gs"] += m.away_score
            teams[m.away_team_id]["ga"] += m.home_score

            if won == 1:
                teams[m.away_team_id]["l"] += 1
            if won == 2:
                teams[m.away_team_id]["w"] += 1
                teams[m.away_team_id]["points"] += 3
            if won == 0:
                teams[m.away_team_id]["d"] += 1
                teams[m.away_team_id]["points"] += 1

        self.save(teams, table_type)
        self.update_positions(table_type)

    def save(self, teams, table_type):
        LeagueTable.objects.filter(league__id=self.league_id, season__id=self.season_id, table_type=table_type).delete()
        cache.delete("league_table_" + str(self.league_id))

        for team_id, obj in teams.iteritems():
            tlt = LeagueTable(league_id=self.league_id, season_id=self.season_id, team_id=team_id)
            tlt.table_type = table_type
            tlt.points = obj["points"]
            tlt.gp = obj["gp"]
            tlt.gs = obj["gs"]
            tlt.ga = obj["ga"]
            tlt.w = obj["w"]
            tlt.d = obj["d"]
            tlt.l = obj["l"]
            tlt.save()

        return True

    def update_positions(self, table_type):
        def table_pos(one, two):
            if one.points == two.points:

                if one.gp > two.gp:
                    return 1
                elif one.gp < two.gp:
                    return -1

                one_points_diff = one.ga - one.gs
                two_points_diff = two.ga - two.gs

                if one_points_diff > two_points_diff:
                    return 1
                elif one_points_diff < two_points_diff:
                    return -1
                else:
                    if one.ga > two.ga:
                        return 1
                    else:
                        return -1
            else:
                if one.points > two.points:
                    return -1
                else:
                    return 1

        tlt = list(LeagueTable.objects.filter(league__id=self.league_id, season__id=self.season_id,
                                              table_type=table_type).order_by('-points'))

        tlt.sort(table_pos)
        pos = 1
        for t in tlt:
            t.position = pos
            t.save()
            pos += 1

    def regenerate_all():
        LeagueTable.objects.all().delete()
        leagues = Leagues().get_leagues_list()
        for l in leagues:
            for sid in range(1, 8):
                gt = GenerateTables(l.id, sid)  # league_id, season_id
                gt.gt(1)
                gt.g_home(2)
                gt.g_away(3)


if __name__ == '__main__':

    LeagueTable.objects.filter(season__id=settings.CURRENT_SEASON_ID).delete()
    leagues = Leagues().get_leagues_list()
    for l in leagues:
        gt = GenerateTables(l.id, settings.CURRENT_SEASON_ID)  # league_id, season_id
        gt.gt(1)
        gt.g_home(2)
        gt.g_away(3)
