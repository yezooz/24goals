# coding=utf-8
import os
import sha
import random
import re
import logging

from django.db import models
from django.contrib.auth.models import *
from django.db.models.manager import Manager
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template import Context, loader
from django.contrib.admin.views.decorators import staff_member_required

from datetime import datetime, timedelta
from time import strftime, gmtime
from myscore.main.models import *
from myscore.libs.slughifi import slughifi
import myscore.libs.helpers as helpers
import cPickle as pickle

# from libs.fulltext_search import SearchManager 

class RegistrationManager(models.Manager):
    """
    Custom manager for the RegistrationProfile model.

    The methods defined here provide shortcuts for account creation
    and activation (including generation and emailing of activation
    keys), and for cleaning out expired inactive accounts.

    """

    def activate_user(self, activation_key):
        """
        Given the activation key, makes a User's account active if the
        activation key is valid and has not expired.

        Returns the User if successful, or False if the account was
        not found or the key had expired.

        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point even trying to look it up
        # in the DB.
        if re.match('[a-f0-9]{40}', activation_key):
            try:
                user_profile = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not user_profile.activation_key_expired():
                # Account exists and has a non-expired key. Activate it.
                user = user_profile.user
                user.is_active = True
                user.save()
                return user
        return False

    def create_inactive_user(self, username, password, email, send_email=True, favourite_team_id=0, country_id=0,
                             country_code=''):
        """
        Creates a new User and a new RegistrationProfile for that
        User, generates an activation key, and mails it.

        Pass ``send_email=False`` to disable sending the email.

        """
        # Create the user.
        new_user = User.objects.create_user(username, email, password)
        new_user.is_active = False
        new_user.save()

        # Generate a salted SHA1 hash to use as a key.
        salt = sha.new(str(random.random())).hexdigest()[:5]
        activation_key = sha.new(salt + new_user.username).hexdigest()

        # And finally create the profile.
        new_profile = self.create(user=new_user, username=username, activation_key=activation_key,
                                  favourite_team_id=favourite_team_id, country_id=country_id, country_code=country_code,
                                  lang=settings.LANGUAGE_CODE)

        if send_email:
            from django.core.mail import EmailMessage

            if settings.LANGUAGE_CODE == 'pl':
                current_domain = "24gole.pl"
                subject = "Aktywuj konto w serwisie %s" % current_domain
                sender = u'24gole <marek@24gole.pl>'
                template_name = 'main/activation_email_pl.txt'
            else:
                current_domain = "24goals.com"
                subject = "Activate your account on %s" % current_domain
                sender = u'24goals <marek@24goals.com>'
                template_name = 'main/activation_email_en.txt'

            message_template = loader.get_template(template_name)
            message_context = Context({'site_url': 'http://www.%s/' % current_domain,
                                       'activation_key': activation_key,
                                       'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS})

            message = message_template.render(message_context)

            recipients = [new_user.email]
            EmailMessage(subject, message, sender, recipients).send()

        return new_user

    def delete_expired_users(self):
        """
        Removes unused profiles and their associated accounts.

        This is provided largely as a convenience for maintenance
        purposes; if a RegistrationProfile's key expires without the
        account being activated, then both the RegistrationProfile and
        the associated User become clutter in the database, and (more
        importantly) it won't be possible for anyone to ever come back
        and claim the username. For best results, set this up to run
        regularly as a cron job.

        If you have a User whose account you want to keep in the
        database even though it's inactive (say, to prevent a
        troublemaker from accessing or re-creating his account), just
        delete that User's RegistrationProfile and this method will
        leave it alone.

        """
        for profile in self.all():
            if profile.activation_key_expired():
                user = profile.user
                if not user.is_active:
                    user.delete()  # Removing the User will remove the RegistrationProfile, too.


class Accounts(models.Model):
    LANGS = (
        (0, 'any'),
        (1, 'pl'),
        (2, 'en'),
    )

    objects = RegistrationManager()

    # wszystkie niezbedne pola
    user = models.OneToOneField(User, unique=True)
    username = models.CharField(blank=True, max_length=100)
    activation_key = models.CharField(max_length=40, default=0)
    key_expires = models.DateTimeField(default=datetime.datetime.now())
    avatar = models.ImageField(upload_to="images/", blank=True, null=True)

    live_points = models.IntegerField(blank=True, null=False, default=0)
    points = models.IntegerField(blank=True, null=False, default=0)
    activity_points = models.IntegerField(blank=True, null=False, default=0)
    activity_level = models.IntegerField(blank=True, null=False,
                                         default=0)  # measure frequency of visits + other activities
    has_hidden_picks = models.BooleanField(default=False)

    favourite_team_id = models.IntegerField(blank=True, null=False, default=0)
    favourite_team_name_en = models.CharField(blank=True, max_length=100)
    favourite_team_name_pl = models.CharField(blank=True, max_length=100)
    country_id = models.IntegerField(blank=True, null=True, default=0)
    country_code = models.CharField(blank=True, max_length=2)
    lang = models.CharField(blank=True, max_length=2)

    messages_count = models.IntegerField(blank=True, null=False, default=0)
    unred_messages_count = models.IntegerField(blank=True, null=False, default=0)
    comments_count = models.IntegerField(blank=True, null=False, default=0)
    analyses_count = models.IntegerField(blank=True, null=False, default=0)
    news_count = models.IntegerField(blank=True, null=False, default=0)
    images_count = models.IntegerField(blank=True, null=False, default=0)
    videos_count = models.IntegerField(blank=True, null=False, default=0)
    referer_count = models.IntegerField(blank=True, null=False, default=0)

    topics_count = models.IntegerField(blank=True, null=True, default=0)
    posts_count = models.IntegerField(blank=True, null=True, default=0)
    chalkboard_entries_count = models.IntegerField(blank=True, null=True, default=0)

    friends = models.TextField(blank=True)

    about_me = models.CharField(max_length=255)
    msn = models.CharField(blank=True, max_length=100)
    skype = models.CharField(blank=True, max_length=100)
    jabber = models.CharField(blank=True, max_length=100)
    gg = models.CharField(blank=True, max_length=10)
    yahoo = models.CharField(blank=True, max_length=100)
    icq = models.CharField(blank=True, max_length=20)
    www = models.CharField(blank=True, max_length=100)

    ref_id = models.IntegerField(blank=True, null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    class Admin:
        list_filter = ['created_at']
        list_display = ('id', '__unicode__', 'points', 'comments_count', 'analyses_count')

    def id(self):
        return self.user.id

    def __unicode__(self):
        return self.user.username

    def activation_key_expired(self):
        expiration_date = timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.user.date_joined + expiration_date <= datetime.datetime.now()

    activation_key_expired.boolean = True

    def get_profile(self, username):

        key = "user_data_%s" % (username)
        c = cache.get(key)
        if c is not None:
            return pickle.loads(c)

        sql = """
			SELECT
				a.user_id,
				a.username,
				a.points,
				a.activity_points,
				a.has_hidden_picks,
				a.favourite_team_id,
				a.favourite_team_name_en,
				a.favourite_team_name_pl,
				a.country_id,
				a.country_code,
				a.lang,
				a.messages_count,
				a.unred_messages_count,
				a.comments_count,
				a.analyses_count,
				a.news_count,
				a.images_count,
				a.videos_count,
				a.referer_count,
				u.date_joined,
				u.is_staff,
				u.is_active,
				u.is_superuser
			FROM
				auth_user as u
			LEFT JOIN
				accounts as a ON a.user_id = u.id
			WHERE
				u.username = '%s'
		""" % username

        logging.debug(sql)

        from django.db import connection

        cursor = connection.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()

        if row is None:
            return False

        yesterday = datetime.datetime.now() + datetime.timedelta(days=-1)
        yesterday = "%d-%d-%d" % (int(yesterday.year), int(yesterday.month), int(yesterday.day))
        month_start = "%d-%d-01" % (int(datetime.date.today().year), int(datetime.date.today().month))

        sql = """
			SELECT
				ato.points,
				ato.position,
				ato.avg,
				ato.avg_position,
				ato.prev_month,
				ato.prev_month_avg,
				atm.points,
				atm.position,
				atm.avg,
				atm.avg_position,
				atm.prev_month,
				atm.prev_month_avg
			FROM
				accounts_table as ato, accounts_table as atm
			WHERE
				ato.username = '%s' AND
				ato.table_type = 'o' AND
				ato.league_id = 0 AND
				ato.season_id = %s AND
				ato.date = '%s' AND
				atm.table_type = 'm' AND
				atm.league_id = 0 AND
				atm.date = '%s' AND
				atm.season_id = %s
			LIMIT 1
		""" % (username, settings.CURRENT_SEASON_ID, yesterday, month_start, settings.CURRENT_SEASON_ID)

        logging.debug(sql)

        cursor = connection.cursor()
        cursor.execute(sql)
        row2 = cursor.fetchone()

        a = Accounts(username=row[1],
                     points=row[2],
                     activity_points=row[3],
                     has_hidden_picks=row[4],
                     favourite_team_id=row[5],
                     favourite_team_name_en=row[6],
                     favourite_team_name_pl=row[7],
                     country_id=row[8],
                     country_code=row[9],
                     lang=row[10],
                     messages_count=row[11],
                     unred_messages_count=row[12],
                     comments_count=row[13],
                     analyses_count=row[14],
                     news_count=row[15],
                     images_count=row[16],
                     videos_count=row[17],
                     referer_count=row[18]
                     )

        a.user_id = row[0]
        a.joined_at = row[19]
        a.is_staff = row[20]
        a.is_active = row[21]
        a.is_superuser = row[22]

        if row2 is not None:
            a.ato_points = row2[0]
            a.ato_position = row2[1]
            a.ato_avg = row2[2]
            a.ato_avg_position = row2[3]
            a.ato_prev_month = row2[4]
            a.ato_prev_month_avg = row2[5]
            a.atm_points = row2[6]
            a.atm_position = row2[7]
            a.atm_avg = row2[8]
            a.atm_avg_position = row2[9]
            a.atm_prev_month = row2[10]
            a.atm_prev_month_avg = row2[11]

        cache.set(key, pickle.dumps(a))
        return a

    # ---

    # SUPPORTERS

    def get_supporters(self, extra_where=""):
        # return Accounts.objects.filter(points__gt=0).order_by('-points')
        query = "SELECT a.points as points, u.username as username, t.name_en as fav, a.country_code as country_code, a.activity_points as account_points FROM accounts as a LEFT JOIN auth_user as u ON u.id = a.user_id LEFT JOIN teams as t on t.id = a.favourite_team_id LEFT JOIN leagues as l on l.id = t.current_league_id where a.points > 0 %s order by points desc" % extra_where

        logging.debug(query)

        from django.db import connection

        cursor = connection.cursor()
        cursor.execute(query)
        res = cursor.fetchall()

        return res

    def get_supporters_by_team(self, team_id):
        return Accounts.objects.filter(favourite_team_id=team_id, points__gt=0).order_by('-points')

    def get_supporters_by_league(self, league_id):
        return self.get_supporters(extra_where="and l.id = %s" % league_id)

    def get_top_overall_supporters(self):
        return self.get_supporters()

    def get_top_month_supporters(self, year_no=0, month_no=0, league_id=0):
        if year_no == 0:
            year_no = datetime.date.today().year
        if month_no == 0:
            month_no = datetime.date.today().month

        query = "SELECT at.points AS points, u.username AS username, t.name_en AS fav, a.country_code AS country_code, a.activity_points as account_points FROM accounts_table AS at LEFT JOIN accounts AS a ON at.user_id = a.user_id LEFT JOIN auth_user AS u ON at.user_id = u.id LEFT JOIN teams AS t ON t.id = a.favourite_team_id WHERE at.date = '%s-%s-01' AND at.table_type = 'm' AND at.league_id = %s AND at.season_id = %s ORDER BY at.position" % (
        year_no, month_no, league_id, settings.CURRENT_SEASON_ID)

        logging.debug(query)

        from django.db import connection

        cursor = connection.cursor()
        cursor.execute(query)
        res = cursor.fetchall()

        return res

    # SOCIAL

    def add_friend(self, friend_id):
        # TODO:
        # dodaj do tabeli Friends
        # zaktualizuj denormalized friends_list
        pass

    def remove_friend(self, friend):
        # TODO: as above
        pass


class AccountsActivity(models.Model):
    ACTIONS = (
        ('news', 'news'),
        ('news_video', 'news video'),
        ('news_image', 'news photo'),
        ('match_analysis', 'match analysis'),
        ('match_image', 'match photo'),
        ('match_video', 'match video'),
        ('match_points', 'prediction game'),
        ('referer', 'referal joined'),
        ('trophies', 'trophies points'),
        ('video', 'video'),
    )

    user_id = models.IntegerField(blank=True, null=True)
    username = models.CharField(blank=True, max_length=100)
    dst_id = models.IntegerField(blank=True, null=True)
    action_type = models.CharField(blank=True, max_length=100, choices=ACTIONS)
    points = models.IntegerField(blank=True, null=True, default=0)

    is_calculated = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(blank=True, default=datetime.datetime.now())

    class Admin:
        list_filter = ['action_type', 'is_calculated', 'is_confirmed']
        list_display = ('id', 'user_id', 'username', 'points', 'action_type', 'is_calculated', 'created_at')

    class Meta:
        db_table = 'accounts_activity'
        verbose_name = 'AccountsActivity'
        verbose_name_plural = 'AccountsActivities'

    def __unicode__(self):
        return "%s > %s" % (self.username, self.action_type)


class AccountsActivityTable(models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    username = models.CharField(blank=True, max_length=100)
    table_type = models.CharField(blank=True, max_length=1, default='o')
    league_id = models.IntegerField(blank=True, null=True, default=0)
    season_id = models.IntegerField(blank=True, null=True, default=settings.CURRENT_SEASON_ID)

    points = models.IntegerField(blank=True, null=True, default=0)
    date = models.DateField()

    class Admin: pass

    class Meta:
        db_table = 'accounts_activity_table'
        verbose_name = 'AccountsActivityTable'

    def __unicode__(self):
        return "%s > %s" % (self.username, self.action_type)


class Trophies(models.Model):
    league_id = models.IntegerField(blank=True, null=True, default=0)
    position = models.IntegerField(blank=True, null=True, max_length=2)
    points = models.IntegerField(blank=True, null=True, default=0)
    priority = models.IntegerField(blank=True, null=True, default=0)

    name_en = models.CharField(blank=True, max_length=255)
    name_pl = models.CharField(blank=True, max_length=255)
    description_en = models.TextField(blank=True)
    description_pl = models.TextField(blank=True)

    image_url = models.CharField(blank=True, max_length=255)

    class Admin:
        list_filter = ['position', 'league_id']
        list_display = ('id', 'name_en', 'name_pl', 'position', 'points', 'league_id', 'image_url')

    class Meta:
        db_table = 'trophies'
        verbose_name = 'trophy'
        verbose_name_plural = 'trophies'

    def __unicode__(self): return self.name_pl


class AccountsTrophies(models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    username = models.CharField(blank=True, max_length=100)
    trophy_id = models.IntegerField(blank=True, null=True, default=0)

    league_id = models.IntegerField(blank=True, null=True, default=0)
    season_id = models.IntegerField(blank=True, null=True, default=settings.CURRENT_SEASON_ID)
    priority = models.IntegerField(blank=True, null=True, default=0)

    date = models.DateField()

    class Admin:
        list_filter = ['league_id', 'season_id', 'trophy_id']
        list_display = ('id', 'user_id', 'username', 'trophy_id', 'league_id', 'season_id')

    class Meta:
        db_table = 'accounts_trophies'
        verbose_name = 'AccountsTrophy'
        verbose_name_plural = 'AccountsTrophies'

    def __unicode__(self):
        return "%s got trophy_id:%s" % (self.username, self.trophy_id)


class Friends(models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    friend_id = models.IntegerField(blank=True, null=True)

    class Admin: pass

    class Meta:
        db_table = 'friends'
        verbose_name = 'friend'

    def __unicode__(self):
        return "%s is friend of %s" % (self.friend_id, self.user_id)


class Groups(models.Model):
    group_id = models.IntegerField(blank=True, null=True, default=0)
    league_id = models.IntegerField(blank=True, null=True, default=0)
    owner_id = models.IntegerField(blank=True, null=True, default=0)

    name = models.CharField(blank=True, max_length=100)
    description = models.CharField(blank=True, max_length=255)
    members = models.TextField(blank=True)

    chalkboard_entries_count = models.IntegerField(blank=True, null=True, default=0)
    is_invite_only = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=True)

    class Admin: pass

    class Meta:
        db_table = 'groups'
        verbose_name = 'group'

    def __unicode__(self): return self.name

    def add_member(self, member_id):
        # TODO:
        # dodaj to tabeli Members
        # zaktualizuj co trzeba
        pass

    def remove_member(self, member_id):
        # TODO: as above
        pass


class Members(models.Model):
    group_id = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)

    is_owner = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)

    joined_at = models.DateTimeField(blank=True, default=datetime.datetime.now())

    class Admin: pass

    class Meta:
        db_table = 'group_members'
        verbose_name = 'member'

    def __unicode__(self):
        return "%s is member of group %s" % (self.user_id, self.group_id)


class Forums(models.Model):
    group_id = models.IntegerField(blank=True, null=True)

    name = models.CharField(blank=True, max_length=100)
    description = models.CharField(blank=True, max_length=255)

    members_only = models.BooleanField(default=False)
    topics_count = models.IntegerField(blank=True, null=True, default=0)
    posts_count = models.IntegerField(blank=True, null=True, default=0)

    class Admin: pass

    class Meta:
        db_table = 'forums'
        verbose_name = 'forum'

    def __unicode__(self): return self.name

    def add_topic(self): pass

    def close_topic(self): pass


class Topics(models.Model):
    forum_id = models.IntegerField(blank=True, null=True)
    group_id = models.IntegerField(blank=True, null=True)
    match_id = models.IntegerField(blank=True, null=True, default=0)
    player_id = models.IntegerField(blank=True, null=True, default=0)

    name = models.CharField(blank=True, max_length=100)
    description = models.CharField(blank=True, max_length=255)
    owner_name = models.CharField(blank=True, max_length=100)

    posts_count = models.IntegerField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    is_sticked = models.BooleanField(default=False)

    ip = models.CharField(blank=True, null=True, max_length=20, default='127.0.0.1')
    browser = models.CharField(blank=True, null=True, max_length=120, default='')
    created_at = models.DateTimeField(blank=True, default=datetime.datetime.now())

    class Admin: pass

    class Meta:
        db_table = 'topics'
        verbose_name = 'topic'

    def __unicode__(self): return self.name

    def add_post(self): pass

    def close_post(self): pass

    def stick_post(self): pass

    def unstick_post(self): pass


class Posts(models.Model):
    topic_id = models.IntegerField(blank=True, null=True)
    forum_id = models.IntegerField(blank=True, null=True)
    match_id = models.IntegerField(blank=True, null=True, default=0)
    player_id = models.IntegerField(blank=True, null=True, default=0)

    username = models.CharField(blank=True, max_length=100)
    content = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)

    ip = models.CharField(blank=True, null=True, max_length=20, default='127.0.0.1')
    browser = models.CharField(blank=True, null=True, max_length=120, default='')
    created_at = models.DateTimeField(blank=True, default=datetime.datetime.now())

    class Admin: pass

    class Meta:
        db_table = 'posts'
        verbose_name = 'post'

    def __unicode__(self): return self.username


class Chalkboards(models.Model):
    group_id = models.IntegerField(blank=True, null=True, default=0)
    user_id = models.IntegerField(blank=True, null=True, default=0)

    username = models.CharField(blank=True, max_length=100)
    title = models.CharField(blank=True, max_length=100)
    content = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)

    ip = models.CharField(blank=True, null=True, max_length=20, default='127.0.0.1')
    browser = models.CharField(blank=True, null=True, max_length=120, default='')
    created_at = models.DateTimeField(blank=True, default=datetime.datetime.now())

    class Admin: pass

    class Meta:
        db_table = 'chalkboards'
        verbose_name = 'chalkboard'

    def __unicode__(self):
        return "%s wrote %s on chalkboard" % (self.username, self.title)

    def add_entry(self, request, username, title, content): pass

    def remove_entry(self, id):    pass


class GroupNews(models.Model):
    group_id = models.IntegerField(blank=True, null=True)

    username = models.CharField(blank=True, max_length=100)
    title = models.CharField(blank=True, max_length=100)
    content = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)

    ip = models.CharField(blank=True, null=True, max_length=20, default='127.0.0.1')
    browser = models.CharField(blank=True, null=True, max_length=120, default='')
    created_at = models.DateTimeField(blank=True, default=datetime.datetime.now())

    class Admin: pass

    class Meta:
        db_table = 'group_news'
        verbose_name = 'group_news'
        verbose_name_plural = 'group_news'

    def __unicode__(self):
        return "%s wrote %s as group news" % (self.username, self.title)

    def add_entry(self, request, username, title, content): pass

    def remove_entry(self, id): pass


class UsersTable(models.Model):
    league_id = models.IntegerField(blank=True, null=True, default=0)
    season_id = models.IntegerField(blank=True, null=True, default=settings.CURRENT_SEASON_ID)
    table_type = models.CharField(blank=True, max_length=1,
                                  choices=(('o', 'overall'), ('m', 'by month'), ('w', 'by week'), ('2', '2'),),
                                  default='o')
    user = models.ForeignKey(User)
    username = models.CharField(blank=True, max_length=100)

    six = models.IntegerField(blank=True, null=True, default=0)
    four = models.IntegerField(blank=True, null=True, default=0)
    three = models.IntegerField(blank=True, null=True, default=0)
    one = models.IntegerField(blank=True, null=True, default=0)
    zero = models.IntegerField(blank=True, null=True, default=0)
    minus_one = models.IntegerField(blank=True, null=True, default=0)
    minus_five = models.IntegerField(blank=True, null=True, default=0)

    avg = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    picked = models.IntegerField(blank=True, null=True, default=0)
    points = models.IntegerField(blank=True, null=True, default=0)
    position = models.IntegerField(blank=True, null=True, default=0)
    avg_position = models.IntegerField(blank=True, null=True, default=0)
    prev_week = models.IntegerField(blank=True, null=True, default=0)
    prev_month = models.IntegerField(blank=True, null=True, default=0)
    prev_week_picks = models.IntegerField(blank=True, null=True, default=0)
    prev_month_picks = models.IntegerField(blank=True, null=True, default=0)
    prev_week_points = models.IntegerField(blank=True, null=True, default=0)
    prev_month_points = models.IntegerField(blank=True, null=True, default=0)
    prev_week_avg = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    prev_month_avg = models.DecimalField(max_digits=4, decimal_places=2, default=0)

    date = models.DateField()

    class Admin: pass

    class Meta:
        db_table = 'accounts_table'


class FansTable(models.Model):
    league_id = models.IntegerField(blank=True, null=True, default=10)
    season_id = models.IntegerField(blank=True, null=True, default=settings.CURRENT_SEASON_ID)
    table_type = models.CharField(blank=True, max_length=1,
                                  choices=(('p', 'by points'), ('a', 'by average points'), ('f', 'by fans count')),
                                  default='p')
    team = models.ForeignKey("Teams")

    fans = models.IntegerField(blank=True, null=True, default=0)
    points = models.IntegerField(blank=True, null=True, default=0)
    avg = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    position = models.IntegerField(blank=True, null=True, default=0)
    date = models.DateField(default=datetime.date.today())

    class Admin:
        pass

    class Meta:
        db_table = 'fans_table'

    # ---

    def get_current_by_points(self, team_id=0, limit=10):
        date = datetime.date.today()
        if team_id == 0:
            ft = FansTable.objects.filter(season_id=settings.CURRENT_SEASON_ID, table_type='p')
            return ft.order_by('-points')[:int(limit)]
        else:
            return FansTable.objects.get(league_id=limit, season_id=settings.CURRENT_SEASON_ID,
                                         team=Teams.objects.get(pk=team_id), table_type='p', date=date).order_by(
                '-points')


class ActivityTable(models.Model):
    table_type = models.CharField(blank=True, max_length=1,
                                  choices=(('o', 'overall'), ('m', 'by month'), ('w', 'by week')), default='o')
    user = models.ForeignKey(User)

    daily_avg = models.DecimalField(max_digits=4, decimal_places=3)
    monthly_avg = models.DecimalField(max_digits=4, decimal_places=3)
    points = models.IntegerField(blank=True, null=True, default=0)
    position = models.IntegerField(blank=True, null=True, default=0)

    # monthly stats
    news_count = models.IntegerField(blank=True, null=True, default=0)
    comments_count = models.IntegerField(blank=True, null=True, default=0)
    analysis_count = models.IntegerField(blank=True, null=True, default=0)
    images_count = models.IntegerField(blank=True, null=True, default=0)
    videos_count = models.IntegerField(blank=True, null=True, default=0)
    bonus_count = models.IntegerField(blank=True, null=True, default=0)
    penalty_count = models.IntegerField(blank=True, null=True, default=0)

    last_date = models.DateTimeField(blank=True, default=datetime.datetime.now())
    last_position = models.IntegerField(blank=True, null=True, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Admin: pass

    class Meta:
        db_table = 'activity_table'


class Countries(models.Model):
    code = models.CharField(blank=True, max_length=2)
    name_en = models.CharField(blank=True, max_length=100)
    name_en_url = models.CharField(blank=True, max_length=100)
    name_pl = models.CharField(blank=True, max_length=100)
    name_pl_url = models.CharField(blank=True, max_length=100)
    fifa_rank = models.IntegerField(blank=True, null=False)
    uefa_rank = models.IntegerField(blank=True, null=False)

    class Admin: pass

    class Meta:
        db_table = 'countries'
        verbose_name = 'country'
        verbose_name_plural = 'countries'

    def __unicode__(self): return self.name_en


class Languages(models.Model):
    name_en = models.CharField(blank=True, max_length=100)
    name_pl = models.CharField(blank=True, max_length=100)

    class Admin:
        pass

    class Meta:
        db_table = 'languages'
        verbose_name = 'language'
        verbose_name_plural = 'languages'


class Seasons(models.Model):
    lead_year = models.IntegerField(blank=True, null=False)
    title = models.CharField(blank=True, max_length=20)
    url = models.CharField(blank=True, max_length=20)
    is_current = models.BooleanField(default=False)

    class Admin: pass

    class Meta:
        db_table = 'seasons'
        verbose_name = 'Season'

    def __unicode__(self): return self.title


class Teams(models.Model):
    not_country = models.BooleanField(default=True)
    name_en = models.CharField(blank=True, max_length=255)
    name_en_url = models.CharField(blank=True, max_length=100)
    name_pl = models.CharField(blank=True, max_length=255)
    name_pl_url = models.CharField(blank=True, max_length=100)
    name_espn = models.CharField(blank=True, max_length=100)
    name_live = models.CharField(blank=True, max_length=100)

    country = models.ForeignKey("Countries")
    current_league_id = models.CharField(blank=True, max_length=3, default=0)

    class Admin:
        search_fields = ['name_en', 'name_pl', 'name_espn', 'name_live']

    class Meta:
        db_table = 'teams'
        verbose_name = 'Team'

    def __unicode__(self): return self.name_en

    def save(self):
        self.name_en_url = slughifi(self.name_en)
        self.name_pl_url = slughifi(self.name_pl)

        super(Teams, self).save()

    # after

    def get_name_espn(self):
        return self.name_espn

    def get_squad(self):
        return TeamSquad.objects.filter(team__id=self.id)


class TeamSquad(models.Model):
    player = models.ForeignKey("Players")
    team = models.ForeignKey("Teams")
    season = models.ForeignKey("Seasons")

    no = models.IntegerField(blank=True, null=False)

    class Admin: pass

    class Meta:
        db_table = 'team_squad'
        verbose_name = 'Team_Squad'


class TeamStats(models.Model):
    team = models.ForeignKey("Teams")
    season = models.ForeignKey("Seasons")

    goals = models.IntegerField(blank=True, null=False)
    shots_on_goal = models.IntegerField(blank=True, null=False)
    fouls = models.IntegerField(blank=True, null=False)
    corners = models.IntegerField(blank=True, null=False)
    offsides = models.IntegerField(blank=True, null=False)
    possession = models.IntegerField(blank=True, null=False)
    yellow_cards = models.IntegerField(blank=True, null=False)
    red_cards = models.IntegerField(blank=True, null=False)
    saves = models.IntegerField(blank=True, null=False)

    class Admin:
        pass

    class Meta:
        db_table = 'team_stats'
        verbose_name = 'Team_Stats'


class Leagues(models.Model):
    PROGRESS = (
        ('x', 'Unused'),
        ('g', 'Groups stage'),
        ('6', '1/16'),
        ('8', '1/8'),
        ('4', '1/4'),
        ('2', 'Semi-final'),
        ('f', 'Final'),
    )

    TYPES = (
        ('s', 'Regular season'),
        ('c', 'Cups'),
        ('f', 'Friendly'),
        ('a', 'Fans league'),
    )

    country = models.ForeignKey("Countries")
    country_code = models.CharField(max_length=2, default="")
    league_type = models.CharField(blank=True, max_length=1, choices=TYPES, default="s")
    league_level = models.IntegerField(blank=True, null=True, default=1)
    progress = models.CharField(blank=True, max_length=1, choices=PROGRESS, db_index=True, default="x")
    has_groups = models.IntegerField(blank=True, null=False, max_length=1, default=0)
    to_display = models.BooleanField(default=True)

    name_en = models.CharField(blank=True, max_length=100)
    name_en_url = models.CharField(blank=True, max_length=100)
    name_pl = models.CharField(blank=True, max_length=100)
    name_pl_url = models.CharField(blank=True, max_length=100)
    name_espn = models.CharField(blank=True, max_length=100)

    class Admin:
        search_fields = ['name_en', 'name_pl', 'name_espn']

    class Meta:
        db_table = 'leagues'
        verbose_name = 'League'

    def __unicode__(self):
        return "%s | %s" % (self.country, self.name_en)

    def save(self):
        self.name_en_url = slughifi(self.name_en)
        self.name_pl_url = slughifi(self.name_pl)

        super(Leagues, self).save()

    # after

    def get_leagues_list(self):
        return Leagues.objects.filter(to_display=1).order_by('league_level', 'name_en')

    def get_season_leagues(self):
        return Leagues.objects.filter(league_type='s', to_display=1)

    def get_cups_leagues(self):
        return Leagues.objects.filter(league_type='c', to_display=1)


class LeagueTeams(models.Model):
    """List of teams in the league"""

    MOVING = (
        ('u', 'Up'),
        ('d', 'Down'),
        ('n', 'Not'),
    )

    league = models.ForeignKey("Leagues")
    team = models.ForeignKey("Teams")
    season = models.ForeignKey("Seasons")

    points = models.IntegerField(blank=True, null=False, default=0)
    moving = models.CharField(blank=True, max_length=1, choices=MOVING)

    class Admin:
        pass

    class Meta:
        db_table = 'league_teams'
        verbose_name = 'League_team'

    def __unicode__(self):
        return "%s" % (self.team.name_en)


# DEFAULT_CACHE_TIME = 15 # 15 seconds
# # TODO
# # - Come up with a better method for invalidation
# # - Add invalidation for count() when a queryset is invalidated
# # - Find a way to make AutoCacheManager override `objects` in models
# # - Add some handling to allow CacheManager to react differently based on query type (get, count, filter, select_related)
# 
# # CacheManager -- A manager to store and retrieve cached objects using CACHE_BACKEND
# # (Optional) <string key_prefix> -- the key prefix for all cached objects on this model [default: db_table]
# # (Optional) <int timeout> -- in seconds, the maximum time before data is invalidated
# 
# # cachemanager.clean() -- Invalidates cached data
# # <instance/queryset data> -- the queryset, or instance of the object to be invalidated
# class CacheManager(models.Manager):
#	def __init__(self, *args, **kwargs):
#		self.key_prefix = kwargs.pop('key_prefix', None)
#		self.timeout = kwargs.pop('timeout', None)
#		Manager.__init__(self)
# 
#	def get_query_set(self):
#		return CachedQuerySet(self.model, self.timeout, self.key_prefix)
# 
#	# clean will accept either a queryset or an instance
#	def clean(self, data):
#		# invalidate the .get() request
#		if isinstance(data, self.model):
#			self.clean(self.filter(pk=self._get_pk_val()))
#		elif isinstance(data, CachedQuerySet):
#			self.clean()
#		else:
#			raise TypeError("instance or queryset required for data, got %r" % (data,))
# 
# # CachedQuerySet -- Extends the QuerySet object -- additionally adds a .cache() method
# 
# # queryset.cache() -- Overrides CacheManager's options for this QuerySet
# # (Optional) <string key_prefix> -- the key prefix for all cached objects on this model [default: db_table]
# # (Optional) <int timeout> -- in seconds, the maximum time before data is invalidated
# 
# # queryset.clean() -- Removes queryset from the cache -- recommended to use cachemanager.clean()
# # must be called as the last method of the queryset
# # <instance/queryset data> -- the queryset, or instance of the object to be invalidated
# class CachedQuerySet(QuerySet):
#	def __init__(self, model=None, *args, **kwargs):
#		self.__cache_key = None
#		self.key_prefix = kwargs.pop('key_prefix', model and model._meta.db_table or '')
#		self.timeout = kwargs.pop('timeout', getattr(cache, 'default_timeout', DEFAULT_CACHE_TIME))
#		if not isinstance(self.key_prefix, basestring):
#			raise TypeError("string required for key_prefix, got %r" % (self.key_prefix,))
#		if not isinstance(self.timeout, int):
#			raise TypeError("integer required for timeout, got %r" % (self.timeout,))
#		QuerySet.__init__(self, model)
# 
#	def _get_sorted_clause_key(self):
#		return (isinstance(i, basestring) and i.lower().replace('`', '').replace("'", '') or str(tuple(sorted(i))) for i in self._get_sql_clause())
# 
#	def _get_cache_key(self, xtra=''):
#		if not self.__cache_key:
#			self.__cache_key = self.key_prefix + str(hash(''.join(self._get_sorted_clause_key()))) + xtra
#		return self.__cache_key
# 
#	def _get_data(self):
#		data = cache.get(self._get_cache_key())
#		if data is None:
#			data = QuerySet._get_data(self)
#			cache.set(self._get_cache_key(), [d for d in data], self.timeout)
#		return data
# 
#	def count(self):
#		count = cache.get(self._get_cache_key('count'))
#		if count is None:
#			count = int(QuerySet.count(self))
#			cache.set(self._get_cache_key('count'), count, self.timeout)
#		return count
# 
#	def cache(self, *args, **kwargs):
#		self.key_prefix = kwargs.pop('key_prefix', self.key_prefix)
#		self.timeout = kwargs.pop('timeout', self.timeout)
#		if not isinstance(self.key_prefix, basestring):
#			raise TypeError("string required for key_prefix, got %r" % (self.key_prefix,))
#		if not isinstance(self.timeout, int):
#			raise TypeError("integer required for timeout, got %r" % (self.timeout,))
# 
#	def clean(self):
#		cache.delete(self._get_cache_key())

class Matches(models.Model):
    PROGRESS = (
        ('o', 'Open'),
        ('d', 'During'),
        ('f', 'Finished'),
        ('c', 'Cancelled'),
        ('p', 'Postponed'),
    )

    SOURCES = (
        ('o', 'OWN'),
        ('e', 'EPSN'),
        ('l', 'LiveScore.com'),
    )

    # TODO: find a way to make `objects` actually set correctly
    # objects = CacheManager()
    # no_cache = Manager()

    # TODO: know how to clean this w/o guessing for CacheManager
    # def delete(self, *args, **kwargs):
    #	self.__class__.objects.clean(self)
    #	Manager.delete(self, *args, **kwargs)
    #
    # def save(self, *args, **kwargs):
    #	Manager.save(self, *args, **kwargs)
    #	self.__class__.objects.clean(self)

    # league_id = models.IntegerField(blank=True, null=False)
    league = models.ForeignKey("Leagues")
    season = models.ForeignKey("Seasons")
    stadium_id = models.IntegerField(blank=True, null=False)

    status = models.CharField(blank=True, max_length=1, choices=PROGRESS, default="o")
    minute = models.CharField(blank=True, max_length=3)
    home_team = models.ForeignKey("Teams", related_name="home_team")
    away_team = models.ForeignKey("Teams", related_name="away_team")
    home_score = models.SmallIntegerField(blank=False, default=-1)
    away_score = models.SmallIntegerField(blank=False, default=-1)
    espn_home_team_id = models.IntegerField(blank=True, null=False)
    espn_away_team_id = models.IntegerField(blank=True, null=False)
    source = models.CharField(blank=True, max_length=1, choices=SOURCES)
    espn_match_id = models.IntegerField(blank=True, null=False)
    live_match_id = models.IntegerField(blank=True, null=False)
    crowd = models.CharField(blank=True, max_length=11, default=0)

    manual = models.BooleanField(default=False)
    match_date = models.DateField()
    match_time = models.TimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(default=datetime.datetime.now())

    can_comment = models.BooleanField(default=True)
    can_analyse = models.BooleanField(default=True)
    can_review = models.BooleanField(default=True)

    comments_count_pl = models.IntegerField(default=0)
    comments_count_en = models.IntegerField(default=0)
    analysis_count_pl = models.IntegerField(default=0)
    analysis_count_en = models.IntegerField(default=0)
    images_count = models.IntegerField(default=0)
    videos_count = models.IntegerField(default=0)

    is_accepted = models.BooleanField(default=False)
    is_posponned = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)

    class Admin:

        list_filter = ['match_date', 'manual', 'is_accepted']
        list_display = (
        'id', 'home_team_espn', 'home_score', 'away_score', 'away_team_espn', 'minute', 'status', 'manual',
        'get_league', 'get_stadium', 'crowd')

    class Meta:
        db_table = 'matches'
        verbose_name = 'match'
        verbose_name_plural = 'matches'

    def __unicode__(self):
        return "%s - %s (%s)" % (self.home_team.name_pl, self.away_team.name_pl, self.id)

    def home_team_espn(self):
        return self.home_team.get_name_espn()

    def away_team_espn(self):
        return self.away_team.get_name_espn()

    def get_stadium(self):
        stadium = Stadiums.objects.get(pk=self.stadium_id)
        return stadium.name_espn

    def get_league(self):
        league = Leagues.objects.get(pk=self.league_id)
        return league.name_espn

    def get_competition(self):
        competition = Competitions.objects.get(pk=self.competition_id)
        return competition

    # ---

    # BY LEAGUE
    def get_results_by_league(self, league_id=False, status=['f'], match_date=0):
        matches = Matches.objects.filter(season__id=settings.CURRENT_SEASON_ID, status__in=status)
        if league_id:
            matches = matches.filter(league__id=league_id)

        if match_date != 0:
            matches = matches.filter(match_date=match_date)
        # TODO!!!
        # else:
        #	matches = matches.filter(match_date__gte=datetime.date.today())
        #
        # count = today_matches.count()
        # if count == 0:
        #	matches = matches.filter(match_date__gte=datetime.date.today())
        #	only_todays = False
        # else:
        #	matches = today_matches

        if 'f' in status:
            return matches.select_related().order_by('status', '-match_date', 'match_time')
        else:
            return matches.select_related().order_by('status', 'match_date', 'match_time')

    def get_fixtures_by_league(self, league_id=False, status=['o'], match_date=0):
        return self.get_results_by_league(league_id=league_id, status=status, match_date=match_date)

    def get_live_fixtures_by_league(self, league_id=False, status=['d', 'o'], match_date=0):
        return self.get_fixtures_by_league(league_id=league_id, status=status, match_date=match_date)

    # BY TEAM
    def get_results_by_team(self, team_id=False, status=['f'], match_date=0):
        from django.db.models import Q

        matches = Matches.objects.filter(season__id=settings.CURRENT_SEASON_ID, status__in=status)
        if team_id:
            matches = matches.filter(Q(home_team__id=team_id) | Q(away_team__id=team_id))

        if match_date != 0:
            matches = matches.filter(match_date=match_date)

        return matches.select_related().order_by('status', 'match_date')

    def get_fixtures_by_team(self, team_id=False, status=['o'], match_date=0):
        return self.get_results_by_team(team_id=team_id, status=status, match_date=match_date)

    def get_live_fixtures_by_team(self, team_id=False, status=['d', 'o'], match_date=0):
        return self.get_fixtures_by_team(team_id=team_id, status=status, match_date=match_date)

    # ---

    def get_comments(self):
        return Comments.objects.filter(dst='m', is_accepted=1, dst_id=self.id, lang=settings.LANGUAGE_CODE).order_by(
            'root_id', 'created_at')[:15]

    def get_all_comments(self):
        return Comments.objects.filter(dst='m', is_accepted=1, dst_id=self.id, lang=settings.LANGUAGE_CODE).order_by(
            'root_id', 'created_at')

    def get_comments_count(self):
        if settings.LANGUAGE_CODE == 'pl':
            return self.comments_count_pl
        else:
            return self.comments_count_en

    def get_analysis(self):
        return Comments.objects.filter(dst='a', is_accepted=1, dst_id=self.id, lang=settings.LANGUAGE_CODE).order_by(
            'created_at')

    def get_all_analysis(self):
        return Comments.objects.filter(dst='a', is_accepted=1, dst_id=self.id, lang=settings.LANGUAGE_CODE).order_by(
            'created_at')

    def get_analysis_count(self):
        if settings.LANGUAGE_CODE == 'pl':
            return self.analysis_count_pl
        else:
            return self.analysis_count_en

    def get_images(self):
        return Images.objects.filter(dst='match', dst_id=self.id, is_accepted=1, is_processed=1, is_deleted=0).order_by(
            '-created_at', 'name')

    def get_all_images(self):
        return Images.objects.filter(dst='match', dst_id=self.id, is_accepted=1, is_processed=1, is_deleted=0).order_by(
            '-created_at', 'name')

    def get_images_count(self):
        # return Images.objects.filter(dst='match', dst_id=self.id, is_accepted=1, is_deleted=0).count()
        return self.images_count

    def get_videos(self):
        return Videos.objects.filter(dst='match', dst_id=self.id, is_accepted=1, is_deleted=0).order_by('-created_at',
                                                                                                        'name')

    def get_all_videos(self):
        return Videos.objects.filter(dst='match', dst_id=self.id, is_accepted=1, is_deleted=0).order_by('-created_at',
                                                                                                        'name')

    def get_videos_count(self):
        # return Videos.objects.filter(dst='match', dst_id=self.id, is_accepted=1, is_deleted=0).count()
        return self.videos_count

    # ---

    def on_start(self):
        pass

    def on_finish(self):
        from myscore.libs.generate_tables import GenerateTables
        from myscore.libs.count_points import CountPoints

        LeagueTable.objects.filter(league__id=self.league_id).delete()
        gt = GenerateTables(self.league_id, settings.CURRENT_SEASON_ID)  # league_id, season_id
        gt.gt()
        gt.g_home()
        gt.g_away()

    # NOT WORKING FOR SOME REASON
    # SO I'M MOVING IT TO CRON FOR A WHILE
    # count points
    # cp = CountPoints()
    # cp.calculate_picks()

    def on_cancel(self):
        pass


class MatchDetails(models.Model):
    HA = (
        ('h', 'Home'),
        ('a', 'Away')
    )

    ACTIONS = (
        ('y', 'Yellow Card'),
        ('r', 'Red Card'),
        ('g', 'Goal'),
    )

    ACTION_INFOS = (
        ('', 'None'),
        ('p', 'Penalty'),
        ('m', 'Miss Pen'),
        ('o', 'Own Goal'),
    )

    match = models.ForeignKey("Matches", related_name="details")
    side = models.CharField(blank=True, max_length=1, choices=HA)

    minute = models.PositiveSmallIntegerField(blank=True, null=False)
    action = models.CharField(blank=True, max_length=1, choices=ACTIONS)
    action_info = models.CharField(blank=True, max_length=1, choices=ACTION_INFOS)
    player_id = models.IntegerField(blank=True, null=False, default=0)
    player_name = models.CharField(blank=True, max_length=100, default="")
    side = models.CharField(blank=True, max_length=5)
    espn_player_id = models.IntegerField(blank=True, null=False, default=0)
    espn_player_name = models.CharField(max_length=100, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Admin: pass

    class Meta:
        db_table = 'match_details'
        verbose_name = 'match_detail'
        ordering = ['minute']


class MatchStats(models.Model):
    HA = (
        ('h', 'Home'),
        ('a', 'Away')
    )

    match = models.ForeignKey("Matches", related_name='stats')
    side = models.CharField(blank=True, max_length=1, choices=HA)

    shots = models.IntegerField(blank=True, null=True, default=0)
    shots_on_goal = models.IntegerField(blank=True, null=True, default=0)
    fouls = models.IntegerField(blank=True, null=True, default=0)
    corners = models.IntegerField(blank=True, null=True, default=0)
    offsides = models.IntegerField(blank=True, null=True, default=0)
    possession = models.IntegerField(blank=True, null=True, default=0)
    yellow_cards = models.IntegerField(blank=True, null=True, default=0)
    red_cards = models.IntegerField(blank=True, null=True, default=0)
    saves = models.IntegerField(blank=True, null=True, default=0)

    class Admin: pass

    class Meta:
        db_table = 'match_stats'
        verbose_name = 'match_stat'


class MatchSquad(models.Model):
    HA = (
        ('h', 'Home'),
        ('a', 'Away')
    )

    match = models.ForeignKey("Matches", related_name="squad")
    player = models.ForeignKey("Players")
    side = models.CharField(blank=True, max_length=1, choices=HA)

    started_as_sub = models.BooleanField(default=False)

    class Admin:
        pass

    class Meta:
        db_table = 'match_squad'
        verbose_name = 'Match_Squad'

    def __unicode__(self): return "MatchSquad"


class MatchSubs(models.Model):
    HA = (
        ('h', 'Home'),
        ('a', 'Away')
    )

    match = models.ForeignKey("Matches", related_name="subs")
    side = models.CharField(blank=True, max_length=1, choices=HA)
    in_player = models.ForeignKey("Players", related_name="in_player")
    out_player = models.ForeignKey("Players", related_name="out_player")
    minute = models.IntegerField(blank=True, null=False)
    reason = models.CharField(blank=True, max_length=255)

    class Admin: pass

    class Meta:
        db_table = 'match_subs'
        verbose_name = 'Match_Sub'


class Players(models.Model):
    first_name = models.CharField(blank=True, max_length=100, default="")
    last_name = models.CharField(blank=True, max_length=100, default="")
    espn_name = models.CharField(blank=True, max_length=100)
    espn_id = models.IntegerField(blank=True, null=False, default=0)

    current_team_id = models.IntegerField(blank=True, null=False, default=0)
    current_team_name = models.CharField(blank=True, max_length=100)

    born = models.DateField(auto_now_add=True)
    birthplace = models.CharField(blank=True, max_length=50)
    height = models.CharField(blank=True, max_length=20)
    position = models.CharField(blank=True, max_length=1)
    nationality = models.CharField(blank=True, max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Admin:
        search_fields = ['last_name', 'first_name', 'espn_name', 'current_team_name']

    class Meta:
        db_table = 'players'
        verbose_name = 'Player'

    def __unicode__(self):
        return "%s, %s (%s)" % (self.last_name, self.first_name, self.current_team_name)


class PlayerHistory(models.Model):
    season_id = models.IntegerField(blank=True, null=False, default=0)
    team_id = models.IntegerField(blank=True, null=False)

    games_started = models.IntegerField(blank=True, null=False)
    used_as_sub = models.IntegerField(blank=True, null=False)
    goals = models.IntegerField(blank=True, null=False)
    assists = models.IntegerField(blank=True, null=False)
    shots = models.IntegerField(blank=True, null=False)
    shots_on_goal = models.IntegerField(blank=True, null=False)
    yellow_cards = models.IntegerField(blank=True, null=False)
    red_cards = models.IntegerField(blank=True, null=False)
    fouls_commited = models.IntegerField(blank=True, null=False)
    fouls_suffered = models.IntegerField(blank=True, null=False)
    saves = models.IntegerField(blank=True, null=False)
    offsides = models.IntegerField(blank=True, null=False)

    wins = models.IntegerField(blank=True, null=False)
    draws = models.IntegerField(blank=True, null=False)
    losses = models.IntegerField(blank=True, null=False)

    class Admin: pass

    class Meta:
        db_table = 'player_history'
        verbose_name = 'PlayerHistory'
        verbose_name_plural = 'PlayerHistories'


class PlayerTransfer(models.Model):
    player = models.ForeignKey("Players")

    from_id = models.IntegerField(default=0)
    from_string = models.CharField(blank=True, max_length=100)
    to_id = models.IntegerField(default=0)
    to_string = models.CharField(blank=True, max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Admin: pass

    class Meta:
        db_table = 'players_transfers'
        verbose_name = 'PlayerTransfer'
        verbose_name_plural = 'PlayersTransfers'


class Stadiums(models.Model):
    name_en = models.CharField(blank=True, max_length=100)
    name_en_url = models.CharField(blank=True, max_length=100)
    name_pl = models.CharField(blank=True, max_length=100)
    name_pl_url = models.CharField(blank=True, max_length=100)
    name_espn = models.CharField(blank=True, max_length=100)

    home_team_id = models.IntegerField(blank=True, null=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Admin: pass

    class Meta:
        db_table = 'stadiums'
        verbose_name = 'Stadium'

    def __unicode__(self): return "%s (%s)" % (self.name_en, self.name_espn)

    def get_name_espn(self): return self.name_espn


class Picks(models.Model):
    match = models.ForeignKey("Matches", related_name='picks')
    user = models.ForeignKey(User)
    home_score = models.CharField(blank=True, max_length=1)
    away_score = models.CharField(blank=True, max_length=1)
    points = models.SmallIntegerField(blank=True, null=False, default=0)
    is_calculated = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Admin:
        pass

    class Meta:
        db_table = 'picks'
        verbose_name = 'Pick'

    # ===

    def get_user_picks(self, user_id, condition='', date=None):

        if date is None:
            date_condition = ''
            limit_condition = 'LIMIT 50'
        else:
            date_condition = "AND m.match_date = '%s'" % str(date)
            limit_condition = ''

        sql = """
			SELECT 
				p.id, 
				p.home_score, 
				p.away_score,
				m.home_score, 
				m.away_score,
				ht.name_en,
				ht.name_pl,
				ht.name_en_url,
				ht.name_pl_url,
				at.name_en,
				at.name_pl,
				at.name_en_url,
				at.name_pl_url,
				m.id,
				m.minute,
				m.match_date,
				m.match_time,
				m.status,
				p.points
			FROM 
				picks as p
			LEFT JOIN 
				matches as m ON (m.id = p.match_id)
			INNER JOIN
				teams as ht ON (m.home_team_id = ht.id)
			INNER JOIN
				teams as at ON (m.away_team_id = at.id)
			WHERE
				p.user_id = %s
				%s
				%s
			ORDER BY
				p.is_calculated ASC,
				m.match_date DESC
			%s""" % (user_id, date_condition, condition, limit_condition)

        logging.debug(sql)

        from django.db import connection

        cursor = connection.cursor()
        cursor.execute(sql)

        result_list = []
        for row in cursor.fetchall():
            p = Picks(id=row[0], home_score=row[1], away_score=row[2], points=row[18])
            p.match_home_score = row[3]
            p.match_away_score = row[4]
            p.home_team_name_en = row[5]
            p.home_team_name_pl = row[6]
            p.home_team_name_en_url = row[7]
            p.home_team_name_pl_url = row[8]
            p.away_team_name_en = row[9]
            p.away_team_name_pl = row[10]
            p.away_team_name_en_url = row[11]
            p.away_team_name_pl_url = row[12]
            p.match_id = row[13]
            p.match_minute = row[14]
            p.match_date = row[15]
            p.match_time = row[16]
            p.match_status = row[17]
            result_list.append(p)

        return result_list


class NewsManager(models.Manager):
    def example(self):
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute("""
			SELECT p.id, p.question, p.poll_date, COUNT(*)
			FROM polls_opinionpoll p, polls_response r
			WHERE p.id = r.poll_id
			GROUP BY 1, 2, 3
			ORDER BY 3 DESC""")
        result_list = []
        for row in cursor.fetchall():
            p = self.model(id=row[0], question=row[1], poll_date=row[2])
            p.num_responses = row[3]
            result_list.append(p)
        return result_list


class News(models.Model):
    LANGS = (
        ('en', 'EN'),
        ('pl', 'PL'),
    )

    caption = models.CharField(blank=True, max_length=255)
    short_content = models.TextField(blank=True)
    content = models.TextField(blank=True)
    source = models.CharField(blank=True, max_length=300)
    url = models.SlugField(prepopulate_from=("",), max_length=300)

    user = models.ForeignKey(User)
    league_id = models.IntegerField(blank=True, null=False, default=0)
    team_id = models.IntegerField(blank=True, null=False, default=0)
    country_id = models.IntegerField(blank=True, null=False, default=0)
    match_id = models.IntegerField(blank=True, null=False, default=0)
    lang = models.CharField(blank=True, max_length=2, choices=LANGS)

    in_community = models.BooleanField(default=False)
    can_comment = models.BooleanField(default=True)

    comments_count_pl = models.IntegerField(default=0)
    comments_count_en = models.IntegerField(default=0)
    images_count = models.IntegerField(default=0)
    videos_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)

    # potrzebne do grupowania newsow
    related_counter = models.IntegerField(default=0)
    related_to_id = models.IntegerField(default=0)
    related_to_head_id = models.IntegerField(default=0)

    assign_league_logo = models.ForeignKey("Leagues", blank=True, null=True)
    assign_team_logo = models.ForeignKey("Teams", blank=True, null=True)

    is_accepted = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_temp = models.BooleanField(default=False)
    is_promoted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(default=datetime.datetime.now())

    objects = models.Manager()
    news_objects = NewsManager()

    class Meta:
        db_table = 'news'
        verbose_name = 'News'
        verbose_name_plural = 'News'

    class Admin:
        pass

    # methods
    def __unicode__(self):
        return "%s (%s)" % (self.caption, self.created_at)

    def save(self):
        self.url = slughifi(self.caption)
        self.short_content = self.parse_lines(self.short_content)
        self.content = self.parse_lines(self.content)

        if self.league_id > 0 and self.country_id == 0:
            self.country_id = Leagues.objects.get(pk=self.league_id).country.id

        super(News, self).save()

    # after

    def accept(self):
        self.is_accepted = 1
        self.is_deleted = 0
        self.published_at = datetime.datetime.now()
        self.save()

        # activity points
        AccountsActivity(user_id=self.user.id, username=str(self.user), dst_id=self.id, action_type='news', points='20',
                         is_calculated=0, is_confirmed=1, created_at=self.published_at).save()

        # send email
        if self.lang == 'pl':
            mail_content = """Dziękujemy, news który dodałeś/aś jest już widoczny na stronie.
			
