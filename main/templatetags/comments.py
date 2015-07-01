from django import template

register = template.Library()


class CommentsIn(template.Node):
    def __init__(self, var1, var2):
        self.var1, self.var2 = var1, var2

    def __unicode__(self):
        return "<CommentsIn>"

    def render(self, context):
        comms = template.resolve_variable(self.var1, context)
        id = template.resolve_variable(self.var2, context)

        if comms[int(id)] == "empty":
            context['current_comments'] = ''
        else:
            context['current_comments'] = comms[int(id)]
        return ''


def showcomments(parser, token):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r takes two arguments" % bits[0]
    return CommentsIn(bits[1], bits[2])


showcomments = register.tag('showcomments', showcomments)


class CommentsCountIn(template.Node):
    def __init__(self, var1, var2):
        self.var1, self.var2 = var1, var2

    def __unicode__(self):
        return "<CommentsCountIn>"

    def render(self, context):
        comms = template.resolve_variable(self.var1, context)
        id = template.resolve_variable(self.var2, context)

        if comms[int(id)] == "empty":
            return 0
        else:
            return len(comms[int(id)])


def showcommentscount(parser, token):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r takes three arguments" % bits[0]
    return CommentsCountIn(bits[1], bits[2])


showcommentscount = register.tag('showcommentscount', showcommentscount)
