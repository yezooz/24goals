# coding=utf-8
import os
import urlparse
import re

from django import newforms as forms
from django.db.models import Q
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, Http404
from django.conf import settings
from django.template import RequestContext
from django.utils.translation import ugettext as _

from myscore.main.models import *
import sys
import myscore.libs.helpers as helpers
from myscore.main.modules import menu
import myscore.main.helpers.league_tables as league_tables
from myscore.main.modules.matches import league_table, last_matches


# TODO: move matches to model
def index(request, country_name=None, league_name=None, status_name=None, match_date=None):
    only_todays = True
    only_future = False
    matches = Matches.objects

    picks = Picks.objects.filter(user=request.user).select_related()

    if match_date:
        matches = matches.filter(match_date=match_date)

        if league_name:
            league_id = helpers.reveal_league_name(league_name)
            matches = matches.filter(league__id=league_id, status__in=['o', 'f', 'd'])
    else:
        if league_name:
            league_id = helpers.reveal_league_name(league_name)
            matches = matches.filter(league__id=league_id, status__in=['o', 'f', 'd'])

        today_matches = matches.filter(match_date=datetime.date.today())
        count = today_matches.count()
        if count <= 5:
            matches = matches.filter(match_date__gte=datetime.date.today())

            only_todays = False
            if count == 0:
                only_future = True
        else:
            only_todays = True
            matches = today_matches

    if status_name:
        status = helpers.reveal_status_name(status_name)
        if status:
            matches = matches.filter(status=status)

    if league_name:
        league_id = helpers.reveal_league_name(league_name)
        league_name2 = league_name.replace("-", " ")

        if not match_date:
            matches = matches.order_by("match_date", "match_time")[:12]

        return render_to_response('matches/index_with_table.html', {
            'matches': matches,
            'picks': picks,
            'status_name': status_name,
            'league_name': league_name,
            'league_name2': league_name2,
            'match_date': match_date,
            'league_table': league_table.render(league_id),
            'menu': menu.render(request, 'matches', 'index', {'status_name': status_name, 'league_name': league_name},
                                False), }, context_instance=RequestContext(request))

    matches = matches.filter(status__in=['o', 'f', 'd'])
    if match_date:
        matches = matches.order_by("league", "match_date", "match_time")
    else:
        if not only_todays:
            matches = matches.order_by("match_date", "league", "match_time")[:20]
        else:
            matches = matches.order_by("match_date", "league", "match_time")

    return render_to_response('matches/index.html', {
        'matches': matches,
        'picks': picks,
        'status_name': status_name,
        'league_name': league_name,
        'match_date': match_date,
        'only_todays': only_todays,
        'only_future': only_future,
        'menu': menu.render(request, 'matches', 'index',
                            {'status_name': status_name, 'league_name': league_name, 'today': match_date}, False),
    }, context_instance=RequestContext(request))


def details(request, home_team, away_team, match_id, show_full=None):
    try:
        match = Matches.objects.get(pk=match_id)
        league = Leagues.objects.get(pk=match.league.id)
        squads = MatchSquad.objects.filter(match=match)
    except:
        raise Http404

    if match.status == "o":
        return render_to_response('matches/details_before.html', {
            'match': match,
            'league_table': league_table.render(league.id, match.home_team_id, match.away_team_id),
            'squads': squads,
            'last5_home': last_matches.render_team(match.home_team.id, 5, True),
            'last5_away': last_matches.render_team(match.away_team.id, 5, True),
            'menu': menu.render(request, 'matches', 'details', {'match_id': match_id}, True),
        }, context_instance=RequestContext(request))

    else:
        template = 'matches/details.html'
        if show_full == "images":
            template = 'matches/show_images.html'
        elif show_full == "videos":
            template = 'matches/show_videos.html'
        elif show_full == "comments":
            template = 'matches/show_comments.html'
        elif show_full == "analysis":
            template = 'matches/show_analysis.html'

        return render_to_response(template, {
            'match': match,
            'squads': squads,
            'menu': menu.render(request, 'matches', 'details', {'match_id': match_id}, True),
        }, context_instance=RequestContext(request))


