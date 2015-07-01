import urllib2
import re
import os
import logging

import sys
import BeautifulSoup
import datetime
import time
# django settings
sys.path.append(os.path.dirname(__file__) + "../../")
os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_production_pl'
# os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_pl'

from django.db import models
from myscore.main.models import *


class Save:
    def getLeagueByEspn(self, name):
        """get league_id or create one"""

        league, created = Leagues.objects.get_or_create(name_espn=name)
        return int(league.id)

    def getTeamByEspn(self, name):
        """get team_id or create one"""
        # team, created = Teams.objects.get_or_create(name_espn=name, defaults={'country_id' : 1})
        # return int(team.id)

        try:
            team = Teams.objects.get(name_espn=name)
            return int(team.id)
        except:
            return 0

    def getStadiumByEspn(self, name):
        """get stadium_id or create one"""
        if name is None:
            return 0

        stadium, created = Stadiums.objects.get_or_create(name_espn=name)
        return int(stadium.id)

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

    def save_match(self, match, update_score=True, source='e'):

        try:
            m = Matches.objects.get(espn_match_id=match["match_id"])
            # why updated it again ?

            if update_score:
                if m.status == 'p' or m.status == 'c' or (m.status == 'o' and match["status"] == 'o') or m.manual == 1:
                    return False

                # match's actions
                if m.status == "o" and match["status"] == "d":
                    m.on_start()
                if m.status == "d" and match["status"] == "f":
                    m.on_finish()
                if m.status == "o" and match["status"] == "p":
                    m.on_cancel()

                # stop this freakin' out ESPN
                if int(m.home_score) > int(match["home_score"]) or int(m.away_score) > int(match["away_score"]) or (
                        int(m.minute) > int(match["minute"]) and int(m.minute) != 0):
                    return False

        except Matches.DoesNotExist:
            m = Matches()
            m.espn_match_id = match["match_id"]
            m.season_id = 1
        except TypeError:
            return False

        m.espn_home_team_id = match["home_team_id"]
        m.espn_away_team_id = match["away_team_id"]
        m.home_score = match["home_score"]
        m.away_score = match["away_score"]
        m.source = source
        if match["league_name"] != "" and match["league_name"] != "all":
            m.league_id = Leagues.objects.get(pk=int(self.getLeagueByEspn(match["league_name"]))).id

        # forget it if unknown team
        try:
            m.home_team = Teams.objects.get(pk=self.getTeamByEspn(match["home_team_name"]))
            m.away_team = Teams.objects.get(pk=self.getTeamByEspn(match["away_team_name"]))
            if m.home_team == 0 or m.away_team == 0:
                return False

        except:
            return False

        m.stadium_id = self.getStadiumByEspn(match["stadium"])
        m.crowd = match["crowd"]
        m.match_time = match["time"]
        if match["date"] != "":
            m.match_date = match["date"]
        m.minute = match["minute"]
        m.status = match["status"]
        if update_score:
            m.save()

        MatchDetails.objects.filter(match__id=m.id, action__in=['g', 'r', '']).delete()
        for detail in match["details"]:

            d = MatchDetails()
            d.match = m

            try:
                p = self.getPlayerByEspn(detail["player_id"], detail["player_name"])
                d.player_id = p.id
                d.espn_player_name = str(detail["player_name"])
                d.espn_player_id = str(detail["player_id"])
                if detail["player_id"] is None:
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

            try:
                d.home_score = int(detail["home_score"])
                d.away_score = int(detail["away_score"])
            except ValueError:
                d.home_score = 0
                d.away_score = 0

            d.minute = detail["minute"]
            d.side = detail["side"]

            action = detail["action"]
            if action == 'Goal':
                d.action = 'g'
            elif action == 'Yellow Card':
                d.action = 'y'
            elif action == 'Red Card':
                d.action = 'r'

            action_info = detail["action_info"]
            if action_info == 'og':
                d.action_info = 'o'
            elif action_info == 'pen miss':
                d.action_info = 'm'
            elif action_info == 'pen':
                d.action_info = 'p'

            try:
                d.save()
            except:
                return False

    def save_matches(self, matches, update_score=True):

        for match in matches:
            self.save_match(match, update_score)


# ===


