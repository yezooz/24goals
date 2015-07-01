# coding=utf-8
from myscore.main.models import Comments
# from django.db.models import Q
from django.template.loader import render_to_string
from django.http import HttpResponse, Http404
from django.conf import settings
# import myscore.libs.helpers as helpers

def comments(request, news_id):
    comments = Comments().get_comments_by_news(news_id=news_id, lang=settings.LANGUAGE_CODE, latest=0)
    try:
        news = News.objects.get(pk=news_id)
    except:
        raise Http404

    return HttpResponse(render_to_string('modules/ajax/news/comments.html', {'comments': comments, 'news': news}),
                        mimetype='text/html')
