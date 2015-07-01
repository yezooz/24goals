from django.utils.cache import patch_response_headers


class CacheMiddleware(object):
    def process_response(self, request, response):

        if request.method != 'GET': return response
        if not response.status_code == 200: return response
        if request.META['PATH_INFO'].find('/static/') == -1 or \
                        request.META['PATH_INFO'].find('/static/images/avatars') > -1:
            return response
        # Try to get the timeout from the "max-age" section of the "Cache-
        # Control" header before reverting to using the default cache_timeout
        # length.
        # timeout = get_max_age(response)
        # if timeout == None:
        timeout = 3600 * 8
        if timeout == 0: return response

        patch_response_headers(response, timeout)
        return response
