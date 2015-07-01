# coding=utf-8
import logging
import re

from django import newforms as forms
from django.views.static import serve
from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

import datetime
from myscore.main.models import *
from myscore.main.modules import menu
import myscore.main.helpers.league_tables as league_tables

attrs_dict = {'class': 'required'}
username_re = re.compile(r'^[A-Za-z]{1,}\w*$')

# def index(request):
#   	
# 	# if not request.user.is_anonymous():
# 		# return render_to_response('accounts/dashboard.html', {}, context_instance=RequestContext(request))
# 	picks = Picks.objects.filter(user=request.user).select_related()
# 	news = News().get_news(slice_for_me=False)[:6]
# 	news2 = news[2:6]
# 	news = news[:2]
# 	# TODO: MOVE TO MODEL
# 	only_todays = True
# 	matches = Matches.objects.all()
# 	
# 	today_matches = matches.filter(match_date=datetime.date.today())
# 	count = today_matches.count()
# 	if count == 0:
# 		matches = matches.filter(match_date__gte=datetime.date.today())
# 		only_todays = False
# 	else:
# 		matches = today_matches
# 	
# 	matches = matches.filter(status__in=['o', 'd', 'f']).select_related().order_by('match_date', 'match_time')
# 	if not only_todays:
# 		matches = matches[:5]
# 
# 
# 	return render_to_response('index.html', {
# 			'matches' : matches, 
# 			'picks' : picks, 
# 			'news' : news, 
# 			'news2' : news2,  
# 			'only_todays' : only_todays, 
# 			}, context_instance=RequestContext(request))
# 

def index(request):
    top_news = News().get_news(slice_for_me=False)[:1]

    only_todays = True
    matches = Matches.objects.all()

    today_matches = matches.filter(match_date=datetime.date.today())
    count = today_matches.count()
    if count == 0:
        matches = matches.filter(match_date__gte=datetime.date.today())
        only_todays = False
    else:
        matches = today_matches

    matches = matches.filter(status__in=['o', 'd', 'f']).select_related().order_by('match_date', 'match_time')
    if not only_todays:
        matches = matches[:5]

    if not request.user.is_anonymous():
        return render_to_response('index_.html', {
            'top_news': top_news,
            'matches': matches,
            'only_todays': only_todays,
        }, context_instance=RequestContext(request))
    else:
        return render_to_response('index.html', {
            'top_news': top_news,
            'matches': matches,
            'only_todays': only_todays,
        }, context_instance=RequestContext(request))


# -----

def log_out(request):
    logout(request)
    request.session['flash_msg'] = {'sukces': _('Wylogowano.')}
    return HttpResponseRedirect("/")


def log_in(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            request.session['flash_msg'] = {'sukces': _('Logowanie powiodlo sie.')}
            return HttpResponseRedirect("/")
        else:
            request.session['flash_msg'] = {'bledy': _('Konto nieaktywne.')}
            return HttpResponseRedirect("/")
    else:
        request.session['flash_msg'] = {'bledy': _('Dane nieprawidlowe.')}
        return HttpResponseRedirect("/")


class RegistrationForm(forms.Form):
    # countries = Countries.objects.all().order_by('name_en')

    countries = []
    if settings.LANGUAGE_CODE == 'pl':
        cini = 1
        for c in Countries.objects.all().order_by('name_pl'):
            countries.append((c.id, c.name_pl))
    else:
        cini = 177
        for c in Countries.objects.all().order_by('name_en'):
            countries.append((c.id, c.name_en))

    teams = []
    if settings.LANGUAGE_CODE == 'pl':
        tini = 180
        for t in Teams.objects.filter(not_country=1).order_by('name_pl'):
            teams.append((t.id, t.name_pl))
    else:
        tini = 19
        for t in Teams.objects.filter(not_country=1).order_by('name_en'):
            teams.append((t.id, t.name_en))

    username = forms.CharField(max_length=30, widget=forms.TextInput(attrs=attrs_dict))
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=50)))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict))
    country = forms.ChoiceField(choices=(countries), initial=cini)
    team = forms.ChoiceField(choices=(teams), initial=tini)

    # tos = forms.BooleanField(widget=forms.CheckboxInput(attrs=attrs_dict))

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        if 'username' in self.cleaned_data:
            if not username_re.search(self.cleaned_data['username']):
                raise forms.ValidationError(
                    _('Usernames can only contain letters, numbers and underscores and cannot begin with number.'))
            if len(self.cleaned_data['username']) < 4:
                raise forms.ValidationError(_('Username can\'t be shorter than 4 characters.'))
            try:
                user = User.objects.get(username__exact=self.cleaned_data['username'])
            except User.DoesNotExist:
                return self.cleaned_data['username']
            raise forms.ValidationError(_('This username is already taken. Please choose another.'))

    def clean_email(self):
        """
        Validates that the email is not already	in use.
        """
        if 'email' in self.cleaned_data:
            try:
                email = User.objects.get(email__exact=self.cleaned_data['email'])
            except User.DoesNotExist:
                return self.cleaned_data['email']
            except:
                raise forms.ValidationError(_('Some else registered with this email address. Please choose another.'))
            raise forms.ValidationError(_('Some else registered with this email address. Please choose another.'))

    def clean_password2(self):
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data and self.cleaned_data['password1'] == \
                self.cleaned_data['password2']:
            return self.cleaned_data['password2']
        raise forms.ValidationError(_('You must type the same password each time'))

    def clean_country(self):
        return self.cleaned_data['country']

    def clean_team(self):
        return self.cleaned_data['team']

    # def clean_tos(self):
    # 	if self.cleaned_data.get('tos', False):
    # 		return self.cleaned_data['tos']
    # 	raise forms.ValidationError(_('You must agree to the terms to register'))


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            country = Countries.objects.get(pk=int(form.cleaned_data['country']))

            new_user = Accounts.objects.create_inactive_user(username=form.cleaned_data['username'],
                                                             password=form.cleaned_data['password2'],
                                                             email=form.cleaned_data['email'], send_email=True,
                                                             favourite_team_id=form.cleaned_data['team'],
                                                             country_id=form.cleaned_data['country'],
                                                             country_code=country.code)

            Accounts.objects.delete_expired_users()

            if settings.LANGUAGE_CODE == 'pl':
                return HttpResponseRedirect('/rejestracja/kompletna/')
            else:
                return HttpResponseRedirect('/register/completed/')

    else:
        form = RegistrationForm()

    return render_to_response('main/registration_form.html', {
        'form': form, }, context_instance=RequestContext(request))


def registered(request):
    # if has_keyrequest.META["HTTP_REFERER"].find("/rejestracja/") >= 0:
    return render_to_response('main/registered.html', {}, context_instance=RequestContext(request))


# else: return HttpResponseRedirect("/")


def activate(request, activation_key):
    activation_key = activation_key.lower()  # Normalize before trying anything with it.
    account = Accounts.objects.activate_user(activation_key)
    return render_to_response('main/activate.html', {
        'account': account,
        'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS}, context_instance=RequestContext(request))


def sitemap(request, filename):
    return serve(request, filename, document_root=settings.STATIC_DIR[0] + "/sitemaps/")
