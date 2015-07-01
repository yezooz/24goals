# coding=utf-8
import logging
from PIL import Image
import re

from django import newforms as forms
from django.db.models import Q
from django.conf import settings
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponseNotFound, Http404
from django.template import RequestContext
from django.utils.translation import ugettext as _

import math
from myscore.main.models import *
from cStringIO import StringIO
import datetime
import myscore.libs.helpers as helpers
from myscore.main.modules import menu
import myscore.main.helpers.league_tables as league_tables


def index(request, country_name=False, league_name=False, news_date=None, page_no=1, search_query=None):
    """Main NEWS page"""

    try:
        page_no = int(page_no)
    except:
        page_no = 1

    if request.POST.has_key('search_query'):
        if len(request.POST['search_query']) > 3:
            return HttpResponseRedirect("/news/%s/%s/" % (_('szukaj'), request.POST['search_query']))
        else:
            return HttpResponseRedirect('/news/')

    # get news
    if search_query is not None:
        search_query = search_query
        news = News.objects.filter(Q(caption__search=search_query) | Q(short_content__search=search_query)).filter(
            is_accepted=1, is_deleted=0, is_temp=0, lang=settings.LANGUAGE_CODE).order_by('-published_at')
    else:
        search_query = ''
        news = News().get_news(country_name=country_name, league_name=league_name, news_date=news_date, page_no=page_no,
                               slice_for_me=False)
    news_count = news.count()
    news = news[(page_no * settings.PER_PAGE) - settings.PER_PAGE:settings.PER_PAGE * page_no]

    return render_to_response('news/index.html', {
        'news': news,
        'page_no': page_no,
        'pages': int(math.ceil(news_count / settings.PER_PAGE)) + 1,
        'league_name': league_name,
        'news_date': news_date,
        'news_count': news_count,
        'menu': menu.render(request, 'news', 'index', {'today': news_date, 'league_name': league_name}, False),
        'search_query': search_query,
    }, context_instance=RequestContext(request))


def details(request, news_id, show_full=None):
    """Gets specified news"""

    news = get_object_or_404(News, pk=news_id)
    if not news.is_accepted and not request.user.is_authenticated():
        return HttpResponseRedirect("/news/")

    elif not news.is_accepted and request.user.is_authenticated() and not request.user.is_staff:
        return HttpResponseRedirect("/news/")

    else:
        # increment counter for non-staff
        if request.user.is_authenticated() and request.user.is_staff == 0:
            news.view_count += 1
            news.save()

        template = 'news/details.html'

        return render_to_response(template, {
            'news': news,
            'menu': menu.render(request, 'news', 'index', {'today': news.published_at.date()}, False),
        }, context_instance=RequestContext(request))


