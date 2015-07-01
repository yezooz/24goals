import urllib
import re
import os

import sys
import BeautifulSoup
import datetime
import time
# django settings
sys.path.append(os.path.dirname(__file__) + "../../")
os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_production_pl'
# os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings'

from django.db import models
from myscore.main.models import *
# from django.shortcuts import render_to_response
# from django.http import HttpResponseRedirect, HttpResponse


class Save:
    def __init__(self, espn_match_id):
        self.match = Matches.objects.get(espn_match_id=espn_match_id)

    def getPlayerByEspn(self, espn_id, espn_name):
        """get player_id or create one"""
        if espn_id is None:
            espn_id = 0

        try:
            player, created = Players.objects.get_or_create(espn_id=espn_id, defaults={'espn_name': espn_name})
        except:
            player = Players.objects.filter(espn_id=espn_id)[0]

        if espn_id == player.espn_id and len(str(espn_name)) > len(str(player.espn_name)):
            player.espn_name = espn_name
            player.save()

        return player

    def save_match_stats(self, stats):
        MatchStats.objects.filter(match__id=self.match.id).delete()

        m1 = MatchStats(match=self.match, side='h')
        m2 = MatchStats(match=self.match, side='a')

        # {'possession': [u'54', u'46'], 'fouls': [u'6', u'13'], 'corners': [u'12', u'4'], 'saves': [u'6', u'14'], 'yellow': [u'2', u'1'], 'offsides': [u'1', u'1'], 'shots': [u'23', u'15'], 'on goal': [u'14', u'7'], 'red': [u'0', u'0']}

        m1.shots = stats["shots"][0]
        m2.shots = stats["shots"][1]

        m1.shots_on_goal = stats["on goal"][0]
        m2.shots_on_goal = stats["on goal"][1]

        m1.possession = stats["possession"][0]
        m2.possession = stats["possession"][1]

        m1.fouls = stats["fouls"][0]
        m2.fouls = stats["fouls"][1]

        m1.corners = stats["corners"][0]
        m2.corners = stats["corners"][1]

        m1.saves = stats["saves"][0]
        m2.saves = stats["saves"][1]

        m1.offsides = stats["offsides"][0]
        m2.offsides = stats["offsides"][1]

        m1.yellow_cards = stats["yellow"][0]
        m2.yellow_cards = stats["yellow"][1]

        m1.red_cards = stats["red"][0]
        m2.red_cards = stats["red"][1]

        m1.save()
        m2.save()

    def save_match_squad(self, squad, side):
        MatchSquad.objects.filter(match__id=self.match.id, side=side).delete()
        MatchSubs.objects.filter(match__id=self.match.id, side=side).delete()

        if side == 'h':
            yside = 'left'
        else:
            yside = 'right'
        MatchDetails.objects.filter(match__id=self.match.id, side=yside, action='y').delete()

        # {{'squad': [{'73647': 'Bartosz Bialkowski'}, {'7860': 'Chris Baird'}, {'77653': 'Gareth Bale'}, {'83357': 'Danny Guthrie'}, {'7862': 'Claus Lundekvam'}, {'36196': 'Pedro Pele'}, {'67796': 'Nathan Dyer'}, {'42766': 'Andrew Surman'}, {'8107': 'Jermaine Wright'}, {'25236': 'Marek Saganowski'}], 'substitutes': [{'22506': 'Kevin Miller'}, {'8108': 'Chris Makin'}, {'37335': 'Jhon Viafara'}, {'32242': 'Leon Best'}, {'35385': 'Grzegorz Rasiak'}], 'substitutions': [{'out_player_id': '7860', 'in_player_id': '37335', 'minute': '46'}, {'out_player_id': '25236', 'in_player_id': '35385', 'minute': '60'}, {'out_player_id': '67796', 'in_player_id': '32242', 'minute': '73'}]}

        for s in squad["squad"]:
            m = MatchSquad(match=self.match, side=side)
            m.player = self.getPlayerByEspn(s.keys()[0], s.values()[0])
            m.started_as_sub = False
            m.save()

        for s in squad["substitutes"]:
            m = MatchSquad(match=self.match, side=side)
            m.player = self.getPlayerByEspn(s.keys()[0], s.values()[0])
            m.started_as_sub = True
            m.save()

        for s in squad["substitutions"]:
            m = MatchSubs(match=self.match, side=side)
            m.in_player = self.getPlayerByEspn(s["in_player_id"], "")
            m.out_player = self.getPlayerByEspn(s["out_player_id"], "")
            m.minute = s["minute"]
            m.save()

        for s in squad["yellows"]:
            d = MatchDetails(match=self.match, side=side)
            try:
                p = self.getPlayerByEspn(s["player_id"], s["player_name"])
                d.player_id = p.id
                d.espn_player_name = str(s["player_name"])
                d.espn_player_id = int(s["player_id"])
                if s["player_id"] is None:
                    d.espn_player_id = 0
                if p.last_name != "":
                    d.player_name = p.last_name
                    if p.first_name != "":
                        d.player_name = p.first_name + " " + p.last_name
                else:
                    d.player_name = d.espn_player_name
            except KeyError:
                d.player_id = 0
                d.espn_player_id = 0
                d.espn_player_name = ""

            d.home_score = 0
            d.away_score = 0
            d.minute = s["minute"]
            d.side = yside
            d.action = 'y'
            d.save()

    def update_time(self, match_time):
        self.match.match_time = match_time
        self.match.save()


