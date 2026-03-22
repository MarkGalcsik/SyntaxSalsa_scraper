"""
fix_products.py
---------------
1. Hotcakes_Import_Full.xlsx  — SKU cleanup + Name fordítás/strukturálás
2. dancemaster_import.xlsx    — Name strukturálás (már részben magyar, de átrendezés kell)

Struktúra cél: "Márka Modell, magyar termékleírás"
Pl: "Bloch Arise Split Sole, bőr balettcipő"

Használat:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python fix_products.py
"""

import os
import re
import time
import requests
import pandas as pd
from openpyxl import load_workbook

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
REQUEST_DELAY = 0.3   # seconds between API calls

# ---------------------------------------------------------------------------
# SKU cleanup
# ---------------------------------------------------------------------------

def clean_sku(raw: str) -> str:
    """Keep only 'PREFIX-DIGITS', strip everything after the number."""
    if not isinstance(raw, str):
        return raw
    # Normalize escaped newlines
    raw = raw.replace('\\n', ' ').replace('\n', ' ')
    # Match PREFIX-DIGITS and stop
    m = re.match(r'([A-Z]+-\d+)', raw)
    return m.group(1) if m else raw.strip()


# ---------------------------------------------------------------------------
# Name translation/restructuring via Claude
# ---------------------------------------------------------------------------

NAME_SYSTEM_PROMPT = """
Te egy táncos webshop szövegírója vagy. Feladatod termékneveket strukturálni és magyarra fordítani.

Szabályok:
- Ha van márkanév (pl. Bloch, Capezio, Sansha), tartsd meg az elején
- Ha van modellnév/kód (pl. Arise, SD16), tartsd meg a márka után
- Utána szóközzel (NEM vesszővel) írj rövid, tömör magyar leírást (max 5-6 szó)
- Ha nincs márkanév, kezdd rögtön a magyar leírással
- Ne adj hozzá semmit ami nincs az eredetiben (pl. ne találj ki méretet, színt)
- Csak a terméknevet add vissza, semmi mást, semmilyen magyarázatot
- FONTOS: a végeredményben sehol ne szerepeljen vessző

Példák:
"Women's Milk Silk Fabric Tassel Dance Skirt Training Performance Dancewear" -> "Rojtos latin szoknya selyem anyag"
"Bloch Arise Split Sole Leather Ballet Shoe" -> "Bloch Arise Split Sole bőr balettcipő"
"Men's 2cm Black Leatherette Heels Ballroom Dance Shoes" -> "Férfi standard tánccipő 2cm sarok"
"Kids Gold Leatherette Flats Jazz Teaching & Practice Shoes" -> "Gyerek jazz cipő arany műbőr"
"Full-Toe Yoga Pilates Grip Five-Toe Socks" -> "Yoga Pilates csúszásgátló zokni"
"Capezio Pirouette II, bőr balettcipő" -> "Capezio Pirouette II bőr balettcipő"
""".strip()


def translate_names_batch(names: list[str]) -> list[str]:
    """Send a batch of names to Claude, get back translated names in order."""
    if not ANTHROPIC_API_KEY:
        print("HIBA: ANTHROPIC_API_KEY nincs beállítva.")
        return names

    numbered = "\n".join(f"{i+1}. {n}" for i, n in enumerate(names))
    user_msg = (
        f"Az alábbi {len(names)} terméknevet strukturáld/fordítsd le a szabályok szerint.\n"
        f"Pontosan {len(names)} sort adj vissza, számozva (1. ... 2. ... stb.):\n\n"
        f"{numbered}"
    )

    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2000,
                "system": NAME_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_msg}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()

        # Parse numbered lines: "1. Name" -> ["Name", ...]
        results = []
        for line in raw.splitlines():
            line = line.strip()
            m = re.match(r'^\d+\.\s*(.+)', line)
            if m:
                results.append(m.group(1).strip())

        if len(results) == len(names):
            return results
        else:
            print(f"  FIGYELEM: {len(names)} nevet küldtünk, {len(results)} érkezett vissza — eredeti marad")
            return names

    except Exception as e:
        print(f"  API hiba: {e} — eredeti nevek maradnak")
        return names


def process_names(names_series: pd.Series, batch_size: int = 20, label: str = "") -> pd.Series:
    """Translate all names in batches, show progress."""
    names = names_series.tolist()
    total = len(names)
    result = list(names)

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = names[start:end]
        print(f"  {label} [{start+1}-{end}/{total}] fordítás...", end=" ", flush=True)
        translated = translate_names_batch(batch)
        result[start:end] = translated
        print("OK")
        if end < total:
            time.sleep(REQUEST_DELAY)

    return pd.Series(result, index=names_series.index)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fix_hotcakes():
    path = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\scraping\scraper\ferfi_latin_cr.xlsx"
    out  = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\scraping\scraper\ferfi_latin_cr_jav.xlsx"

    print("\n=== Hotcakes_Import_Full.xlsx ===")
    df = pd.read_excel(path, sheet_name="Main", dtype=str).fillna("")

    # 1. SKU cleanup
    print(f"SKU tisztítás ({len(df)} sor)...")
    df["SKU"] = df["SKU"].apply(clean_sku)
    print("  Kész.")

    # 2. Name translation
    print(f"Name fordítás/strukturálás...")
    df["Name"] = process_names(df["Name"], batch_size=20, label="Hotcakes")

    # 3. Rebuild SLUG from new Name
    df["SLUG"] = df["Name"].apply(
        lambda n: re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')
    )

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Main", index=False)
    print(f"  Mentve: {out}")


def fix_dancemaster():
    path = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\scraping\scraper\ferfi_latin_cr.xlsx"
    out  = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\scraping\scraper\ferfi_latin_cr.xlsx"

    print("\n=== dancemaster_import.xlsx ===")
    df = pd.read_excel(path, dtype=str).fillna("")

    print(f"Name strukturálás ({len(df)} sor)...")
    df["Name"] = process_names(df["Name"], batch_size=20, label="Dancemaster")

    # Rebuild SLUG from new Name
    if "SLUG" in df.columns:
        df["SLUG"] = df["Name"].apply(
            lambda n: re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')
        )

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        sheet_name = "Main" if "SLUG" in df.columns else "Sheet1"
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"  Mentve: {out}")


if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        print("HIBA: Az ANTHROPIC_API_KEY környezeti változó nincs beállítva.")
        print("  export ANTHROPIC_API_KEY='sk-ant-...'")
        exit(1)

    fix_hotcakes()
    fix_dancemaster()
    print("\nMinden kész!")