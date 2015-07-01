from django import template
from django.conf import settings

register = template.Library()


class ChooseLang(template.Node):
    def __init__(self, str_en, str_pl):
        self.en = str_en
        self.pl = str_pl

    def __unicode__(self):
        return self.en

    def render(self, context):
        en = template.resolve_variable(self.en, context)
        pl = template.resolve_variable(self.pl, context)

        if settings.LANGUAGE_CODE == 'pl':
            return pl
        else:
            return en


def lang(parser, token):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r takes two arguments" % bits[0]
    return ChooseLang(bits[1], bits[2])


lang = register.tag('lang', lang)