# ===


class ESPNMatchDetailsDownload:
    def latin1_to_ascii(self, unicrap):
        """This takes a UNICODE string and replaces Latin-1 characters with
            something equivalent in 7-bit ASCII. It returns a plain ASCII string.
            This function makes a best effort to convert Latin-1 characters into
            ASCII equivalents. It does not just strip out the Latin-1 characters.
            All characters in the standard 7-bit ASCII range are preserved.
            In the 8th bit range all the Latin-1 accented letters are converted
            to unaccented equivalents. Most symbol characters are converted to
            something meaningful. Anything not converted is deleted.
        """
        xlate = {0xc0: 'A', 0xc1: 'A', 0xc2: 'A', 0xc3: 'A', 0xc4: 'A', 0xc5: 'A',
                 0xc6: 'Ae', 0xc7: 'C',
                 0xc8: 'E', 0xc9: 'E', 0xca: 'E', 0xcb: 'E',
                 0xcc: 'I', 0xcd: 'I', 0xce: 'I', 0xcf: 'I',
                 0xd0: 'Th', 0xd1: 'N',
                 0xd2: 'O', 0xd3: 'O', 0xd4: 'O', 0xd5: 'O', 0xd6: 'O', 0xd8: 'O',
                 0xd9: 'U', 0xda: 'U', 0xdb: 'U', 0xdc: 'U',
                 0xdd: 'Y', 0xde: 'th', 0xdf: 'ss',
                 0xe0: 'a', 0xe1: 'a', 0xe2: 'a', 0xe3: 'a', 0xe4: 'a', 0xe5: 'a',
                 0xe6: 'ae', 0xe7: 'c',
                 0xe8: 'e', 0xe9: 'e', 0xea: 'e', 0xeb: 'e',
                 0xec: 'i', 0xed: 'i', 0xee: 'i', 0xef: 'i',
                 0xf0: 'th', 0xf1: 'n',
                 0xf2: 'o', 0xf3: 'o', 0xf4: 'o', 0xf5: 'o', 0xf6: 'o', 0xf8: 'o',
                 0xf9: 'u', 0xfa: 'u', 0xfb: 'u', 0xfc: 'u',
                 0xfd: 'y', 0xfe: 'th', 0xff: 'y',
                 0xa1: '!', 0xa2: '{cent}', 0xa3: '{pound}', 0xa4: '{currency}',
                 0xa5: '{yen}', 0xa6: '|', 0xa7: '{section}', 0xa8: '{umlaut}',
                 0xa9: '{C}', 0xaa: '{^a}', 0xab: '<<', 0xac: '{not}',
                 0xad: '-', 0xae: '{R}', 0xaf: '_', 0xb0: '{degrees}',
                 0xb1: '{+/-}', 0xb2: '{^2}', 0xb3: '{^3}', 0xb4: "'",
                 0xb5: '{micro}', 0xb6: '{paragraph}', 0xb7: '*', 0xb8: '{cedilla}',
                 0xb9: '{^1}', 0xba: '{^o}', 0xbb: '>>',
                 0xbc: '{1/4}', 0xbd: '{1/2}', 0xbe: '{3/4}', 0xbf: '?',
                 0xd7: '*', 0xf7: '/'
                 }

        r = ''
        for i in unicrap:
            if xlate.has_key(ord(i)):
                r += xlate[ord(i)]
            elif ord(i) >= 0x80:
                pass
            else:
                r += str(i)
        return r

    def get_page(self, url):
        """Fetches an arbitrary page from the web"""

        try:
            location = urllib.urlopen(url)
        except IOError, (errno, strerror):
            return False
        content = location.read()

        # Clear out all troublesome whitespace
        content = content.replace("\n", "")
        content = content.replace("\r", "")
        content = content.replace("\t", "")
        content = content.replace("> ", ">")
        content = content.replace("  ", " ")
        content = self.latin1_to_ascii(content)

        location.close()
        return content

    def get_file(self, path):
        """Returns file's content"""
        f = open(path)
        lines = ""
        for line in f.readlines():
            lines = lines + line

        return lines

    def generate_tree(self, page):
        """Converts a string of HTML into a document tree"""
        return BeautifulSoup.BeautifulSoup(page)


