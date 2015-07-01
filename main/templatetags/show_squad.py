from django import template

register = template.Library()


class ShowSquad(template.Node):
    def __init__(self, var1):
        self.var1 = var1

    def __unicode__(self):
        return "<ShowSquad>"

    def render(self, context):
        squads = template.resolve_variable(self.var1, context)
        squads = list(squads)

        squad_line = []

        home_i = 0
        away_i = 0

        for squad in squads:
            squad_line.append({})

            if squad.side == "h":
                squad_line[home_i]["home"] = squad.player
                home_i += 1
            elif squad.side == "a":
                squad_line[away_i]["away"] = squad.player
                away_i += 1

        main_line = squad_line[0:11]
        subs_line = squad_line[11:home_i]
        context['squad_lines'] = main_line
        context['subs_line'] = subs_line
        return ''


def show_squad(parser, token):
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one arguments" % bits[0]
    return ShowSquad(bits[1])


show_squad = register.tag('show_squad', show_squad)
