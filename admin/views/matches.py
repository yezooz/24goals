# coding=utf-8
from django import oldforms, template
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache

from myscore.main.models import *


@staff_member_required
def multi_edit(request, ids="", action="", action_id=""):
    matches = Matches.objects.filter(id__in=ids.split(","))

    teams = []
    for m in matches:
        teams.append(int(m.home_team.id))
        teams.append(int(m.away_team.id))

    players = Players.objects.filter(current_team_id__in=teams).order_by("last_name", "first_name")

    # global refresh
    if request.POST and action == "global_refresh":
        for match in matches:
            prev_status = match.status

            match.status = request.POST["status"]
            match.save()

            # calculate points
            if prev_status != 'f' and request.POST["status"] == 'f':
                match.on_finish()

        return HttpResponseRedirect("/admin/main/matches/multi_edit/" + ids)

    # add
    if request.POST and action == "add":
        det = MatchDetails()
        player = ""

        det.match = Matches.objects.get(pk=action_id)
        if request.POST.has_key("minute") and request.POST["minute"] != "":
            det.minute = request.POST["minute"]
        else:
            return HttpResponseRedirect("/admin/main/matches/multi_edit/" + ids)

        if request.POST["left_player"] != "":
            det.side = "left"
            player = int(request.POST["left_player"])
            det.match.save()

        elif request.POST["right_player"] != "":
            det.side = "right"
            player = int(request.POST["right_player"])
            det.match.save()
        else:
            return HttpResponseRedirect("/admin/main/matches/multi_edit/" + ids)

        player = Players.objects.get(pk=int(player))
        det.player_id = player.id
        det.player_name = "%s %s" % (player.last_name, player.first_name)
        det.espn_player_id = player.espn_id
        det.espn_player_name = player.espn_name
        det.action = request.POST["action"]
        det.action_info = request.POST["action_info"]
        det.save()

        return HttpResponseRedirect("/admin/main/matches/multi_edit/" + ids)

    # remove
    if action == "remove" and len(action_id) > 0:
        det = MatchDetails.objects.get(pk=action_id)
        if det.side == "left" and det.action == "g" and det.action_info != "m":
            det.match.home_score -= 1
            det.match.save()
        elif det.side == "right" and det.action == "g" and det.action_info != "m":
            det.match.away_score -= 1
            det.match.save()

        det.delete()
        return HttpResponseRedirect("/admin/main/matches/multi_edit/" + ids)

    # refresh
    if request.POST and action == "refresh":
        match = Matches.objects.get(pk=action_id)

        if request.POST["minute"] != match.minute:
            match.minute = request.POST["minute"]

        prev_status = match.status
        match.status = request.POST["status"]

        match.match_date = request.POST["match_date"]
        match.match_time = request.POST["match_time"]
        match.home_score = request.POST["home_score"]
        match.away_score = request.POST["away_score"]
        match.save()

        # calculate points
        if prev_status != 'f' and request.POST["status"] == 'f':
            match.on_finish()

        return HttpResponseRedirect("/admin/main/matches/multi_edit/" + ids)


    # stats
    if action == "stats":
        stats = MatchStats.objects.filter(match=action_id).order_by('-side')
        match = Matches.objects.get(pk=action_id)
        if request.POST:
            post = request.POST.copy()

            try:
                if len(stats) < 2:
                    stat = MatchStats(match=match, side="h")
                else:
                    stat = MatchStats(id=stats[0].id, match=match, side="h")
                stat.shots = post["shots_home"]
                stat.shots_on_goal = post["shots_on_goal_home"]
                stat.fouls = post["fouls_home"]
                stat.corners = post["corners_home"]
                stat.offsides = post["offsides_home"]
                stat.possession = post["possession_home"]
                stat.yellow_cards = post["yellow_cards_home"]
                stat.red_cards = post["red_cards_home"]
                stat.saves = post["saves_home"]
                stat.save()

                if len(stats) < 2:
                    stat = MatchStats(match=match, side="a")
                else:
                    stat = MatchStats(id=stats[1].id, match=match, side="a")
                stat.shots = post["shots_away"]
                stat.shots_on_goal = post["shots_on_goal_away"]
                stat.fouls = post["fouls_away"]
                stat.corners = post["corners_away"]
                stat.offsides = post["offsides_away"]
                stat.possession = post["possession_away"]
                stat.yellow_cards = post["yellow_cards_away"]
                stat.red_cards = post["red_cards_away"]
                stat.saves = post["saves_away"]
                stat.save()
            except:
                return render_to_response("admin/matches/edit_stats.html",
                                          {'stats': stats, 'home_team': match.home_team, 'away_team': match.away_team},
                                          RequestContext(request, {}), )

            return HttpResponseRedirect("/admin/main/matches/multi_edit/" + ids)
        else:
            return render_to_response("admin/matches/edit_stats.html",
                                      {'stats': stats, 'home_team': match.home_team, 'away_team': match.away_team},
                                      RequestContext(request, {}), )



    # squad
    if action == "squad":
        match = Matches.objects.get(pk=action_id)
        home_squad = list(Players.objects.filter(current_team_id=match.home_team.id).order_by('position', 'last_name'))
        away_squad = list(Players.objects.filter(current_team_id=match.away_team.id).order_by('position', 'last_name'))

        if request.POST:
            post = request.POST.copy()
            MatchSquad.objects.filter(match=match).delete()

            for k, v in post.iteritems():

                if k.startswith("home_") and v != [u'']:
                    pid = k.replace("home_", "")
                    v = int(v[0])

                    sq = MatchSquad(side="h", match=match)
                    sq.player = Players.objects.get(pk=int(pid))
                    sq.started_as_sub = v - 1
                    sq.save()

                elif k.startswith("away_") and v != [u'']:
                    pid = k.replace("away_", "")
                    v = int(v[0])

                    sq = MatchSquad(side="a", match=match)
                    sq.player = Players.objects.get(pk=int(pid))
                    sq.started_as_sub = v - 1
                    sq.save()

            return HttpResponseRedirect("/admin/main/matches/multi_edit/" + ids)
        else:
            match_squad = MatchSquad.objects.filter(match=match).order_by('-side', 'started_as_sub')

            return render_to_response("admin/matches/edit_squad.html",
                                      {'match': match, 'home_squad': home_squad, 'away_squad': away_squad,
                                       'match_squad': match_squad}, RequestContext(request, {}), )

    return render_to_response(
        "admin/matches/multi_edit.html",
        {'matches': matches, 'players': players},
        RequestContext(request, {}),
    )


