from django import template

register = template.Library()


class IfOr(template.Node):
    '''
    Like {% if %} but ...
    '''

    def __init__(self, var1, var2, var3, nodelist_true, nodelist_false, negate):
        self.var1, self.var2, self.var3 = var1, var2, var3
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __unicode__(self):
        return "<IfWon>"

    def render(self, context):
        val1 = template.resolve_variable(self.var1, context)
        val2 = template.resolve_variable(self.var2, context)
        val3 = template.resolve_variable(self.var3, context)
        try:
            if val1 == val3 or val2 == val3:
                return self.nodelist_true.render(context)
            return self.nodelist_false.render(context)
        except TypError:
            return ""


def ifequalor(parser, token, negate):
    bits = token.contents.split()
    if len(bits) != 4:
        raise template.TemplateSyntaxError, "%r takes three arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfOr(bits[1], bits[2], bits[3], nodelist_true, nodelist_false, negate)


register.tag('ifequalor', lambda parser, token: ifequalor(parser, token, False))
