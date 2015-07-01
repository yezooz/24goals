from django.http import HttpResponseRedirect


class LangSwitchMiddleware(object):
    def __init__(self):
        pass

    def process_request(self, request):
        if request.META['HTTP_HOST'].find('8000') >= 0 and (
            request.COOKIES.has_key('django_language') and request.COOKIES['django_language']) != 'PL':
            return HttpResponseRedirect("http://www.24goals.com%s" % request.META['PATH_INFO'])
        elif request.META['HTTP_HOST'].find('24gole.pl') >= 0 and (
            request.COOKIES.has_key('django_language') and request.COOKIES['django_language']) == 'PL':
            return HttpResponseRedirect("http://www.24gole.pl%s" % request.META['PATH_INFO'])
        else:
            pass
