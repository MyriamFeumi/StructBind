import csv
import os
from config import DATASET_CSV

if not os.path.exists(DATASET_CSV):
    print("Dataset vide — lancez features.py d'abord")
    exit()

with open(DATASET_CSV, 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f, delimiter=';'))

positifs = sum(1 for r in rows if r['label'] == '1')
negatifs = sum(1 for r in rows if r['label'] == '0')
total    = len(rows)
ratio    = negatifs / positifs if positifs > 0 else 0

print(f"\n{'='*40}")
print(f"  DATASET — Statistiques")
print(f"{'='*40}")
print(f"  Positifs (label=1) : {positifs}")
print(f"  Négatifs (label=0) : {negatifs}")
print(f"  Total              : {total}")
print(f"  Ratio neg/pos      : {ratio:.2f}")
print(f"  (idéal : 1.0-3.0)  ")
print(f"{'='*40}")