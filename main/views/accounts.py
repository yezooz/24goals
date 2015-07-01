# coding=utf-8
import logging

from django import newforms as forms
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import loader, Context
from django.core.mail import send_mail
from django.template import RequestContext
from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.cache import cache
from django.db import connection

from time import strptime
from myscore.main.models import *
from myscore.main.modules import menu
import myscore.main.helpers.league_tables as league_tables


def my_profile(request):
    """show current user's profile"""

    if request.user.is_anonymous():
        return HttpResponseRedirect("/")

    # TODO: naprawić to
    def check_passwords(old_pass, new_pass1, new_pass2, user):
        if old_pass and user.check_password(old_pass):

            if new_pass1 == new_pass2:
                user.set_password(new_pass1)
                return True
            else:
                return False
        else:
            return False

    def thumbnail_string(buf, size=(80, 80)):
        from StringIO import StringIO
        from PIL import Image

        f = StringIO(buf)
        image = Image.open(f)
        if image.mode not in ('L', 'RGB'):
            image = image.convert('RGB')
        image = image.resize(size, Image.ANTIALIAS)
        o = StringIO()
        image.save(o, "JPEG")
        return o.getvalue()

    def check_avatar(value):
        from StringIO import StringIO
        from PIL import Image

        if 'content-type' in value:
            main, sub = value['content-type'].split('/')
            if not (main == 'image' and sub in ['jpeg', 'gif', 'png']):
                request.session['flash_msg'] = {'bledy': _('JPEG, PNG, GIF only.')}
        try:
            img = Image.open(StringIO(value['content']))
            x, y = img.size
        except:
            request.session['flash_msg'] = {
            'bledy': _('Upload a valid image. The file you uploaded was either not an image or a corrupted image.')}
            return {}

        if x > 800 or y > 600:
            request.session['flash_msg'] = {'bledy': _('Upload a valid image. This one is too big in size.')}
        if x > 80 and y > 80:
            img = Image.open(StringIO(thumbnail_string(value['content'])))

        return img

    try:
        acc = Accounts.objects.get(pk=request.user.id)
    except:
        raise Http404

    # CHANGE PASSWORD
    post = request.POST.copy()
    if request.method == 'POST' and "change_pass" in post:
        if check_passwords(post['old_pass'], post['pass1'], post['pass2'], request.user):
            request.session['flash_msg'] = {'sukces': 'Hasło zostało zmienione'}
        else:
            request.session['flash_msg'] = {'bledy': 'Podane hasła są niepoprawne'}

        return HttpResponseRedirect(request.META['PATH_INFO'])

    # CHANGE AVATAR
    if request.method == 'POST' and "avatar" in request.FILES:
        from StringIO import StringIO
        from PIL import Image

        image = check_avatar(request.FILES['avatar'])
        if type(image) != type({}):
            # needed to save GIF format to jpeg
            image = image.convert("RGB")
            # Save the avatar as a jpeg
            avatar_path = '%simages/avatars/avatar_%s.jpg' % (settings.MEDIA_ROOT, request.user.id)
            image.save(avatar_path, 'jpeg')

            request.session['flash_msg'] = {'sukces': 'Zaktualizowano awatar'}
        # Save avatar path in profile

        return HttpResponseRedirect(request.META['PATH_INFO'])

    # EDIT PROFILE DATA
    if request.method == 'POST' and "change_profile" in post:
        post = request.POST.copy()

        acc.msn = post['im_msn']
        acc.skype = post['im_skype']
        acc.jabber = post['im_jabber']
        acc.gg = post['im_gg']
        acc.yahoo = post['im_yahoo']
        acc.icq = post['im_icq']
        acc.about_me = post['about_me']
        acc.www = post['www']
        acc.save()

        request.session['flash_msg'] = {'sukces': _('Zaktualizowano profil')}
        return HttpResponseRedirect(request.META['PATH_INFO'])

    return render_to_response("accounts/my_profile.html", {
        'account': acc,
        'teams': Teams.objects.filter(not_country=1).order_by('name_pl'),
        'countries': Countries.objects.all().order_by('name_en'),
        'menu': menu.render(request, 'users', 'index', {}, True), }, context_instance=RequestContext(request))


