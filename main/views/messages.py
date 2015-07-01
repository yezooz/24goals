# coding=utf-8
import logging

from django import newforms as forms
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.core.cache import cache

from myscore.main.models import Accounts, Messages


def inbox(request, friend='', page=1):
    msgs = Messages().get_in(request.user, friend, page)
    logging.info(msgs)

    return render_to_response('messages/list.html', {'messages': msgs, 'selected': 'inbox'},
                              context_instance=RequestContext(request))


def outbox(request, friend='', page=1):
    msgs = Messages().get_out(request.user, friend, page)
    logging.info(msgs)

    return render_to_response('messages/list.html', {'messages': msgs, 'selected': 'outbox'},
                              context_instance=RequestContext(request))


def spam(request, page=1):
    msgs = Messages().get_spam(request.user, page)
    logging.info(msgs)

    return render_to_response('messages/list.html', {'messages': msgs, 'selected': 'spam'},
                              context_instance=RequestContext(request))


def trash(request, page=1):
    msgs = Messages().get_deleted(request.user, page)
    logging.info(msgs)

    return render_to_response('messages/list.html', {'messages': msgs, 'selected': 'trash'},
                              context_instance=RequestContext(request))


def details(request, msg_id):
    try:
        message = Messages.objects.get(pk=msg_id)
    except:
        raise Http404  # nie ma takiej wiadomosci
    if not message.is_red:
        message.is_red = 1
        message.save()
    side = ''
    if message.to == str(request.user):
        side = 'in'

    if request.method == 'POST':
        post = request.POST.copy()
        if post.has_key('reply'):
            pass

        # spam
        elif post.has_key('spam'):
            message.mark_as_spam()
            logging.info("Oznaczono wiadomość %s jako spam" % message.id)
            request.flash.sukces = _("Oznaczono wiadomosc jako spam")

        elif post.has_key('not-spam'):
            message.mark_as_not_spam()
            logging.info("Oznaczono wiadomość %s jako nie-spam" % message.id)
            request.flash.sukces = _("Oznaczono wiadomosc jako nie spam")

        # delete
        elif post.has_key('delete'):
            message.mark_as_deleted()
            logging.info("Oznaczono wiadomość %s jako usunieta" % message.id)
            request.flash.sukces = _("Usunieto wiadomosc")

        elif post.has_key('not-delete'):
            message.mark_as_not_deleted()
            logging.info("Oznaczono wiadomość %s jako nie-usunieta" % message.id)
            request.flash.sukces = _("Przywrocono wiadomosc")

        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return render_to_response('messages/details.html', {'msg': message, 'side': side},
                              context_instance=RequestContext(request))


def send(request, username, reply_of=None):
    class SendPmForm(forms.Form):

        subject = forms.CharField()
        content = forms.CharField(widget=forms.widgets.Textarea(attrs={'rows': 4, 'cols': 20}))

    if request.method == 'POST':
        post = request.POST.copy()
        form = SendPmForm(request.POST)

        if form.is_valid() == True:
            # save as not accepted
            c = Messages(sender=request.user.id, receiver=receiver_id, subject=post['subject'], content=post['content'],
                         has_sent=True)
            c.save()  # walidacja logowania

            return HttpResponseRedirect('/messages')

        else:
            return render_to_response('messages/send.html', {'form': form.as_table()},
                                      context_instance=RequestContext(request))

    else:
        form = SendPmForm()

    return render_to_response('messages/send.html', {'form': form.as_table()}, context_instance=RequestContext(request))
