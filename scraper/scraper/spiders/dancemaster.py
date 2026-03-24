import scrapy
import re
from scraper.items import HotcakesProductItem


class DancemasterSpider(scrapy.Spider):
    name = "dancemaster"

    MAX_PER_CATEGORY = 50

    start_urls = [
        #'https://www.dancemaster.hu/tanccipo/noi-tanccipo',
        #'https://www.dancemaster.hu/tancruhak/tancruhak-noknek',
        'https://www.dancemaster.hu/tanc-kiegeszitok/tanckiegeszitok',
        #'https://www.dancemaster.hu/tanccipo/ferfi-tanccipo',
        #'https://www.dancemaster.hu/tancruhak/tancruhak-ferfiaknak',
        'https://www.dancemaster.hu/tanc-kiegeszitok',
        #'https://www.dancemaster.hu/tanccipo/tanccipo-gyerekeknek',
        #'https://www.dancemaster.hu/tancruhak/gyermekek',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_counts = {}

    def parse(self, response):
        self.logger.info(f"Kategória oldal betöltve: {response.url}")

        base_url = response.url.split('?')[0]
        if base_url not in self.category_counts:
            self.category_counts[base_url] = 0

        collected = self.category_counts[base_url]
        if collected >= self.MAX_PER_CATEGORY:
            self.logger.info(f"Elérte a {self.MAX_PER_CATEGORY} termékes limitet: {base_url}")
            return

        product_links = response.css('.product-thumb .image a::attr(href)').getall()

        product_links = list(dict.fromkeys(product_links))

        remaining = self.MAX_PER_CATEGORY - collected
        links_to_scrape = [l for l in product_links if "/blog/" not in l][:remaining]

        for link in links_to_scrape:
            self.category_counts[base_url] += 1
            yield response.follow(link, self.parse_product, cb_kwargs={'category_url': base_url})

        if self.category_counts[base_url] < self.MAX_PER_CATEGORY:
            next_page = response.css('ul.pagination li.next a::attr(href)').get()
            if next_page:
                self.logger.info(f"Következő oldalra ugrás: {next_page}")
                yield response.follow(next_page, self.parse)

    def parse_product(self, response, category_url=None):
        self.logger.info(f"Termékoldal feldolgozása: {response.url}")
        item = HotcakesProductItem()

        name = response.css('h1.product-title-default::text').get()
        if not name:
            name = response.css('h1::text').get()
        item['Name'] = name.strip() if name else "Ismeretlen termék"


        price = None
        price_selectors = [
            '.product-price .final-price::text',
            '.product-price .price-new::text',
            '.product-price span::text',
            '[class*="final-price"]::text',
            '[class*="price-new"]::text',
            '[class*="price"]::text',
        ]
        for sel in price_selectors:
            price = response.css(sel).get()
            if price and re.search(r'\d', price):
                break

        if price and re.search(r'\d', price):
            digits = re.sub(r'[^\d]', '', price)
            item['Price'] = digits + " Ft"
        else:
            all_text = response.text
            ft_match = re.search(r'(\d[\d\s]{2,})\s*Ft', all_text)
            if ft_match:
                digits = re.sub(r'[^\d]', '', ft_match.group(1))
                item['Price'] = digits + " Ft"
            else:
                item['Price'] = "0 Ft"


        product_id = response.css('input[name="product_id"]::attr(value)').get()

        name_letters = re.sub(r'[^a-zA-Z]', '', item['Name'])
        prefix = name_letters[:3].upper() if len(name_letters) >= 3 else name_letters.upper()

        if product_id:
            item['SKU'] = f"{prefix}-{product_id.strip()}"
        else:
            fallback_num = str(abs(hash(item['Name'])))[:5]
            item['SKU'] = f"{prefix}-{fallback_num}"

        description_parts = response.css(
            '#product-description .col-sm-6:first-child p::text, '
            '#product-description .col-sm-6:first-child p b::text, '
            '#product-description p::text, '
            '.product-description p::text'
        ).getall()
        if description_parts:
            item['Description'] = " ".join([p.strip() for p in description_parts if p.strip()])
        else:
            item['Description'] = ""

        # --- KÉP ---
        img_url = response.css('#product-image-slideshow .owl-item img::attr(src)').get()
        if not img_url:
            img_url = response.css('.product-image .thumbnail img::attr(src)').get()
        if not img_url:
            img_url = response.css('img.img-responsive::attr(src)').get()

        item['ImageUrl'] = response.urljoin(img_url) if img_url else ""

        yield item