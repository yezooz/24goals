# coding=utf-8
from myscore.main.models import Accounts
# from django.db.models import Q
from django.template.loader import render_to_string
# from myscore.libs.cache import TemplatesCache as tcache
from django.core.cache import cache
# import myscore.libs.helpers as helpers

def last_picks(user_id, limit=10):
    # EXAMPLE
    try:
        limit = int(limit)
    except:
        limit = 10

    users = Accounts().get_supporters()[:limit]
    ret = render_to_string('modules/users/finest_supporters.html', {'users': users})
    cache.set(key, ret)
    return ret


def last_activity(user_id, limit=10):
    pass
