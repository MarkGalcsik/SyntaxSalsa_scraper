# SyntaxSalsa Scraper

Ez a projekt egy **Pythonra** és **Scrapy** frameworkre épülő web scraper. A célja táncos ruházatokat, cipőket és kiegészítőket forgalmazó weboldalakról a termékadatok és képek automatikus kinyerése, majd ezek exportálása egy a **Hotcakes** import struktúrájának megfelelő Excel fájlba.

---

##  A projektben szereplő Spiderek (Pókok)

A projekt keretében két fő adatgyűjtő script készült:
* **danceandsway.py**: A [Dance and Sway](https://www.danceandsway.com/en-hu/) weboldaláról gyűjti ki a termékeket.
* **dancemaster.py**: A [Dancemaster](https://www.dancemaster.hu/) webáruházból gyűjti ki az adatokat.

---

##  Adatfeldolgozás és Működés

Az adatok és fájlok formázása a `pipelines.py` fájlban történik:
* **Képkezelés:** A rendszer automatikusan letölti a termékképeket, majd azokat a generált **SKU alapján nevezi el**.
* **Excel export:** A kinyert adatokat (név, ár, leírás, kategória stb.) a scraper a Hotcakes rendszer által elvárt Excel struktúrába menti ki.

---

##  Fejlesztési Környezet és Verziókövetés

A fejlesztés egy virtuális környezetben történt.
* **Virtuális környezet létrehozása:** `python -m venv venv`
* **Verziókövetés:** A projekt Git alapú verziókövetést használ (`git init`).
* **Repository:** Annak érdekében, hogy a kód könnyebben csatolható és hivatkozható legyen a Mantis tickethez, a teljes projekt fel lett töltve egy GitHub repository-ba.

---

##  Telepítés és Futtatás

A projekt helyi gépen történő futtatásához kövesd az alábbi lépéseket:

1. **Klónozd a repository-t**, majd a terminálban lépj be a projekt gyökérmappájába.
2. **Aktiváld a virtuális környezetet** (Windows esetén):
   ```bash
   venv\Scripts\activate
   ```
3. **Csomagok telepítése**
    ```
    pip install -r requirements.txt
    ```
4. **Scraper elindítása**
    ```
    scrapy crawl danceandswy/dancemaster
    ```

## Fejlestés menete:

A fejlesztéshez **Claude AI** és a **Scrapy** dokumentációt használtam. Mivel még ezelőtt nem igazán fejlesztettem még scrapert, így ezek hatalmas segítségek voltak. A dokumentáció áttanulmányozásával és a projekt struktúrájának a megértésével kezdtem claude és olykor a gemini segítségével.

A chrome DevTools-t weboldalak szerkezetének feltérképezésére használtam. Ennek segítségével nyertem ki azokat a pontos CSS szelektorokat, amelyek alapján a pókok tudják, hogy pontosan mit kell kimenteniük.

Ezt követően hozzákezdtem a pókok fejlesztésébe. Itt amint már említettem két pókot is létrehoztam a két oldal scrapeléséhez. Oldalanként kb 50 termékre maximalizáltam a scrapinget, mivel nem sok értelmét láttam többnek. Ennél a folyamatnál is használtam AI támogatását. Az AI által írt kódot átellenőriztem és a szükséges módosításokat elvégeztem.

Az adatok feldolgozásával és az exceles mentéssel ért végez a scraping. A képeket egy images mappába png formátumban tölti le a script. 
A kapott adatokat egy Pandas DataFrame-be tölti be, majd ezt a már említett excel struktúrába menti. 

A fejlesztés végén megtörtént a git commit és a push, továbbá dokumentáció megírása is. 