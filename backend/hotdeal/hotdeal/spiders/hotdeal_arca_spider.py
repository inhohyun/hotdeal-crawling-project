import scrapy
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import DataUtils

PROJECT_ROOT_PATH = DataUtils.get_current_development()

class ArcaSpider(scrapy.Spider):
    name = "arca_hotdeal"
    custom_settings = {
        'ITEM_PIPELINES': {
            "hotdeal.pipelines.HotdealPipeline": 300,
        },
        'FEEDS': {
            f'{PROJECT_ROOT_PATH}/app/static/arca_hotdeal.csv': {
                'format': 'csv',
                'encoding': 'utf-8',
                'overwrite': True,
            },
        },
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1,
        'LOG_ENABLED': False
    }
    def __init__(self):
        self.site = "arca"
        
    def start_requests(self):
        print(f"Crawl Start {self.site} ")
        urls = [
            f'https://arca.live/b/hotdeal?p={idx}' for idx in range(1, 6)
        ]
        
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
            
    def parse(self, response):
        
        base = response.xpath("//div[contains(@class, 'list-table hybrid')]//div[contains(@class, 'vrow hybrid')]")
        
        for arca in base:            
            
            col_title = arca.xpath(".//span[contains(@class, 'vcol col-title')]//span[contains(@class, 'badges')]")
            vrow_bottom = arca.xpath(".//div[contains(@class, 'vrow-bottom deal')]")   
            
            yield { 
                "site": self.site,
                "url": arca.xpath(".//a[contains(@class, 'title hybrid-title')]/@href").get(),
                "recommend": vrow_bottom.xpath(".//span[contains(@class, 'vcol col-rate')]/text()").get(),  
                "title": arca.xpath(".//a[contains(@class, 'title hybrid-title')]/text()[2]").get(),
                "comment": arca.xpath(".//a[contains(@class, 'title hybrid-title')]//span[contains(@class, 'comment-count')]/text()").get(),
                "shoppingmall": col_title.xpath(".//span[contains(@class, 'deal-store')]//text()").get(),
                "price": vrow_bottom.xpath(".//span[contains(@class, 'deal-price')]/text()").get(),
                "deliveryfee": vrow_bottom.xpath(".//span[contains(@class, 'deal-delivery')]/text()").get(),
                "category": col_title.xpath(".//a[contains(@class, 'badge')]//text()").get(),
                "time": vrow_bottom.xpath(".//span[contains(@class, 'vcol col-time')]/time/@datetime").get(),
                "author": vrow_bottom.xpath(".//span[contains(@class, 'user-info')]/span/@data-filter").get(),
                "views": vrow_bottom.xpath(".//span[contains(@class, 'vcol col-view')]/text()").get()
            }
        
