from django.conf import settings
from django.template.loader import render_to_string

from myscore.main.modules import who_online
from myscore.main.models import *

# from django.core.cache import cache

def process(request):
    if not request.user.is_anonymous():
        return {
            'layout_lang': "partials/layout_%s.html" % settings.LANGUAGE_CODE,
            'online': who_online.render(),
            'account': Accounts().get_profile(str(request.user)),
        }
    else:
        return {
            'layout_lang': "partials/layout_%s.html" % settings.LANGUAGE_CODE,
            'online': who_online.render(),
        }


def flash(request):
    if 'bledy' in request.flash:
        print 'bledy'
        flash = request.flash['bledy']
        del request.flash['bledy']
        return {'flash': render_to_string("partials/flash_bledy.html", {'msg': flash})}
    elif 'sukces' in request.flash:
        print 'sukces'
        flash = request.flash['sukces']
        del request.flash['sukces']

    elif 'flash' in request.session:
        flash = request.session['flash']

        try:
            flash = render_to_string("partials/flash_sukces.html", {'msg': flash['sukces']})
        except:
            pass

        try:
            flash = render_to_string("partials/flash_bledy.html", {'msg': flash['bledy']})
        except:
            pass

        del request.session['flash']
        return {'flash': flash}
    elif 'now' in request.flash:
        print 'now'
        flash = request.flash['now']
        del request.flash['now']
        return {'flash': flash}

    return {'flash': None}