class ESPNDownload:
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

        lynx = True

        if lynx:
            try:
                lynxcmd = "lynx -dump -source -useragent='Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)' %s" % url
                content = os.popen(lynxcmd).read()
            except IOError, (errno, strerror):
                return False
        else:
            try:
                location = urllib2.urlopen(url)
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

        if not lynx:
            location.close()
        return content

    def get_and_save_page(self, url, update_score=True):
        save = Save()
        html = self.get_page(url)
        html = unicode(html)

        page = self.generate_tree(html)  # convert to BS object
        league, date = self.get_league_and_date_by_path(url)

        matches = parse.parse_matches(page, date, league)
        save.save_matches(matches, update_score)

        return True

    def get_and_save_whole_league(self, start_url):

        save = Save()
        html = self.get_page(start_url)
        html = unicode(html)

        page = self.generate_tree(html)  # convert to BS object
        league, date = self.get_league_and_date_by_path(start_url)

        next_url = self.next_link(page)
        matches = parse.parse_matches(page, date, league)
        save.save_matches(matches)

        if next_url == False:
            return True

        while (1):
            time.sleep(10)

            html = self.get_page(next_url)
            if html == False:
                return False

            page = self.generate_tree(html)
            league, date = self.get_league_and_date_by_path(next_url)

            matches = parse.parse_matches(page, date, league)
            save.save_matches(matches)

            next_url = self.next_link(page)
            if next_url == False:
                return True

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

    def next_link(self, page):
        """Get 'next' link on matches list page"""

        date_links = page.find(name='div', attrs={'id': 'prevNext'}).findAll(name='a', recursive=False)
        if len(date_links) == 2:
            data = re.search("<a.*league=([\w\d.]+)\&.*date=([\d]{8}).*>", str(date_links[1])).groups()
            return "http://soccernet-akamai.espn.go.com/scoreboard?league=%s&date=%s&cc=5739" % (data[0], data[1])
        return False

    def get_league_and_date_by_path(self, path):

        try:
            m = re.match(".*league=([\w\d.]{3,})\&date=([\d]{8}).*", path).groups()
            league = m[0]
            date = m[1]
        except:
            return "", ""

        return league, date


