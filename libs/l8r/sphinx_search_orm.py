# Sphinx Search Engine ORM for Django models
# search = SphinxSearch([index=<string>, weight=[<int>,], mode=<string>])
# http://www.sphinxsearch.com/

import socket
from struct import *

import select

SPHINX_SERVER = 'localhost'
SPHINX_PORT = 3312

# known searchd commands
SEARCHD_COMMAND_SEARCH = 0
SEARCHD_COMMAND_EXCERPT = 1

# current client-side command implementation versions
VER_COMMAND_SEARCH = 0x107
VER_COMMAND_EXCERPT = 0x100

# known searchd status codes
SEARCHD_OK = 0
SEARCHD_ERROR = 1
SEARCHD_RETRY = 2
SEARCHD_WARNING = 3

# known match modes
SPH_MATCH_ALL = 0
SPH_MATCH_ANY = 1
SPH_MATCH_PHRASE = 2
SPH_MATCH_BOOLEAN = 3
SPH_MATCH_EXTENDED = 4

# known sort modes
SPH_SORT_RELEVANCE = 0
SPH_SORT_ATTR_DESC = 1
SPH_SORT_ATTR_ASC = 2
SPH_SORT_TIME_SEGMENTS = 3
SPH_SORT_EXTENDED = 4

# known attribute types
SPH_ATTR_INTEGER = 1
SPH_ATTR_TIMESTAMP = 2

# known grouping functions
SPH_GROUPBY_DAY = 0
SPH_GROUPBY_WEEK = 1
SPH_GROUPBY_MONTH = 2
SPH_GROUPBY_YEAR = 3
SPH_GROUPBY_ATTR = 4


class SearchError(Exception):
    def __init__(self, message):
        self.message = message

    def __unicode__(self):
        return str(self.message)


