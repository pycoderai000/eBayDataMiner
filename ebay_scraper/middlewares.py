import datetime
import random

class ProxyMiddleware:
    def __init__(self, proxies):
        self.proxies = proxies
        self.failed_proxies = {}

    @classmethod
    def from_crawler(cls, crawler):
        proxy_file = crawler.settings.get('PROXY_LIST_FILE')
        with open(proxy_file, 'r') as f:
            proxies = [line.strip() for line in f]
        return cls(proxies)

    def process_request(self, request, spider):
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy
            spider.logger.info(f"[{spider.get_current_time()}] [URL: {request.url}] [Proxy: {proxy}] [Status: Initializing] [Comment: Using proxy {proxy}]")

    def process_response(self, request, response, spider):
        proxy = request.meta.get('proxy')
        if not self.is_valid_response(response):
            retry_times = spider.custom_settings['RETRY_TIMES']
            retry_count = self.failed_proxies.get(proxy, 0) + 1
            if retry_count <= retry_times:
                delay = 2 ** retry_count  # Exponential backoff formula
                spider.logger.info(f"[{spider.get_current_time()}] [URL: {request.url}] [Proxy: {proxy}] [Status: {response.status}] [Comment: Retrying {retry_count}]")
                return self._retry(request, delay)
            else:
                self._exclude_proxy(proxy, spider, request, response)
                return self._retry(request)
        else:
            spider.logger.info(f"[{spider.get_current_time()}] [URL: {request.url}] [Proxy: {proxy}] [Status: {response.status}] [Comment: Success]")
        return response

    def process_exception(self, request, exception, spider):
        proxy = request.meta.get('proxy')
        if proxy:
            retry_times = spider.custom_settings['RETRY_TIMES']
            retry_count = self.failed_proxies.get(proxy, 0) + 1
            if retry_count <= retry_times:
                delay = 2 ** retry_count  # Exponential backoff formula
                spider.logger.info(f"[{spider.get_current_time()}] [URL: {request.url}] [Proxy: {proxy}] [Status: Failure] [Comment: Retrying {retry_count}]")
                return self._retry(request, delay)
            else:
                self._exclude_proxy(proxy, spider, request)
        return self._retry(request)

    def _retry(self, request, delay=None):
        retryreq = request.copy()
        retryreq.dont_filter = True
        retryreq.priority = request.priority + 1
        if delay:
            retryreq.meta['retry_delay'] = delay
        return retryreq

    def _exclude_proxy(self, proxy, spider, request=None, response=None):
        self.proxies.remove(proxy)
        self.failed_proxies[proxy] = self.failed_proxies.get(proxy, 0) + 1
        if response:
            spider.logger.info(f"[{spider.get_current_time()}] [URL: {request.url}] [Proxy: {proxy}] [Status: {response.status}] [Comment: Proxy {proxy} excluded due to failure]")
        else:
            spider.logger.info(f"[{spider.get_current_time()}] [URL: {request.url}] [Proxy: {proxy}] [Status: Failure] [Comment: Proxy {proxy} excluded due to exception]")

        # Log excluded proxy and reason
        with open('excluded_proxies.log', 'a') as f:
            reason = "Too many failures" if response else "Exception"
            f.write(f"{datetime.datetime.now()} - Proxy {proxy} excluded: {reason}\n")

    def is_valid_response(self, response):
        if response.status == 200 and "keyword" in response.text.lower():
            return True
        return False