def image_upload(request, match_id):
    def process_image(photo):
        img = ImageProcessing()

        new_img_S = img.rescale(photo, 120, 80, False)
        new_img_M = img.rescale(photo, 410, 230, False)
        new_img_L = img.rescale(photo, 635, 235, False)

        return (new_img_S, new_img_M, new_img_L)

    content_type = photo_data.get('content-type')
    if content_type:
        main, sub = content_type.split('/')
        if not (main == 'image' and sub in ['jpeg', 'gif', 'png']):
            pass

    if 'photo' in request.FILES:
        error = False

        try:
            img = Image.open(StringIO(request.FILES['photo']['content']))
            request.FILES['photo']['dimensions'] = img.size
        except:
            error = True

        post = request.POST.copy()
        post.update(request.FILES)

        if form.is_valid():
            i = Images(name=cleaned_data['name'], user_id=1, dst="match", dst_id=match_id, is_processed=1,
                       ip=request.META['REMOTE_ADDR'], browser=request.META['HTTP_USER_AGENT'])

        if cleaned_data['photo']:
            photo = cleaned_data['photo']

            splitname = os.path.splitext(photo['filename'])
            filename = splitname[0] + "_0" + splitname[1]
            i.save_image_file(filename, photo['content'])

            img_L, img_M, img_S = process_image(photo['content'])
            filename_L = splitname[0] + "_1" + splitname[1]
            filename_M = splitname[0] + "_2" + splitname[1]
            filename_S = splitname[0] + "_3" + splitname[1]

            # 635x235
            fL = open(settings.MEDIA_ROOT + "tests/images/" + filename_L, "w+")
            fL.writelines(img_L)
            i = Images(name=cleaned_data['name'], user_id=1, dst="match", dst_id=match_id, is_processed=1,
                       ip=request.META['REMOTE_ADDR'], browser=request.META['HTTP_USER_AGENT'])
            i.save_image_file(filename_L, img_L)
            fL.close()

            # 410x230
            fM = open(settings.MEDIA_ROOT + "tests/images/" + filename_M, "w+")
            fM.writelines(img_M)
            i = Images(name=cleaned_data['name'], user_id=1, dst="match", dst_id=match_id, is_processed=1,
                       ip=request.META['REMOTE_ADDR'], browser=request.META['HTTP_USER_AGENT'])
            i.save_image_file(filename_M, img_M)
            fM.close()

            # 120x80
            fS = open(settings.MEDIA_ROOT + "tests/images/" + filename_S, "w+")
            fS.writelines(img_S)
            i = Images(name=cleaned_data['name'], user_id=1, dst="match", dst_id=match_id, is_processed=1,
                       ip=request.META['REMOTE_ADDR'], browser=request.META['HTTP_USER_AGENT'])
            i.save_image_file(filename_S, img_S)
            fS.close()


def url_upload(url, match_id, user_id):
    # not empty
    if url == "":
        return
    # validate
    img_name = re.search("http:\/\/(.*)\.(jpg|jpeg|png|gif|tiff|bmp)", url)
    if not img_name:
        return

    img = Images()
    img.name = "nazwa"
    img.description = ""
    img.dst = "match"
    img.dst_id = match_id
    img.link = url
    img.user = user_id
    img.username = ''
    img.is_processed = 1
    img.save()


def add_photos(request, match_id, step=None):
    if not step:
        step = "step_1"

    try:
        match = Matches.objects.get(pk=match_id)
    except:
        raise Http404
    if request.POST:
        post = request.POST.copy()
        template = "matches/add_images.html"
        if post.has_key('how'):
            step = "step_2"
            template = "matches/add_images_%s.html" % post["how"]

        if post.has_key('photo_url_1'):
            # process images
            for i in range(1, 21):
                img = post["photo_url_" + str(i)]
                url_upload(img, match_id, request.user)

            template = "matches/added_images.html"

        return render_to_response(template, {
            'match': match,
            'photos_count': range(1, 21),
            'step': step,
            'menu': menu.render(request, 'matches', 'add_photos', {'match_id': match_id}, True),
        }, context_instance=RequestContext(request))

    return render_to_response('matches/add_images.html', {
        'match': match,
        'photos_count': range(1, 21),
        'step': step,
        'menu': menu.render(request, 'matches', 'add_photos', {'match_id': match_id}, True),
    }, context_instance=RequestContext(request))


