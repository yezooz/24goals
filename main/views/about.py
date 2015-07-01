# coding=utf-8
from django.template import RequestContext
from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from myscore.main.models import *
from myscore.main.modules import menu


def about_us(request):
    return render_to_response("about/about_us_%s.html" % settings.LANGUAGE_CODE, {},
                              context_instance=RequestContext(request))


def contact(request):
    # STILL TO DO!
    if request.POST:
        # walidacja
        if request.POST['reason'] == "" or request.POST['content'] == "":
            return HttpResponseRedirect(_('/kontakt'))

        m = Mailing()
        m.sender = request.POST['email']
        m.rcp = "marek@24gole.pl"
        m.subject = "formularz kontaktowy - " + str(request.POST['reason'])
        m.content = request.POST['content']
        m.ip = request.META['REMOTE_ADDR']
        m.save()

        m = Mailing()
        m.sender = request.POST['email']
        m.rcp = "marcin@24gole.pl"
        m.subject = "formularz kontaktowy - " + str(request.POST['reason'])
        m.content = request.POST['content']
        m.ip = request.META['REMOTE_ADDR']
        m.save()

        request.session['flash_msg'] = {'sukces': _('Dziekujemy wiadomosc zostala przeslana')}

        return HttpResponseRedirect(_('/kontakt'))

    return render_to_response("about/contact_%s.html" % settings.LANGUAGE_CODE, {},
                              context_instance=RequestContext(request))


def for_press(request):
    return render_to_response("about/for_press_%s.html" % settings.LANGUAGE_CODE, {},
                              context_instance=RequestContext(request))


def rules(request):
    return render_to_response("about/rules_%s.html" % settings.LANGUAGE_CODE, {},
                              context_instance=RequestContext(request))


def help(request, subject):
    return render_to_response("about/help/%s.html" % subject, {'menu': menu.render(request, 'main', 'index', {}, True)},
                              context_instance=RequestContext(request))


def contest(request):
    """contest"""
    return render_to_response("about/contest_%s.html" % settings.LANGUAGE_CODE, {},
                              context_instance=RequestContext(request))
