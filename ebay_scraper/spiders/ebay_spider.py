import time
import scrapy
import json
import datetime
from scrapy.utils.project import get_project_settings
from ebay_scraper.items import EbayScraperItem

class EbaySpider(scrapy.Spider):
    name = 'ebay'
    custom_settings = {
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 503, 504, 400, 429, 408],
        'DOWNLOADER_MIDDLEWARES': {
            'ebay_scraper.middlewares.ProxyMiddleware': 543,
        },
        'ITEM_PIPELINES': {
            'ebay_scraper.pipelines.SavingPipeline': 300,
        },
        'CONCURRENT_REQUESTS': 1000,
        'DOWNLOAD_DELAY': 0.01,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1000,
        'CONCURRENT_REQUESTS_PER_IP': 1000,
    }

    def open_spider(self, spider):
        self.logger.info(f"Spider opened: {spider.name}")

    def start_requests(self):
        self.logger.info("Starting to read input.json file")
        with open('input.json') as f:
            data = json.load(f)

        chunk_size = get_project_settings().get('CHUNK_SIZE', 300)
        self.logger.info(f"Processing URLs in chunks of size {chunk_size}")
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            for keyword_info in chunk:
                keyword = keyword_info["keyword"]
                links = keyword_info["links"]
                for url in links:
                    self.logger.info(f"Yielding request for URL: {url}")
                    yield scrapy.Request(url, self.parse_response, meta={'proxy': ''})
            time.sleep(get_project_settings().get('SLEEP_TIME', 2))  # Introduce sleep between chunks

    def parse_response(self, response):
        self.logger.info(f"Parsing response for URL: {response.url}")
        item = EbayScraperItem()
        item['url'] = response.url
        item['status'] = response.status
        item['content'] = response.text
        yield item

        # Log success or failure
        if response.status == 200:
            self.logger.info(f"[{self.get_current_time()}] [URL: {response.url}] [Proxy: {response.meta.get('proxy', 'None')}] [Status: {response.status}] [Comment: Success]")
        else:
            self.logger.info(f"[{self.get_current_time()}] [URL: {response.url}] [Proxy: {response.meta.get('proxy', 'None')}] [Status: {response.status}] [Comment: Failed]")

    def get_current_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def closed(self, reason):
        self.logger.info(f"Spider closed: {reason}")
        print(f"Spider closed: {reason}")