def details(request, username):
    """show someone's profile"""
    return details_picks(request, username, 'all')


def details_picks(request, username, range):
    weekdays = (_('Sa'), _('Su'), _('Mo'), _('Tu'), _('We'), _('Th'), _('Fr'))
    months = (
    _('January'), _('February'), _('March'), _('April'), _('May'), _('June'), _('July'), _('August'), _('September'),
    _('October'), _('November'), _('December'))

    # caching
    if username == request.user or (not request.user.is_anonymous() and request.user.is_staff):
        key = "username_%s_picks_%s_all_lang_%s" % (username, range, settings.LANGUAGE_CODE)
    else:
        key = "username_%s_picks_%s_lang_%s" % (username, range, settings.LANGUAGE_CODE)
    # c = cache.get(key)
    # if c is not None:
    # return HttpResponse(c)

    try:
        user = User.objects.get(username=username)
    except:
        raise Http404

    condition = ""
    if range == "all" and (user == request.user or (not request.user.is_anonymous() and request.user.is_staff)):
        condition = "AND m.status IN ('f', 'd', 'o')"
    elif range == "all":
        condition = "AND p.is_calculated = 1 AND m.status IN ('f')"
    elif range == "archive":
        condition = "AND p.is_calculated = 1 AND m.status IN ('f')"
    elif range == "pending" and (user == request.user or (not request.user.is_anonymous() and request.user.is_staff)):
        condition = "AND p.is_calculated = 0 AND m.status IN ('f', 'd', 'o')"

    if request.GET.has_key('date'):
        selected_date = request.GET['date'].split('-')
        picks = Picks().get_user_picks(user.id, condition=condition,
                                       date=datetime.date(*strptime(request.GET['date'], "%Y-%m-%d")[0:3]))
    else:
        selected_date = ('a', 'b', 'c')
        picks = Picks().get_user_picks(user.id, condition=condition)

    # rozne menu w zaleznosci gdzie jestesmy
    if str(request.user) == str(username):
        who = 'user'
    else:
        who = 'users'

    ret = render_to_string("accounts/details_picks.html", {
        'selected_date': selected_date,
        'range': range,
        'show_user': user,
        'picks': picks,
        'menu': menu.render(request, who, 'details_picks', {'username': username}, False),
        'weekdays': weekdays,
        'months': months,
    }, context_instance=RequestContext(request)),
    cache.set(key, ret)

    return HttpResponse(ret)


