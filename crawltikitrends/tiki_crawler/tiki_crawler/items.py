import scrapy

class TikiCrawlerItem(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    quantity_sold = scrapy.Field()
    rating = scrapy.Field()
    comments = scrapy.Field()
