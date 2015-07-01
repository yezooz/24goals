# coding=utf-8
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache

from myscore.main.models import Accounts


def mini_box(username, with_avatar=True):
    # caching
    key = "user_%s_mini_box_lang_%s_avatars_%s" % (username, settings.LANGUAGE_CODE, with_avatar)
    c = cache.get(key)
    if c: return c

    user = Accounts().get_profile(username)
    ret = render_to_string('modules/users/mini_box.html', {'user': user})
    cache.set(key, ret)
    return ret


def online(with_avatar=True, limit=5):
    # MESS!
    # caching
    key = "users_online_lang_%s_avatars_%s_limit_%s" % (settings.LANGUAGE_CODE, with_avatar, limit)
    c = cache.get(key)
    if c: return c

    user = Accounts().get_profile(username)
    ret = render_to_string('modules/users/online.html', {'user': user})
    cache.set(key, ret)
    return ret


def joined(with_avatar=True, limit=5):
    # MESS!
    # caching
    key = "users_joined_lang_%s_avatars_%s_limit_%s" % (settings.LANGUAGE_CODE, with_avatar, limit)
    c = cache.get(key)
    if c: return c

    user = Accounts().get_profile(username)
    ret = render_to_string('modules/users/joined.html', {'user': user})
    cache.set(key, ret)
    return ret