@staff_member_required
def index(request):
    if request.POST:
        # create FILTER
        if request.POST.has_key('filter'):
            filter = False
            top_filter = False

            matches = Matches.objects.all()
            if request.POST['filter_mid'] != "":
                matches = matches.filter(id=request.POST['filter_mid'])
                filter = True
                top_filter = True

            if request.POST['filter_emid'] != "":
                matches = matches.filter(espn_match_id=request.POST['filter_emid'])
                filter = True
                top_filter = True

            if request.POST['filter_league_id'] > 0:
                matches = matches.filter(league__id=request.POST['filter_league_id'])
                filter = True

            if request.POST['filter_season_id'] > 0:
                matches = matches.filter(season__id=request.POST['filter_season_id'])
                filter = True

            if request.POST['filter_date_start'] != "":
                matches = matches.filter(match_date__gte=request.POST['filter_date_start'])
                filter = True

            if request.POST['filter_date_end'] != "":
                matches = matches.filter(match_date__lte=request.POST['filter_date_end'])
                filter = True

            if request.POST.has_key('filter_status') and request.POST['filter_status'] != "0":
                matches = matches.filter(status=request.POST['filter_status'])
                filter = True

            if request.POST['filter_manual'] != "":
                matches = matches.filter(manual=request.POST['filter_manual'])
                filter = True

            if top_filter:
                matches = matches.select_related().order_by('match_date', 'match_time')
            elif filter:
                matches = matches.select_related().order_by('match_date', 'match_time')[:50]
            else:
                matches = matches.filter(status="d").select_related().order_by('match_date', 'match_time')[:100]

        # select elements to EDIT
        elif request.POST.has_key('edit'):
            ids = []
            for id in request.POST.iterkeys():
                if id.find('edit_') >= 0:
                    ids.append(id.replace('edit_', ''))

            if len(ids) > 0:
                path = ",".join(ids)
                return HttpResponseRedirect(request.path + 'multi_edit/' + path)

    else:
        matches = Matches.objects.filter(match_date__gte=datetime.date.today()).order_by('match_date', 'match_time')[
                  :20]

    leagues = Leagues.objects.all().order_by('name_pl')
    seasons = Seasons.objects.all().order_by('-is_current', '-title')

    return render_to_response(
        "admin/matches/index.html",
        {'matches': matches, 'leagues': leagues, 'seasons': seasons},
        RequestContext(request, {}),
    )


@staff_member_required
def multi_add(request, league_id=None):
    if not league_id:
        leagues = Leagues.objects.all().order_by('name_espn')
        return render_to_response("admin/matches/multi_add.html", {'leagues': leagues}, RequestContext(request, {}))

    multi_count = range(1, 11)
    teams = list(Teams.objects.all().order_by('name_pl'))
    seasons = list(Seasons.objects.all().order_by('-is_current', 'title'))

    if request.POST:
        post = request.POST.copy()

        for i in multi_count:
            i = str(i)
            if post["home_team_" + i] != "" and post["away_team_" + i] != "" and post["match_date_" + i] != "" and post[
                        "match_time_" + i] != "":
                d1, d2, d3 = post["match_date_" + i].split("-")
                t1, t2 = post["match_time_" + i].split(":")

                m = Matches()
                m.home_team = Teams.objects.get(pk=int(post["home_team_" + i]))
                m.away_team = Teams.objects.get(pk=int(post["away_team_" + i]))
                m.match_date = datetime.date(int(d1), int(d2), int(d3))
                m.match_time = datetime.time(int(t1), int(t2))
                m.home_score = post["home_score_" + i]
                m.away_score = post["away_score_" + i]
                m.league = Leagues.objects.get(pk=league_id)
                m.season_id = post["season_id_" + i]
                m.minute = 0
                m.status = "c"
                m.stadium_id = 0
                m.save()

                request.user.message_set.create(message="Dodano mecz o ID %s" % m.id)

        return HttpResponseRedirect("/admin/main/matches/multi_add/")

    return render_to_response("admin/matches/multi_add.html",
                              {'teams': teams, 'seasons': seasons, 'multi_count': multi_count},
                              RequestContext(request, {}), )

    # match_detailed view with editing MatchDetails
    # fully customized list-search view
