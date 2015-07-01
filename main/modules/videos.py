# coding=utf-8
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache

from myscore.main.models import Videos, VideoCategories


def latest_videos(screenshot_only=False, limit=10):
    # caching
    key = "videos_only_screenshot_%s_lang_%s_limit_%s" % (screenshot_only, settings.LANGUAGE_CODE, limit)
    c = cache.get(key)
    if c: return c

    ret = render_to_string('modules/videos.html', {'videos': Videos().get_latest(limit)})
    cache.set(key, ret)
    return ret


def video_categories(selected=None):
    if selected is None: selected = ''

    # caching
    key = "video_categories_selected_%s_lang_%s" % (selected, settings.LANGUAGE_CODE)
    c = cache.get(key)
    if c: return c

    ret = render_to_string('modules/video_categories.html',
                           {'video_categories': VideoCategories().get_categories(), 'selected': selected})
    cache.set(key, ret)
    return ret
