# coding=utf-8
from myscore.main.models import Comments
# from django.db.models import Q
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
# import myscore.libs.helpers as helpers


def comments(request, match_id):
    comments = Comments().get_comments_by_match(match_id=match_id, lang=settings.LANGUAGE_CODE, latest=0)

    if comments.count() > 0:
        return HttpResponse(render_to_string('modules/ajax/matches/comments.html',
                                             {'comments': comments, 'match_id': match_id, 'request': request}),
                            mimetype='text/html')
    else:
        return HttpResponse("", mimetype='text/html')
