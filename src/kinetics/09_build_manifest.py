from __future__ import annotations
from pathlib import Path
import csv, hashlib
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "SHA256SUMS.csv"
rows=[]
for p in sorted(ROOT.rglob("*")):
    if p.is_file() and p != OUT and "__pycache__" not in p.parts:
        rows.append((str(p.relative_to(ROOT)), p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()))
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["relative_path","bytes","sha256"]); w.writerows(rows)
print(f"Wrote {OUT} with {len(rows)} entries")
