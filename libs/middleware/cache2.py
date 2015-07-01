from django.conf import settings
from django.core.cache import cache
from django.utils.cache import get_cache_key, learn_cache_key, patch_response_headers

import cPickle as pickle


class CacheMiddleware(object):
    def __init__(self):
        pass

    def process_request(self, request):
        if not request.method in ('GET', 'HEAD') or request.GET:
            return None  # Don't bother checking the cache.
        if request.META['PATH_INFO'].find("/static") == 0 or request.META['PATH_INFO'].find("/admin") == 0:
            return None

        # resp = TemplatesCache.get(request)
        # if resp:
        # return resp
        # else:
        # return None

    def process_response(self, request, response):
        "Sets the cache, if needed."
        if request.META['PATH_INFO'].find("/static") == 0 or request.META['PATH_INFO'].find("/admin") == 0:
            return response
        if request.method != 'GET':
            return response
        if not response.status_code == 200:
            return response

        # patch_response_headers(response)
        # cache_key = learn_cache_key(request, response)
        # cache.set(cache_key, response)
        # TemplatesCache.set(response, request)

        return response


class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable


class TemplatesCache(object):
    def get_dict(request, key=None):
        if not key:
            key = request.META['PATH_INFO']

        dict = cache.get("elements__%s" % str(key))
        if dict is None:
            cache.set("elements__%s" % str(key), pickle.dumps({}))
            return {}
        else:
            return pickle.loads(dict)

    get_dict = Callable(get_dict)

    def set_dict(request, key=None):
        if not key:
            key = request.META['PATH_INFO']

        if request.user.id is None:
            user_id = 0
        else:
            user_id = request.user.id

        dict = TemplatesCache.get_dict(request, key)
        dict[int(user_id)] = 1

        pickled = pickle.dumps(dict)
        cache.set("elements__%s" % str(key), pickled)

    set_dict = Callable(set_dict)

    def empty_dict(key):
        cache.set("elements__%s" % str(key), pickle.dumps({}))

    empty_dict = Callable(empty_dict)

    def get_key(request, key=None):
        if not key:
            key = request.META['PATH_INFO']

        return "template__%s__%s" % (str(key), request.user.id)

    get_key = Callable(get_key)

    def get(request, key=None):
        dict = TemplatesCache.get_dict(request, key)
        if request.user.id is None:
            user_id = 0
        else:
            user_id = request.user.id

        if dict.has_key(user_id):
            pickled = cache.get(TemplatesCache.get_key(request, key))
            if pickled is None:
                return False
            else:
                return pickle.loads(pickled)
        else:
            return False

    get = Callable(get)

    def set(response, request, key=None):

        cache.set(TemplatesCache.get_key(request, key), pickle.dumps(response))
        TemplatesCache.set_dict(request, key)

        return response

    set = Callable(set)

    def get_and_mod(haystack, needle, request, key=None):
        response = TemplatesCache.get(request, key)

        if response:
            content_copy = response.content
            response.content = content_copy.replace(haystack, needle)

        return response

    get_and_mod = Callable(get_and_mod)

    def delete_key(request, key=None, clean=False):
        if not key:
            key = request.META['PATH_INFO']
        if request.user.id is None:
            user_id = 0
        else:
            user_id = request.user.id

        dict = TemplatesCache.get_dict(request, key)
        try:
            del dict[int(user_id)]
        except:
            return

        pickled = pickle.dumps(dict)
        cache.set("elements__%s" % str(key), pickled)

        if clean and key is not None and cache.has_key(key):
            cache.delete(key)

    delete_key = Callable(delete_key)
    remove_key = Callable(delete_key)

    def delete_path(request, key=None):
        if not key:
            key = request.META['PATH_INFO']
        TemplatesCache.empty_dict(key)

    delete_path = Callable(delete_path)
