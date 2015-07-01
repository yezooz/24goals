import urllib2
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


class Save:
    def getTeamByLive(self, name):
        """get team_id or create one"""

        team = Teams.objects.get(name_live=name)
        return int(team.id)


# ===

class LSDownload:
    def get_page(self, url):
        """Fetches an arbitrary page from the web"""

        try:
            # timeout in seconds
            timeout = 20
            socket.setdefaulttimeout(timeout)

            req = urllib2.Request(url)
            opener = urllib2.build_opener()
            req.add_header('User-Agent',
                           'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)')
            first = BeautifulSoup.BeautifulSoup(opener.open(req).read())

            forms = first.findAll('form')
            if not forms:
                return None
            form = forms[0]

            postdata = []
            for intag in form.findAllNext('input'):

                if intag['type'] == 'hidden':
                    postdata.append((intag['name'], intag['value']))
                elif intag['type'] == 'password':
                    postdata.append((intag['name'], password))
                elif intag['type'] == 'checkbox':
                    postdata.append((intag['name'], 'n'))
                elif intag['type'] == 'text' and intag['name'] == 'login':
                    postdata.append(('login', myYahooID))
                elif intag['type'] == 'submit':
                    if intag.has_key(['name']):
                        postdata.append((intag['name'], intag['value']))
                    else:
                        postdata.append(('submit', intag['value']))

            req = urllib2.Request(url + "/default.dll?page=home", urlencode(postdata))
            opener = urllib2.build_opener()
            req.add_header('User-Agent',
                           'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)')
            content = opener.open(req).read()

        except IOError, (errno, strerror):
            return False

        return content

    def get_and_save_page(self, url):
        save = Save()
        html = self.get_page(url)

        page = self.generate_tree(html)  # convert to BS object

        return page

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


class LSAnalyse:
    def parse_matches(self, page):

        def parse_line(line):
            minute, home, away, home_score, away_score, status = 0, "", "", "", "", "o"

            line = line.findAll('td')
            for l in line:
                cont = True

                if l.has_key('width'):

                    if int(l['width']) == 118 and l.has_key('align'):
                        save = Save()
                        try:
                            home = save.getTeamByLive(l.contents[0])
                        except:
                            home = 0

                    elif int(l['width']) == 118:
                        try:
                            away = save.getTeamByLive(l.contents[0])
                        except:
                            away = 0

                    elif int(l['width']) == 50 and re.match(".*\d{1}\s{1}-\s{1}\d{1}.*", str(l.contents[0])):
                        score = re.search(".*(\d{1})\s{1}-\s{1}(\d{1}).*", str(l.contents[0])).groups()
                        home_score, away_score = score

                    elif int(l['width']) == 45 and len(l.contents) == 3:
                        minute = l.contents[2]

                    elif int(l['width']) == 45 and str(l.contents[0]).strip() == "&nbsp;FT":
                        minute = "FT"

            minute = str(minute).strip()
            if minute == "HT":
                minute = -3
                status = "d"

            elif minute == "ET":
                minute = -1
                status = "d"

            elif minute == "FT":
                minute = 90
                status = "f"

            elif re.match("[\d]{1,3}'", minute):
                minute = re.search("([\d]{1,3})'", minute).groups()
                minute = int(minute[0])
                status = "d"

            elif re.match(".*[\d]{2}:[\d]{2}", minute):
                minute = 0
                status = "o"
            else:
                minute = 0
                status = "o"

            return int(minute), home, home_score, away_score, away, status

        results = []
        for line in page.findAll(name='tr', attrs={'bgcolor': '#cfcfcf'}):
            minute, home, home_score, away_score, away, status = parse_line(line)
            results.append((minute, home, home_score, away_score, away, status))

        for line in page.findAll(name='tr', attrs={'bgcolor': '#dfdfdf'}):
            minute, home, home_score, away_score, away, status = parse_line(line)
            results.append((minute, home, home_score, away_score, away, status))

        return results


if __name__ == '__main__':

    # go!
    get = LSDownload()
    parse = LSAnalyse()
    save = Save()

    url = "http://www.livescore.com"

    while (1):
        home_teams = []
        db_matches = list(Matches.objects.filter(match_date=datetime.date.today(), status__in=['o', 'd', 'f']))
        for dm in db_matches:
            home_teams.append(dm.home_team.id)

        if len(db_matches) > 0:
            try:
                page = get.get_and_save_page(url)
            except:
                print "problem z pobieraniem strony"
                time.sleep(15)
                continue
        else:
            print "skipped at %s" % str(datetime.datetime.now())
            time.sleep(30 * 60)  # half an hour

        matches = parse.parse_matches(page)
        for match in matches:
            try:
                minute, home, home_score, away_score, away, status = match[0], match[1], match[2], match[3], match[4], \
                                                                     match[5]

                if home in home_teams and status != "o":
                    m = Matches.objects.get(match_date=datetime.date.today(), home_team__id=home)

                    m.home_score = home_score
                    m.away_score = away_score

                    # match's actions
                    if m.status == "o" and status == "d":
                        m.on_start()
                    if m.status == "d" and status == "f":
                        m.on_finish()
                    if m.status == "o" and status == "p":
                        m.on_cancel()

                    m.status = status
                    m.minute = minute
                    m.save()
            except:
                print "error found. skipped!"
                pass

        print datetime.datetime.now()
        time.sleep(45)

    # Traceback (most recent call last):
    #   File "import_live.py", line 236, in ?
    #     page = get.get_and_save_page(url)
    #   File "import_live.py", line 120, in get_and_save_page
    #     html = self.get_page(url)
    #   File "import_live.py", line 111, in get_page
    #     except IOError, (errno, strerror):
    # ValueError: need more than 1 value to unpack
