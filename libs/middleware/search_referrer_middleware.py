import urlparse
import cgi
import re


class SearchReferrerMiddleware(object):
    SEARCH_PARAMS = {
        'AltaVista': 'q',
        'Ask': 'q',
        'Google': 'q',
        'Live': 'q',
        'Lycos': 'query',
        'MSN': 'q',
        'Yahoo': 'p',
    }

    NETWORK_RE = r"""^
        (?P<subdomain>[-.a-z\d]+\.)?
        (?P<engine>%s)
        (?P<top_level>(?:\.[a-z]{2,3}){1,2})
        (?P<port>:\d+)?
        $(?ix)"""

    @classmethod
    def parse_search(cls, url):

        """
        Extract the search engine, domain, and search term from `url`
        and return them as (engine, domain, term). For example,
        ('Google', 'www.google.co.uk', 'django framework'). Note that
        the search term will be converted to lowercase and have normalized
        spaces.

        The first tuple item will be None if the referrer is not a
        search engine.
        """
    try:
        parsed = urlparse.urlsplit(url)
        network = parsed[1]
        query = parsed[3]
    except (AttributeError, IndexError):
        return (None, None, None)
    for engine, param in cls.SEARCH_PARAMS.iteritems():
        match = re.match(NETWORK_RE % engine, network)
        if match and match.group(2):
            term = cgi.parse_qs(query).get(param)
            if term and term[0]:
                term = ' '.join(term[0].split()).lower()
                return (engine, network, term)
    return (None, network, None)


# Here's where your code goes!
# It can be any middleware method that needs search engine detection
# functionality... this is just my example.
def process_view(self, request, view_func, view_args, view_kwargs):
    from django.views.generic.date_based import object_detail

    referrer = request.META.get('HTTP_REFERER')
    engine, domain, term = self.parse_search(referrer)
    if engine and view_func is object_detail:

# The client got to this object's page from a search engine.
# This might be useful for determining the object's popularity.
# Get the object using object_detail's queryset.
# Log this search using a custom Visit model or something.
