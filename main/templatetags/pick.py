from django import template
from django.utils.translation import ugettext as _

register = template.Library()


class ShowPickIn(template.Node):
    def __init__(self, var1, var2, var3):
        self.var1, self.var2, self.var3 = var1, var2, var3

    def __unicode__(self):
        return "<ShowPickIn>"

    def render(self, context):
        picks = template.resolve_variable(self.var1, context)
        match_id = template.resolve_variable(self.var2, context)
        which = template.resolve_variable(self.var3, context)

        try:
            for p in picks:
                if p.match_id == match_id:
                    if which == "home":
                        return p.home_score
                    elif which == "away":
                        return p.away_score
                    elif which == "points":
                        if int(p.points) > 0:
                            return "<span style='color: green'>+" + str(p.points) + " " + _('pkt') + ".</span>"
                        else:
                            return "<span style='color: red'>" + str(p.points) + " " + _('pkt') + ".</span>"

                    # context['home_pred_score'] = p.home_score
                    # context['away_pred_score'] = p.away_score
                    # context['pred_points'] = "+" + str(p.points) + " {% trans 'pkt' %}."
                    return ""
            return ""
        except:
            return ""


def showpick(parser, token):
    bits = token.contents.split()
    if len(bits) != 4:
        raise template.TemplateSyntaxError, "%r takes three arguments" % bits[0]
    return ShowPickIn(bits[1], bits[2], bits[3])


showpick = register.tag('showpick', showpick)
