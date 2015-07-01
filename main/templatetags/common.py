import re

from django.template import Node
from django.template import TemplateSyntaxError, Library
from django.conf import settings

import datetime
from time import strptime

register = Library()


class GetCurrentLanguageNode(Node):
    def __init__(self, variable):
        self.variable = variable

    def render(self, context):
        context[self.variable] = "partials/layout_" + settings.LANGUAGE_CODE + ".html"
        return ''


def do_get_current_language_layout(parser, token):
    """
    This will store the current language in the context.

    Usage::

        

    This will fetch the currently active language and
    put it's value into the ``language_lang`` context
    variable.
    """
    args = token.contents.split()
    if len(args) != 3 or args[1] != 'as':
        raise TemplateSyntaxError, "'get_current_language_lang' requires 'as variable' (got %r)" % args
    return GetCurrentLanguageNode(args[2])


register.tag('get_current_language_layout', do_get_current_language_layout)


# YOUTUBE
# http://i.ytimg.com/vi/OgQYCLzWczk/default.jpg
# http://www.youtube.com/v/
@register.filter
def yt_screen(link):
    if link.find('youtube.com/v/') > 0:
        ls = re.search(".*youtube.com/v/([A-Za-z0-9_\-]{5,}).*", link).groups()
        return "http://i.ytimg.com/vi/%s/default.jpg" % ls[0]
    else:
        return False


@register.filter
def EQ(value, arg): return value == arg


@register.filter
def LT(value, arg): return value < arg


@register.filter
def GT(value, arg): return value > arg


@register.filter
def LTE(value, arg): return value <= arg


@register.filter
def GTE(value, arg): return value >= arg


@register.filter
def NE(value, arg): return value != arg


@register.filter
def IS(value, arg): return value is arg


@register.filter
def IN(value, arg): return value in arg


@register.filter
def MINUS(value, arg): return value - arg


@register.filter
def PLUS(value, arg): return value + arg


@register.filter
def TIMES(value, arg): return value * arg


@register.filter
def DIV(value, arg): return value / arg


@register.filter
def EALIER_THAN(value, arg):
    try:
        if arg == 'NOW': arg = str(datetime.date.today())
        r = datetime.datetime(*strptime(value, "%Y-%m-%d")[0:5]) - datetime.datetime(*strptime(arg, "%Y-%m-%d")[0:5])
    except TypeError:
        return False
    if ((r.days * 3600) + r.seconds) > 0:
        return True
    else:
        return False


@register.filter
def LATER_THAN(value, arg):
    try:
        if arg == 'NOW': arg = str(datetime.date.today())
        r = datetime.datetime(*strptime(value, "%Y-%m-%d")[0:5]) - datetime.datetime(*strptime(arg, "%Y-%m-%d")[0:5])
    except TypeError:
        return False
    if ((r.days * 3600) + r.seconds) < 0:
        return True
    else:
        return False


@register.filter
def EQUALS_TODAY(value):
    try:
        r = datetime.datetime(*strptime(value, "%Y-%m-%d")[0:5]) - datetime.datetime(
            *strptime(str(datetime.date.today()), "%Y-%m-%d")[0:5])
    except TypeError:
        return True
    if r.days == 0:
        return True
    else:
        return False


LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 10
LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 8
NUM_PAGES_OUTSIDE_RANGE = 2
ADJACENT_PAGES = 4
PER_PAGE = 20


def digg_paginator(context):
    if context["pages"] > 1:
        context["is_paginated"] = True
    else:
        context["is_paginated"] = False

    if context["is_paginated"]:

        path = context['request'].META['PATH_INFO']
        if path.find('strona-') > -1:
            base_url = path[0:path.find('strona-')]
        elif path.find('page-') > -1:
            base_url = path[0:path.find('page-')]
        else:
            base_url = path

        " Initialize variables "
        in_leading_range = in_trailing_range = False
        pages_outside_leading_range = pages_outside_trailing_range = range(0)

        if (context["pages"] <= LEADING_PAGE_RANGE_DISPLAYED):
            in_leading_range = in_trailing_range = True
            page_numbers = [n for n in range(1, context["pages"] + 1) if n > 0 and n <= context["pages"]]

        elif (context["page_no"] <= LEADING_PAGE_RANGE):
            in_leading_range = True
            page_numbers = [n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1) if n > 0 and n <= context["pages"]]
            pages_outside_leading_range = [n + context["pages"] for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        elif (context["page_no"] > context["pages"] - TRAILING_PAGE_RANGE):
            in_trailing_range = True
            page_numbers = [n for n in range(context["pages"] - TRAILING_PAGE_RANGE_DISPLAYED + 1, context["pages"] + 1)
                            if n > 0 and n <= context["pages"]]
            pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
        else:
            page_numbers = [n for n in
                            range(context["page_no"] - ADJACENT_PAGES, context["page_no"] + ADJACENT_PAGES + 1) if
                            n > 0 and n <= context["pages"]]
            pages_outside_leading_range = [n + context["pages"] for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
            pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]

        if context["pages"] == 1:
            has_previous, previous = False, False
            has_next = True
            next = context["page_no"] + 1
        elif context["page_no"] > 1 and context["page_no"] < context["pages"]:
            has_previous = True
            previous = context["page_no"] - 1
            has_next = True
            next = context["page_no"] + 1
        elif context["pages"] == context["page_no"]:
            has_next, next = False, False
            has_previous = True
            previous = context["page_no"] - 1
        else:
            has_next = True
            next = context["page_no"] + 1
            has_previous, previous = False, False

        return {
            "base_url": base_url,
            "is_paginated": context["is_paginated"],
            "previous": previous,
            "has_previous": has_previous,
            "next": next,
            "has_next": has_next,
            "results_per_page": PER_PAGE,
            "page": context["page_no"],
            "pages": context["pages"],
            "page_numbers": page_numbers,
            "in_leading_range": in_leading_range,
            "in_trailing_range": in_trailing_range,
            "pages_outside_leading_range": pages_outside_leading_range,
            "pages_outside_trailing_range": pages_outside_trailing_range
        }


register.inclusion_tag("partials/paginator.html", takes_context=True)(digg_paginator)