def add(request, step):
    """News adding forms"""

    if step not in ('1', '2', '3'):
        return HttpResponseRedirect("1/")

    """Krok 1"""
    if step == '1':

        class AddNewsForm(forms.Form):
            caption = forms.CharField(min_length=5, max_length=255,
                                      widget=forms.widgets.TextInput({'size': 40, 'style': 'font-size: 16pt;'}))
            content = forms.CharField(min_length=30, widget=forms.widgets.Textarea(attrs={'rows': 10, 'cols': 5}))
            source = forms.CharField(min_length=3, max_length=100,
                                     widget=forms.widgets.TextInput({'size': 30, 'style': 'font-size: 13pt;'}))

        if request.method == 'POST':
            post = request.POST.copy()
            form = AddNewsForm(request.POST)

            """Walidacja formularza"""
            if form.is_valid() == True:
                """Jezeli powracalismy do pierwszego kroku juz z newsem"""
                if 'add_news_id' in request.session:
                    try:
                        n = News.objects.get(pk=request.session.get('add_news_id'))
                        n.caption = post['caption']
                        n.short_content = post['content']
                        n.source = post['source']
                        n.league_id = post['related_league_id']
                        n.assign_league_logo_id = post['related_league_id']
                        n.is_temp = 1
                        n.save()
                    except:
                        return HttpResponseRedirect("%s../1" % request.META['PATH_INFO'])

                # Pierwsze przejscie
                else:
                    n = News(caption=post['caption'], short_content=post['content'], source=post['source'],
                             user=request.user, is_accepted=0, is_temp=1, lang=settings.LANGUAGE_CODE)
                    n.save()

                    request.session['add_news_id'] = n.id

                return HttpResponseRedirect("%s../2" % request.META['PATH_INFO'])
            else:
                """Bledne dane w formularzu"""

                leagues = [(0, _('Wybierz z listy') + ' ...')]
                for l in Leagues().get_leagues_list():
                    if settings.LANGUAGE_CODE == 'pl':
                        leagues.append((l.id, "%s" % l.name_pl))
                    else:
                        leagues.append((l.id, "%s" % l.name_en))

                return render_to_response("news/add_%s.html" % step, {
                    'form': form,
                    'leagues': leagues,
                }, context_instance=RequestContext(request))
        # GET
        else:
            leagues = [(0, _('Wybierz z listy') + ' ...')]
            for l in Leagues().get_leagues_list():
                if settings.LANGUAGE_CODE == 'pl':
                    leagues.append((l.id, "%s" % l.name_pl))
                else:
                    leagues.append((l.id, "%s" % l.name_en))

            """Jezeli wracamy do pierwszego kroku juz z newsem"""
            if 'add_news_id' in request.session:
                try:
                    news = News.objects.get(pk=request.session.get('add_news_id'))
                    if news.user != request.user:
                        del request.session['add_news_id']
                        return HttpResponseRedirect("%s../1" % request.META['PATH_INFO'])
                except:
                    return HttpResponseRedirect("%s../1" % request.META['PATH_INFO'])

                """Zapisujemy zaktualizowane dane"""
                form = AddNewsForm({'caption': news.caption, 'content': news.short_content.replace("<br />", ""),
                                    'source': news.source})
                return render_to_response("news/add_%s.html" % step, {
                    'form': form,
                    'news': news,
                    'path_info': request.META.get('PATH_INFO'),
                    'leagues': leagues,
                }, context_instance=RequestContext(request))

            # Calkowicie nowa sesja
            else:
                form = AddNewsForm()
                return render_to_response("news/add_%s.html" % step, {
                    'form': form,
                    'path_info': request.META.get('PATH_INFO'),
                    'leagues': leagues,
                }, context_instance=RequestContext(request))

    """Krok 2"""
    if step == '2':
        """Sprawdzamy czy na pewno mamy klucz w sesji i kilka innych rzeczy"""
        if 'add_news_id' in request.session:
            try:
                news = News.objects.get(pk=request.session.get('add_news_id'))
                if news.user != request.user:
                    del request.session['add_news_id']
                    return HttpResponseRedirect("%s../1" % request.META['PATH_INFO'])
            except:
                return HttpResponseRedirect("%s../1" % request.META['PATH_INFO'])

        else:
            return HttpResponseRedirect("%s../1" % request.META['PATH_INFO'])

        """Wybieramy odpowiedni krok w zaleznosci od akcji usera"""
        if request.method == 'POST':
            """Zapisujemy news"""
            if request.POST.has_key('save'):
                news.is_temp = 0
                news.save()

                return HttpResponseRedirect("%s../3" % request.META['PATH_INFO'])

            if request.POST.has_key('edit'):
                return HttpResponseRedirect("%s../1" % request.META['PATH_INFO'])

        # GET
        else:
            return render_to_response("news/add_%s.html" % step, {
                'news': news,
                'path_info': request.META.get('PATH_INFO'),
            }, context_instance=RequestContext(request))

    """Krok 3"""
    if step == '3':
        """Sprawdzamy czy na pewno mamy klucz w sesji i kilka innych rzeczy"""
        if 'add_news_id' in request.session:
            news = News.objects.get(pk=request.session.get('add_news_id'))
            if news.user != request.user:
                del request.session['add_news_id']
                return HttpResponseRedirect("%s../1" % request.META['PATH_INFO'])

            News().inform_moderators(news.id)
            del request.session['add_news_id']
            return render_to_response("news/add_%s.html" % step, {
                'news': news,
                'path_info': request.META.get('PATH_INFO'),
            }, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect("%s../1" % request.META['PATH_INFO'])

        # return render_to_response("news/add_%s.html" % step, {}, context_instance=RequestContext(request))


def image_upload(request, news_id):
    def process_image(photo):
        img = ImageProcessing()

        new_img_S = img.rescale(photo, 120, 80, False)
        new_img_M = img.rescale(photo, 410, 230, False)
        new_img_L = img.rescale(photo, 635, 235, False)

        return (new_img_S, new_img_M, new_img_L)

    class UploadForm(forms.Form):
        name = forms.CharField(max_length=30, required=True, label='Name of the image')
        photo = forms.Field(widget=forms.FileInput, required=False, label='Photo',
                            help_text='Upload an image (max %s kilobytes)' % settings.MAX_PHOTO_UPLOAD_SIZE)

        # methods
        def clean_photo(self):
            if self.cleaned_data.get('photo'):
                photo_data = self.cleaned_data['photo']
                if 'error' in photo_data:
                    raise forms.ValidationError(
                        _('Upload a valid image. The file you uploaded was either not an image or a corrupted image.'))

                content_type = photo_data.get('content-type')
                if content_type:
                    main, sub = content_type.split('/')
                    if not (main == 'image' and sub in ['jpeg', 'gif', 'png']):
                        raise forms.ValidationError(_('JPEG, PNG, GIF only.'))

                size = len(photo_data['content'])
                if size > settings.MAX_PHOTO_UPLOAD_SIZE * 1024:
                    raise forms.ValidationError(_('Image too big'))

                width, height = photo_data['dimensions']
                if width > settings.MAX_PHOTO_WIDTH:
                    raise forms.ValidationError(_('Max width is %s' % settings.MAX_PHOTO_WIDTH))
                if height > settings.MAX_PHOTO_HEIGHT:
                    raise forms.ValidationError(_('Max height is %s' % settings.MAX_PHOTO_HEIGHT))
            else:
                raise forms.ValidationError('Select image first')

            return self.cleaned_data['photo']

    if request.method == 'POST':
        # hack to trigger validation even with file upload

        if 'photo' in request.FILES:

            try:
                img = Image.open(StringIO(request.FILES['photo']['content']))
                request.FILES['photo']['dimensions'] = img.size
            except:
                request.FILES['photo']['error'] = True

            new_data = request.POST.copy()
            new_data.update(request.FILES)

            form = UploadForm(new_data)

            if form.is_valid():
                cleaned_data = form.cleaned_data
                i = Images(name=cleaned_data['name'], user_id=1, dst="news", dst_id=news_id, is_processed=1,
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
                i = Images(name=cleaned_data['name'], user_id=1, dst="news", dst_id=news_id, is_processed=1,
                           ip=request.META['REMOTE_ADDR'], browser=request.META['HTTP_USER_AGENT'])
                i.save_image_file(filename_L, img_L)
                fL.close()

                # 410x230
                fM = open(settings.MEDIA_ROOT + "tests/images/" + filename_M, "w+")
                fM.writelines(img_M)
                i = Images(name=cleaned_data['name'], user_id=1, dst="news", dst_id=news_id, is_processed=1,
                           ip=request.META['REMOTE_ADDR'], browser=request.META['HTTP_USER_AGENT'])
                i.save_image_file(filename_M, img_M)
                fM.close()

                # 120x80
                fS = open(settings.MEDIA_ROOT + "tests/images/" + filename_S, "w+")
                fS.writelines(img_S)
                i = Images(name=cleaned_data['name'], user_id=1, dst="news", dst_id=news_id, is_processed=1,
                           ip=request.META['REMOTE_ADDR'], browser=request.META['HTTP_USER_AGENT'])
                i.save_image_file(filename_S, img_S)
                fS.close()

    form = UploadForm()
    return render_to_response('news/image_upload.html', {
        'form': form.as_table(),
    }, context_instance=RequestContext(request))


def url_upload(request, url, news_id, user_id):
    # not empty
    if url == "":
        return
    # validate
    img_name = re.search("http:\/\/(.*)\.(jpg|jpeg|png|gif|tiff|bmp)", url)
    if not img_name:
        return

    img = Images(ip=request.META['REMOTE_ADDR'], browser=request.META['HTTP_USER_AGENT'])
    img.name = "nazwa"
    img.description = ""
    img.dst = "news"
    img.dst_id = news_id
    img.link = url
    img.user = user_id
    img.username = ''
    img.is_processed = 1
    img.save()


def add_photos(request, news_id, step=None):
    if not step:
        step = "step_1"

    try:
        news = News.objects.get(pk=news_id)
    except:
        raise Http404
    if request.POST:
        post = request.POST.copy()
        template = "news/add_images.html"
        if post.has_key('how'):
            step = "step_2"
            template = "news/add_images_%s.html" % post["how"]

        if post.has_key('photo_url_1'):
            # process images
            for i in range(1, 21):
                img = post["photo_url_" + str(i)]
                url_upload(request, img, news_id, request.user)

            template = "news/added_images.html"

        return render_to_response(template, {
            'news': news,
            'photos_count': range(1, 21),
            'step': step,
        }, context_instance=RequestContext(request))

    return render_to_response('news/add_images.html', {
        'news': news,
        'photos_count': range(1, 21),
        'step': step,
    }, context_instance=RequestContext(request))


def add_videos(request, news_id):
    try:
        news = News.objects.get(pk=news_id)
    except:
        raise Http404

    class UploadVideoLinkForm(forms.Form):
        name = forms.CharField(required=False, max_length=255,
                               widget=forms.widgets.TextInput({'size': 40, 'style': 'font-size: 20pt;'}))
        description = forms.CharField(required=False, widget=forms.widgets.Textarea(
            attrs={'rows': 2, 'cols': 5, 'style': 'font-size: 13pt;'}))
        link = forms.RegexField(regex=".*", max_length=500, required=True,
                                widget=forms.widgets.Textarea(attrs={'rows': 4, 'cols': 20}))  # to regex field

    if request.POST:
        form = UploadVideoLinkForm(request.POST)
        post = request.POST.copy()

        if form.is_valid():
            vid = Videos(content=post["link"], name=post["name"], description=post["description"], dst="news",
                         dst_id=news_id, user=request.user, ip=request.META['REMOTE_ADDR'],
                         browser=request.META['HTTP_USER_AGENT'])
            vid.save()

            return render_to_response('news/added_video.html', {
                'news': news,
            }, context_instance=RequestContext(request))
        else:
            return render_to_response('news/add_videos.html', {
                'form': form,
                'news': news,
            }, context_instance=RequestContext(request))

    form = UploadVideoLinkForm()
    return render_to_response('news/add_videos.html', {
        'form': form,
        'news': news,
    }, context_instance=RequestContext(request))


def add_comment(request, news_id):
    """
    Comment adding forms
    """

    class AddCommentForm(forms.Form):
        content = forms.CharField(min_length=3, widget=forms.widgets.Textarea(attrs={'rows': 4, 'cols': 20}))
        response_to = forms.CharField(required=False, widget=forms.widgets.HiddenInput())

    if request.POST.has_key('content'):

        form = AddCommentForm(request.POST)
        if form.is_valid() == True:
            # save as not accepted
            c = Comments(dst_id=news_id, dst='n', is_accepted=1, ip=request.META['REMOTE_ADDR'],
                         browser=request.META['HTTP_USER_AGENT'])

            content = request.POST['content']
            # empty comment ?
            if len(content) < 3:
                request.session['flash_msg'] = {'bledy': _("Komentarz za krotki")}
                return HttpResponseRedirect(request.META["HTTP_REFERER"])
            # spam filter
            if re.compile(
                    '(sex|porn|cum shot|viagra|penis|kurwa|kurwy|jebany|jebani|kutas|chuje|huje|jebac|szmaty)').search(
                    content) != None:
                request.session['flash_msg'] = {'bledy': _("Komentarz zawiera niedozwolone wyrazy")}
                return HttpResponseRedirect(request.META["HTTP_REFERER"])

            content = content.replace("<br />\n", "\n")
            c.content = content.replace("\n", "<br />\n")

            if request.user.is_authenticated():
                c.user = request.user
                c.username = str(request.user)
            else:
                c.user = 0
                if len(request.POST["username"]) == 3:
                    request.session['flash_msg'] = {'bledy': _("Brak autora komentarza")}
                    return HttpResponseRedirect(request.META["HTTP_REFERER"])
                c.username = request.POST["username"]

            c.lang = settings.LANGUAGE_CODE
            c.save()  # walidacja logowania i duplikacji (o ile mozliwe)

            # update
            if request.POST.has_key('response_to'):
                # przydala by sie walidacja czy ID jest prawidlowe
                if request.POST['response_to'] != "":
                    c.root_id = int(request.POST['response_to'])
                else:
                    c.root_id = c.id
            else:
                c.root_id = c.id

            c.save()  # update

            # increment comments_count
            tn = News.objects.get(pk=news_id)
            if c.lang == 'pl':
                tn.comments_count_pl = tn.comments_count_pl + 1
            else:
                tn.comments_count_en = tn.comments_count_en + 1
            tn.save()

            # usun i utworz cache
            request.session['flash_msg'] = {'sukces': _("Dodano komentarz")}
            return HttpResponseRedirect(request.META["HTTP_REFERER"])  # jezeli AJAX to bez przekierowania

    else:
        pass

    request.session['flash_msg'] = {'sukces': _("Dodano komentarz")}
    if request.META.has_key('HTTP_REFERER'):
        return HttpResponseRedirect(request.META["HTTP_REFERER"])
    else:
        return HttpResponseRedirect('/')
