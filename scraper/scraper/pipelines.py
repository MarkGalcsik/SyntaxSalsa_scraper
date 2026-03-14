import os
import requests
from PIL import Image
import io
import pandas as pd
import re
from urllib.parse import urlparse


class HotcakesExportPipeline:
    def __init__(self):
        self.items = []
        self.image_dir = 'images'

        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

    def process_item(self, item, spider):
        # --- KÉP LETÖLTÉSE ---
        img_url = item.get('ImageUrl')
        item['Image'] = ""

        if img_url:
            # Képfájl neve = SKU (pl. CAP-12345.png)
            sku = item.get('SKU', 'kep')
            safe_sku = re.sub(r'[^a-zA-Z0-9\-_]', '_', sku)
            image_filename = f"{safe_sku}.png"
            item['Image'] = image_filename

            # Ha relatív URL, tegyük elé a domain-t
            if img_url.startswith('/'):
                #img_url = "https://www.dancemaster.hu" + img_url
                img_url = "https://www.danceandsway.com" + img_url

            try:
                resp = requests.get(img_url, timeout=10)
                if resp.status_code == 200:
                    image = Image.open(io.BytesIO(resp.content))
                    if image.mode not in ('RGB', 'RGBA'):
                        image = image.convert('RGBA')
                    file_path = os.path.join(self.image_dir, image_filename)
                    image.save(file_path, "PNG")
                    spider.logger.info(f"Kép mentve: {file_path}")
                else:
                    spider.logger.warning(f"Kép letöltés sikertelen ({resp.status_code}): {img_url}")
            except Exception as e:
                spider.logger.error(f"Hiba a kép letöltésekor ({img_url}): {e}")

        self.items.append(item)
        return item

    def close_spider(self, spider):
        if not self.items:
            spider.logger.warning("Nincs termék, Excel nem készül.")
            return

        main_columns = [
            "SLUG", "Active", "Featured", "SKU", "Name", "Product Type",
            "MSRP", "Cost", "Price", "Manufacturer", "Vendor", "Image",
            "Description", "Search Keywords", "Meta Title", "Meta Description",
            "Meta Keywords", "Tax Schedule", "Tax Exempt", "Weight", "Length",
            "Width", "Height", "Extra Ship Fee", "Ship Mode", "Non-Shipping Product",
            "Ships in a Separate Box", "Allow Reviews", "Minimum Qty",
            "Inventory Mode", "Inventory", "StockOut", "Low Stock at",
            "Roles", "Searchable", "AllowUpcharge", "UpchargeAmount", "UpchargeUnit"
        ]

        main_rows = []

        for item in self.items:
            slug = re.sub(r'[^a-z0-9]+', '-', item['Name'].lower()).strip('-')

            row = {col: "" for col in main_columns}
            row["SLUG"] = slug
            row["Active"] = "YES"
            row["Featured"] = "NO"
            row["SKU"] = item.get("SKU", "")
            row["Name"] = item.get("Name", "")
            row["Product Type"] = "Generic"
            row["MSRP"] = ""
            row["Cost"] = ""
            row["Price"] = item.get("Price", "0")
            row["Image"] = item.get("Image", "")
            row["Description"] = item.get("Description", "")
            row["Tax Exempt"] = "NO"
            row["Ship Mode"] = "ShipFromSite"
            row["Non-Shipping Product"] = "NO"
            row["Ships in a Separate Box"] = "NO"
            row["Allow Reviews"] = "YES"
            row["Minimum Qty"] = 1
            row["Inventory Mode"] = "AlwayInStock"
            row["Inventory"] = 0
            row["Searchable"] = "YES"
            row["AllowUpcharge"] = "NO"
            main_rows.append(row)


        df_main = pd.DataFrame(main_rows, columns=main_columns)

        excel_path = "Hotcakes_Import_Full.xlsx"
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_main.to_excel(writer, sheet_name='Main', index=False)

        spider.logger.info(f"SIKER: Excel mentve: {excel_path} ({len(self.items)} termék)")