class SphinxSearch(object):
    def __init__(self, index=None, **kwargs):
        self._select_related = False
        self._select_related_args = {}
        self._filters = {}
        self._query = ''
        self._offset = 0
        self._limit = 20
        self._min_id = 0  # we dont use this currently
        self._max_id = 0xFFFFFFFF  # dont use this either
        self._maxmatches = 1000
        self._sort = SPH_SORT_RELEVANCE
        self._sortby = 'desc'
        self._groupby = ''
        self._groupfunc = SPH_GROUPBY_DAY
        self._groupsort = '@group desc'
        self._result_cache = None
        if index:
            self._index = index
        if 'mode' in kwargs:
            self.mode(kwargs['mode'])
        else:
            self._mode = SPH_MATCH_ANY
        if 'weights' in kwargs:
            self.weights(kwargs['weights'])
        else:
            self._weights = []

    def __get__(self, instance, instance_model, **kwargs):
        if instance != None:
            raise AttributeError, "Manager isn't accessible via %s instances" % type.__name__
        self._model = instance_model
        self._index = self._model._meta.db_table
        return self

    def __repr__(self):
        return repr(self._get_data())

    def __len__(self):
        return len(self._get_data())

    def __iter__(self):
        return iter(self._get_data())

    def __getitem__(self, k):
        if not isinstance(k, (slice, int)):
            raise TypeError
        assert (not isinstance(k, slice) and (k >= 0)) \
               or (isinstance(k, slice) and (k.start is None or k.start >= 0) and (k.stop is None or k.stop >= 0)), \
            "Negative indexing is not supported."
        if self._result_cache is None:
            if type(k) == slice:
                self._offset = k.start
                self._limit = k.stop - k.start
                return self._get_results()
            else:
                self._offset = k
                self._limit = 1
                return self._get_results()[0]
        else:
            return self._result_cache[k]

    def _get_data(self):
        if self._result_cache is None:
            self._result_cache = list(self._get_results())
        return self._result_cache

    def query(self, string):
        if self._query != string:
            self._query = string
            self._result_cache = None
        return self

    def mode(self, mode):
        assert (mode in [SPH_MATCH_ALL, SPH_MATCH_ANY, SPH_MATCH_PHRASE, SPH_MATCH_BOOLEAN, SPH_MATCH_EXTENDED])
        self._mode = mode
        return self

    def weights(self, weights):
        assert (isinstance(weights, list))
        for w in weights:
            assert (isinstance(w, int))
        self._weights = weights

    # only works on attributes
    def filter(self, **kwargs):
        for k, v in kwargs.iteritems():
            assert (isinstance(k, str))
            assert (isinstance(v, list))
            assert (v)
            for value in v:
                assert (isinstance(value, int))
            self._filters.append({'key': k, 'val': v})
        return self

    # only works on attributes
    def exclude(self, **kwargs):
        for k, v in kwargs.iteritems():
            assert (isinstance(k, str))
            assert (isinstance(v, list))
            assert (v)
            for value in v:
                assert (isinstance(value, int))
            self._filters.append({'key': k, 'val': v, 'exclude': 1})
        return self

    # you cannot order by @weight (it always orders in descending)
    # keywords are @id, @weight, @rank, and @relevance
    def order_by(self, *args):
        sort_by = []
        for arg in args:
            sort = 'ASC'
            if arg[0] == '-':
                arg = arg[1:]
                sort = 'DESC'
            if arg == 'id':
                arg = '@id'
            assert (isinstance(arg, str))
            sort_by.append('%s %s' % (arg, sort))
        if sort_by:
            self._sort = SPH_SORT_EXTENDED
            self._sortby = ', '.join(sort_by)
        return self

    # pass these thru on the queryset and let django handle it
    def select_related(self, **kwargs):
        self._select_related = True
        self._select_related_args.udpate(**kwargs)
        return self

    # sphinxapi
    def _connect(self):
        """
        connect to searchd server
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SPHINX_SERVER, SPHINX_PORT))
        except socket.error, msg:
            if sock:
                sock.close()
            raise SearchError, 'connection to %s:%s failed (%s)' % (SPHINX_SERVER, SPHINX_PORT, msg)
        v = unpack('>L', sock.recv(4))
        if v < 1:
            sock.close()
            raise SearchError, 'expected searchd protocol version, got %s' % v
        # all ok, send my version
        sock.send(pack('>L', 1))
        return sock

    def _get_response(self, sock, client_ver):
        """
        get and check response packet from searchd server
        """
        (status, ver, length) = unpack('>2HL', sock.recv(8))
        response = ''
        left = length
        while left > 0:
            chunk = sock.recv(left)
            if chunk:
                response += chunk
                left -= len(chunk)
            else:
                break
        sock.close()

        # check response
        read = len(response)
        if not response or read != length:
            if length:
                raise SearchError, 'failed to read searchd response (status=%s, ver=%s, len=%s, read=%s)' \
                                   % (status, ver, length, read)
            raise SearchError, 'received zero-sized searchd response'

        # check status
        if status == SEARCHD_WARNING:
            wend = 4 + unpack('>L', response[0:4])[0]
            self._warning = response[4:wend]
            return response[wend:]
        elif status == SEARCHD_ERROR:
            raise SearchError, 'searchd error: ' + response[4:]
        elif status == SEARCHD_RETRY:
            raise SearchError, 'temporary searchd error: ' + response[4:]
        elif status != SEARCHD_OK:
            raise SearchError, 'unknown status code %d' % status

        # check version
        if ver < client_ver:
            self._warning = 'searchd command v.%d.%d older than client\'s v.%d.%d, some options might not work' \
                            % (ver >> 8, ver & 0xff, client_ver >> 8, client_ver & 0xff)
        return response

    def _get_results(self):
        sock = self._connect()
        if not sock:
            raise SearchError, "unknown error trying to connect"

        # build request
        req = [pack('>4L', self._offset, self._limit, self._mode, self._sort)]
        req.append(pack('>L', len(self._sortby)))
        req.append(self._sortby)
        req.append(pack('>L', len(self._query)))
        req.append(self._query)
        req.append(pack('>L', len(self._weights)))
        for w in self._weights:
            req.append(pack('>L', w))
        req.append(pack('>L', len(self._index)))
        req.append(self._index)
        req.append(pack('>L', self._min_id))
        req.append(pack('>L', self._max_id))
        # filters
        req.append(pack('>L', len(self._filters)))
        for f in self._filters:
            req.append(pack('>L', len(f['key'])))
            req.append(f['key'])
            if ('val' in f):
                req.append(pack('>L', len(f['val'])))
                for v in f['val']:
                    req.append(pack('>L', v))
            else:
                req.append(pack('>3L', 0, f['min'], f['max']))
            req.append(pack('>L', f['exc']))

        # group-by, max-matches, group-sort
        req.append(pack('>2L', self._groupfunc, len(self._groupby)))
        req.append(self._groupby)
        req.append(pack('>2L', self._maxmatches, len(self._groupsort)))
        req.append(self._groupsort)

        # send query, get response
        req = ''.join(req)

        length = len(req)
        req = pack('>2HL', SEARCHD_COMMAND_SEARCH, VER_COMMAND_SEARCH, length) + req
        sock.send(req)
        response = self._get_response(sock, VER_COMMAND_SEARCH)
        if not response:
            return {}

        # parse response
        result = {}
        max_ = len(response)

        # read schema
        p = 0
        fields = []
        attrs = []

        nfields = unpack('>L', response[p:p + 4])[0]
        p += 4
        while nfields > 0 and p < max_:
            nfields -= 1
            length = unpack('>L', response[p:p + 4])[0]
            p += 4
            fields.append(response[p:p + length])
            p += length

        nattrs = unpack('>L', response[p:p + 4])[0]
        p += 4
        while nattrs > 0 and p < max_:
            nattrs -= 1
            length = unpack('>L', response[p:p + 4])[0]
            p += 4
            attr = response[p:p + length]
            p += length
            type_ = unpack('>L', response[p:p + 4])[0]
            p += 4
            attrs.append([attr, type_])

        # read match count
        count = unpack('>L', response[p:p + 4])[0]
        p += 4

        # read matches
        results = []
        while count > 0 and p < max_:
            count -= 1
            doc, weight = unpack('>2L', response[p:p + 8])
            p += 8 + (len(attrs) * 4)
            results.append(doc)
        sock.close()

        if results:
            qs = self._model.objects.filter(pk__in=results)
            if self._select_related:
                qs = qs.select_related(self._select_related_args)
            queryset = dict([(o.id, o) for o in qs])
            results = [queryset[k] for k in results if k in queryset]
        return results
