from django import template

import datetime

register = template.Library()

# TIME ZONES
class TimeZoneNode(template.Node):
    def __init__(self, var1, var2, var3):
        self.var1, self.var2, self.var3 = var1, var2, var3

    def __unicode__(self):
        return "<TimeZoneNode>"

    def render(self, context):
        date = template.resolve_variable(self.var1, context)
        time = template.resolve_variable(self.var2, context)
        zone = template.resolve_variable(self.var3, context)  # int; -12/+12

        try:
            y, m, d = str(date).split("-")
            h, i, s = str(time).split(":")
            date = datetime.datetime(int(y), int(m), int(d), int(h), int(i), int(s))
            context['match_time_zone'] = date + datetime.timedelta(hours=zone)

            return ""
        except:
            return ""


def timezone(parser, token):
    bits = token.contents.split()
    if len(bits) != 4:
        raise template.TemplateSyntaxError, "%r takes three arguments" % bits[0]
    return TimeZoneNode(bits[1], bits[2], bits[3])


timezone = register.tag('timezone', timezone)

# YESTERDAY - TODAY - TOMORROW [-2-0-+4]
class DatesRangeNode(template.Node):
    def __init__(self, var1):
        self.var1 = var1

    def __unicode__(self):
        return "<DatesRangeNode>"

    def render(self, context):
        today = template.resolve_variable(self.var1, context)
        if not today:
            today = str(datetime.date.today())

        try:
            y, m, d = str(today).split("-")
            date = datetime.datetime(int(y), int(m), int(d), 0, 0, 0)
            context['today_minus_2'] = date + datetime.timedelta(days=-2)
            context['yesterday'] = date + datetime.timedelta(days=-1)
            context['today'] = date
            context['tomorrow'] = date + datetime.timedelta(days=1)
            context['today_plus_2'] = date + datetime.timedelta(days=2)
            context['today_plus_3'] = date + datetime.timedelta(days=3)
            context['today_plus_4'] = date + datetime.timedelta(days=4)

            return ""
        except:
            return ""


def datesrange(parser, token):
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one argument" % bits[0]
    return DatesRangeNode(bits[1])


datesrange = register.tag('datesrange', datesrange)
