# coding=utf-8
from django.template.loader import render_to_string
from django.core.cache import cache

# standard box
def render():
    anon_count = 0
    reg_users = []

    users = cache.get("who_online")
    if users is None:
        reg_users = ()
        anon_count = 0
    else:
        keys = users.keys()
        keys.sort()

        for u in keys:
            if u.startswith('anon_'):
                anon_count += 1
            else:
                reg_users.append(u)

    return render_to_string('modules/who_online.html', {'users': reg_users, 'anon_count': anon_count})
