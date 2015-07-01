# coding=utf-8
import logging

from django import newforms as forms
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

import math
from myscore.main.models import *
import myscore.libs.helpers as helpers
from myscore.libs.slughifi import slughifi
from myscore.main.modules import menu


def index(request, cat_name, username, page_no=1, search_query=None):
    try:
        page_no = int(page_no)
    except:
        page_no = 1

    if request.POST.has_key('search_query'):
        if len(request.POST['search_query']) > 3:
            return HttpResponseRedirect("/%s/%s/%s/" % (_('filmy'), _('szukaj'), request.POST['search_query']))
        else:
            return HttpResponseRedirect("/%s/" % (_('filmy')))

    if search_query is not None:
        search_query = search_query
        vids = Videos.objects.filter(name__search=search_query)
    else:
        search_query = ''
        vids = Videos().get_videos(cat_name, username)
    vids_count = vids.count()
    print (page_no * settings.PER_PAGE) - settings.PER_PAGE
    print settings.PER_PAGE * page_no
    vids = vids[(page_no * settings.PER_PAGE) - settings.PER_PAGE:(settings.PER_PAGE * page_no) + 1]  # 21

    return render_to_response('videos/index.html', {
        'videos': vids,
        'page_no': page_no,
        'pages': int(math.ceil(vids_count / settings.PER_PAGE)) + 1,
        'vids_count': vids_count,
        'search_query': search_query,
        'cat_name': cat_name,
    }, context_instance=RequestContext(request))


def details(request, video_id, video_name):
    video = Videos.objects.get(pk=video_id)
    try:
        video_cat = VideoCategories.objects.get(pk=video.cat_id)
    except:
        Mailing().add(rcp="marek@24gole.pl", subject=u"Błędna kategoria w filmie o ID %s" % video.id,
                      content='jak w temacie...', sender="24gole <marek@24gole.pl>")
        video_cat = VideoCategories()
    # increment counter for non-staff
    if request.user.is_authenticated() and request.user.is_staff == 0:
        video.view_count += 1
        video.save()

    return render_to_response('videos/details.html', {
        'video': video,
        'video_cat': video_cat,
    }, context_instance=RequestContext(request))


def add(request, step, cat_name=None):
    def validate_cat_name(cat_name):
        if cat_name is None: return False
        if settings.LANGUAGE_CODE == 'pl':
            try:
                vc = VideoCategories.objects.get(name_pl_url=cat_name)
            except:
                return False
            return vc.id
        else:
            try:
                vc = VideoCategories.objects.get(name_en_url=cat_name)
            except:
                return False
            return vc.id

    class AddVideoForm(forms.Form):
        name = forms.CharField(min_length=5, max_length=255,
                               widget=forms.widgets.TextInput({'size': 50, 'style': 'font-size: 16pt;'}))
        content = forms.CharField(min_length=10, widget=forms.widgets.Textarea(attrs={'rows': 5, 'cols': 5}))
        # cat_name = forms.CharField(widget=forms.Select(choices=([(int(vc.id), vc.name_pl) for vc in get_categories()])))
        cat_name = forms.CharField(min_length=2)

    if step == 0:
        if settings.LANGUAGE_CODE == 'pl':
            print request.META['PATH_INFO']
            return HttpResponseRedirect(request.META['PATH_INFO'].replace('/dodaj/', '/dodaj/1/'))
        else:
            return HttpResponseRedirect(request.META['PATH_INFO'].replace('/add/', '/add/1/'))

    try:
        step = int(step)
    except:
        step = 1
    if cat_name is None or not validate_cat_name(cat_name): cat_name = None
    if step not in (1, 2, 3):
        return HttpResponseRedirect("/%s/%s/" % (_('filmy'), _('dodaj')))

    """Krok 1"""
    if step == 1:
        if request.method == 'POST':
            post = request.POST.copy()
            form = AddVideoForm(request.POST)

            if form.is_valid() == True and validate_cat_name(post['cat_name']):
                if 'add_video_id' in request.session:
                    try:
                        v = Videos.objects.get(pk=request.session.get('add_video_id'))
                        v.name = post['name']
                        v.content = post['content']
                        v.dst = 'other'
                        v.dst_id = 0
                        v.cat_id = validate_cat_name(post['cat_name'])
                        v.url = slughifi(post['name'])
                        v.is_temp = 1
                        v.username = str(request.user)
                        v.save()
                    except:
                        return HttpResponseRedirect(request.META['PATH_INFO'].replace('/1/', '/2/'))

                # Pierwsze przejscie
                else:
                    v = Videos(is_accepted=0, is_temp=1, lang=settings.LANGUAGE_CODE, url=slughifi(post['name']))
                    v.name = post['name']
                    v.content = post['content']
                    v.dst = 'other'
                    v.dst_id = 0
                    v.cat_id = validate_cat_name(post['cat_name'])
                    v.url = slughifi(post['name'])
                    v.user = request.user
                    v.username = str(request.user)
                    v.save()

                    request.session['add_video_id'] = v.id

                return HttpResponseRedirect(request.META['PATH_INFO'].replace('/1/', '/2/'))

            else:
                """Bledne dane w formularzu"""
                return render_to_response("videos/add_1.html", {
                    'form': form,
                    'path_info': request.META.get('PATH_INFO'),
                    'cat_name': cat_name,
                    'vid_cats': VideoCategories().get_categories(),
                }, context_instance=RequestContext(request))

        else:
            if 'add_video_id' in request.session:
                try:
                    v = Videos.objects.get(pk=request.session.get('add_video_id'))
                    form = AddVideoForm({'name': v.name, 'content': v.content})
                except:
                    form = AddVideoForm()
            else:
                form = AddVideoForm()

            return render_to_response('videos/add_1.html', {
                'form': form,
                'path_info': request.META.get('PATH_INFO'),
                'vid_cats': VideoCategories().get_categories(),
                'cat_name': cat_name,
            }, context_instance=RequestContext(request))

    elif step == 2:
        if 'add_video_id' in request.session:
            try:
                video = Videos.objects.get(pk=request.session.get('add_video_id'))
                if video.user != video.user:
                    del request.session['add_video_id']
                    return HttpResponseRedirect(request.META['PATH_INFO'].replace('/2/', '/1/'))
            except:
                return HttpResponseRedirect(request.META['PATH_INFO'].replace('/2/', '/1/'))

        else:
            return HttpResponseRedirect(request.META['PATH_INFO'].replace('/2/', '/1/'))

        """Wybieramy odpowiedni krok w zaleznosci od akcji usera"""
        if request.method == 'POST':
            """Zapisujemy news"""
            if request.POST.has_key('save'):
                video.is_temp = 0
                video.save()

                del request.session['add_video_id']

                Videos().inform_moderators(video.id)

                return HttpResponseRedirect("/%s/%s/" % (_('filmy'), _('dodano')))

            if request.POST.has_key('edit'):
                return HttpResponseRedirect(request.META['PATH_INFO'].replace('/2/', '/1/'))

        # GET
        else:
            return render_to_response("videos/add_%s.html" % step, {
                'video': video,
                'path_info': request.META.get('PATH_INFO'),
                'cat_name': cat_name,
                'vid_cats': VideoCategories().get_categories(),
            }, context_instance=RequestContext(request))

    elif step == 3:
        return render_to_response("videos/added.html", {
            'cat_name': cat_name,
            'vid_cats': VideoCategories().get_categories(),
        }, context_instance=RequestContext(request))
