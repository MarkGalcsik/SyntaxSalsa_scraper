# SyntaxSalsa Scraper

Ez a projekt egy **Pythonra** és **Scrapy** frameworkre épülő web scraper. A célja táncos ruházatokat, cipőket és kiegészítőket forgalmazó weboldalakról a termékadatok és képek automatikus kinyerése, majd ezek exportálása egy a **Hotcakes** import struktúrájának megfelelő Excel fájlba.
---

## Miért Scrapy?

Nem egy egyszerű könyvtár, hanem egy komplett, robusztus keretrendszer.

A legnagyobb előny az úgynevezett Pipeline rendszer. Ahelyett, hogy a pók (spider) kódjába lenne belezsúfolva az adatok letöltése, tisztítása és mentése, a Scrapy szétválasztja ezeket a feladatokat. A pók csak kinyeri az adatot, míg a pipeline feldolgozza azt.
Emellett támogatja a CSS és XPath szelektorokat, így a DevTOOls-ból kinyert szelektorokat szinte egy az egyben, konvertálás nélkül tudtam átemelni a kódomba.
A képek kezelése is egyszerű a keretrendszerben. Az ImagesPipeline automatikusan kezeli a képek aszinkron letöltését, elkeüli a duplikát letöltést és könnyen testreszabható. A képeket ennek köszönhetően a termékek SKU nevével látom ezzel, annak érdekében, hogy könnyen felismerhető legyen.


##  A projektben szereplő Spiderek (Pókok)

A projekt keretében két fő adatgyűjtő script készült:
* **danceandsway.py**: A [Dance and Sway](https://www.danceandsway.com/en-hu/) weboldaláról gyűjti ki a termékeket.
* **dancemaster.py**: A [Dancemaster](https://www.dancemaster.hu/) webáruházból gyűjti ki az adatokat.

A két oldal kiválasztása nem volt véletlenszerű.
* A két weboldal lefedi az általunk meghatározott termékkínálatot. Olyan termékkategórák szerepelnek az alábbi webshopokban, mint a Latin, Balett, vagy Salsa, ugyanazok, amiket mi is meghatároztunk.
* Emellett a két oldal kombinálásával a scraperünk egy sokkal diverzifikáltabb jellemző termékporfóloót tudunk kialakítani. A két oldal a nemzetközi és hazai piac igényeit és árazási trendjeit tükrözi.
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

## Fejlesztés menete:

A fejlesztéshez **Claude AI** és a **Scrapy** dokumentációt használtam. Mivel még ezelőtt nem igazán fejlesztettem még scrapert, így ezek hatalmas segítségek voltak. A dokumentáció áttanulmányozásával és a projekt struktúrájának a megértésével kezdtem claude és olykor a gemini segítségével.

A chrome DevTools-t weboldalak szerkezetének feltérképezésére használtam. Ennek segítségével nyertem ki azokat a pontos CSS szelektorokat, amelyek alapján a pókok tudják, hogy pontosan mit kell kimenteniük.

Ezt követően hozzákezdtem a pókok fejlesztésébe. Itt amint már említettem két pókot is létrehoztam a két oldal scrapeléséhez. Oldalanként kb 50 termékre maximalizáltam a scrapinget, mivel nem sok értelmét láttam többnek. Ennél a folyamatnál is használtam AI támogatását. Az AI által írt kódot átellenőriztem és a szükséges módosításokat elvégeztem.

Az adatok feldolgozásával és az exceles mentéssel ért végez a scraping. A képeket egy images mappába png formátumban tölti le a script. 
A kapott adatokat egy Pandas DataFrame-be tölti be, majd ezt a már említett excel struktúrába menti. 

A fejlesztés végén megtörtént a git commit és a push, továbbá dokumentáció megírása is. 

# Adatfeldolgozó és Tisztító Segédscriptek

A nyers adatok kinyerése után szükség van az adatok tisztítására és keresőoptimalizálására. Ehhez a projekt mappájában három kiegészítő Python script készült.

## AI Leírás és SEO generátor:

Nem mindegyik termékhez volt jól strukturált magyar leírás, továbbá SEO metadatokat sem kezelte az eredeti projekt megfelelően ezért szükség volt egy olyan megoldásra, ami ezt gyorsan, átláthatóan és egyszerűen megoldja.

* **Cél:** Magyar nyelvű, HTML formátumú termékleírások és a hozzájuk tartozó SEO metaadatok automatikus legenerálása.
* **Működése:** A script beolvassa az összeállított excel fájlt és soronként elküldi a terméknevet és a nyers leírást a Claude API-nak. Két dedikált promptot futtat. Az egyik egy fix html struktúrájú leírást generál a másik pedig egy JSON formátumú SEO csomagot ad vissza. Az eredményeket a meglévő excel oszlopokba új fájlként elmenti.
* **Miért volt rá szükség?** A scraper által kinyert nyers leírások vizuálisan formázatlanok, vagy túl rövidek, vagy egyszerűen más struktúrájúak voltak, mint én azt kitaláltam. Emellett a SEO-t a scraper nem kezeli.

  ## Képválogató és mozgató script

  Ez egy egyszerűbb, rövidebb script
  * **Cél:** A végleges excel importban szereplő termékekhez tartozó képek automatikus kiválogatása és átmásolása egy üres import_ready mappába.
  * **Működés:** Egy egyszerű szöveges fájlból beolvassa a feltöltéshez szükséges képek neveit, majd a scraper által letöltött nyers images mappábólátmásolja őket a images_ready célmappába. A folyamat végén pedig kilistázza a sikeres átmásolt, illetve a hiányző fájlokat.
  * **Miért volt rá szükség?** A scraping folyamat során több kép került letöltésre, mint amennyire szükségem van, így sokkal gyorsabban és igazából egyszerűbben tudom a kiválasztott termék képét feltölteni a HotCakes-be.
 
  ##  Név tisztító/fordító script

  Mivel az egyik oldal az angol nyelvű, így szükség van a termékek lefordítására, emellett a scraping folyamat során az SKU-knál egyedi értékek vannak, viszont a könnyebb megkülönböztetés miatt úgy gondoltam szüség van az SKU-k újragondolására.
  * **Cél:** A terméknevek magyarra fordítása.
  * **Működés:** A  Claude API segítségével, kötegelve lefordítja a termékneveket.
  * **MIért volt rá szükség?** A külföldi oldalakról kinyert nevek gyakran következetetlenek, vagy fölösleges kifejezéseket tartalmaznak. Úgy gondolom egy webshopnak fontos az, hogy a terméknevek megfelelőek és egységesek legyenek. A manuális átírás ennél a termékmennyiségnél nagyon hosszú lenne, így az AI alapú atuomatizáció jelentős időt spórolt meg.
