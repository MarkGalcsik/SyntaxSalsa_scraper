import scrapy
import re
import json
from scraper.items import HotcakesProductItem 

class DancemasterSpider(scrapy.Spider):
    name = "dancemaster"
    
    start_urls = [
        'https://www.dancemaster.hu/tanccipo/noi-tanccipo/balett-spicc-cipo'
    ]

    def parse(self, response):
        self.logger.info(f"Kategória oldal betöltve: {response.url}")
        
        # 1. Termék linkek kigyűjtése a termékkártyákról
        product_links = response.css('.product-thumb .image a::attr(href)').getall()
        
        for link in list(set(product_links)):
            if "/blog/" not in link: 
                yield response.follow(link, self.parse_product)

        # 2. Lapozás (Pagination) - Megkeresi a ">" gombot
        next_page = response.css('ul.pagination li.next a::attr(href)').get()
        if next_page:
            self.logger.info(f"Következő oldalra ugrás: {next_page}")
            yield response.follow(next_page, self.parse)

    def parse_product(self, response):
        self.logger.info(f"Termékoldal feldolgozása: {response.url}")
        item = HotcakesProductItem()
        
        # --- NÉV ---
        # A h1.product-title-default tartalmazza a teljes nevet
        name = response.css('h1.product-title-default::text').get()
        if not name:
            name = response.css('h1::text').get()
        item['Name'] = name.strip() if name else "Ismeretlen termék"
        
        # --- ÁR ---
        # A beküldött HTML-ben: <span class="final-price">9 230 Ft</span>
        price = response.css('.product-price .final-price::text').get()
        if price:
            # Csak a számokat tartjuk meg (pl. "9 230 Ft" -> "9230")
            item['Price'] = re.sub(r'[^\d]', '', price) + " Ft"
        else:
            item['Price'] = "0 Ft"
            
        # --- SKU (Cikkszám / Product ID) ---
        # Elsődlegesen a 'product_id' hidden input-ot használjuk, mert ez mindig egyedi
        sku = response.css('input[name="product_id"]::attr(value)').get()
        if not sku:
            # Másodlagos: ha van kint szöveges cikkszám
            sku = response.xpath('//li[contains(text(), "Cikkszám")]/text()').get()
        
        if sku:
            item['SKU'] = sku.replace('Cikkszám:', '').strip()
        else:
            # Végső eset: generálunk a névből
            item['SKU'] = re.sub(r'[^a-zA-Z0-9]', '-', item['Name'].lower())[:15]
            
        # --- LEÍRÁS ---
        # A leírás a #product-description alatti első col-sm-6-ban van
        description_parts = response.css('#product-description .col-sm-6:first-child p::text, #product-description .col-sm-6:first-child p b::text').getall()
        if description_parts:
            item['Description'] = " ".join([p.strip() for p in description_parts if p.strip()])
        else:
            item['Description'] = "Nincs leírás."
            
        # --- KÉP ---
        # A fő kép a slideshow első eleme
        img_url = response.css('#product-image-slideshow .owl-item img::attr(src)').get()
        if not img_url:
            # Fallback a főképre, ha a slideshow nem töltődne be
            img_url = response.css('.product-image .thumbnail img::attr(src)').get()
            
        item['ImageUrl'] = response.urljoin(img_url) if img_url else ""
            
        yield item