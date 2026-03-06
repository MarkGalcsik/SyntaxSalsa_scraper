import scrapy

class HotcakesProductItem(scrapy.Item):
    Name = scrapy.Field()
    Price = scrapy.Field()
    SKU = scrapy.Field()
    Description = scrapy.Field()
    ImageUrl = scrapy.Field()
    Image = scrapy.Field() # Ezt a pipeline tölti majd ki a letöltött fájlnévvel