def details_classification(request, username, range, limit):
    # caching
    if username == request.user or (not request.user.is_anonymous() and request.user.is_staff):
        key = "username_%s_classification_%s_all_lang_%s" % (username, range, settings.LANGUAGE_CODE)
    else:
        key = "username_%s_classification_%s_lang_%s" % (username, range, settings.LANGUAGE_CODE)
    # c = cache.get(key)
    # if c is not None:
    # return HttpResponse(c)

    try:
        user = User.objects.get(username=username)
    except:
        raise Http404

    if range == 'all':
        table_type = 'o'
    elif range == 'month':
        table_type = 'm'
    else:
        table_type = 'o'

    tables = {}
    leagues = [league for league in Leagues().get_leagues_list()]
    leagues.insert(0, 0)

    # --- queries ---
    for league in leagues:
        if league == 0:
            league_id = 0
            league_name_en = ''
            league_name_pl = ''
        else:
            league_id = league.id
            league_name_en = league.name_en
            league_name_pl = league.name_pl

        tables[str(league_id)] = []

        sql = """
			SELECT 
				position, points, date
			FROM
				accounts_table
			WHERE
				table_type = '%s' AND
				league_id = %s AND
				season_id = %s AND
				username = '%s'
			ORDER BY
				date DESC
		""" % (table_type, league_id, settings.CURRENT_SEASON_ID, str(username))

        logging.debug(sql)

        cursor = connection.cursor()
        cursor.execute(sql)

        row = cursor.fetchone()
        if row is not None and row[0] is not None:
            position = row[0]
            last_date = row[2]

            if position <= limit:
                q_limit = "5"
            else:
                q_limit = "4"
        else:
            position = 0
            q_limit = "4"
            sql = "SELECT MAX(date) FROM accounts_table WHERE table_type = '%s' AND	league_id = %s AND season_id = %s" % (
            table_type, league_id, settings.CURRENT_SEASON_ID)
            logging.debug(sql)

            cursor = connection.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            last_date = row[0]

        sql = """
			SELECT 
				username, position, points, picked, six, four, three, one, zero, minus_one, avg, prev_week, prev_month
			FROM
				accounts_table
			WHERE
				table_type = '%s' AND
				league_id = %s AND
				season_id = %s AND
				date = '%s'
			ORDER BY 
				position ASC
			LIMIT %s
		""" % (table_type, league_id, settings.CURRENT_SEASON_ID, str(last_date), q_limit)

        logging.debug(sql)

        cursor = connection.cursor()
        cursor.execute(sql)

        for row in cursor.fetchall():
            acc = Accounts(username=row[0], points=row[2])
            acc.position = row[1]
            acc.picked = row[3]
            acc.six = row[4]
            acc.four = row[5]
            acc.three = row[6]
            acc.one = row[7]
            acc.zero = row[8]
            acc.minus_one = row[9]
            acc.avg = row[10]
            acc.prev_week = row[11]
            acc.prev_month = row[12]
            acc.league_name_en = league_name_en
            acc.league_name_pl = league_name_pl
            tables[str(league_id)].append(acc)

        if q_limit == "4":
            sql = """
				SELECT 
					username, position, points, picked, six, four, three, one, zero, minus_one, avg, prev_week, prev_month 
				FROM
					accounts_table
				WHERE
					table_type = '%s' AND
					league_id = %s AND
					season_id = %s AND
					username = '%s' AND
					date = '%s'
				LIMIT 1
			""" % (table_type, league_id, settings.CURRENT_SEASON_ID, str(username), str(last_date))

            logging.debug(sql)

            cursor = connection.cursor()
            cursor.execute(sql)

            row = cursor.fetchone()
            if row is not None:
                acc = Accounts(username=str(username), points=row[2])
                acc.position = row[1]
                acc.picked = row[3]
                acc.six = row[4]
                acc.four = row[5]
                acc.three = row[6]
                acc.one = row[7]
                acc.zero = row[8]
                acc.minus_one = row[9]
                acc.avg = row[10]
                acc.prev_week = row[11]
                acc.prev_month = row[12]
                acc.league_name_en = league_name_en
                acc.league_name_pl = league_name_pl
                tables[str(league_id)].append(acc)
            else:
                acc = Accounts(username=str(username), points=0)
                acc.position = False
                acc.picked = 0
                acc.six = 0
                acc.four = 0
                acc.three = 0
                acc.one = 0
                acc.zero = 0
                acc.minus_one = 0
                acc.avg = 0
                acc.prev_week = 0
                acc.prev_month = 0
                acc.league_name_en = league_name_en
                acc.league_name_pl = league_name_pl
                tables[str(league_id)].append(acc)

    # rozne menu w zaleznosci gdzie jestesmy
    if str(request.user) == str(username):
        who = 'user'
    else:
        who = 'users'

    ret = render_to_string("accounts/details_classification.html", {
        'range': range,
        'show_user': user,
        'tables': tables,
        'menu': menu.render(request, who, 'details_classification', {'username': username}, False),
    }, context_instance=RequestContext(request)),
    cache.set(key, ret)

    return HttpResponse(ret)


