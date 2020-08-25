# -*- coding: utf-8 -*-

# Scrapy settings for justwatch project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "recipes"

SPIDER_MODULES = ["recipes.spiders"]
NEWSPIDER_MODULE = "recipes.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 64

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 32
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
#     # "Accept": "application/json, text/plain, */*",
#     # "Accept-Language": "en-US,en;q=0.5",
#     # "Accept-Encoding": "gzip, deflate, br",
#     "Referer": "http://www.allrecipes.com/",
#     "Origin": "http://www.allrecipes.com",
# }

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'justwatch.middlewares.JustwatchSpiderMiddleware': 543,
# }


# ROTATING_PROXY_LIST = [
#     "localhost:24000",
#     # ...
# ]


# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {"scrapy_crawlera.CrawleraMiddleware": 610}

DOWNLOADER_MIDDLEWARES = {
    # ...
    "shanghai.retry.RetryMiddleware": 500,
    "rotating_proxies.middlewares.RotatingProxyMiddleware": 610,
    "rotating_proxies.middlewares.BanDetectionMiddleware": 620,
    # ...
}
# RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 403, 408, 429]
# RETRY_ENABLED = True


# RETRY_TIMES = 4
# Retry on most error codes since proxies fail for different reasons

# CRAWLERA_ENABLED = True
# CRAWLERA_APIKEY = "36e19f1cd1df41cfaa3dcd5a05bc64ee"


# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html

# LOG_FORMATTER = "shanghai.logging.PoliteLogFormatter"
# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False
# LOG_LEVEL = "INFO"
# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 60 * 60 * 24 * 30  # 72 hours
# HTTPCACHE_DIR = "httpcache_recipes"
# HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408, 429]
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.DbmCacheStorage"
# HTTPCACHE_POLICY = "shanghai.cache.CachePolicy"
