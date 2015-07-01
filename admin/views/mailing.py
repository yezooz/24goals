# coding=utf-8
import logging

from django import oldforms, template
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache

import datetime
import time
from myscore.main.models import *


@staff_member_required
def index(request):
    if request.POST:
        # create FILTER
        if request.POST.has_key('filter'):
            filter = False
            top_filter = False

            images = Images.objects.filter(is_processed=1)
            if request.POST['filter_nid'] != "":
                images = images.filter(dst_id=request.POST['filter_nid'], dst="news")
                filter = True
                top_filter = True

            elif request.POST['filter_mid'] != "":
                images = images.filter(dst_id=request.POST['filter_mid'], dst="match")
                filter = True
                top_filter = True

            if request.POST['filter_uid'] != "":
                images = images.filter(user__id=request.POST['filter_uid'])
                filter = True
                top_filter = True

            if request.POST['filter_date_start'] != "":
                images = images.filter(created_at__gte=request.POST['filter_date_start'])
                filter = True

            if request.POST['filter_date_end'] != "":
                images = images.filter(created_at__lte=request.POST['filter_date_end'])
                filter = True

            if request.POST['filter_accepted'] != "":
                images = images.filter(is_accepted=request.POST['filter_accepted'], is_deleted=0)
                filter = True

            elif request.POST['filter_deleted'] != "":
                images = images.filter(is_deleted=request.POST['filter_deleted'])
                filter = True

            if top_filter:
                images = images.select_related().order_by('created_at')
            elif filter:
                images = images.select_related().order_by('created_at')[:10]
            else:
                images = images.filter(is_accepted=0, is_deleted=0).select_related().order_by('created_at')[:10]

        # select elements to EDIT
        elif request.POST.has_key('delete'):
            ids = []
            for id in request.POST.iterkeys():
                if id.find('delete_') >= 0:
                    ids.append(id.replace('delete_', ''))

            if len(ids) > 0:
                cs = Images.objects.in_bulk(ids).values()
                for c in cs:
                    c.mark_as_deleted()

                return HttpResponseRedirect(request.path)

    else:
        images = Images.objects.filter(is_accepted=0, is_deleted=0).order_by('created_at')[:10]

    return render_to_response(
        "admin/images/index.html",
        {'images': images},
        RequestContext(request, {}),
    )


@staff_member_required
def generate(request):
    if request.POST and request.POST['template_id'] != "" and request.POST['lang'] != "":

        mt = MailingTemplates.objects.get(pk=request.POST['template_id'])
        if request.POST['test_mail']:
            m = Mailing(subject=mt.subject, content=mt.content, is_sent=0, ip='127.0.0.1',
                        sent_at=datetime.datetime(1970, 1, 1, 0, 0, 0))
            if request.POST['lang'] == 'pl':
                m.sender = "24gole <marek@24gole.pl>"
            else:
                m.sender = "24goals <marek@24goals.com>"
            m.rcp = "marek@24gole.pl"
            m.save()

            request.user.message_set.create(message="Maile zostały wygenerowane. Należy je teraz wysłać.")
            return HttpResponseRedirect("/admin/")

        mail_set = Accounts.objects.filter(user__is_active=True, lang=request.POST['lang'])
        for mail in mail_set:
            m = Mailing(subject=mt.subject, content=mt.content, is_sent=0, ip='127.0.0.1',
                        sent_at=datetime.datetime(1970, 1, 1, 0, 0, 0))
            if request.POST['lang'] == 'pl':
                m.sender = "24gole <marek@24gole.pl>"
            else:
                m.sender = "24goals <marek@24goals.com>"
            m.rcp = mail.user.email
            m.save()

        request.user.message_set.create(message="Maile zostały wygenerowane. Należy je teraz wysłać.")
        return HttpResponseRedirect("/admin/")

    templates = MailingTemplates.objects.all()

    return render_to_response(
        "admin/mailing/generate.html",
        {'templates': templates, },
        RequestContext(request, {}),
    )


def send(request):
    mailings = Mailing.objects.filter(is_sent=0)

    for mail in mailings:
        try:
            resp = send_mail(mail.subject, mail.content, mail.sender, [mail.rcp, ], fail_silently=False)
            mail.is_sent = 1
            mail.sent_at = datetime.datetime.now()
            mail.save()
        except:
            logging.error("error sending message:%s" % str(mail.id))
            mail.is_sent = 0
            mail.save()

        time.sleep(1)

    return HttpResponse("sent!")
