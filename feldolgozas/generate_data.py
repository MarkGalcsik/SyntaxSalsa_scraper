import pandas as pd
import os, re, time, requests, json

# ─── Konfiguráció ────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages'
MODEL             = 'claude-sonnet-4-20250514'

INPUT_PATH  = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\import\import_forditott_product\import1.xlsx"
OUTPUT_PATH = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\import\import_forditott_product\import1_1.xlsx"

DELAY_BETWEEN_ROWS = 0.5   # másodperc (API rate limit elkerülése)

# ─── Promptok ────────────────────────────────────────────────────────────────

DESCRIPTION_PROMPT = """
Te egy profi táncos webshop szövegírója vagy. Feladatod vonzó magyar nyelvű termékleírást írni
a megadott terméknév és meglévő leírás alapján.

Kövesd PONTOSAN ezt a struktúrát, HTML formátumban:

<p><strong>[Egy mondatos, figyelemfelkeltő alcím]</strong></p>
<p>[2-3 mondatos bevezető – mi a termék, mire való, kinek ajánlott]</p>
<p><strong>Miért válaszd?</strong></p>
<p>[2-3 mondat a főbb előnyökről]</p>
<p><strong>Technikai jellemzők</strong></p>
<ul>
<li>[jellemző 1]</li>
<li>[jellemző 2]</li>
<li>[jellemző 3]</li>
</ul>

Stílus: lelkes, szakmai, közérthető. Célközönség: táncosok, táncpedagógusok.
Csak a leírás HTML szövegét add vissza, semmi mást.
""".strip()

SEO_PROMPT = """
Te egy profi SEO szakértő vagy, aki táncos webshopnak dolgozik. Feladatod SEO mezők kitöltése
a megadott terméknév és leírás alapján. Válaszolj KIZÁRÓLAG valid JSON formátumban, így:

{
  "search_keywords": "kulcsszó1, kulcsszó2, kulcsszó3, kulcsszó4, kulcsszó5",
  "meta_title": "Terméknév – rövid, kulcsszavas cím",
  "meta_description": "150-160 karakteres vonzó leírás, tartalmazza a főbb kulcsszavakat és CTA-t.",
  "meta_keywords": "kulcsszó1, kulcsszó2, kulcsszó3, kulcsszó4, kulcsszó5"
}

Szabályok:
- search_keywords: 5-8 releváns magyar keresési kifejezés vesszővel elválasztva
- meta_title: max 60 karakter, tartalmazza a terméknevet és egy-két kulcsszót
- meta_description: 150-160 karakter, vonzó, tartalmaz CTA-t (pl. "Rendelje meg most!")
- meta_keywords: 5-8 kulcsszó vesszővel elválasztva
- Minden mező magyar nyelvű legyen
- Csak a JSON objektumot add vissza, semmi mást
""".strip()

# ─── API hívások ─────────────────────────────────────────────────────────────

def call_api(system_prompt: str, user_message: str, max_tokens: int) -> str:
    """Általános Anthropic API hívás."""
    response = requests.post(
        ANTHROPIC_API_URL,
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        json={
            'model': MODEL,
            'max_tokens': max_tokens,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': user_message}],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()['content'][0]['text'].strip()


def generate_description(name: str, existing_desc: str) -> str:
    user_msg = f"Terméknév: {name}\n\nMeglévő leírás (forrásanyag):\n{existing_desc}"
    return call_api(DESCRIPTION_PROMPT, user_msg, max_tokens=800)


def generate_seo(name: str, description: str) -> dict:
    user_msg = f"Terméknév: {name}\n\nTermékleírás:\n{description}"
    raw = call_api(SEO_PROMPT, user_msg, max_tokens=400)
    raw = re.sub(r'^```json\s*|^```\s*|```$', '', raw, flags=re.MULTILINE).strip()
    return json.loads(raw)

# ─── Segédfüggvények ──────────────────────────────────────────────────────────

def already_has_description(text: str) -> bool:
    """True ha a leírás már kész HTML formátumban van (<p> vagy <h2> taggel kezdődik)."""
    stripped = text.strip()
    return stripped.startswith('<p') or stripped.startswith('<h2')

# ─── Fő logika ────────────────────────────────────────────────────────────────

def main():
    # Eredeti fájl betöltése (fejléc az 1. sorban van, 0-indexed → header=1)
    original_raw = pd.read_excel(INPUT_PATH, dtype=str, header=None).fillna('')
    group_header = original_raw.iloc[0]  # az extra fejlécsor megőrzéséhez

    df = pd.read_excel(INPUT_PATH, dtype=str, header=1).fillna('')
    total = len(df)
    skipped = 0
    processed = 0
    errors = 0

    for idx, row in df.iterrows():
        name        = row.get('Name', '').strip()
        existing    = row.get('Description', '').strip()
        row_display = f"[{idx + 1}/{total}] {name}"

        if not name:
            print(f"{row_display} → KIHAGYVA (nincs terméknév)")
            skipped += 1
            continue

        if already_has_description(existing):
            print(f"{row_display} → KIHAGYVA (már van kész leírás)")
            skipped += 1
            continue

        print(f"{row_display} → generálás...", end=' ', flush=True)

        try:
            # 1. Leírás generálás
            new_desc = generate_description(name, existing)
            df.at[idx, 'Description'] = new_desc
            time.sleep(DELAY_BETWEEN_ROWS)

            # 2. SEO generálás
            seo = generate_seo(name, new_desc)
            df.at[idx, 'Search Keywords'] = seo.get('search_keywords', '')
            df.at[idx, 'Meta Title']      = seo.get('meta_title', '')
            df.at[idx, 'Meta Description'] = seo.get('meta_description', '')
            df.at[idx, 'Meta Keywords']   = seo.get('meta_keywords', '')

            print('OK')
            processed += 1

        except Exception as e:
            print(f'HIBA: {e}')
            errors += 1

        time.sleep(DELAY_BETWEEN_ROWS)

    # ─── Mentés (eredeti csoportfejléc megőrzésével) ──────────────────────────
    with pd.ExcelWriter(OUTPUT_PATH, engine='openpyxl') as writer:
        pd.DataFrame([group_header.tolist()]).to_excel(
            writer, index=False, header=False, sheet_name='Sheet1'
        )
        df.to_excel(
            writer, index=False, header=True,
            sheet_name='Sheet1', startrow=1
        )

    print(f"\n{'─' * 50}")
    print(f"Kész! Mentve: {OUTPUT_PATH}")
    print(f"  Feldolgozva : {processed}")
    print(f"  Kihagyva    : {skipped}")
    print(f"  Hibás       : {errors}")
    print(f"{'─' * 50}")


if __name__ == '__main__':
    main()