# coding=utf-8
import fpformat

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import ugettext as _

import datetime
from myscore.main.models import *


class LeagueTables:
    def __init__(self, today):
        self.today = today

        data = {}
        data["top_users"] = Accounts.objects.select_related().order_by('-points')[:10]
        data["top_cl_users"] = UsersTable.objects.select_related().filter(table_type='o', season_id=3, league_id=9,
                                                                          date=today).order_by('position')[:5]
        data["top_en_users"] = UsersTable.objects.select_related().filter(table_type='o', season_id=3, league_id=1,
                                                                          date=today).order_by('position')[:5]
        data["top_fr_users"] = UsersTable.objects.select_related().filter(table_type='o', season_id=3, league_id=5,
                                                                          date=today).order_by('position')[:5]
        data["top_es_users"] = UsersTable.objects.select_related().filter(table_type='o', season_id=3, league_id=4,
                                                                          date=today).order_by('position')[:5]
        data["top_de_users"] = UsersTable.objects.select_related().filter(table_type='o', season_id=3, league_id=6,
                                                                          date=today).order_by('position')[:5]
        data["top_pl_users"] = UsersTable.objects.select_related().filter(table_type='o', season_id=3, league_id=8,
                                                                          date=today).order_by('position')[:5]
        data["top_it_users"] = UsersTable.objects.select_related().filter(table_type='o', season_id=3, league_id=3,
                                                                          date=today).order_by('position')[:5]

        data["top_fans"] = FansTable.objects.select_related().filter(table_type='p', season_id=3,
                                                                     league_id=10).order_by('position')[:5]

        self.data = data

    def common_line(self, users):
        usrs = ""

        i = 1
        for u in users:
            usrs += u"""<li><a href="/%s/%s/" title="%s">%s. %s (<strong>%s %s.</strong>)</a></li>""" % (
            _('Uzytkownik URL'), u.user, u.user, i, u.user, u.points, _('pkt'))
            i += 1

        return usrs

    def render(self):
        code = cache.get("template_league_tables")
        if code != None:
            return code

        data = self.data
        code = ""

        if "top_fans" in data and len(data["top_fans"]) > 0:
            code += u"""<div class="modul">
				<h4 class="tytul"><a href="/%s/">%s (TOP 5)</a></h4>
				<ol class="lista">""" % (_('liga-kibicow'), _('Liga Kibicow'))

            i = 1
            for t in data["top_fans"]:
                code += u"""<li><a href="/kibice/%s">%s. <strong>%s</strong> (%s)</a></li>""" % (
                t.team.name_en_url, i, t.team.name_pl, t.points)
                i += 1

            code += u"""<li><span style="text-align: right;"><a href="/%s/">%s &raquo;</a></span></li>
						</ol></div>""" % (_('liga-kibicow'), _('wszystkie'))
        # code += "</ol></div>"

        if "top_users" in data and len(data["top_users"]) > 0:
            code += u"""<div class="modul">
				<h4 class="tytul"><a href="/%s/">Najlepiej typujący</a></h4>
				<ol class="lista">%s<li><span style="text-align: right;"><a href="/%s/">wszyscy &raquo;</a></span></li></ol></div>""" % (
            _('Typer URL'), self.common_line(data["top_users"]), _('Typer URL'))

        if "top_cl_users" in data and len(data["top_cl_users"]) > 0:
            code += u"""<div class="modul">
				<h4 class="tytul"><a href="/typer/liga-mistrzow/" style="background-image: url(/static/images/ikona_fl_cl.png);" title="5 najlepiej typująych w lidze mistrzów">Najlepsza 5.</a></h4><ol class="lista">%s<li><span style="text-align: right;"><a href="/typer/liga-mistrzow/">wszyscy &raquo;</a></span></li></ol></div>""" % self.common_line(
                data["top_cl_users"])

        if "top_en_users" in data and len(data["top_en_users"]) > 0:
            code += u"""<div class="modul">
				<h4 class="tytul"><a href="/typer/angielska/" style="background-image: url(/static/images/ikona_fl_en.png);" title="5 najlepiej typująych w angielskiej">Najlepsza 5.</a></h4><ol class="lista">%s<li><span style="text-align: right;"><a href="/typer/angielska/">wszyscy &raquo;</a></span></li></ol></div>""" % self.common_line(
                data["top_en_users"])

        if "top_fr_users" in data and len(data["top_fr_users"]) > 0:
            code += u"""<div class="modul">
				<h4 class="tytul"><a href="/typer/francuska/" style="background-image: url(/static/images/ikona_fl_fr.png);" title="5 najlepiej typująych w francuskiej">Najlepsza 5.</a></h4><ol class="lista">%s<li><span style="text-align: right;"><a href="/typer/francuska/">wszyscy &raquo;</a></span></li></ol></div>""" % self.common_line(
                data["top_fr_users"])

        if "top_es_users" in data and len(data["top_es_users"]) > 0:
            code += u"""<div class="modul">
				<h4 class="tytul"><a href="/typer/hiszpanska/" style="background-image: url(/static/images/ikona_fl_es.png);" title="5 najlepiej typująych w hiszpańskiej">Najlepsza 5.</a></h4><ol class="lista">%s<li><span style="text-align: right;"><a href="/typer/hiszpanska/">wszyscy &raquo;</a></span></li></ol></div>""" % self.common_line(
                data["top_es_users"])

        if "top_de_users" in data and len(data["top_de_users"]) > 0:
            code += u"""<div class="modul">
				<h4 class="tytul"><a href="/typer/niemiecka/" style="background-image: url(/static/images/ikona_fl_de.png);" title="5 najlepiej typująych w niemieckiej">Najlepsza 5.</a></h4><ol class="lista">%s<li><span style="text-align: right;"><a href="/typer/niemiecka/">wszyscy &raquo;</a></span></li></ol></div>""" % self.common_line(
                data["top_de_users"])

        if "top_pl_users" in data and len(data["top_pl_users"]) > 0:
            code += u"""<div class="modul">
				<h4 class="tytul"><a href="/typer/polska/" style="background-image: url(/static/images/ikona_fl_pl.png);" title="5 najlepiej typująych w polskiej">Najlepsza 5.</a></h4><ol class="lista">%s<li><span style="text-align: right;"><a href="/typer/polska/">wszyscy &raquo;</a></span></li></ol></div>""" % self.common_line(
                data["top_pl_users"])

        if "top_it_users" in data and len(data["top_it_users"]) > 0:
            code += u"""<div class="modul">
				<h4 class="tytul"><a href="/typer/wloska/" style="background-image: url(/static/images/ikona_fl_it.png);" title="5 najlepiej typująych w włoskiej">Najlepsza 5.</a></h4><ol class="lista">%s<li><span style="text-align: right;"><a href="/typer/wloska/">wszyscy &raquo;</a></span></li></ol></div>""" % self.common_line(
                data["top_it_users"])

        cache.set("template_league_tables", code, 3600 * 4)
        return code