def add_videos(request, match_id):
    class UploadVideoLinkForm(forms.Form):
        name = forms.CharField(required=False, max_length=255,
                               widget=forms.widgets.TextInput({'size': 40, 'style': 'font-size: 20pt;'}))
        description = forms.CharField(required=False, widget=forms.widgets.Textarea(
            attrs={'rows': 3, 'cols': 5, 'style': 'font-size: 13pt;'}))
        link = forms.RegexField(regex=".*", max_length=1000, required=True,
                                widget=forms.widgets.Textarea(attrs={'rows': 4, 'cols': 20}))  # to regex field

    if request.POST:
        form = UploadVideoLinkForm(request.POST)
        post = request.POST.copy()

        if form.is_valid():
            vid = Videos(content=post["link"], name=post["name"], description=post["description"], dst="match",
                         dst_id=match_id, user=request.user, ip=request.META['REMOTE_ADDR'],
                         browser=request.META['HTTP_USER_AGENT'])
            vid.save()

            try:
                match = Matches.objects.get(pk=match_id)
            except:
                raise Http404

            return render_to_response('matches/added_video.html', {
                'match': match,
                'menu': menu.render(request, 'matches', 'add_videos', {'match_id': match_id}, True)
            }, context_instance=RequestContext(request))
        else:
            try:
                match = Matches.objects.get(pk=match_id)
            except:
                raise Http404
            return render_to_response('matches/add_videos.html', {
                'form': form,
                'match': match,
                'menu': menu.render(request, 'matches', 'add_videos', {'match_id': match_id}, True),
            }, context_instance=RequestContext(request))

    form = UploadVideoLinkForm()
    try:
        match = Matches.objects.get(pk=match_id)
    except:
        raise Http404
    return render_to_response('matches/add_videos.html', {
        'form': form,
        'match': match,
        'menu': menu.render(request, 'matches', 'add_videos', {'match_id': match_id}, True),
    }, context_instance=RequestContext(request))


def add_comment(request, match_id):
    """
    Comment adding forms
    """

    post = request.POST.copy()
    post["content"] = post["comment_content_" + str(match_id)]
    post["response_to"] = post["response_to_" + str(match_id)]

    c = Comments(dst_id=match_id, dst='m', is_accepted=1, ip=request.META['REMOTE_ADDR'],
                 browser=request.META['HTTP_USER_AGENT'])
    if request.user.is_authenticated():
        c.user = request.user
        c.username = str(request.user)
    else:
        # c.user = 0
        if len(request.POST["username_" + str(match_id)]) == 0:
            request.session['flash_msg'] = {'bledy': _("Brak autora komentarza")}
            return HttpResponseRedirect(request.META["HTTP_REFERER"])

        c.username = post["username_" + str(match_id)]

    content = post["comment_content_" + str(match_id)].replace("\n", "<br />\n")

    # empty comment ?
    if len(content) < 3:
        request.session['flash_msg'] = {'bledy': _("Komentarz za krotki")}
        return HttpResponseRedirect(request.META["HTTP_REFERER"])
    # spam filter
    if re.compile('(sex|porn|cum shot|viagra|penis)').search(content) != None:
        request.session['flash_msg'] = {'bledy': _("Komentarz zawiera niedozwolone wyrazy")}
        return HttpResponseRedirect(request.META["HTTP_REFERER"])

    content = content.replace("<br />\n", "\n")
    c.content = content.replace("\n", "<br />\n")

    c.lang = settings.LANGUAGE_CODE
    c.save()  # walidacja logowania i duplikacji (o ile mozliwe)

    # increment comments_count
    try:
        tm = Matches.objects.get(pk=match_id)
    except:
        raise Http404
    if c.lang == 'pl':
        tm.comments_count_pl = tm.comments_count_pl + 1
    else:
        tm.comments_count_en = tm.comments_count_en + 1
    tm.save()

    # update
    # przydala by sie walidacja czy ID jest prawidlowe
    if post["response_to"] != "":
        c.root_id = int(post["response_to"])
    else:
        c.root_id = c.id

    c.save()  # update

    # delete cache
    # tcache.delete_key(request, urlparse.urlsplit(request.META["HTTP_REFERER"])[2])

    request.session['flash_msg'] = {'sukces': _("Dodano komentarz")}
    return HttpResponseRedirect(request.META["HTTP_REFERER"])