def details_stats(request, username):
    # caching
    key = "username_%s_stats_lang_%s" % (username, settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c is not None:
        return HttpResponse(c)

    user = Accounts().get_profile(username)
    stats = UsersTable.objects.filter(username=username, table_type='o', league_id=0)

    # rozne menu w zaleznosci gdzie jestesmy
    if str(request.user) == str(username):
        who = 'user'
    else:
        who = 'users'

    ret = render_to_string("accounts/details_stats.html", {
        'user': user,
        'stats': stats,
        'menu': menu.render(request, who, 'details_stats', {'username': username}, False),
    }, context_instance=RequestContext(request)),
    cache.set(key, ret)

    return HttpResponse(ret)


def details_activity(request, username):
    # caching
    key = "username_%s_activity_lang_%s" % (username, settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c is not None:
        return HttpResponse(c)

    user = Accounts().get_profile(username)

    # --- TROFEA ---
    sql = """
		SELECT
			t.points, t.name_en, t.name_pl, at.date
		FROM
			accounts_trophies as at
		LEFT JOIN
			trophies as t ON t.id = at.trophy_id
		WHERE
			at.username = '%s'
	""" % str(username)

    logging.debug(sql)

    cursor = connection.cursor()
    cursor.execute(sql)

    trophies = []
    trophies_points = 0
    for row in cursor.fetchall():
        trophies_points += int(row[0])
        t = Trophies(points=row[0], name_en=row[1], name_pl=row[2])
        t.date = row[3]
        trophies.append(t)

    # --- NEWSY ---
    sql = """
		SELECT
			aa.points, n.id, n.caption, n.url, n.published_at
		FROM
			accounts_activity as aa
		LEFT JOIN
			news as n ON n.id = aa.dst_id
		WHERE
			aa.is_calculated = 1 AND
			aa.action_type = 'news' AND
			aa.username = '%s'
		ORDER BY
			n.published_at DESC
	""" % str(username)

    logging.debug(sql)

    cursor = connection.cursor()
    cursor.execute(sql)

    news = []
    news_points = 0
    for row in cursor.fetchall():
        news_points += int(row[0])
        n = News(id=row[1], caption=row[2], url=row[3], published_at=row[4])
        n.points = row[0]
        news.append(n)


    # --- ZDJECIA ---
    sql = """
		SELECT
			aa.points, i.id, i.name, i.link, i.created_at
		FROM
			accounts_activity as aa
		LEFT JOIN
			images as i ON i.id = aa.dst_id
		WHERE
			aa.is_calculated = 1 AND
			(aa.action_type = 'news_image' OR aa.action_type = 'match_image') AND
			aa.username = '%s'
		ORDER BY
			i.created_at DESC
	""" % str(username)

    logging.debug(sql)

    cursor = connection.cursor()
    cursor.execute(sql)

    images = []
    images_points = 0
    for row in cursor.fetchall():
        images_points += int(row[0])
        i = Images(id=row[1], name=row[2], link=row[3], created_at=row[4])
        i.points = row[0]
        images.append(i)


    # --- FILMY ---
    sql = """
		SELECT
			aa.points, v.id, v.name, v.content, v.created_at
		FROM
			accounts_activity as aa
		LEFT JOIN
			videos as v ON v.id = aa.dst_id
		WHERE
			aa.is_calculated = 1 AND
			(aa.action_type = 'news_video' OR aa.action_type = 'match_video') AND
			aa.username = '%s'
		ORDER BY
			v.created_at DESC
	""" % str(username)

    logging.debug(sql)

    cursor = connection.cursor()
    cursor.execute(sql)

    videos = []
    videos_points = 0
    for row in cursor.fetchall():
        videos_points += int(row[0])
        v = Videos(id=row[1], name=row[2], content=row[3], created_at=row[4])
        v.points = row[0]
        videos.append(v)


    # --- PICKS ---
    sql = """
		SELECT
			SUM(aa.points), COUNT(*)
		FROM
			accounts_activity as aa
		WHERE
			aa.is_calculated = 1 AND
			aa.action_type = 'match_points' AND
			aa.username = '%s'
		ORDER BY
			aa.dst_id
	""" % str(username)

    logging.debug(sql)

    cursor = connection.cursor()
    cursor.execute(sql)
    row = cursor.fetchone()
    if row is not None and row[0] is not None:
        picks_points = row[0]
        picks_count = row[1]
    else:
        picks_points = 0
        picks_count = 0


    # rozne menu w zaleznosci gdzie jestesmy
    if str(request.user) == str(username):
        who = 'user'
    else:
        who = 'users'

    ret = render_to_string("accounts/details_activity.html", {
        'user': user,
        'stats': {
            'trophies': trophies,
            'trophies_points': trophies_points,
            'news': news,
            'news_points': news_points,
            'images': images,
            'images_points': images_points,
            'videos': videos,
            'videos_points': videos_points,
            'picks_count': picks_count,
            'picks_points': picks_points,
            'total_points': trophies_points + news_points + images_points + videos_points + picks_points
        },
        'menu': menu.render(request, who, 'details_activity', {'username': username}, False),
    }, context_instance=RequestContext(request)),
    cache.set(key, ret, 15 * 60)  # cache for 15 min

    return HttpResponse(ret)


def details_compare(request, username, other_username):
    # caching
    key = "username_%s_stats_lang_%s" % (username, settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c is not None:
        return HttpResponse(c)

    stats = UsersTable.objects.filter(username=username, table_type='o', league_id=0)

    ret = render_to_string("accounts/details_stats.html", {
        'stats': stats,
        'menu': menu.render(request, 'user', 'details_stats', {}, True),
    }, context_instance=RequestContext(request)),
    cache.set(key, ret)

    return HttpResponse(ret)


def show_users(request, letter=None):
    """display all users available to see by current user"""
    if not letter:
        letter = "a"
    users = Accounts.objects.filter(user__username__istartswith=letter, user__is_active=1).select_related().order_by(
        '-points')

    alphabet = (
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w',
    'x', 'y', 'z')
    return render_to_response("accounts/show_users.html", {
        'users': users,
        'alphabet': alphabet,
        'letter': letter,
        'menu': menu.render(request, 'users', 'index', {}, True),
    }, context_instance=RequestContext(request))


def register_user(request):
    """
    User registration
    """
    teams = []
    for t in Teams.objects.all().order_by('name_espn'):
        teams.append((t.id, t.name_espn))

    class RegisterUserForm(forms.Form):
        username = forms.CharField(min_length=3, max_length=15)
        password1 = forms.CharField(min_length=4, widget=forms.PasswordInput())
        password2 = forms.CharField(min_length=4, widget=forms.PasswordInput(), label=_('Repeat your password'))
        email = forms.EmailField()
        fav_team = forms.ChoiceField(choices=(teams))
        fav_team_other = forms.CharField(min_length=3, max_length=100)

        def clean_password1(self):
            if self.data['password1'] != self.data['password2']:
                raise forms.ValidationError(_('Passwords are not the same'))
            return self.data['password1']

        def clean_username(self):
            try:
                User.objects.get(username=self.data['username'])
                raise forms.ValidationError(_('Someone is already using this username. Please pick an other.'))
            except User.DoesNotExist:
                return self.data['username']

    if request.method == 'POST':
        post = request.POST.copy()
        form = RegisterUserForm(request.POST)

        if form.is_valid():
            u = User.objects.create_user(post['username'], post['email'], post['password1'])
            u.save()
            a = Accounts(user_id=u.id)
            a.save()

            # confirmation email
            # t = loader.get_template('email/registration.txt')
            # c = Context({
            # 'username': request.POST.get('username'),
            # 'product_name': 'Your Product Name',
            # 'product_url': 'http://www.yourproject.com/',
            # 'login_url': 'http://www.yourproject.com/login/',
            # })

            # send_mail('Rejestracja', t.render(c), 'rejestracja@w3net.pl', [post['email'],], fail_silently=False)


            return HttpResponseRedirect('accounts/registered.html')

        else:
            return render_to_response('accounts/register_user.html', {
                'form': form, }, context_instance=RequestContext(request))

    else:
        form = RegisterUserForm()
        return render_to_response('accounts/register_user.html', {
            'form': form, }, context_instance=RequestContext(request))