Redakcja 24gole"""
            Mailing().add(rcp=self.user.email, subject='Twój news jest już widoczny na stronie', content=mail_content,
                          sender="Moderacja 24gole.pl <marek@24gole.pl>")
        else:
            mail_content = """Thank you, content you've added is visible on the site from now.
			
24goals team"""
            Mailing().add(rcp=self.user.email, subject='Your news is now visible on the site', content=mail_content,
                          sender="Moderator 24goals.com <marek@24goals.com>")

    def refuse(self, reason_id):
        self.is_accepted = 0
        self.is_deleted = 1
        self.save()

        # send email
        ar = AutoReplies.objects.get(pk=reason_id)
        if self.lang == 'pl':
            mail_content = ar.content_pl
            Mailing().add(rcp=self.user.email, subject='Twój news został odrzucony przez moderatora',
                          content=mail_content, sender="Moderacja 24gole.pl <marek@24gole.pl>")
        else:
            mail_content = ar.content_en
            Mailing().add(rcp=self.user.email, subject='Your news has been refused by moderator', content=mail_content,
                          sender="Moderator 24goals.com <marek@24goals.com>")

    def unaccept(self):
        self.is_accepted = 0
        self.save()

    def mark_as_deleted(self):
        self.is_deleted = 1
        self.save()

    def mark_as_not_deleted(self):
        self.is_deleted = 0
        self.save()

    def inform_moderators(self, news_id):
        mail_content = """Użytkownik dodał news. Link: http://www.24gole.pl/admin/main/news/%s/""" % news_id
        Mailing().add(rcp="marcin@24gole.pl", subject=u"Użytkownik dodał news", content=mail_content,
                      sender="24gole <marek@24gole.pl>")
        Mailing().add(rcp="marek@24gole.pl", subject=u"Użytkownik dodał news", content=mail_content,
                      sender="24gole <marek@24gole.pl>")

    def parse_lines(self, content):
        lines = []
        for l in content.splitlines():
            l = l.replace("\n", "")
            lines.append(l.replace("<br />", ""))

        return "<br />\n".join(lines)

    # ---

    def get_news(self, news=False, country_name=False, league_name=False, news_date=0, page_no=1, slice_for_me=True,
                 lang=settings.LANGUAGE_CODE, order_by='-published_at'):
        if not news:
            news = News.objects.filter(is_accepted=1, is_deleted=0, is_temp=0, lang=lang)

        if league_name:
            league_id = helpers.reveal_league_name(league_name)
            if league_id:
                news = news.filter(league_id=league_id)

        elif country_name:
            country_id = helpers.reveal_country_name(country_name)
            if country_id:
                news = news.filter(country_id=country_id)

        if news_date != 0 and news_date != None:
            if type(news_date) == type(()) and len(news_date) == 2:
                try:
                    news = news.filter(published_at__range=(news_date[0], news_date[1]))
                except:
                    pass
            else:
                try:
                    from_news_date = datetime.datetime.strptime(news_date, "%Y-%m-%d")
                    to_news_date = from_news_date + datetime.timedelta(hours=23, minutes=59, seconds=59)
                    news = news.filter(published_at__range=(from_news_date, to_news_date))
                except:
                    pass

        try:
            page_no = int(page_no)
        except:
            page_no = 1

        if slice_for_me:
            return news.select_related().order_by(order_by)[
                   (page_no * settings.PER_PAGE) - settings.PER_PAGE:settings.PER_PAGE * page_no]
        else:
            return news.select_related().order_by(order_by)

    def get_unaccepted_news(self, country_name=False, league_name=False, news_date=0, page_no=1):
        return self.get_news(news=self.objects.filter(is_accepted=0, is_deleted=0, is_temp=0),
                             country_name=country_name, league_name=league_name, news_date=news_date, page_no=page_no)

    def get_temp_news(self, country_name=False, league_name=False, news_date=0, page_no=1):
        return self.get_news(news=self.objects.filter(is_accepted=0, is_deleted=0, is_temp=1),
                             country_name=country_name, league_name=league_name, news_date=news_date, page_no=page_no)

    def get_all_news(self, country_name=False, league_name=False, news_date=0, page_no=1):
        return self.get_news(news=self.objects.all(), country_name=country_name, league_name=league_name,
                             news_date=news_date, page_no=page_no)

    # ---

    # RELATED

    def get_related_to_league(self, league_id, news_date=0, lang=settings.LANGUAGE_CODE, order_by='-published_at'):
        if league_id == 0:
            news = News.objects.filter(is_accepted=1, is_deleted=0, is_temp=0, lang=lang)
        else:
            news = News.objects.filter(league_id=int(league_id), is_accepted=1, is_deleted=0, is_temp=0, lang=lang)

        if news_date != 0 and news_date != None:
            if type(news_date) == type(()) and len(news_date) == 2:
                try:
                    news = news.filter(published_at__range=(news_date[0], news_date[1]))
                except:
                    pass
            else:
                try:
                    from_news_date = datetime.datetime.strptime(news_date, "%Y-%m-%d")
                    to_news_date = from_news_date + datetime.timedelta(hours=23, minutes=59, seconds=59)
                    news = news.filter(published_at__range=(from_news_date, to_news_date))
                except:
                    pass

        return news.select_related().order_by(order_by)

    def get_related_to_team(self, team_id, news_date=0, lang=settings.LANGUAGE_CODE, order_by='-published_at'):

        try:
            news = News.objects.filter(assign_team_logo__id=int(team_id), is_accepted=1, is_deleted=0, is_temp=0,
                                       lang=lang)
        except:
            return False

        if news_date != 0 and news_date != None:
            if type(news_date) == type(()) and len(news_date) == 2:
                try:
                    news = news.filter(published_at__range=(news_date[0], news_date[1]))
                except:
                    pass
            else:
                try:
                    from_news_date = datetime.datetime.strptime(news_date, "%Y-%m-%d")
                    to_news_date = from_news_date + datetime.timedelta(hours=23, minutes=59, seconds=59)
                    news = news.filter(published_at__range=(from_news_date, to_news_date))
                except:
                    pass

        return news.select_related().order_by(order_by)

    def get_not_related_to_team(self, league_name, team_id, news_date=0, lang=settings.LANGUAGE_CODE):
        try:
            league_id = helpers.reveal_league_name(league_name)
            news = News.objects.filter(league_id=league_id).exclude(assign_team_logo__id=int(team_id), is_accepted=1,
                                                                    is_deleted=0, is_temp=0, lang=lang)
        except:
            return False

        if news_date != 0: news = news.filter(published_at=news_date)

        return news.select_related().order_by('-published_at')

    # ---

    # COMMENTS
    def get_comments(self):
        return Comments.objects.filter(dst='n', is_accepted=1, dst_id=self.id, lang=settings.LANGUAGE_CODE).order_by(
            'root_id', 'created_at')[:5]

    def get_all_comments(self):
        return Comments.objects.filter(dst='n', is_accepted=1, dst_id=self.id, lang=settings.LANGUAGE_CODE).order_by(
            'root_id', 'created_at')

    def get_comments_count(self):
        if settings.LANGUAGE_CODE == 'pl':
            return self.comments_count_pl
        else:
            return self.comments_count_en

    def get_comments_count_db(self):
        return Comments.objects.filter(dst='n', is_accepted=1, dst_id=self.id, lang=settings.LANGUAGE_CODE).count()

    # IMAGES
    def get_images(self):
        return Images.objects.filter(dst='news', dst_id=self.id, is_accepted=1, is_processed=1, is_deleted=0).order_by(
            '-created_at', 'name')

    def get_all_images(self):
        return Images.objects.filter(dst='news', dst_id=self.id, is_accepted=1, is_processed=1, is_deleted=0).order_by(
            '-created_at', 'name')

    def get_images_count(self):
        return self.images_count

    def get_images_count_db(self):
        return self.get_all_images().count()

    # VIDEOS
    def get_videos(self):
        return Videos.objects.filter(dst='news', dst_id=self.id, is_accepted=1, is_deleted=0).order_by('-created_at',
                                                                                                       'name')

    def get_all_videos(self):
        return Videos.objects.filter(dst='news', dst_id=self.id, is_accepted=1, is_deleted=0).order_by('-created_at',
                                                                                                       'name')

    def get_videos_count(self):
        return self.videos_count

    def get_videos_count_db(self):
        return self.get_all_videos().count()


