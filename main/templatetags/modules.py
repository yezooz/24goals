# from django.template import Node, Variable
# from django.template import TemplateSyntaxError, TokenParser, Library
# from django.template import TOKEN_TEXT, TOKEN_VAR
from django.template import Library
from django.conf import settings

register = Library()

# --- NEWS

@register.inclusion_tag('modules/render.html')
def latest_league_headlines(league_id=0, limit=10, start_from=0):
    from myscore.main.modules.news import related_news

    return {"render": related_news.render_league(league_id, limit, start_from)}


@register.inclusion_tag('modules/render.html')
def latest_team_headlines(team_id, limit=10):
    from myscore.main.modules.news import related_news

    return {"render": related_news.render_team(team_id, limit)}


@register.inclusion_tag('modules/render.html')
def most_popular_league_headlines(team_id, limit=10):
    from myscore.main.modules.news import related_news

    return {"render": related_news.most_popular_league(team_id, limit)}


@register.inclusion_tag('modules/render.html')
def most_popular_team_headlines(team_id, limit=10):
    from myscore.main.modules.news import related_news

    return {"render": related_news.most_popular_team(team_id, limit)}


@register.inclusion_tag('modules/render.html')
def other_headlines(league_name, team_id, limit=10):
    from myscore.main.modules.news import other_news

    return {"render": other_news.render(league_name, team_id, limit)}


@register.inclusion_tag('modules/render.html')
def promoted_news():
    from myscore.main.modules.news import promoted_news

    return {"render": promoted_news.render()}


# --- MATCHES

@register.inclusion_tag('modules/render.html')
def match_results(league_id=0, team_id=0):
    from myscore.main.modules.matches import results

    return {"render": results.render_results(league_id, team_id)}


@register.inclusion_tag('modules/render.html')
def match_fixtures(league_id=0, team_id=0):
    from myscore.main.modules.matches import results

    return {"render": results.render_fixtures(league_id, team_id)}


@register.inclusion_tag('modules/render.html')
def match_live_fixtures(league_id=0, team_id=0):
    from myscore.main.modules.matches import results

    return {"render": results.render_live_fixtures(league_id, team_id)}


# --- TEAMS

@register.inclusion_tag('modules/render.html')
def league_table(league_id, team_id=0, team_id_2=0):
    from myscore.main.modules.matches import league_table

    return {"render": league_table.render(league_id, team_id, team_id_2)}


@register.inclusion_tag('modules/render.html')
def latest_matches(team_id):
    from myscore.main.modules.matches import last_matches

    return {"render": last_matches.render_team(team_id)}


# --- USERS

@register.inclusion_tag('modules/render.html')
def user_mini_box(username, with_avatar=True):
    from myscore.main.modules.users import users

    return {"render": users.mini_box(username, with_avatar)}


@register.inclusion_tag('modules/render.html')
def users_joined(with_avatar=True, limit=5):
    from myscore.main.modules.users import users

    return {"render": users.joined(with_avatar, limit)}


@register.inclusion_tag('modules/render.html')
def users_online(with_avatar=True, limit=5):
    from myscore.main.modules.users import users

    return {"render": users.online(with_avatar, limit)}


@register.inclusion_tag('modules/render.html')
def top_supporters(team_id=0, limit=10):
    from myscore.main.modules.supp_league import supp_league

    return {"render": supp_league.render(team_id, limit)}


@register.inclusion_tag('modules/render.html')
def top_users(league_id=0, team_id=0, limit=10):
    from myscore.main.modules.users import top_users

    return {"render": top_users.render(league_id, team_id, limit)}


@register.inclusion_tag('modules/render.html')
def top_users_month(year_no=0, month_no=0, limit=10):
    from myscore.main.modules.users import top_users

    return {"render": top_users.top_month(year_no, month_no, limit)}


# --- CONTENT

@register.inclusion_tag('modules/render.html')
def latest_videos(only_screenshot=False, limit=10):
    from myscore.main.modules import videos

    return {"render": videos.latest_videos(only_screenshot, limit)}


@register.inclusion_tag('modules/render.html')
def video_categories(selected=None):
    from myscore.main.modules import videos

    return {"render": videos.video_categories(selected)}
