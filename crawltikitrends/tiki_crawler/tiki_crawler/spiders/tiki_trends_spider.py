
import scrapy #framework crawl dữ liệu
import json
from datetime import datetime
from scrapy import signals #dùng để gắn hàm khi kết thúc crawl (spider_closed)
import os #thao tác với file/thư mục.
import random
import time
from pytrends.request import TrendReq #truy vấn Google Trends
import re #xử lý chuỗi với biểu thức chính quy.
from .proxies import proxy_list

class TikiTrendsSpider(scrapy.Spider):
    name = "tiki_trends"
    allowed_domains = ["tiki.vn"]
    base_url = "https://tiki.vn/api/personalish/v1/blocks/listings?limit=40&category=1789&page={page}&tick=1&platform=web"

    custom_settings = {
        'FEEDS': {
            'data/datatrends.json': {
                'format': 'json',
                'encoding': 'utf-8',
            }
        },
        'ROBOTSTXT_OBEY': False,
        # 'LOG_ENABLED': True,
        # 'LOG_LEVEL': 'DEBUG',  # DEBUG | INFO | WARNING | ERROR | CRITICAL
        # 'LOG_FILE': 'logs/tiki_trends.log',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Referer': 'https://tiki.vn',
    }

    blacklist_keywords = ['ốp lưng', 'tai nghe', 'sạc', 'cáp', 'kính cường lực', 'giá đỡ', 'loa', 'dock', 'bảo vệ', 'miếng dán', 'đọc sách', 'bàn']
    valid_brands = ['samsung', 'apple', 'xiaomi', 'oppo', 'realme', 'vivo', 'nokia', 'tecno', 'infinix', 'asus', 'motorola']

    def __init__(self):
        self.products = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TikiTrendsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
#phát tín hiệu chạy spider_closed
        return spider

    def start_requests(self):
        yield scrapy.Request(
#yield ở đây giúp Scrapy xử lý bất đồng bộ (asynchronous) nhiều request cùng lúc.
            url=self.base_url.format(page=1),
            headers=self.headers,
            callback=self.parse,
            meta={'page': 1}
        )

    def parse(self, response):
        json_response = json.loads(response.text)
        products = json_response.get('data', [])

        for product in products:
            name = product.get('name', '').lower()
            brand = product.get('brand', {}).get('name', '').lower() if product.get('brand') else ""

            if any(keyword in name for keyword in self.blacklist_keywords):
                continue
            if brand and not any(valid in brand for valid in self.valid_brands):
                continue

            product_id = product.get('id')
            product_detail_url = f"https://tiki.vn/api/v2/products/{product_id}"

            yield scrapy.Request(
                url=product_detail_url,
                headers=self.headers,
                callback=self.parse_product,
                meta={'brand': brand}
            )

        if products:
            next_page = response.meta['page'] + 1
            next_url = self.base_url.format(page=next_page)
            yield scrapy.Request(
                url=next_url,
                headers=self.headers,
                callback=self.parse,
                meta={'page': next_page}
            )

    def parse_product(self, response):
        product_data = json.loads(response.text)
        product_id = product_data.get('id')
        item = {
            'id': product_id,
            'name': product_data.get('name'),
            'brand': product_data.get('brand', {}).get('name'),
            'price': product_data.get('price'),
            'quantity_sold': product_data.get('quantity_sold', {}).get('value'),
            'rating_average': product_data.get('rating_average'),
            'image': product_data.get('thumbnail_url'),
            'review_count': product_data.get('review_count'),
            'specs': product_data.get('specifications', []),
            'comments': [],
        }

        comments_url = f"https://tiki.vn/api/v2/reviews?product_id={product_id}&limit=20&page=1"
        yield scrapy.Request(
            url=comments_url,
            headers=self.headers,
            callback=self.parse_comments,
            meta={'item': item, 'product_id': product_id, 'page': 1}
        )

    def parse_comments(self, response):
        item = response.meta['item']
        product_id = response.meta['product_id']
        page = response.meta['page']

        json_response = json.loads(response.text)
        comment_data = json_response.get('data', [])

        for cmt in comment_data:
            item['comments'].append({
                'commenter_name': cmt.get('created_by', {}).get('name'),
                'content': cmt.get('content'),
                'rating': cmt.get('rating'),
            })

        if comment_data:
            next_page = page + 1
            next_url = f"https://tiki.vn/api/v2/reviews?product_id={product_id}&limit=20&page={next_page}"
            yield scrapy.Request(
                url=next_url,
                headers=self.headers,
                callback=self.parse_comments,
                meta={'item': item, 'product_id': product_id, 'page': next_page}
            )
        else:
            self.products.append(item)

    def spider_closed(self, spider):
        def clean_keyword(text):
            text = text.strip() #Xoá khoảng trắng ở đầu và cuối chuỗi
            text = re.sub(r'^(Điện thoại|Smartphone|Mobile|Máy Tính Bảng)\s+', '', text, flags=re.IGNORECASE)
            remove_keywords = [
                r'\(.*?\)', r'\d+\s*GB\s*/\s*\d+\s*GB', r'\d+\s*GB', r'\d+\s*MP',
                r'Zoom\s*\d+x', r'S\s*Pen', r'Hàng\s+Chính\s+Hãng', r'Camera',
                r'Màu.*?( |,|$)', r'AI', r'\d+\s*mAh', r'\d+\s*Hz', r'Wifi'
            ]
            for pattern in remove_keywords:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            text = re.sub(r'[^a-zA-ZÀ-ỹ0-9\s]', '', text)
            text = re.sub(r'\s+', ' ', text)
            return ' '.join(text.split()[:4])

        def get_google_trends(keyword, max_retries=5):

            for attempt in range(1, max_retries + 1):
                proxy = proxy_list[(attempt - 1) % len(proxy_list)]
                try:
                    pytrends = TrendReq(
                        hl='vi-VN',
                        tz=420, #múi g vn
                        timeout=(1, 2),
                        proxies=[proxy] if proxy else None,
                        requests_args={'headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                        }}
                    )
                    pytrends.build_payload([keyword], cat=0, timeframe='today 1-m', geo='VN')
                    data = pytrends.interest_over_time()
                    if not data.empty:
                        return int(data[keyword].mean())
                except Exception as e:
                    print(f" Lỗi trends '{keyword}' lần {attempt} → {e}")
                    time.sleep(random.uniform(10, 15))
            return 0

        for item in self.products:
            cleaned_name = clean_keyword(item.get('name', ''))
            trend = get_google_trends(cleaned_name)
            item['google_trend_score'] = trend
            print(f"{cleaned_name} → {trend}")
            time.sleep(random.uniform(20, 30))

        os.makedirs('data', exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = {"thời_gian_lấy_dữ_liệu": timestamp}
        final_data = [header] + self.products
        with open('data/datatrends.json', 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(" Hoàn tất crawl và thêm dữ liệu Google Trends.")
