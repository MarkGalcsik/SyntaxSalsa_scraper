import shutil
import os
from collections import defaultdict

# --- KONFIGURÁCIÓ ---
SOURCE_DIR = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis"
DEST_DIR   = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\import\images_ready"
NAMES_FILE = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\scraping\feldolgozas\kepek_lista.txt"
# ---------------------

# Nevek beolvasása
with open(NAMES_FILE, encoding="utf-8") as f:
    raw_lines = [line.strip() for line in f if line.strip()]

# Duplikát ellenőrzés a TXT-ben
name_counts = defaultdict(int)
for name in raw_lines:
    name_counts[name] += 1

duplicates_in_txt = {name: count for name, count in name_counts.items() if count > 1}
if duplicates_in_txt:
    print("⚠  DUPLIKÁT NEVEK A TXT FÁJLBAN:")
    for name, count in duplicates_in_txt.items():
        print(f"   '{name}' → {count}×")
    print()

# Egyedi nevek listája (sorrendet megőrizve)
IMAGE_NAMES = list(dict.fromkeys(raw_lines))

# --- Végigmegyünk a forrás mappán és almappáin, indexet építünk ---
# name → [teljes elérési út, ...] (egy névhez több találat is lehetséges!)
file_index = defaultdict(list)

for dirpath, dirnames, filenames in os.walk(SOURCE_DIR):
    for fname in filenames:
        file_index[fname].append(os.path.join(dirpath, fname))

# Duplikát fájlnév ellenőrzés a forrás mappában
duplicates_in_src = {name: paths for name, paths in file_index.items() if len(paths) > 1}
if duplicates_in_src:
    print("⚠  DUPLIKÁT FÁJLNEVEK A FORRÁS MAPPÁBAN (almappákban többször szerepel):")
    for name, paths in duplicates_in_src.items():
        if name in IMAGE_NAMES:   # csak a listában szereplőket jelezzük
            print(f"   '{name}' megtalálható {len(paths)} helyen:")
            for p in paths:
                print(f"      {p}")
    print()

os.makedirs(DEST_DIR, exist_ok=True)

found      = 0
not_found  = []
skipped_dup = []

for name in IMAGE_NAMES:
    dst = os.path.join(DEST_DIR, name)

    matches = file_index.get(name, [])

    if len(matches) == 0:
        print(f"  ✘  NEM TALÁLHATÓ: {name}")
        not_found.append(name)

    elif len(matches) == 1:
        shutil.copy2(matches[0], dst)
        print(f"  ✔  {name}  ←  {matches[0]}")
        found += 1

    else:
        # Több helyen is megvan → az elsőt másoljuk, de figyelmeztetünk
        shutil.copy2(matches[0], dst)
        print(f"  ⚠  DUPLIKÁT (az elsőt másoltam): {name}")
        for p in matches:
            print(f"      {p}")
        skipped_dup.append(name)
        found += 1

# --- Összesítő ---
print(f"\n{'='*55}")
print(f"Kész.")
print(f"  Kimásolt fájlok         : {found}")
print(f"  Nem találtam            : {len(not_found)}")
print(f"  Duplikát (1. példány)   : {len(skipped_dup)}")
print(f"  Duplikát a TXT-ben      : {len(duplicates_in_txt)}")

if not_found:
    print(f"\nHiányzó fájlok ({len(not_found)} db):")
    for n in not_found:
        print(f"  - {n}")

if skipped_dup:
    print(f"\nDuplikát forrás fájlok ({len(skipped_dup)} db) – mindig az első találatot másoltam:")
    for n in skipped_dup:
        print(f"  - {n}")