from scrapy.utils.httpobj import urlparse_cached


class CachePolicy(object):
    def __init__(self, settings):
        self.ignore_schemes = settings.getlist("HTTPCACHE_IGNORE_SCHEMES")
        self.ignore_domains = settings.getlist("HTTPCACHE_IGNORE_DOMAINS")
        self.ignore_http_codes = [int(x) for x in settings.getlist("HTTPCACHE_IGNORE_HTTP_CODES")]

    def should_cache_request(self, request):
        parsed = urlparse_cached(request)
        return parsed.scheme not in self.ignore_schemes and parsed.netloc not in self.ignore_domains

    def should_cache_response(self, response, request):
        return response.status == 200

    def is_cached_response_fresh(self, response, request):
        if "refresh_cache" in request.meta:
            return False
        return True

    def is_cached_response_valid(self, cachedresponse, response, request):
        if "refresh_cache" in request.meta:
            return False
        return True
