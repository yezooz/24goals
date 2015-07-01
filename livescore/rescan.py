import urllib2
import getopt
import re
import os
import socket
from urllib import urlencode

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
            "<div class=\"stadium\" style=\"text-align:.*right;\">(<span.*</span>)?([\w\W]+)?(\&nbsp)?.*</div>",
            stadium, re.U)

        try:
            return stadium.groups()[1]
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

        return time.group('time')

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
            if type(match.groups()) != type(()): return False
        except AttributeError:
            return False

        return match.group('match_id')

    def parse_match(self, gc, date=""):
        time, minute, status = self.parse_time(gc)  # str, str
        if status == False:
            return False

        match_id = self.parse_match_id(str(gc.find(name='tr', attrs={'class': 'linksRow'})))  # int

        time, minute, status = self.parse_time(gc)  # time, int, str
        crowd = self.parse_crowd(gc)  # str
        stadium = self.parse_stadium(gc)  # str
        caption = self.parse_caption(gc)
        if type(time) != type(datetime.time(0, 0)):
            time = datetime.time(0, 0)

        match = {
            'match_id': match_id,
            'date': date,
            'time': time,
            'minute': minute,
            'status': status,
            'stadium': stadium,
            'crowd': crowd,
            'home_team_name': caption["home_team_name"],
            'away_team_name': caption["away_team_name"],
            'home_team_id': caption["home_team_id"],
            'away_team_id': caption["away_team_id"],
            'home_score': caption["home_score"],
            'away_score': caption["away_score"],
        }

        return match

    def parse_matches(self, container, date=""):
        """ Get and parse every match box"""
        if date != "":
            date = re.search("([\d]{4})([\d]{2})([\d]{2})", date).groups()
            date = datetime.date(int(date[0]), int(date[1]), int(date[2]))
        else:
            date = datetime.date.today()
        matches_container = []

        for gc in container.findAll(name='div', attrs={'class': 'gameContainer'}):
            try:
                match = self.parse_match(gc, date)
                try:
                    Matches.objects.get(espn_match_id=match["match_id"])
                    matches_container.append(match)
                except:
                    continue
            except:
                continue

        return matches_container


# ---

class Save:
    def getTeamByEspn(self, name):
        """get team_id or create one"""

        team, created = Teams.objects.get_or_create(name_espn=name, defaults={'country_id': 1})
        return int(team.id)

    def getStadiumByEspn(self, name):
        """get stadium_id or create one"""
        if name is None:
            return 0

        stadium, created = Stadiums.objects.get_or_create(name_espn=name)
        return int(stadium.id)

    # ---

    def save_match(self, match):

        try:
            m = Matches.objects.get(espn_match_id=match["match_id"])
        except:
            return False

        m.match_time = match["time"]
        if match["date"] != "":
            m.match_date = match["date"]
        m.minute = match["minute"]
        m.status = match["status"]
        m.save()

        return True

    def save_matches(self, matches):

        for match in matches:
            self.save_match(match)


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

        lynx = False

        if lynx:
            try:
                lynxcmd = "lynx -dump -source -useragent='Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)' %s" % url
                content = os.popen(lynxcmd).read()
            except IOError, (errno, strerror):
                return False
        else:
            try:
                # timeout in seconds
                timeout = 20
                socket.setdefaulttimeout(timeout)

                req = urllib2.Request(url)
                opener = urllib2.build_opener()
                req.add_header('User-Agent',
                               'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)')

                location = opener.open(req)
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

    def get_and_save_page(self, url):
        save = Save()
        html = self.get_page(url)
        html = unicode(html)

        page = self.generate_tree(html)  # convert to BS object
        date = self.get_date_by_path(url)

        matches = parse.parse_matches(page, date)
        save.save_matches(matches)

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

    def get_date_by_path(self, path):

        try:
            m = re.match(".*league=([\w\d.]{3,})\&date=([\d]{8}).*", path).groups()
            return m[1]
        except:
            return ""


if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "clstu")
    # go!
    get = ESPNDownload()
    parse = ESPNAnalyse()
    save = Save()

    if len(args) == 1:
        print "scanning next %s days" % int(args[0])

        for d in xrange(int(args[0])):
            day = datetime.datetime.now() + datetime.timedelta(days=int(d))

            path = "http://soccernet-akamai.espn.go.com/scoreboard?league=all&date=%s&&refresh=45&cc=5739" % day.strftime(
                '%Y%m%d')
            print "getting %s" % path

            # cancel all day's matches
            matches = Matches.objects.filter(match_date=day.strftime('%Y-%m-%d'), status__in=['o', 'c', 'p']).exclude(
                league__id=8)
            for m in matches:
                m.status = 'c'
                m.save()

            try:
                get.get_and_save_page(path)
            except:
                # for safety reasons
                print "error. reverting!"
                matches = Matches.objects.filter(match_date=day.strftime('%Y-%m-%d'), status='c')
                for m in matches:
                    m.status = 'o'
                    m.save()

    else:
        print """Unknown action:

Usage:
- number_of_days_ahead"""
