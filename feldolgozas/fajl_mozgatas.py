import shutil
import os

# --- KONFIGURÁCIÓ ---
SOURCE_DIR = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\import\images"
DEST_DIR   = r"C:\M\Corvinus\4.félév\rendszerfejlesztes\2.fazis\import\images_ready"

NAMES_FILE = r"kepek_lista.txt"   # a .txt fájl elérési útja (vagy csak a neve, ha ugyanabban a mappában van a scripttel)
# ---------------------

# Nevek beolvasása
with open(NAMES_FILE, encoding="utf-8") as f:
    IMAGE_NAMES = [line.strip() for line in f if line.strip()]

os.makedirs(DEST_DIR, exist_ok=True)

found     = 0
not_found = []

for name in IMAGE_NAMES:
    src = os.path.join(SOURCE_DIR, name)
    dst = os.path.join(DEST_DIR, name)

    if os.path.isfile(src):
        shutil.copy2(src, dst)
        print(f"  ✔  {name}")
        found += 1
    else:
        print(f"  ✘  NEM TALÁLHATÓ: {name}")
        not_found.append(name)

print(f"\nKész. Kimásolt: {found} | Nem találtam: {len(not_found)}")

if not_found:
    print("\nHiányzó fájlok:")
    for n in not_found:
        print(f"  - {n}")