class ESPNAnalyse:
    def parse_time(self, gc):
        """
        Returns match's start time, current minute or status

        Possible values:
        XX'
        10:10 UK
        Half, Final
        1st, 2nd
        ET (Extra Time)
        """

        def match(time_str):
            if time_str == "Half":
                time = 0
                minute = -3
                status = 'd'
            elif time_str == "ET":
                time = 0
                minute = -1
                status = 'd'
            elif time_str == "Final":
                time = 0
                minute = 90
                status = 'f'
            elif re.match(".*[\d]{2}:[\d]{2} UK", time_str):
                time = re.search(".*([\d]{2}):([\d]{2}) UK", time_str).groups()
                time = datetime.time(int(time[0]), int(time[1]))
                minute = 0
                status = 'o'
            elif re.match(".*[\d]{1,3}\'", time_str):
                time = 0
                minute = re.search("([\d]{1,3})\'", time_str).groups()[0]
                status = 'd'
            elif re.match(".*[\d]{1,3} min", time_str):
                time = 0
                minute = re.search("([\d]{1,3}) min", time_str).groups()[0]
                status = 'd'
            elif time_str == "1st":
                time = 0
                minute = -4
                status = 'd'
            elif time_str == "2nd":
                time = 0
                minute = -2
                status = 'd'
            else:
                time = 0
                minute = 0
                status = 'c'

            return time, minute, status

        # (o)pen / (s)tarted / (f)inished
        try:
            t = gc.find(name='div', attrs={'class': 'teamTop_inGame'}).contents
            if type(t) == type([]) and len(t) > 0:
                return match(str(t[0]).strip())
            else:
                pass
        except AttributeError:
            pass

        try:
            t = gc.find(name='div', attrs={'class': 'teamTop'}).a.contents
            if type(t) == type([]):
                return match(str(t[0]).strip())
            else:
                pass

        except AttributeError:
            pass

        try:
            t = gc.find(name='div', attrs={'class': 'teamTop'}).contents
            if type(t) == type([]):
                if str(t[0]).strip() == "Postp.":  # match postponed
                    return 0, 0, 'p'
                else:  # match cancelled or sth ;)
                    return 0, 0, 'c'
            else:
                pass

        except AttributeError:
            pass

        return False, False, False

    def parse_stadium(self, gc):
        """ Returns stadium's name """

        stadium = str(gc.find(name='div', attrs={'class': 'stadium'})).strip()
        stadium = re.search(
            "<div class=\"stadium\" style=\"text-align:.*right;\">(<span.*</span>)?(?P<stadium_name>[\w\W]+)?(\&nbsp)?.*</div>",
            stadium, re.U)

        try:
            return stadium.group('stadium_name')
        except AttributeError:
            return ""

    def parse_crowd(self, gc):
        """ Returns number of spectacles """

        try:
            stadium = str(gc.find(name='div', attrs={'class': 'stadium'}).contents[0]).strip()
            crowd = re.search("([0-9{1,4}]*[,]*[0-9{3}]+)", stadium).groups()[0]

            if len(crowd) < 3:
                return 0
            else:
                return crowd
        except AttributeError:
            return ""
        except IndexError:
            return ""

    def parse_caption(self, match):
        """ Returns playing teams and score"""

        home_team = match.find(name='td', attrs={'class': 'leftTeam'})
        home_team_id = re.search("team\?id=([\d]+)\"", str(home_team)).groups()[0]
        home_team = home_team.a.string

        away_team = match.find(name='td', attrs={'class': 'rightTeam'})
        away_team_id = re.search("team\?id=([\d]+)\"", str(away_team)).groups()[0]
        away_team = away_team.a.string

        score = match.find(name='td', attrs={'class': 'totalScore'}).a
        scores = re.search("([\d]+)([&nbsp;-]+)([\d]+)", str(score))

        try:
            home_score = scores.groups()[0]
            away_score = scores.groups()[2]

        except AttributeError:
            home_score = -1
            away_score = -1

        return {'home_team_name': home_team, 'away_team_name': away_team, 'home_team_id': home_team_id,
                'away_team_id': away_team_id, 'home_score': home_score, 'away_score': away_score}

    def parse_time_detail(self, time):
        """ Returns minute of detail (INT) """

        time = re.search("<td class=\"timeCol\">((?P<time>[\d]{1,3})\')?</td>", time)

        try:
            if type(time.groups()) != type(()):
                return ""
        except AttributeError:
            return ""

        minute = time.group('time')

        return minute

    def parse_score_detail(self, score):
        """ Returns scores of detail """

        score = re.search("<td class=\"scoreCol\">((?P<home_score>[\d]{1,3}) - (?P<away_score>[\d]{1,3}))?</td>", score)

        try:
            if type(score.groups()) != type(()):
                return "", ""
        except AttributeError:
            return "", ""

        home_score = score.group('home_score')
        away_score = score.group('away_score')

        return home_score, away_score

    def parse_match_id(self, links_row):
        """ Returns match_id """
        match = re.search(".*href=\"/match\?id=(?P<match_id>[\d]{1,8}){1}.*", links_row)

        try:
            if type(match.groups()) != type(()):
                return False
        except AttributeError:
            return False

        match_id = match.group('match_id')

        return match_id

    def parse_left_detail(self, left_top):
        """ Parsing all left side of match box """

        left = re.search(
            "<td class=\"leftCol\">(<a.*href=\"/players.*\?id=(?P<player_id>[\d]{1,8}){1}\&.*\">)?(?P<player_name>[\w\'\` ]+)(</a>)?[ ]?(\((?P<action_info>[\w ]+)\))?[ ]?(<img.*alt=\"(?P<action>[\w ]+)\")?.*</td>",
            left_top, re.U)

        try:
            if type(left.groups()) != type(()):
                return False
        except AttributeError:
            return False

        player_id = left.group('player_id')
        player_name = left.group('player_name')
        action_info = left.group('action_info')
        action = left.group('action')

        return {'player_id': player_id, 'player_name': player_name, 'action': action, 'action_info': action_info,
                'side': 'left'}

    def parse_right_detail(self, right_top):
        """ Parsing all right side of match box"""

        right = re.search(
            "<td class=\"rightCol\">(<img.*alt=\"(?P<action>[\w ]+)\".*/>)?[ ]?(<a.*href=\"/players.*\?id=(?P<player_id>[\d]{1,8}){1}\&.*\">)?(?P<player_name>[\w\' ]+)(</a>)?[ ]?(\((?P<action_info>[\w ]+)\))?.*</td>",
            right_top, re.U)

        try:
            if type(right.groups()) != type(()):
                return False
        except AttributeError:
            return False

        player_id = right.group('player_id')
        player_name = right.group('player_name')
        action_info = right.group('action_info')
        action = right.group('action')

        return {'player_id': player_id, 'player_name': player_name, 'action': action, 'action_info': action_info,
                'side': 'right'}

    def parse_details(self, match):
        """ Parsing match details """
        dts = []

        details = match.find(name='table', attrs={'class': 'scoreTable'}).tbody
        for detail in details.findAll('tr'):

            left_side = self.parse_left_detail(str(detail.find(name='td', attrs={'class': 'leftCol'})))
            right_side = self.parse_right_detail(str(detail.find(name='td', attrs={'class': 'rightCol'})))

            if type(left_side) == type({}):
                dt = left_side
            elif type(right_side) == type({}):
                dt = right_side
            else:
                continue
            dt["minute"] = self.parse_time_detail(str(detail.find(name='td', attrs={'class': 'timeCol'})))
            dt["home_score"], dt["away_score"] = self.parse_score_detail(
                str(detail.find(name='td', attrs={'class': 'scoreCol'})))

            dts.append(dt)
        return dts

    def parse_match(self, gc, date="", league_name="", needed=()):
        time, minute, status = self.parse_time(gc)  # str, str
        if status == False:
            return False

        match_id = self.parse_match_id(str(gc.find(name='tr', attrs={'class': 'linksRow'})))  # int
        if len(needed) > 0 and int(match_id) not in needed:  # czy sciagac ten mecz ?
            return False

        time, minute, status = self.parse_time(gc)  # time, int, str
        crowd = self.parse_crowd(gc)  # str
        stadium = self.parse_stadium(gc)  # str
        caption = self.parse_caption(gc)
        details = self.parse_details(gc)
        if type(time) != type(datetime.time(0, 0)):
            time = datetime.time(0, 0)

        match = {
            'match_id': match_id,
            'date': date,
            'time': time,
            'minute': minute,
            'league_name': league_name,
            'status': status,
            'stadium': stadium,
            'crowd': crowd,
            'home_team_name': caption["home_team_name"],
            'away_team_name': caption["away_team_name"],
            'home_team_id': caption["home_team_id"],
            'away_team_id': caption["away_team_id"],
            'home_score': caption["home_score"],
            'away_score': caption["away_score"],
            'details': details,
        }

        return match

    def parse_matches(self, container, date="", league_name="", needed=()):
        """ Get and parse every match box"""
        if date != "":
            date = re.search("([\d]{4})([\d]{2})([\d]{2})", date).groups()
            date = datetime.date(int(date[0]), int(date[1]), int(date[2]))
        else:
            date = datetime.date.today()
        matches_container = []

        for gc in container.findAll(name='div', attrs={'class': 'gameContainer'}):
            try:
                match = self.parse_match(gc, date, league_name, needed)
                matches_container.append(match)
            except:
                pass

        return matches_container


if __name__ == '__main__':

    # go!
    get = ESPNDownload()
    parse = ESPNAnalyse()
    save = Save()

    league = "all"

    date = "20080112"
    # path = "http://soccernet-akamai.espn.go.com/scoreboard?league=%s&date=%s&&refresh=45&cc=5739" % (league, date)
    # get.get_and_save_page(path)

    # date = "20071208"
    # path = "http://soccernet-akamai.espn.go.com/scoreboard?league=%s&date=%s&refresh=45&cc=5739" % (league, date)
    # get.get_and_save_whole_league(path)

    while (1):
        path = "http://soccernet-akamai.espn.go.com/scoreboard?league=%s&date=%s&refresh=off&cc=5739" % (league, date)
        db_matches = list(Matches.objects.filter(match_date=datetime.date.today(), status__in=['o', 'd', 'f']))

        if len(db_matches) > 0:
            try:
                get.get_and_save_page(path, False)
            except:
                print "problem z pobieraniem strony"
                time.sleep(15)
                continue
        else:
            print "skipped at %s" % str(datetime.datetime.now())
            time.sleep(30 * 60)  # half an hour

        print datetime.datetime.now()
        time.sleep(45)
