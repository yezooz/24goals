# coding=utf-8
from django.template.loader import render_to_string
from django.http import HttpResponse

from myscore.main.models import Accounts


def overlay(request, username):
    return HttpResponse(
        render_to_string('modules/ajax/accounts/overlay.html', {'acc': Accounts().get_profile(username)}),
        mimetype='text/html')
