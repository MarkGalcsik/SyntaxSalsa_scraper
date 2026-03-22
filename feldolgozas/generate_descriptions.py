import pandas as pd
import os, re, time, requests, json
from openpyxl import load_workbook

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages'

SYSTEM_PROMPT = """
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

SEO_SYSTEM_PROMPT = """
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


def generate(name, existing_desc):
    user_msg = f"Terméknév: {name}\n\nMeglévő leírás (forrásanyag):\n{existing_desc}"
    resp = requests.post(
        ANTHROPIC_API_URL,
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 800,
            'system': SYSTEM_PROMPT,
            'messages': [{'role': 'user', 'content': user_msg}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['content'][0]['text'].strip()

def generate_seo(name, description):
    user_msg = f"Terméknév: {name}\n\nTermékleírás:\n{description}"
    resp = requests.post(
        ANTHROPIC_API_URL,
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 400,
            'system': SEO_SYSTEM_PROMPT,
            'messages': [{'role': 'user', 'content': user_msg}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    raw = resp.json()['content'][0]['text'].strip()
    raw = re.sub(r'^```json\s*|^```\s*|```$', '', raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


input_path  = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\import\export_import.xlsx"
output_path = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\import\export_import_fixed.xlsx"

df = pd.read_excel(input_path, dtype=str, header=1).fillna('')
total = len(df)

for idx, row in df.iterrows():
    name = row.get('Name', '').strip()
    existing = row.get('Description', '').strip()
    if not name:
        continue
    print(f'[{idx+1}/{total}] {name} ...', end=' ', flush=True)
    try:
        new_desc = generate(name, existing)
        df.at[idx, 'Description'] = new_desc
        time.sleep(0.3)

        seo = generate_seo(name, new_desc)
        df.at[idx, 'Search Keywords']  = seo.get('search_keywords', '')
        df.at[idx, 'Meta Title']        = seo.get('meta_title', '')
        df.at[idx, 'Meta Description']  = seo.get('meta_description', '')
        df.at[idx, 'Meta Keywords']     = seo.get('meta_keywords', '')

        print('OK')
    except Exception as e:
        print(f'HIBA: {e}')
    time.sleep(0.3)

orig = pd.read_excel(input_path, dtype=str, header=None).fillna('')
group_header = orig.iloc[0]  

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:

    pd.DataFrame([group_header.tolist()]).to_excel(writer, index=False, header=False, sheet_name='Sheet1')
    
    df.to_excel(writer, index=False, header=True, sheet_name='Sheet1', startrow=1)

print(f'\nKész! Mentve: {output_path}')