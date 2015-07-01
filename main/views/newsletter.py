# coding=utf-8
from django import newforms as forms
from django.shortcuts import render_to_response
from django.template import RequestContext

from myscore.main.models import *


def add(request):
    class AddNewsLetterForm(forms.Form):
        email = forms.EmailField(min_length=5, max_length=255,
                                 widget=forms.widgets.TextInput({'size': 30, 'style': 'font-size: 16pt;'}))

    if request.method == 'POST':
        post = request.POST.copy()
        form = AddNewsLetterForm(request.POST)

        if form.is_valid() == True:
            n = Newsletter(email=post['email'], ip=request.META['REMOTE_ADDR'])
            n.save()

        else:
            return render_to_response('news/add.html', {'form': form}, context_instance=RequestContext(request))
    else:
        form = AddNewsLetterForm()
        return render_to_response('newsletter/add.html', {'form': form}, context_instance=RequestContext(request))

    return render_to_response('newsletter/added.html', {}, context_instance=RequestContext(request))
