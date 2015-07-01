from django import template
from django.template import resolve_variable

register = template.Library()


class IfHomeWon(template.Node):
    '''
    Like {% if %} but ...
    '''

    def __init__(self, var1, var2, nodelist_true, nodelist_false, negate):
        self.var1, self.var2 = var1, var2
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __unicode__(self):
        return "<IfWon>"

    def render(self, context):
        val1 = template.resolve_variable(self.var1, context)
        val2 = template.resolve_variable(self.var2, context)
        try:
            if val1 > val2:
                return self.nodelist_true.render(context)
            return self.nodelist_false.render(context)
        except TypError:
            return ""


def ifhomewon(parser, token, negate):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r takes three arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfHomeWon(bits[1], bits[2], nodelist_true, nodelist_false, negate)


register.tag('ifhomewon', lambda parser, token: ifhomewon(parser, token, False))


class IfAwayWon(template.Node):
    '''
    Like {% if %} but ...
    '''

    def __init__(self, var1, var2, nodelist_true, nodelist_false, negate):
        self.var1, self.var2 = var1, var2
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __unicode__(self):
        return "<IfWon>"

    def render(self, context):
        val1 = template.resolve_variable(self.var1, context)
        val2 = template.resolve_variable(self.var2, context)
        try:
            if val1 < val2:
                return self.nodelist_true.render(context)
            return self.nodelist_false.render(context)
        except TypError:
            return ""


def ifawaywon(parser, token, negate):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r takes three arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfAwayWon(bits[1], bits[2], nodelist_true, nodelist_false, negate)


register.tag('ifawaywon', lambda parser, token: ifawaywon(parser, token, False))


class IfDraw(template.Node):
    '''
    Like {% if %} but ...
    '''

    def __init__(self, var1, var2, nodelist_true, nodelist_false, negate):
        self.var1, self.var2 = var1, var2
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __unicode__(self):
        return "<IfWon>"

    def render(self, context):
        val1 = template.resolve_variable(self.var1, context)
        val2 = template.resolve_variable(self.var2, context)
        try:
            if val1 == val2:
                return self.nodelist_true.render(context)
            return self.nodelist_false.render(context)
        except TypError:
            return ""


def ifdraw(parser, token, negate):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r takes three arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfDraw(bits[1], bits[2], nodelist_true, nodelist_false, negate)


register.tag('ifdraw', lambda parser, token: ifdraw(parser, token, False))
