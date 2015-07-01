from django import template

register = template.Library()


class ShowStats(template.Node):
    def __init__(self, var1):
        self.var1 = var1

    def __unicode__(self):
        return "<ShowStats>"

    def render(self, context):
        stats = template.resolve_variable(self.var1, context)

        for stat in stats:

            if stat.side == "h":
                context['home_shots'] = stat.shots
                context['home_shots_on_goal'] = stat.shots_on_goal
                context['home_fouls'] = stat.fouls
                context['home_corners'] = stat.corners
                context['home_offsides'] = stat.offsides
                context['home_possession'] = stat.possession
                context['home_yellow_cards'] = stat.yellow_cards
                context['home_red_cards'] = stat.red_cards

            else:
                context['away_shots'] = stat.shots
                context['away_shots_on_goal'] = stat.shots_on_goal
                context['away_fouls'] = stat.fouls
                context['away_corners'] = stat.corners
                context['away_offsides'] = stat.offsides
                context['away_possession'] = stat.possession
                context['away_yellow_cards'] = stat.yellow_cards
                context['away_red_cards'] = stat.red_cards

        return ''


def show_stats(parser, token):
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one arguments" % bits[0]
    return ShowStats(bits[1])


show_stats = register.tag('show_stats', show_stats)