class ESPNMatchDetailsAnalyse:
    def __init__(self):
        pass

    def parse_info(self, rows):

        time_str = str(rows.findAll('td')[1])
        time = re.search(".*([\d]{2}):([\d]{2}) UK", time_str).groups()
        time = datetime.time(int(time[0]), int(time[1]))

        return time

    def parse_stats(self, rows):
        stats = {'shots': [0, 0], 'on goal': [0, 0], 'fouls': [0, 0], 'corners': [0, 0], 'offsides': [0, 0],
                 'possession': [0, 0], 'yellow': [0, 0], 'red': [0, 0], 'saves': [0, 0]}

        for row in rows.findAll('tr'):
            tds = row.findAll('td')

            try:
                title = tds[0].string

                if title == "Shots (on Goal)":
                    s1 = re.search("(?P<shots>[\d]{1,3})(\((?P<on_goal>[\d]{1,3})\))", tds[1].string)
                    s2 = re.search("(?P<shots>[\d]{1,3})(\((?P<on_goal>[\d]{1,3})\))", tds[2].string)

                    stats["shots"] = [s1.group('shots'), s2.group('shots')]
                    stats["on goal"] = [s1.group('on_goal'), s2.group('on_goal')]

                elif title == "Fouls":
                    stats["fouls"] = [tds[1].string, tds[2].string]

                elif title == "Corner Kicks":
                    stats["corners"] = [tds[1].string, tds[2].string]

                elif title == "Offsides":
                    stats["offsides"] = [tds[1].string, tds[2].string]

                elif title == "Time of Possession":
                    p1 = re.search("(?P<possession>[\d]{2,3})%", tds[1].string)
                    p2 = re.search("(?P<possession>[\d]{2,3})%", tds[2].string)

                    stats["possession"] = [p1.group('possession'), p2.group('possession')]

                elif title == "Yellow Cards":
                    stats["yellow"] = [tds[1].string, tds[2].string]

                elif title == "Red Cards":
                    stats["red"] = [tds[1].string, tds[2].string]

                elif title == "Saves":
                    stats["saves"] = [tds[1].string, tds[2].string]

            except:
                pass

        return stats

    def parse_squad(self, rows):

        last_sect = ""

        home_dets = {'squad': [], 'substitutes': [], 'substitutions': [], 'yellows': []}
        away_dets = {'squad': [], 'substitutes': [], 'substitutions': [], 'yellows': []}

        try:
            for row in rows.findAll('tr'):
                # check out both TD's
                if row.td.string != "None":
                    if row.td.string == "Teams":
                        last_sect = "squad"
                    elif row.td.string == "Substitutes":
                        last_sect = "substitutes"
                    elif row.td.string == "Substitutions":
                        last_sect = "substitutions"
                    elif row.td.string == "Yellow Cards":
                        last_sect = "yellow cards"
                    elif row.td.string == "Red Cards":
                        last_sect = "red cards"

                left = str(row.find(name='td', attrs={'align': 'left'}))
                right = str(row.find(name='td', attrs={'align': 'right'}))

                # SQUAD
                if last_sect == "squad":
                    l = re.search(
                        "<td align=\"(left|right){1}\">.*<a.*href=\"/players.*\?id=(?P<player_id>[\d]{1,8}){1}\&.*>(?P<player_name>[\w\'\`\- ]+)(</a>).*</td>",
                        left, re.U)

                    r = re.search(
                        "<td align=\"(left|right){1}\">.*(<a.*href=\"/players.*\?id=(?P<player_id>[\d]{1,8}){1}\&.*>)?(?P<player_name>[\w\'\`\- ]+)(</a>)?.*</td>",
                        right, re.U)

                    try:
                        home_dets['squad'].append({l.group('player_id'): l.group('player_name')})
                        away_dets['squad'].append({r.group('player_id'): r.group('player_name')})
                    except:
                        pass

                # SUBSITTUTES
                elif last_sect == "substitutes":
                    l = re.search(
                        "<td align=\"(left|right){1}\">.*<a.*href=\"/players.*\?id=(?P<player_id>[\d]{1,8}){1}\&.*>(?P<player_name>[\w\'\`\- ]+)(</a>).*</td>",
                        left, re.U)

                    r = re.search(
                        "<td align=\"(left|right){1}\">.*<a.*href=\"/players.*\?id=(?P<player_id>[\d]{1,8}){1}\&.*>(?P<player_name>[\w\'\`\- ]+)(</a>).*</td>",
                        right, re.U)

                    try:
                        home_dets['substitutes'].append({l.group('player_id'): l.group('player_name')})
                        away_dets['substitutes'].append({r.group('player_id'): r.group('player_name')})
                    except:
                        pass

                # SUBSTITUTIONS
                elif last_sect == "substitutions":
                    l = re.search(
                        "<td align=\"(left|right){1}\"><a href=\"/players/profile\?id=(?P<in_player_id>[\d]{1,8}){1}\&.*>.*</a>for <a href=\"/players/profile\?id=(?P<out_player_id>[\d]{1,8}){1}\&.*>.*</a>(\((?P<minute>[\d]+)\)).*</td>",
                        left, re.U)

                    r = re.search(
                        "<td align=\"(left|right){1}\"><a href=\"/players/profile\?id=(?P<in_player_id>[\d]{1,8}){1}\&.*>.*</a>for <a href=\"/players/profile\?id=(?P<out_player_id>[\d]{1,8}){1}\&.*>.*</a>(\((?P<minute>[\d]+)\)).*</td>",
                        right, re.U)

                    try:
                        home_dets['substitutions'].append(
                            {'minute': l.group('minute'), 'in_player_id': l.group('in_player_id'),
                             'out_player_id': l.group('out_player_id')})
                    except:
                        pass

                    try:
                        away_dets['substitutions'].append(
                            {'minute': r.group('minute'), 'in_player_id': r.group('in_player_id'),
                             'out_player_id': r.group('out_player_id')})
                    except:
                        pass

                # YELLOW CARDS
                elif last_sect == "yellow cards":
                    l = re.search(
                        "<td align=\"(left|right){1}\">.*<a.*href=\"/players.*\?id=(?P<player_id>[\d]{1,8}){1}\&.*>(?P<player_name>[\w\'\`\- ]+)(</a>)(\((?P<minute>[\d]+)\)).*</td>",
                        left, re.U)

                    r = re.search(
                        "<td align=\"(left|right){1}\">.*<a.*href=\"/players.*\?id=(?P<player_id>[\d]{1,8}){1}\&.*>(?P<player_name>[\w\'\`\- ]+)(</a>)(\((?P<minute>[\d]+)\)).*</td>",
                        right, re.U)

                    try:
                        home_dets['yellows'].append({'minute': l.group('minute'), 'player_id': l.group('player_id'),
                                                     'player_name': l.group('player_name')})
                    except:
                        pass

                    try:
                        away_dets['yellows'].append({'minute': r.group('minute'), 'player_id': r.group('player_id'),
                                                     'player_name': r.group('player_name')})
                    except:
                        pass

            return home_dets, away_dets

        except AttributeError:
            print "error"


if __name__ == '__main__':

    matches = Matches.objects.filter(match_date=datetime.date.today(), status__in=['d', 'f'])

    for m in matches:
        if m.espn_match_id:
            try:

                path = "http://soccernet-akamai.espn.go.com/match?id=%s&cc=5739" % (m.espn_match_id)
                print path

                # go!
                get = ESPNMatchDetailsDownload()
                parse = ESPNMatchDetailsAnalyse()
                save = Save(m.espn_match_id)

                f = get.get_page(path)
                page = get.generate_tree(f)

                tables = page.findAll(name='table', attrs={'class': 'tablehead'})

                home_dets, away_dets = parse.parse_squad(tables[0])
                stats = parse.parse_stats(tables[1])
                match_time = parse.parse_info(tables[2])

                save.save_match_stats(stats)
                save.save_match_squad(home_dets, 'h')
                save.save_match_squad(away_dets, 'a')
                save.update_time(match_time)

            except:
                print "error with " + str((m.espn_match_id))

        time.sleep(10)
