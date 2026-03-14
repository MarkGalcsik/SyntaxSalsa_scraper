import scrapy
import re
from scraper.items import HotcakesProductItem


class DanceandswaySpider(scrapy.Spider):
    name = "danceandsway"          

    MAX_PER_CATEGORY = 50          

    start_urls = [
        # === SALSA ===
        'https://www.danceandsway.com/en-hu/collections/salsa-dresses',
        'https://www.danceandsway.com/en-hu/collections/salsa-dance-shoes-1',

        # === LATIN ===
        'https://www.danceandsway.com/en-hu/collections/latin-dance-dress',
        'https://www.danceandsway.com/en-hu/collections/dance-shoes-latin',

        # === BALETT ===
        'https://www.danceandsway.com/en-hu/collections/womens-ballet-dance-shoes',
        'https://www.danceandsway.com/en-hu/collections/dance-leotards-1',   # balett ruha/leotard

        # === ÁLTALÁNOS (női + férfi + gyerek) ===
        'https://www.danceandsway.com/en-hu/collections/women-dance-dresses',
        'https://www.danceandsway.com/en-hu/collections/women-dancewear',
        'https://www.danceandsway.com/en-hu/collections/mens-dance-shoes',
        'https://www.danceandsway.com/en-hu/collections/men-latin-wear',
        'https://www.danceandsway.com/en-hu/collections/kids-dance-shoes-1',
        'https://www.danceandsway.com/en-hu/collections/girls-laitn-dance-wear',   # lány
        'https://www.danceandsway.com/en-hu/collections/dance-skirt',

        # === KIEGÉSZÍTŐK (táska, stb.) ===
        'https://www.danceandsway.com/en-hu/collections/accessories',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_counts = {}
        self.seen_product_urls = set()

    def parse(self, response):
        self.logger.info(f"Kategória oldal: {response.url}")

        base_url = response.url.split('?')[0]
        if base_url not in self.category_counts:
            self.category_counts[base_url] = 0

        collected = self.category_counts[base_url]
        if collected >= self.MAX_PER_CATEGORY:
            self.logger.info(f"Limit elérve ({self.MAX_PER_CATEGORY}): {base_url}")
            return

        # Új oldal terméklinkjei (Quick buy + minden /products/ link)
        product_links = response.css('a[href*="/products/"]::attr(href)').getall()
        product_links = list(dict.fromkeys(product_links))  # duplikációk eltávolítása

        remaining = self.MAX_PER_CATEGORY - collected
        links_to_scrape = [l for l in product_links if "/blog/" not in l][:remaining]

        for link in links_to_scrape:
            absolute_url = response.urljoin(link)
            # FIX #1: Skip already-seen product URLs
            if absolute_url in self.seen_product_urls:
                self.logger.debug(f"Már feldolgozva, kihagyva: {absolute_url}")
                continue
            self.seen_product_urls.add(absolute_url)
            self.category_counts[base_url] += 1
            yield response.follow(link, self.parse_product, cb_kwargs={'category_url': base_url})

        # Lapozás (a danceandsway oldalon működik)
        next_page = response.css(
            'li.next a::attr(href), '
            'a.next::attr(href), '
            'link[rel="next"]::attr(href), '
            'a[href*="page="]::attr(href)'
        ).get()

        if next_page and self.category_counts[base_url] < self.MAX_PER_CATEGORY:
            self.logger.info(f"Következő oldal: {next_page}")
            yield response.follow(next_page, self.parse)

    def parse_product(self, response, category_url=None):
        self.logger.info(f"Termékoldal: {response.url}")
        item = HotcakesProductItem()

        # Név
        name = response.css('h1::text').get(default='').strip()
        item['Name'] = name or "Ismeretlen termék"

        # Ár (USD formátumban marad)
       # Ár kinyerése – specifikus a danceandsway.com jelenlegi struktúrájára
        price_raw = response.css('.price__current::text').get(default='').strip()
        if not price_raw:
            price_raw = response.css(
                '.product-price .price__current::text, .price ::text'
            ).get(default='').strip()

        if price_raw and re.search(r'\d', price_raw):
            
            cleaned = re.sub(r'[^\d]', '', price_raw)  
            item['Price'] = cleaned
        else:
            item['Price'] = 0

        self.logger.info(f"Ár: {item['Price']} | {response.url}")

        # SKU (a Product Code mezőből!)
        product_code = re.search(r'Product Code:\s*(\S+)', response.text)
        product_id = product_code.group(1) if product_code else None

        name_letters = re.sub(r'[^a-zA-Z]', '', item['Name'])
        prefix = name_letters[:3].upper() if len(name_letters) >= 3 else name_letters.upper()

        if product_id:
            item['SKU'] = f"{prefix}-{product_id}"
        else:
            fallback_num = str(abs(hash(item['Name'])))[:5]
            item['SKU'] = f"{prefix}-{fallback_num}"

        # Leírás
        description_parts = response.css(
            '.product-description ::text, '
            '#description ::text, '
            '.description ::text'
        ).getall()
        item['Description'] = " ".join([p.strip() for p in description_parts if p.strip()]) or ""

        # KÉP
        img_url = response.css(
            '.slideshow img::attr(src), '
            '.product-media img::attr(src), '
            'img[src*=".jpg"]::attr(src), '
            'img[src*=".png"]::attr(src)'
        ).get()

        item['ImageUrl'] = response.urljoin(img_url) if img_url else ""

        yield item