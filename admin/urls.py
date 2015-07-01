from django.conf import settings

from django.conf.urls.defaults import *
from myscore.admin.views import *

if settings.USE_I18N:
    i18n_view = 'django.views.i18n.javascript_catalog'
else:
    i18n_view = 'django.views.i18n.null_javascript_catalog'

urlpatterns = patterns('myscore.admin.views',

                       (r'^main/stats/moderate/$', 'stats.moderate'),
                       (r'^main/matches/$', 'matches.index'),
                       (r'^main/matches/multi_edit/(?P<ids>[\d,]+)/((?P<action>\w+)/)?((?P<action_id>\d+)/)?$',
                        'matches.multi_edit'),
                       (r'^main/comments/$', 'comments.index'),
                       (r'^main/comments/(?P<comment_id>\d+)/accept/$', 'comments.accept'),
                       (r'^main/news/$', 'news.index'),
                       (r'^main/news/add/$', 'news.add'),
                       (r'^main/news/(?P<news_id>[\d]+)/$', 'news.edit'),
                       (r'^main/news/(?P<news_id>[\d]+)/accept/$', 'news.accept'),
                       (r'^main/news/(?P<news_id>[\d]+)/refuse/$', 'news.refuse'),
                       (r'^main/videos/$', 'videos.index'),
                       (r'^main/videos/(?P<video_id>[\d]+)/$', 'videos.edit'),
                       (r'^main/videos/(?P<video_id>[\d]+)/accept/$', 'videos.accept'),
                       (r'^main/videos/(?P<video_id>[\d]+)/preview/$', 'videos.preview'),
                       (r'^main/images/$', 'images.index'),
                       (r'^main/images/(?P<image_id>[\d]+)/accept/$', 'images.accept'),
                       (r'^main/matches/multi_add/$', 'matches.multi_add'),
                       (r'^main/matches/multi_add/(?P<league_id>[\d]+)/$', 'matches.multi_add'),
                       (r'^main/teams/multi_edit/$', 'teams.multi_edit'),
                       (r'^main/leagues/multi_edit/$', 'leagues.multi_edit'),
                       (r'^main/seasons/multi_edit/$', 'seasons.multi_edit'),
                       (r'^main/countries/multi_edit/$', 'countries.multi_edit'),
                       (r'^main/languages/multi_edit/$', 'languages.multi_edit'),
                       (r'^main/teams/multi_add/$', 'teams.multi_add'),
                       (r'^main/players/multi_add/$', 'players.multi_add'),
                       (r'^main/players/multi_edit/(?P<team_id>[\d]+)/$', 'players.multi_edit'),
                       (r'^main/players/transfers/(?P<team_id>[\d]+)/$', 'players.transfers'),
                       (r'^main/mailing/send/$', 'mailing.send'),
                       (r'^main/mailing/generate/$', 'mailing.generate'),
                       (r'^', include('django.contrib.admin.urls')),
                       )

del i18n_view