class Comments(models.Model):
    TYPE = (
        ('n', 'news'),
        ('m', 'match'),
        ('a', 'analysis'),
        ('r', 'review'),
        ('p', 'pick'),
    )

    LANGS = (
        ('en', 'EN'),
        ('pl', 'PL'),
    )

    dst = models.CharField(blank=True, max_length=1, choices=TYPE)
    dst_id = models.IntegerField(blank=True, null=False, default=0)
    root_id = models.IntegerField(blank=True, null=False, default=0)
    user = models.ForeignKey(User, null=True, blank=True, default=0)
    username = models.CharField(blank=True, max_length=100, default="")
    lang = models.CharField(blank=True, max_length=2, choices=LANGS)
    content = models.TextField(blank=True)

    ip = models.CharField(blank=True, null=True, max_length=20, default='127.0.0.1')
    browser = models.CharField(blank=True, null=True, max_length=120, default='')
    is_accepted = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(default=datetime.datetime.now())

    def match_minute(self):
        return self.match.minute

    match_minute.short_description = 'Minute'

    class Admin:

        fields = (
            (None, {'fields': ('dst', 'dst_id', 'lang', 'content', 'is_accepted')}),
        )

        search_fields = ['content', 'match__id']
        list_filter = ['created_at', 'modified_at', 'published_at']
        list_display = ('__unicode__', 'content', 'created_at')

    # TODO: filtrowanie wg. meczow, uzytkownikow

    class Meta:
        db_table = 'comments'
        verbose_name = 'Comment'

    # methods
    def __unicode__(self):
        return "%s by %s" % (self.content, self.user)

    def update_counter(self):
        if self.dst == 'n':
            news = News.objects.get(pk=self.dst_id)
            count = Comments.objects.filter(dst=self.dst, dst_id=self.dst_id, is_accepted=1, is_deleted=0,
                                            lang=settings.LANGUAGE_CODE).count()
            if settings.LANGUAGE_CODE == 'pl':
                news.comments_count_pl = count
            else:
                news.comments_count_en = count
            news.save()

        elif self.dst == 'm':
            match = Matches.objects.get(pk=self.dst_id)
            count = Comments.objects.filter(dst=self.dst, dst_id=self.dst_id, is_accepted=1, is_deleted=0,
                                            lang=settings.LANGUAGE_CODE).count()
            if settings.LANGUAGE_CODE == 'pl':
                match.comments_count_pl = count
            else:
                match.comments_count_en = count
            match.save()

        elif self.dst == 'a':
            match = Matches.objects.get(pk=self.dst_id)
            count = Comments.objects.filter(dst=self.dst, dst_id=self.dst_id, is_accepted=1, is_deleted=0,
                                            lang=settings.LANGUAGE_CODE).count()
            if settings.LANGUAGE_CODE == 'pl':
                match.analysis_count_pl = count
            else:
                match.analysis_count_en = count
            match.save()

    def accept(self):
        self.is_accepted = 1
        self.is_published = datetime.datetime.now()
        self.save()

        # update counters
        self.update_counter()

        # activity points
        if self.dst == 'a':
            AccountsActivity(user_id=self.user.id, username=str(self.user), dst_id=self.id,
                             action_type='match_analysis', points='10', is_calculated=0, is_confirmed=1,
                             created_at=self.published_at).save()

    def unaccept(self):
        self.is_accepted = 0
        self.save()

        # moderuj caly watek
        slaves = Comments.objects.filter(root_id=self.id)
        for s in slaves:
            s.is_accepted = 0
            s.save()

        # update counters
        self.update_counter()

    def mark_as_deleted(self):
        self.is_deleted = 1
        self.save()

        # moderuj caly watek
        slaves = Comments.objects.filter(root_id=self.id)
        for s in slaves:
            s.is_deleted = 1
            s.save()

        # update counters
        self.update_counter()

    def mark_as_not_deleted(self):
        self.is_deleted = 0
        self.save()
        # update counters
        self.update_counter()

    def get_comments_by_match(self, match_id, latest=15, lang=settings.LANGUAGE_CODE):
        c = Comments.objects.filter(dst='m', dst_id=match_id, lang=lang, is_accepted=1).order_by('root_id',
                                                                                                 'created_at')
        if latest == 0:
            return c
        else:
            return c[:latest]

    def get_comments_by_news(self, news_id, latest=15, lang='en'):
        c = Comments.objects.filter(dst='n', dst_id=news_id, lang=lang, is_accepted=1).order_by('root_id', 'created_at')
        if latest == 0:
            return c
        else:
            return c[:latest]


