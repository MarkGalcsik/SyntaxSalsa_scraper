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
        # --- 1. KÉP LETÖLTÉSE ---
        img_url = item.get('ImageUrl')
        item['Image'] = "" 

        if img_url:
            parsed_url = urlparse(img_url)
            original_filename = os.path.basename(parsed_url.path)
            if not original_filename:
                original_filename = f"kep_{len(self.items)}"
            
            base_name = os.path.splitext(original_filename)[0]
            image_filename = f"{base_name}.png"
            item['Image'] = image_filename

            if img_url.startswith('/'):
                # Ezt cseréld le annak az oldalnak a domainjére, amit épp kaparsz!
                img_url = "https://www.dancemaster.hu" + img_url 

            try:
                resp = requests.get(img_url, timeout=10)
                if resp.status_code == 200:
                    image = Image.open(io.BytesIO(resp.content))
                    if image.mode not in ('RGB', 'RGBA'):
                        image = image.convert('RGBA')
                    
                    file_path = os.path.join(self.image_dir, image_filename)
                    image.save(file_path, "PNG")
            except Exception as e:
                spider.logger.error(f"Hiba a kép letöltésekor ({img_url}): {e}")

        self.items.append(item)
        return item

    def close_spider(self, spider):
        # --- 2. TÖBB MUNKALAPOS EXCEL GENERÁLÁSA ---
        if not self.items:
            return

        # 1. Main munkalap adatai
        main_columns = [
            "SLUG","Active","Featured","SKU","Name","Product Type","MSRP","Cost","Price",
            "Manufacturer","Vendor","Image","Description","Search Keywords","Meta Title",
            "Meta Description","Meta Keywords","Tax Schedule","Tax Exempt","Weight","Length",
            "Width","Height","Extra Ship Fee","Ship Mode","Non-Shipping Product",
            "Ships in a Separate Box","Allow Reviews","Minimum Qty","Inventory Mode",
            "Inventory","StockOut","Low Stock at","Roles","Searchable","AllowUpcharge",
            "UpchargeAmount","UpchargeUnit"
        ]
        
        main_rows = []
        categories_rows = []
        choices_rows = []
        properties_rows = []

        for item in self.items:
            # Közös SLUG generálása, ami összeköti a munkalapokat
            slug = re.sub(r'[^a-z0-9]+', '-', item['Name'].lower()).strip('-')
            
            # --- MAIN SOR ÖSSZEÁLLÍTÁSA ---
            row = {col: "" for col in main_columns}
            row["SLUG"] = slug
            row["Active"] = "YES"
            row["Featured"] = "NO"
            row["SKU"] = item["SKU"]
            row["Name"] = item["Name"]
            row["Product Type"] = "Táncfelszerelés"
            row["MSRP"] = "0,00 Ft"
            row["Cost"] = "0,00 Ft"
            row["Price"] = item["Price"]
            row["Image"] = item["Image"]
            row["Description"] = item["Description"]
            
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

            # --- KATEGÓRIA SOR ELŐKÉSZÍTÉSE (Csak SLUG) ---
            categories_rows.append({
                "PRODUCT SLUG": slug,
                "CATEGORIES SLUGS": "" # Ide írod majd be kézzel pl. hogy "cipc591,nc591i-tc3a1nccipc591"
            })

            # --- CHOICES SOR ELŐKÉSZÍTÉSE (Csak SLUG, a többi üres) ---
            choices_rows.append({
                "PRODUCT SLUG": slug,
                "CHOICE": "",           # pl. Női cipőméret
                "CHOICE TYPE": "DropDownList", 
                "SHARED": "YES", 
                "CHOICE ITEMS": ""      # pl. - Válasszon -,35,36,37...
            })

            # --- PROPERTIES SOR ELŐKÉSZÍTÉSE ---
            properties_rows.append({
                "PRODUCT SLUG": slug,
                "Property Name": "",    # pl. Szint
                "Value": ""             # pl. Amatőr
            })

        # DataFrame-ek létrehozása
        df_main = pd.DataFrame(main_rows, columns=main_columns)
        df_categories = pd.DataFrame(categories_rows)
        df_choices = pd.DataFrame(choices_rows)
        df_properties = pd.DataFrame(properties_rows)

        excel_path = "Hotcakes_Import_Full.xlsx"
        
        # Több munkalap mentése egyetlen Excel fájlba
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_main.to_excel(writer, sheet_name='Main', index=False)
            df_categories.to_excel(writer, sheet_name='Categories', index=False)
            df_choices.to_excel(writer, sheet_name='Choices', index=False)
            df_properties.to_excel(writer, sheet_name='Type Properties', index=False)
            
        spider.logger.info(f"SIKER: Több munkalapos Excel mentve ide: {excel_path}")