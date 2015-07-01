from django.conf import settings

from django.conf.urls.defaults import *
from myscore.main.views import *

urlpatterns = patterns('',

                       (r'^static/(?P<path>.*)$', 'django.views.static.serve',
                        {'document_root': settings.MEDIA_ROOT, 'show_indexes': False}),
                       (r'^robots.txt$', 'django.views.static.serve',
                        {'path': "/static/sitemaps/robots.txt", 'document_root': settings.MEDIA_ROOT,
                         'show_indexes': False}),
                       (r'^(sitemap[\w-]*.[\w]{3})$', 'myscore.main.views.main.sitemap'),

                       (r'^api/', include('myscore.api.urls')),
                       (r'^admin/', include('myscore.admin.urls')),
                       (r'^scripts/', include('myscore.scripts.urls')),
                       (r'^i18n/', include('django.conf.urls.i18n')),
                       # http://www.djangoproject.com/documentation/i18n/#the-set-language-redirect-view

                       (r'^$', 'myscore.main.views.main.index'),

                       # / [EN]
                       (r'^press/$', 'myscore.main.views.about.for_press'),
                       (r'^contact/$', 'myscore.main.views.about.contact'),
                       (r'^about/$', 'myscore.main.views.about.about_us'),
                       (r'^rules/$', 'myscore.main.views.about.rules'),
                       (r'^help/(?P<subject>[\w-]+)/$', 'myscore.main.views.about.help'),
                       # (r'^contest/$', 'myscore.main.views.about.contest'),
                       # / [PL]
                       (r'^dla-prasy/$', 'myscore.main.views.about.for_press'),
                       (r'^kontakt/$', 'myscore.main.views.about.contact'),
                       (r'^o-nas/$', 'myscore.main.views.about.about_us'),
                       (r'^zasady/$', 'myscore.main.views.about.rules'),
                       (r'^pomoc/(?P<subject>[\w-]+)/$', 'myscore.main.views.about.help'),
                       # (r'^konkurs/$', 'myscore.main.views.about.contest'),

                       # / [EN]
                       (r'^register/$', 'myscore.main.views.main.register'),
                       (r'^register/complete/$', 'myscore.main.views.main.registered'),
                       (r'^register/completed/$', 'myscore.main.views.main.registered'),
                       (r'^register/activate/(?P<activation_key>\w+)/$', 'myscore.main.views.main.activate'),

                       # / [PL]
                       (r'^rejestracja/$', 'myscore.main.views.main.register'),
                       (r'^rejestracja/kompletna/$', 'myscore.main.views.main.registered'),
                       (r'^rejestracja/aktywacja/(?P<activation_key>\w+)/$', 'myscore.main.views.main.activate'),

                       (r'^logout/$', 'myscore.main.views.main.log_out'),
                       (r'^login/$', 'myscore.main.views.main.log_in'),

                       # AJAX
                       (r'^ajax-news-comments/(?P<news_id>\d+)/$', 'myscore.main.modules.ajax.news.comments'),
                       (r'^ajax-match-comments/(?P<match_id>\d+)/$', 'myscore.main.modules.ajax.matches.comments'),
                       (r'^ajax-user-box/(?P<username>\w+)/$', 'myscore.main.modules.ajax.accounts.overlay'),

                       # MATCHES
                       # / [EN]
                       (r'^matches/$', 'myscore.main.views.matches.index'),
                       (r'^matches/send/$', 'myscore.main.views.matches.send'),
                       (r'^match/(?P<home_team>[\w-]+)/(?P<away_team>[\w-]+)/(?P<match_id>\d{1,6})/$',
                        'myscore.main.views.matches.details'),
                       (r'^match/(?P<match_id>\d{1,6})/add_photos/((?P<step>step_\d{1})/)?$',
                        'myscore.main.views.matches.add_photos'),
                       (r'^match/(?P<match_id>\d{1,6})/add_videos/$', 'myscore.main.views.matches.add_videos'),
                       (
                       r'^matches/((?P<country_name>(poland|germany|netherlands|france|england|spain|italy|europe){1})/)?((?P<league_name>(orange-ekstraklasa|2-liga|eredivisie|jupiler-league|bundesliga|2-bundesliga|ligue-1|ligue-2|premiership|league-one|primera-division|segunda-division|serie-a|serie-b|champions-league|uefa-cup){1})/)?((?P<match_date>\d{4}-\d{2}-\d{2})/)?((?P<status_name>(started|finished|upcoming){1})/)?$',
                       'myscore.main.views.matches.index'),
                       # / [PL]
                       (r'^mecze/$', 'myscore.main.views.matches.index'),
                       (r'^mecze/send/$', 'myscore.main.views.matches.send'),
                       (r'^mecz/(?P<home_team>[\w-]+)/(?P<away_team>[\w-]+)/(?P<match_id>\d{1,6})/$',
                        'myscore.main.views.matches.details'),
                       (r'^mecz/(?P<home_team>[\w-]+)/(?P<away_team>[\w-]+)/(?P<match_id>\d{1,6})/rejestracja/$',
                        'myscore.main.views.scripts.match_detail_old_url_redirector'),
                       (r'^mecz/(?P<match_id>\d{1,6})/add_photos/((?P<step>step_\d{1})/)?$',
                        'myscore.main.views.matches.add_photos'),
                       (r'^mecz/(?P<match_id>\d{1,6})/add_videos/$', 'myscore.main.views.matches.add_videos'),
                       (
                       r'^mecze/(?P<league_name>(polska|niemiecka|holenderska|francuska|angielska|hiszpanska|wloska|liga-mistrzow|puchar-uefa){1})/((?P<match_date>\d{4}-\d{2}-\d{2})/)?((?P<status_name>(trwajace|zakonczone|nadchodzace){1})/)?$',
                       'myscore.main.views.scripts.match_old_url_redirector'),
                       (
                       r'^mecze/((?P<country_name>(polska|niemcy|holandia|francja|anglia|hiszpania|wlochy|europa){1})/)?((?P<league_name>(orange-ekstraklasa|2-liga|eredivisie|jupiler-league|bundesliga|2-bundesliga|ligue-1|ligue-2|premiership|league-one|primera-division|segunda-division|serie-a|serie-b|liga-mistrzow|champions-league|puchar-uefa|uefa-cup){1})/)?((?P<match_date>\d{4}-\d{2}-\d{2})/)?((?P<status_name>(trwajace|zakonczone|nadchodzace){1})/)?$',
                       'myscore.main.views.matches.index'),

                       # NEWS
                       (
                       r'^news/(?P<league_name>(polska|niemiecka|holenderska|francuska|angielska|hiszpanska|wloska|liga-mistrzow|puchar-uefa){1})/((?P<news_date>\d{4}-\d{2}-\d{2})/)?$',
                       'myscore.main.views.scripts.news_old_url_redirector'),
                       (
                       r'^news/((?P<country_name>(poland|polska|germany|niemcy|netherlands|holandia|france|francja|england|anglia|spain|hiszpania|italy|wlochy|europe|europa){1})/)?((?P<league_name>(orange-ekstraklasa|2-liga|eredivisie|jupiler-league|bundesliga|2-bundesliga|ligue-1|ligue-2|premiership|league-one|primera-division|segunda-division|serie-a|serie-b|champions-league|liga-mistrzow|uefa-cup|puchar-uefa){1})/)?((?P<news_date>\d{4}-\d{2}-\d{2})/)?((page-|strona-)(?P<page_no>\d{1,})/)?$',
                       'myscore.main.views.news.index'),
                       (r'^news/search/(?P<search_query>\w{3,})/(page-(?P<page_no>\d{1,})/)?$',
                        'myscore.main.views.news.index'),
                       (r'^news/szukaj/(?P<search_query>\w{3,})/(strona-(?P<page_no>\d{1,})/)?$',
                        'myscore.main.views.news.index'),
                       (r'^news/add/((?P<step>(1|2|3){1})/)?$', 'myscore.main.views.news.add'),
                       (r'^news/dodaj/((?P<step>(1|2|3){1})/)?$', 'myscore.main.views.news.add'),
                       (r'^news/(?P<news_id>\d{1,6})/comments/add/$', 'myscore.main.views.news.add_comment'),
                       (r'^news/(?P<news_id>\d{1,6})/add_photos/((?P<step>step_\d{1})/)?$',
                        'myscore.main.views.news.add_photos'),
                       (r'^news/(?P<news_id>\d{1,6})/add_videos/$', 'myscore.main.views.news.add_videos'),
                       (r'^news/(?P<news_id>\d+)/[\w-]+/((?P<show_full>(images|videos|comments))/)?$',
                        'myscore.main.views.news.details'),

                       # TEAMS
                       (r'^(teams|druzyny)/((?P<country_name>[\w-]+)/)?$', 'myscore.main.views.teams.leagues_list'),
                       (r'^(teams|druzyny)/(?P<country_name>[\w-]+)/(?P<league_name>[\w-]+)/((?P<season>[\d-]{4,})/)?$',
                        'myscore.main.views.teams.teams_list'),
                       # (r'^team/(?P<country_name>[\w-]+)/(?P<team_name>[\w-]+)/((?P<season>[\d-]{4,})/)?$', 'myscore.main.views.teams.details'),
                       (r'^(team|druzyna)/(?P<team_name>[\w-]+)/((?P<season>[\d-]{4,})/)?$',
                        'myscore.main.views.teams.details'),
                       (r'^(team|druzyna)/(?P<team_name>[\w-]+)/(results|wyniki)/((?P<season>[\d-]{4,})/)?$',
                        'myscore.main.views.teams.results'),
                       (r'^(team|druzyna)/(?P<team_name>[\w-]+)/(fixtures|terminarz)/((?P<season>[\d-]{4,})/)?$',
                        'myscore.main.views.teams.fixtures'),
                       (r'^(team|druzyna)/(?P<team_name>[\w-]+)/(news|wiadomosci)/((?P<season>[\d-]{4,})/)?$',
                        'myscore.main.views.teams.news'),
                       (
                       r'^(team|druzyna)/(?P<team_name>[\w-]+)/(info|informations|informacje)/((?P<season>[\d-]{4,})/)?$',
                       'myscore.main.views.teams.info'),
                       (r'^(team|druzyna)/(?P<team_name>[\w-]+)/(tables|tabele)/((?P<season>[\d-]{4,})/)?$',
                        'myscore.main.views.teams.tables'),

                       # USER
                       # (r'^messages/$', 'myscore.main.views.messages.list'),
                       # (r'^messages/page(?P<page>\d{1,4})/$', 'myscore.main.views.messages.list'),
                       # (r'^messages/(?P<sender>\w+)/$', 'myscore.main.views.messages.list'),
                       # (r'^messages/(?P<sender>\w+)/page(?P<page>\d{1,4})/$', 'myscore.main.views.messages.list'),

                       # (r'^message/(?P<msg_id>\d{1,4})', 'myscore.main.views.messages.send'),
                       # (r'^messages/send', 'myscore.main.views.messages.send'),

                       # PICKS
                       (
                       r'^(typer|predictions)/((?P<league_name>(polska|polish|niemiecka|german|francuska|french|angielska|english|hiszpanska|spanish|wloska|italian|orange-ekstraklasa|bundesliga|ligue-1|premiership|primera-division|serie-a|liga-mistrzow|champions-league|puchar-uefa|uefa-cup|euro-2008){1})/)?((?P<when_type>(miesiac|month))/)?((?P<when>(styczen|january|luty|february|marzec|march|kwiecien|april|maj|may|czerwiec|june|lipiec|july|sierpien|august|wrzesien|september|pazdziernik|october|listopad|november|grudzien|december){1})/)?$',
                       'myscore.main.views.picks.index'),
                       (
                       r'^(typer|predictions)/((?P<league_name>(polska|polish|niemiecka|german|francuska|french|angielska|english|hiszpanska|spanish|wloska|italian|orange-ekstraklasa|bundesliga|ligue-1|premiership|primera-division|serie-a|liga-mistrzow|champions-league|puchar-uefa|uefa-cup|euro-2008){1})/)?((?P<when_type>(tydzien|week))/)?((?P<when>\d{1,2})/)?$',
                       'myscore.main.views.picks.index'),

                       # FANS LEAGUE
                       # / [EN]
                       (r'^supporters/(?P<team_name>[\w-]+)/$', 'myscore.main.views.fans.show_supporters'),
                       (r'^supporters-league/((?P<table_type>(points|average|supporters-number))/)?$',
                        'myscore.main.views.fans.show_tables'),
                       # / [PL]
                       (r'^kibice/(?P<team_name>[\w-]+)/$', 'myscore.main.views.fans.show_supporters'),
                       (r'^liga-kibicow/((?P<table_type>(punkty|srednia|liczba-kibicow))/)?$',
                        'myscore.main.views.fans.show_tables'),

                       # VIDEOS
                       # / [EN]
                       (r'^videos/(page-(?P<page_no>\d{1,})/)?$', 'myscore.main.views.videos.index',
                        {'cat_name': None, 'username': None}),
                       (r'^videos/search/(?P<search_query>\w{3,})/(page-(?P<page_no>\d{1,})/)?$',
                        'myscore.main.views.videos.index', {'cat_name': None, 'username': None}),
                       (r'^videos/category/(?P<cat_name>[\w-]+)/((page-)(?P<page_no>\d{1,})/)?$',
                        'myscore.main.views.videos.index', {'username': None}),
                       (r'^videos/user/(?P<username>[\w-]+)/((page-)(?P<page_no>\d{1,})/)?$',
                        'myscore.main.views.videos.index', {'cat_name': None}),
                       (r'^videos/add/((?P<cat_name>[\w-]+)/)?$', 'myscore.main.views.videos.add', {'step': 0}),
                       (r'^videos/add/(?P<step>[1-2]{1})/((?P<cat_name>[\w-]+)/)?$', 'myscore.main.views.videos.add'),
                       (r'^videos/added/?$', 'myscore.main.views.videos.add', {'step': 3}),
                       (r'^video/(?P<video_id>[\d]{1,})/(?P<video_name>[\w-]{1,})/$',
                        'myscore.main.views.videos.details'),
                       # / [PL]
                       (r'^filmy/(strona-(?P<page_no>\d{1,})/)?$', 'myscore.main.views.videos.index',
                        {'cat_name': None, 'username': None}),
                       (r'^filmy/szukaj/(?P<search_query>\w{3,})/(strona-(?P<page_no>\d{1,})/)?$',
                        'myscore.main.views.videos.index', {'cat_name': None, 'username': None}),
                       (r'^filmy/kategoria/(?P<cat_name>[\w-]+)/(strona-(?P<page_no>\d{1,})/)?$',
                        'myscore.main.views.videos.index', {'username': None}),
                       (r'^filmy/uzytkownik/(?P<username>[\w]+)/(strona-(?P<page_no>\d{1,})/)?$',
                        'myscore.main.views.videos.index', {'cat_name': None}),
                       (r'^filmy/dodaj/((?P<cat_name>[\w-]+)/)?$', 'myscore.main.views.videos.add', {'step': 0}),
                       (r'^filmy/dodaj/(?P<step>[1-2]{1})/((?P<cat_name>[\w-]+)/)?$', 'myscore.main.views.videos.add'),
                       (r'^filmy/dodano/$', 'myscore.main.views.videos.add', {'step': 3}),
                       (r'^film/(?P<video_id>[\d]{1,})/(?P<video_name>[\w-]{1,})/$',
                        'myscore.main.views.videos.details'),

                       # ACCOUNT
                       (r'^dashboard/$', 'myscore.main.views.accounts.my_profile'),

                       # MESSAGES
                       # / [EN]
                       (r'^user/messages/((?P<friend>\w{3,})/)?(page-(?P<page>\d)/)?$',
                        'myscore.main.views.messages.inbox'),
                       (r'^user/messages/inbox/((?P<friend>\w{3,})/)?(page-(?P<page>\d)/)?$',
                        'myscore.main.views.messages.inbox'),
                       (r'^user/messages/outbox/((?P<friend>\w{3,})/)?(page-(?P<page>\d)/)?$',
                        'myscore.main.views.messages.outbox'),
                       (r'^user/messages/spam/(page-(?P<page>\d)/)?$', 'myscore.main.views.messages.spam'),
                       (r'^user/messages/trash/(page-(?P<page>\d)/)?$', 'myscore.main.views.messages.trash'),
                       (r'^user/message/(?P<msg_id>\d+)/$', 'myscore.main.views.messages.details'),
                       (r'^user/message/(?P<username>\w{3,})/((?P<reply_of>\d+)/)?$',
                        'myscore.main.views.messages.send'),

                       # / [PL]
                       (r'^uzytkownik/wiadomosci/(tylko-od-(?P<friend>\w{3,})/)?(strona-(?P<page>\d)/)?$',
                        'myscore.main.views.messages.inbox'),
                       (r'^uzytkownik/wiadomosci/przychodzace/(tylko-od-(?P<friend>\w{3,})/)?(strona-(?P<page>\d)/)?$',
                        'myscore.main.views.messages.inbox'),
                       (r'^uzytkownik/wiadomosci/wychodzace/(tylko-do-(?P<friend>\w{3,})/)?(strona-(?P<page>\d)/)?$',
                        'myscore.main.views.messages.outbox'),
                       (r'^uzytkownik/wiadomosci/spam/(strona-(?P<page>\d)/)?$', 'myscore.main.views.messages.spam'),
                       (r'^uzytkownik/wiadomosci/kosz/(strona-(?P<page>\d)/)?$', 'myscore.main.views.messages.trash'),
                       (r'^uzytkownik/wiadomosc/(?P<msg_id>\d+)/$', 'myscore.main.views.messages.details'),
                       (r'^uzytkownik/wiadomosc/(?P<username>\w{3,})/((?P<reply_of>\d+)/)?$',
                        'myscore.main.views.messages.send'),

                       (r'^newsletter/$', 'myscore.main.views.newsletter.add'),

                       # / [EN]
                       (r'^user/(?P<username>\w{3,})/$', 'myscore.main.views.accounts.details'),
                       (r'^user/(?P<username>\w{3,})/picks/$', 'myscore.main.views.accounts.details_picks',
                        {'range': 'all'}),
                       (r'^user/(?P<username>\w{3,})/picks/archive/$', 'myscore.main.views.accounts.details_picks',
                        {'range': 'archive'}),
                       (r'^user/(?P<username>\w{3,})/picks/pending/$', 'myscore.main.views.accounts.details_picks',
                        {'range': 'pending'}),
                       (r'^user/(?P<username>\w{3,})/stats/$', 'myscore.main.views.accounts.details_stats'),
                       (r'^user/(?P<username>\w{3,})/classification/month/$',
                        'myscore.main.views.accounts.details_classification', {'range': 'month', 'limit': 5}),
                       (r'^user/(?P<username>\w{3,})/classification/general/$',
                        'myscore.main.views.accounts.details_classification', {'range': 'all', 'limit': 5}),
                       (r'^user/(?P<username>\w{3,})/activity/$', 'myscore.main.views.accounts.details_activity'),
                       (r'^user/(?P<username>\w{3,})/compare/(?P<other_username>\w{3,})/$',
                        'myscore.main.views.accounts.details_compare'),
                       (r'^users/(?P<letter>\w{1})/$', 'myscore.main.views.accounts.show_users'),
                       (r'^users/$', 'myscore.main.views.accounts.show_users'),
                       # / [PL]
                       (r'^uzytkownik/(?P<username>\w{3,})/$', 'myscore.main.views.accounts.details'),
                       (r'^uzytkownik/(?P<username>\w{3,})/typy/$', 'myscore.main.views.accounts.details_picks',
                        {'range': 'all'}),
                       (r'^uzytkownik/(?P<username>\w{3,})/typy/archiwalne/$',
                        'myscore.main.views.accounts.details_picks', {'range': 'archive'}),
                       (
                       r'^uzytkownik/(?P<username>\w{3,})/typy/aktualne/$', 'myscore.main.views.accounts.details_picks',
                       {'range': 'pending'}),
                       (r'^uzytkownik/(?P<username>\w{3,})/statystyki/$', 'myscore.main.views.accounts.details_stats'),
                       (r'^uzytkownik/(?P<username>\w{3,})/klasyfikacje/miesieczna/$',
                        'myscore.main.views.accounts.details_classification', {'range': 'month', 'limit': 10}),
                       (r'^uzytkownik/(?P<username>\w{3,})/klasyfikacje/generalna/$',
                        'myscore.main.views.accounts.details_classification', {'range': 'all', 'limit': 10}),
                       (
                       r'^uzytkownik/(?P<username>\w{3,})/aktywnosc/$', 'myscore.main.views.accounts.details_activity'),
                       (r'^uzytkownik/(?P<username>\w{3,})/porownaj/(?P<other_username>\w{3,})/$',
                        'myscore.main.views.accounts.details_compare'),
                       (r'^uzytkownicy/(?P<letter>\w{1})/$', 'myscore.main.views.accounts.show_users'),
                       (r'^uzytkownicy/$', 'myscore.main.views.accounts.show_users'),

                       (r'^RefreshPlayerNames/$', 'myscore.main.views.scripts.refresh_player_names'),
                       (r'^RegenerateUsersTable/$', 'myscore.libs.users_tables.regenerate_users_table'),
                       (r'^RegenerateFansTable/$', 'myscore.main.views.scripts.regenerate_fans_table'),
                       (r'^RefreshOnline/$', 'myscore.main.views.scripts.refresh_who_online'),

                       )