class Messages(models.Model):
    fm = models.CharField(blank=True, max_length=100)
    to = models.CharField(blank=True, max_length=100)
    subject = models.CharField(blank=True, max_length=100)
    content = models.TextField(blank=True)

    is_spam = models.BooleanField(default=False, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    is_red = models.BooleanField(default=False, db_index=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    # methods
    def __unicode__(self):
        return "from: %s, %s (%s)" % (self.fm, self.subject, self.sent_at)

    def send_message(fm, to, subject, content=""):
        """Sends message"""
        return True

    def get_in(self, user, friend='', page=1):
        m = Messages.objects.filter(to=user, is_spam=0, is_deleted=0)
        if friend is not '' and friend is not None:
            m = m.filter(fm=friend)
        if page is None:
            page = 1

        return m.order_by('-sent_at')[(page - 1) * 20:page * 20]

    def get_out(self, user, friend='', page=1):
        m = Messages.objects.filter(fm=user, is_spam=0, is_deleted=0)
        if friend is not '' and friend is not None:
            m = m.filter(to=friend)
        if page is None:
            page = 1

        return m.order_by('-sent_at')[(page - 1) * 20:page * 20]

    def get_spam(self, user, page=1):
        m = Messages.objects.filter(to=user, is_spam=1, is_deleted=0)
        if page is None:
            page = 1

        return m.order_by('-sent_at')[(page - 1) * 20:page * 20]

    def get_deleted(self, user, page=1):
        m = Messages.objects.filter(to=user, is_deleted=1, is_spam=0)
        if page is None:
            page = 1

        return m.order_by('-sent_at')[(page - 1) * 20:page * 20]

    # --- MARK AS ... ---
    def mark_as_spam(self, id=None):
        if id is None:  # uzywamy self.
            self.is_spam = 1
            self.is_deleted = 0
            self.save()

        else:
            m = Messages.objects.get(pk=id)
            m.is_spam = 1
            m.is_deleted = 0
            m.save()

    def mark_as_not_spam(self, id=None):
        if id is None:  # uzywamy self.
            self.is_spam = 0
            self.is_deleted = 0
            self.save()

        else:
            m = Messages.objects.get(pk=id)
            m.is_spam = 0
            m.is_deleted = 0
            m.save()

    def mark_as_deleted(self, id=None):
        if id is None:  # uzywamy self.
            self.is_deleted = 1
            self.is_spam = 0
            self.save()

        else:
            m = Messages.objects.get(pk=id)
            m.is_deleted = 1
            m.is_spam = 0
            m.save()

    def mark_as_not_deleted(self, id=None):
        if id is None:  # uzywamy self.
            self.is_deleted = 0
            self.is_spam = 0
            self.save()

        else:
            m = Messages.objects.get(pk=id)
            m.is_deleted = 0
            m.is_spam = 0
            m.save()


class Images(models.Model):
    name = models.CharField(blank=False, null=False, max_length=30)
    description = models.CharField(blank=True, max_length=255)
    exif = models.TextField(blank=True)
    image = models.ImageField(upload_to='tests/images/', blank=True, null=False)
    link = models.CharField(blank=True, max_length=255)
    height = models.IntegerField(blank=True, null=False)
    width = models.IntegerField(blank=True, null=False)

    dst_id = models.IntegerField(blank=True, null=False)
    dst = models.CharField(blank=True, max_length=20)
    user = models.ForeignKey(User)
    username = models.CharField(blank=True, max_length=100)

    # possible DST's
    # MATCH, PLAYER, LEAGUE, FLAG, NEWS, LEAGUE_LOGO, TEAM_LOGO, AVATAR
    group_id = models.IntegerField(blank=True, null=True, default=0)
    ip = models.CharField(blank=True, null=True, max_length=20, default='127.0.0.1')
    browser = models.CharField(blank=True, null=True, max_length=120, default='')
    is_accepted = models.BooleanField(default=False)
    is_processed = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'images'
        verbose_name = 'Image'

    class Admin:
        pass

    def update_counter(self):
        if self.dst == 'news':
            news = News.objects.get(pk=self.dst_id)
            news.images_count = Images.objects.filter(dst=self.dst, dst_id=self.dst_id, is_accepted=1,
                                                      is_deleted=0).count()
            news.save()

        elif self.dst == 'match':
            match = Matches.objects.get(pk=self.dst_id)
            match.images_count = Images.objects.filter(dst=self.dst, dst_id=self.dst_id, is_accepted=1,
                                                       is_deleted=0).count()
            match.save()

    def accept(self):
        self.is_accepted = 1
        self.is_deleted = 0
        self.save()

        # update counters
        self.update_counter()

        # activity points
        if self.dst == 'news':
            AccountsActivity(user_id=self.user.id, username=str(self.user), dst_id=self.id, action_type='news_image',
                             points='3', is_calculated=0, is_confirmed=1, created_at=self.created_at).save()

        elif self.dst == 'match':
            AccountsActivity(user_id=self.user.id, username=str(self.user), dst_id=self.id, action_type='match_image',
                             points='3', is_calculated=0, is_confirmed=1, created_at=self.created_at).save()

    def unaccept(self):
        self.is_accepted = 0
        self.save()
        self.update_counter()

    def mark_as_deleted(self):
        self.is_deleted = 1
        self.save()
        self.update_counter()

    def mark_as_not_deleted(self):
        self.is_deleted = 0
        self.save()
        self.update_counter


class Videos(models.Model):
    name = models.CharField(blank=True, max_length=30)
    description = models.CharField(blank=True, max_length=255)
    content = models.TextField(blank=True)
    url = models.SlugField(prepopulate_from=("",), max_length=300)
    lang = models.CharField(blank=True, max_length=2, default='pl')
    # possible DST's
    # MATCH, PLAYER, LEAGUE, NEWS, USER, VAR, OTHER
    dst_id = models.IntegerField(blank=True, null=False, default=0)
    dst = models.CharField(blank=True, max_length=20)
    cat_id = models.IntegerField(blank=True, null=False, default=0)
    user = models.ForeignKey(User)
    username = models.CharField(blank=True, max_length=100)
    group_id = models.IntegerField(blank=True, null=True, default=0)
    view_count = models.IntegerField(default=0)
    ip = models.CharField(blank=True, null=True, max_length=20, default='127.0.0.1')
    browser = models.CharField(blank=True, null=True, max_length=120, default='')
    is_accepted = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_temp = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(default=datetime.datetime.now())

    class Admin:
        pass

    class Meta:
        db_table = 'videos'
        verbose_name = 'Video'

    # ---

    def get_latest(self, limit=10):
        vids = Videos.objects.filter(is_accepted=1, is_deleted=0).order_by('-published_at')[:limit]
        return vids

    def get_videos(self, cat_name=None, username=None):

        if cat_name is not None:
            if settings.LANGUAGE_CODE == 'pl':
                try:
                    cat_check = VideoCategories.objects.get(name_pl_url=cat_name)
                except:
                    return VideoCategories()
                vids = Videos.objects.filter(is_accepted=1, is_deleted=0, dst='other', dst_id=0,
                                             cat_id=cat_check.id).order_by('-published_at')
            else:
                try:
                    cat_check = VideoCategories.objects.get(name_en_url=cat_name)
                except:
                    return VideoCategories()
                vids = Videos.objects.filter(is_accepted=1, is_deleted=0, dst='other', dst_id=0,
                                             cat_id=cat_check.id).order_by('-published_at')

        elif username is not None:
            try:
                user_check = User.objects.get(username=username)
            except:
                return ()

            vids = Videos.objects.filter(is_accepted=1, is_deleted=0, dst='other', dst_id=0,
                                         username=username).order_by('-published_at')
        else:
            vids = Videos.objects.filter(is_accepted=1, is_deleted=0, dst='other', dst_id=0).order_by('-published_at')

        return vids

    # ---

    def inform_moderators(self, video_id):
        mail_content = """Użytkownik dodał film. Link: http://www.24gole.pl/admin/main/videos/%s/""" % video_id
        Mailing().add(rcp="marcin@24gole.pl", subject=u"Użytkownik dodał film", content=mail_content,
                      sender="24gole <marek@24gole.pl>")
        Mailing().add(rcp="marek@24gole.pl", subject=u"Użytkownik dodał film", content=mail_content,
                      sender="24gole <marek@24gole.pl>")

    def update_counter(self):
        if self.dst == 'news':
            news = News.objects.get(pk=self.dst_id)
            news.videos_count = Videos.objects.filter(dst=self.dst, dst_id=self.dst_id, is_accepted=1,
                                                      is_deleted=0).count()
            news.save()

        elif self.dst == 'match':
            match = Matches.objects.get(pk=self.dst_id)
            match.videos_count = Videos.objects.filter(dst=self.dst, dst_id=self.dst_id, is_accepted=1,
                                                       is_deleted=0).count()
            match.save()

    def accept(self):
        self.is_accepted = 1
        self.is_deleted = 0
        self.published_at = datetime.datetime.now()
        self.save()

        # update counters
        self.update_counter()

        # send email
        if self.lang == 'pl':
            mail_content = """Dziękujemy, film który dodałeś/aś jest już widoczny na stronie.
			
Redakcja 24gole"""
            Mailing().add(rcp=self.user.email, subject='Twój film jest już widoczny na stronie', content=mail_content,
                          sender="Moderacja 24gole.pl <marek@24gole.pl>")
        else:
            mail_content = """Thank you, content you've added is visible on the site from now.
			
24goals team"""
            Mailing().add(rcp=self.user.email, subject='Your video is now visible on the site', content=mail_content,
                          sender="Moderator 24goals.com <marek@24goals.com>")

        # activity points
        if self.dst == 'news':
            AccountsActivity(user_id=self.user.id, username=str(self.user), dst_id=self.id, action_type='news_video',
                             points='5', is_calculated=0, is_confirmed=1, created_at=self.published_at).save()

        elif self.dst == 'match':
            AccountsActivity(user_id=self.user.id, username=str(self.user), dst_id=self.id, action_type='match_video',
                             points='5', is_calculated=0, is_confirmed=1, created_at=self.published_at).save()

        elif self.dst == 'other':
            AccountsActivity(user_id=self.user.id, username=str(self.user), dst_id=self.id, action_type='video',
                             points='5', is_calculated=0, is_confirmed=1, created_at=self.published_at).save()

    def unaccept(self):
        self.is_accepted = 0
        self.save()
        self.update_counter()

    def mark_as_deleted(self):
        self.is_deleted = 1
        self.save()
        self.update_counter()

    def mark_as_not_deleted(self):
        self.is_deleted = 0
        self.save()
        self.update_counter()


class VideoCategories(models.Model):
    name_en = models.CharField(blank=True, max_length=100)
    name_en_url = models.CharField(blank=True, max_length=100)
    name_pl = models.CharField(blank=True, max_length=100)
    name_pl_url = models.CharField(blank=True, max_length=100)

    class Admin:
        pass

    class Meta:
        db_table = 'video_categories'
        verbose_name = 'VideoCategory'
        verbose_name_plural = 'VideoCategories'

    def __unicode__(self):
        return self.name_pl

    def get_categories(self):
        if settings.LANGUAGE_CODE == 'pl':
            return VideoCategories.objects.all().order_by('name_pl')
        else:
            return VideoCategories.objects.all().order_by('name_en')


class LeagueTable(models.Model):
    league = models.ForeignKey("Leagues")
    season = models.ForeignKey("Seasons")
    team = models.ForeignKey("Teams")
    table_type = models.IntegerField(default=0)

    position = models.IntegerField(blank=True, null=False, default=0)
    points = models.IntegerField(blank=True, null=False, default=0)
    gp = models.IntegerField(blank=True, null=False, default=0)  # games played
    w = models.IntegerField(blank=True, null=False, default=0)  # won
    d = models.IntegerField(blank=True, null=False, default=0)  # draws
    l = models.IntegerField(blank=True, null=False, default=0)  # losses

    gs = models.IntegerField(blank=True, null=False, default=0)  # goals scored
    ga = models.IntegerField(blank=True, null=False, default=0)  # goals against

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Admin: pass

    class Meta:
        db_table = 'league_table'


class CupsTable(models.Model):
    GROUPS = (
        ('a', 'Group A'),
        ('b', 'Group B'),
        ('c', 'Group C'),
        ('d', 'Group D'),
        ('e', 'Group E'),
        ('f', 'Group F'),
        ('g', 'Group G'),
        ('h', 'Group H'),
    )

    league = models.ForeignKey("Leagues")
    season = models.ForeignKey("Seasons")
    team = models.ForeignKey("Teams")
    groups_name = models.CharField(blank=True, max_length=1, choices=GROUPS)

    position = models.IntegerField(blank=True, null=False, default=0)
    points = models.IntegerField(blank=True, null=False, default=0)
    gp = models.IntegerField(blank=True, null=False, default=0)  # games played
    w = models.IntegerField(blank=True, null=False, default=0)  # won
    d = models.IntegerField(blank=True, null=False, default=0)  # draws
    l = models.IntegerField(blank=True, null=False, default=0)  # losses

    gs = models.IntegerField(blank=True, null=False, default=0)  # goals scored
    ga = models.IntegerField(blank=True, null=False, default=0)  # goals against

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Admin: pass

    class Meta:
        db_table = 'cups_table'


class Newsletter(models.Model):
    email = models.EmailField()
    ip = models.IPAddressField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Admin: pass

    class Meta:
        db_table = 'newsletter'
        verbose_name = 'newsletter'
        verbose_name_plural = 'newsletters'

    def __unicode__(self): return email


class Mailing(models.Model):
    sender = models.CharField(blank=True, max_length=100)
    rcp = models.EmailField()
    subject = models.CharField(blank=True, max_length=255)
    content = models.TextField(blank=True)
    is_sent = models.SmallIntegerField(blank=True, null=True, default=0)
    ip = models.IPAddressField(blank=True)

    sent_at = models.DateTimeField(blank=True, default=datetime.datetime(1970, 1, 1, 0, 0, 0))
    created_at = models.DateTimeField(auto_now_add=True)

    class Admin: pass

    class Meta:
        db_table = 'mailing'

    def __unicode__(self):
        return "From: %s | To: %s | Subject: %s (sent: %s)" % (self.sender, self.rcp, self.subject, self.is_sent)

    def add(self, rcp, subject, content='', ip='127.0.0.1', sender="24gole <marek@24gole.pl"):
        self.rcp = rcp
        self.subject = subject
        self.content = content
        self.ip = ip
        self.sender = sender
        self.is_sent = 0
        self.sent_at = datetime.datetime(1970, 1, 1, 0, 0, 0)
        self.save()


class MailingTemplates(models.Model):
    name = models.CharField(blank=True, max_length=50)
    subject = models.CharField(blank=True, max_length=100)
    content = models.TextField(blank=True)

    class Admin: pass

    class Meta:
        db_table = 'mailing_templates'

    def __unicode__(self): return self.name


class AutoReplies(models.Model):
    TYPES = (
        ('n', 'News'),
    )

    name = models.CharField(blank=True, max_length=100)
    type = models.CharField(blank=True, max_length=1, choices=TYPES)
    content_en = models.TextField(blank=True)
    content_pl = models.TextField(blank=True)

    class Admin: pass

    class Meta:
        db_table = 'mailing_auto_replies'

    def __unicode__(self): return self.name


# logging part

class Logs(models.Model):
    path = models.CharField(blank=True, max_length=255)
    content = models.TextField(blank=True, default='')
    ip = models.CharField(blank=True, max_length=20, default='127.0.0.1')
    browser = models.CharField(blank=True, max_length=120, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    class Admin: pass

    class Meta:
        db_table = 'logs'
        verbose_name = 'log'
        verbose_name_plural = 'logs'

    def __unicode__(self): return created_at


class PointsLog(models.Model):
    TYPE = (
        ('p', 'Picks'),
    )

    type = models.CharField(max_length=1, choices=TYPE)
    type_id = models.IntegerField(blank=True, null=True)
    content = models.CharField(blank=True, max_length=100, default='')
    comment = models.CharField(blank=True, max_length=255, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Admin: pass

    class Meta:
        db_table = "logs_points"
        verbose_name = "Points_Log"


class UserActivity(models.Model):
    user = models.CharField(blank=True, max_length=100)
    request_url = models.CharField(blank=True, max_length=500)
    referer_url = models.CharField(blank=True, max_length=500)
    client_address = models.CharField(blank=True, max_length=100)
    client_host = models.CharField(blank=True, max_length=100)
    browser_info = models.CharField(blank=True, max_length=500)
    error = models.TextField(blank=True)
    date = models.DateTimeField(blank=True)

    class Admin: pass

    class Meta:
        db_table = "logs_user_activity"

    def __unicode__(self): return str(self.user) + '/' + str(self.date)


class BanList(models.Model):
    ip = models.CharField(blank=True, max_length=16)
    username = models.CharField(blank=True, max_length=100)
    is_active = models.BooleanField(default=True)

    class Admin: pass

    class Meta:
        db_table = 'ban_list'

    def __unicode__(self): return str(self.ip) + '|' + str(self.username)
