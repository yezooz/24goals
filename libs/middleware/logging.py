# coding=utf-8
from django.http import HttpResponseForbidden
from django.conf import settings
from django.core.cache import cache

import datetime
from myscore.main.models import UserActivity, BanList

# import cPickle as pickle

# JAKOŚ BADZIEWNIE TO DZIAŁA

class ActivityAndBanning(object):
    def process_request(self, request):
        # exceptions
        except_user_agents = ("Mediapartners-Google/2.1",
                              "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
                              "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")

        if not request.method in ('GET') or request.GET:
            return None  # Don't bother checking the cache.
        if request.META.has_key('PATH_INFO') and request.META['PATH_INFO'].find("/static") == 0 or request.META[
            'PATH_INFO'].find("/admin") == 0:
            return None
        # if request.META['REMOTE_ADDR'] in settings.INTERNAL_IPS:
        # return response
        if request.META.has_key('HTTP_USER_AGENT') and request.META['HTTP_USER_AGENT'] in except_user_agents:
            return None

        # ban list
        # IP
        bl_ip = cache.get("ban_list_ip")
        if bl_ip is None:
            bl_ip = map(lambda x: x.ip, BanList.objects.filter(is_active=1))
            cache.set("ban_list_ip", bl_ip)

        if request.META.has_key('HTTP_X_FORWARDED_FOR'):
            addr = request.META['HTTP_X_FORWARDED_FOR']
        else:
            addr = request.META['REMOTE_ADDR']
        if addr in bl_ip:
            return HttpResponseForbidden(
                "You're banned. If you think it's wrong please contact administrator at marek@24goals.com")

        # USERNAME
        bl_usr = cache.get("ban_list_usr")
        if bl_usr is None:
            bl_usr = ()
            cache.set("ban_list_usr", bl_usr)
        if str(request.user) in bl_usr:
            return HttpResponseForbidden(
                "You're banned. If you think it's wrong please contact administrator at marek@24goals.com")

        if request.META.has_key('HTTP_REFERER'):
            referer = request.META['HTTP_REFERER']
        else:
            referer = ''

        if request.META.has_key('HTTP_X_FORWARDED_FOR') and request.META['REMOTE_ADDR'] == '127.0.0.1':
            addr = request.META['HTTP_X_FORWARDED_FOR']
        else:
            addr = request.META['REMOTE_ADDR']

        self.activity = UserActivity(
            user=request.user,
            date=datetime.datetime.now(),
            request_url=request.META['PATH_INFO'],
            referer_url=referer,
            client_address=addr,
            client_host=request.META['REMOTE_HOST'],
            browser_info=addr
        )
        self.activity.save()

        TODO = """
				DOCELOWO MOZNA ZROBIC TAK, ZE ZAPISUJE PICKELED OBJEKTY ACTIVITY DO MEMCACHE, A POZNIEJ JE W WOLNEJ CHWILI ZAPISUJE Z ODPOWIEDNIM TIMEOUTEM. DZIEKI TEMU ZAOSZCZEDZIMY SPORO NA INSERTACH W SZCZYTOWYCH MOMENTACH
				"""

        return None

    # def process_exception(self,request,exception):
    # self.activity.error = exception
    # self.activity.save()

    # return None


class WhoIsOnline(object):
    def process_request(self, request):
        # exceptions
        except_user_agents = ("Mediapartners-Google/2.1",
                              "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
                              "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")

        if not request.method in ('GET', 'HEAD') or request.GET:
            return None  # Don't bother checking the cache.
        if request.META.has_key('HTTP_USER_AGENT') and request.META['HTTP_USER_AGENT'] in except_user_agents:
            return None
        if request.META['PATH_INFO'].find("/static") == 0 or request.META['PATH_INFO'].find("/admin") == 0:
            return None

        who_online = cache.get("who_online")
        if who_online is None:
            who_online = {}

        if not request.user.is_anonymous():
            who_online[str(request.user)] = datetime.datetime.now()
        else:
            if request.META.has_key('HTTP_X_FORWARDED_FOR'):
                addr = request.META['HTTP_X_FORWARDED_FOR']
            else:
                addr = request.META['REMOTE_ADDR']

            who_online['anon_' + str(addr)] = datetime.datetime.now()
        cache.set("who_online", who_online, 3600 * 24)

        return None
