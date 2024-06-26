# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from hotdeal.utils import convert_to_datetime, convert_to_datetime_detail, FmUtils, ArcaUtils, DataUtils, QzUtils, RuliUtils
import pickle
import re
import base64


class HotdealPipeline:
    
    def __init__(self):
        self.category_dict = None
        
    def open_spider(self, spider):
        spider.logger.info("TestSpider Pipelines Started.")
        
    def process_item(self, item, spider):
        # category_dict 캐싱, 필드 처리
        if self.category_dict is None:
            self.category_dict = DataUtils.get_site_category(item['site'])
        
        item['category'] = item['category'].strip()
        item['category'] = self.category_dict[item['category']] if item['category'] in self.category_dict else "기타"
            
        # recommend 필드 처리        
        if item['recommend'] is None:
            item['recommend'] = '0'
        item['recommend'] = re.sub(r'[\[\]]', '', item['recommend'])

        # comment 필드 처리
        if item['comment'] is None:
            item['comment'] = '0'
        item['comment'] = re.sub(r'[\[\]]', '', item['comment'])

        # site, deliveryfee, price, view 필드 처리
        item['site'] = item['site'].strip()
        item['deliveryfee'] = item['deliveryfee'].strip()
        item['price'] = item['price'].strip()
        

        """
            Time Field Process
            
            Input 1 = HH:MM
            Input 2 = YYYY.MM.DD
            Input 3 = MM-DD
            
            Output -> YYYY-MM-DD HH:MM
        """
                
        if item['site'] == 'fm':
            item['url'] = "https://www.fmkorea.com" + item['url']
            item['time'] = FmUtils.adjust_time(convert_to_datetime(item['time'].strip()))
            
        elif item['site'] == 'arca':
            item['url'] = "https://arca.live" + item['url']
            item['time'] = ArcaUtils.convert_iso_to_str(item['time'].strip())
            item['views'] = item['views'].strip()
            
        elif item['site'] == 'qz':
            item['url'] = "https://quasarzone.com" + item['url']
            item['time'] = convert_to_datetime(item['time'].strip())
            item['views'] = item['views'].strip()
            
            match = re.search(r'\[(.*?)\]', item['title'])
            if match:
                item['shoppingmall'] = match.group(1) if match.group(1) else "기타 쇼핑몰"
            else:
                item['shoppingmall'] = "기타 쇼핑몰"
        
        elif item['site'] == 'ruli':
        
            item['time'] = convert_to_datetime(item['time'].strip())
            item['views'] = item['views'].strip()
            item['author'] = item['author'].strip()
            item['price'] = "가격 미제공"
            item['deliveryfee'] = "배송비 미제공"
            
            match = re.search(r'\[(.*?)\]', item['title'])
            if match:
                item['shoppingmall'] = match.group(1) if match.group(1) else "기타 쇼핑몰"
            else:
                item['shoppingmall'] = "기타 쇼핑몰"
            
        # title 필드 처리
        
        item['title'] = item['title'].strip()

        # author 필드 처리
        item['author'] = re.sub(r'[\s/]', '', item['author'])

        item['deliveryfee'] = DataUtils.remove_keywords(item['deliveryfee'], "배송비", "배달료", "배송료")
        return item

class HotdealDetailPipeline:
        
    def open_spider(self, spider):
        spider.logger.info("TestSpider HotdealDetail Pipelines Started.")
        
    def process_item(self, item, spider):
        # shoppingmall field 처리
        
        item['shoppingmall'] = item['shoppingmall'].strip()
        
        # article이 아예 없는 경우
        if item['article'] is None or item['article'] == 'lazy':
            item['article'] = ""
        
        item['title'] = item['title'].strip()
        item['price'] = str(item['price']).strip()
        item['deliveryfee'] = str(item['deliveryfee']).strip()
        item['product_name'] = item['product_name'].strip()
        item['likes'] = str(item['likes']).strip()
        item['author'] = item['author'].strip()
        
        
        if item['site'] == "fm":
            for comments in item['comments']:
                comments['content'] = [content.strip() for content in comments['content']]
                comments['date'] = convert_to_datetime_detail(comments['date'].replace(" ", "")) 
                comments['author'] = comments['author'].strip()          
                
            item['date'] = convert_to_datetime(item['date'])
            
        elif item['site'] == "arca":
            for comments in item['comments']:
                comments['content'] = comments['content'].strip() if comments['content'] is not None else "Blank"
                comments['author'] = comments['author'].strip()
                comments['date'] = ArcaUtils.convert_iso_to_str(comments['date'].replace(" ", ""))         
                
            item['date'] = ArcaUtils.convert_fromisoformat(item['date'])
        elif item['site'] == "qz":
            # for comments in item['comments']: #TODO 지금 구현 안됨
            #     comments['content'] = comments['content'].strip() if comments['content'] is not None else "Blank"
                # comments['date'] = QzUtils.convert_timeformat(comments['date'].replace(" ", ""))
            
            item['date'] = QzUtils.convert_timeformat(item['date'])
            item['product_name'] = QzUtils.extract_product_name(item['title'])
            
        elif item['site'] == "ruli":
            item['date'] = RuliUtils.convert_timeformat(item['date'])
            
            for comments in item['comments']:
                comments['content'] = comments['content'].strip() if comments['content'] is not None else "Blank"
                comments['author'] = comments['author'].strip() if comments['author'] is not None else "익명"
                comments['date'] = convert_to_datetime(comments['date'].strip()) if comments['date'] is not None else item['date']

            item['price'] = '가격 미제공'
            item['deliveryfee'] = '배송비 미제공'
        
            match = re.search(r'\[(.*?)\]', item['title'])
            if match:
                item['shoppingmall'] = match.group(1) if match.group(1) else "기타 쇼핑몰"
            else:
                item['shoppingmall'] = "기타 쇼핑몰"
                
            item['product_name'] = RuliUtils.extract_product_name(item['title'])
            item['views'] = RuliUtils.remove_whitespace_views(item['views'])
            item['comment_count'] = DataUtils.remove_parentheses(item['comment_count'])
            
            if item['related_url'] is None or item['related_url'] == "":
                item['related_url'] = '연관 url 미제공'
            
        item['comments'] = base64.b64encode(pickle.dumps(item['comments'])).decode('utf-8') # pickle로 comment data 직렬화 -> base64 encoding
        
            
        return item