def add_analyse(request, match_id):
    """
    Analysis adding forms
    """

    try:
        tm = Matches.objects.get(pk=match_id)
    except:
        raise Http404
    if tm.status != "o":
        return HttpResponseRedirect(request.META["HTTP_REFERER"])

    post = request.POST.copy()

    # save as not accepted
    c = Comments(dst_id=match_id, user=request.user, dst='a', root_id=0, ip=request.META['REMOTE_ADDR'],
                 browser=request.META['HTTP_USER_AGENT'])

    content = post["analyse_content_" + str(match_id)]
    # empty comment ?
    if len(content) < 3:
        request.session['flash_msg'] = {'bledy': _('Za krotka analiza meczu')}
        return HttpResponseRedirect(request.META["HTTP_REFERER"])
    # spam filter
    if re.compile('(sex|porn|cum shot|viagra|penis)').search(content) != None:
        request.session['flash_msg'] = {'bledy': _("Analiza zawiera niedozwolone wyrazy")}
        return HttpResponseRedirect(request.META["HTTP_REFERER"])

    content = content.replace("<br />\n", "\n")
    c.content = content.replace("\n", "<br />\n")

    c.lang = settings.LANGUAGE_CODE
    c.is_accepted = 0
    c.save()  # walidacja logowania i duplikacji (o ile mozliwe)

    # delete cache
    # tcache.delete_key(request, urlparse.urlsplit(request.META["HTTP_REFERER"])[2])

    request.session['flash_msg'] = {'sukces': _('Dodano analize meczu')}
    return HttpResponseRedirect(request.META["HTTP_REFERER"])  # jezeli AJAX to bez przekierowania


def send(request):
    if request.POST:

        if request.POST.has_key("pick"):
            return picks_add(request)

        for key in request.POST.iterkeys():

            if key.startswith("add_comment_"):
                mid = key.replace("add_comment_", "")
                return add_comment(request, mid)

            if key.startswith("add_analyse_"):
                mid = key.replace("add_analyse_", "")
                return add_analyse(request, mid)

    if request.META.has_key("HTTP_REFERER"):
        request.session['flash_msg'] = {'sukces': 'Dodano typy'}
        return HttpResponseRedirect(request.META["HTTP_REFERER"])
    else:
        request.session['flash_msg'] = {'sukces': 'Dodano typy'}
        return HttpResponseRedirect("/%s/" % _('Mecze URL'))


def picks_add(request):
    homes = {}
    aways = {}
    to_rem = []

    for f, v in request.POST.iteritems():
        try:
            if f.startswith('pred_home') and v[0] != '':
                homes[f.replace('pred_home_', '')] = int(request.POST[f][-1])
            elif f.startswith('pred_away') and v[0] != '':
                aways[f.replace('pred_away_', '')] = int(request.POST[f][-1])
            elif f.startswith('pred_home') and v[0] == '':
                to_rem.append(f.replace('pred_home_', ''))
            elif f.startswith('pred_away') and v[0] == '':
                to_rem.append(f.replace('pred_away_', ''))
        except ValueError:
            pass

    to_rem = list(set(to_rem))
    for m, s in homes.iteritems():
        if aways.has_key(m) and m not in to_rem:
            try:
                try:
                    match = Matches.objects.get(pk=int(m))
                except:
                    raise Http404
                if match.status == "o":
                    p, created = Picks.objects.get_or_create(user=request.user, match=match,
                                                             defaults={'home_score': homes[m], 'away_score': aways[m]})
                    if not created:
                        p.home_score = homes[m]
                        p.away_score = aways[m]
                        p.save()
            except:
                # TODO: cos z tym zrobic
                pass

    for id in to_rem:
        Picks.objects.filter(user=request.user, match=Matches.objects.get(pk=int(id))).delete()

    if request.META.has_key("HTTP_REFERER"):
        return HttpResponseRedirect(request.META["HTTP_REFERER"])
    else:
        return HttpResponseRedirect("/{% trans 'Mecze URL' %}/")
