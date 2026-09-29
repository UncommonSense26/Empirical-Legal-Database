#!/usr/bin/env python3
"""Identity test that respects published rounding precision."""
import sys, pandas as pd

path = sys.argv[1]
df = pd.read_csv(path, dtype=str, keep_default_na=False)

APS, PBI, PVD = "Average Panel Size", "People Brought In / Trial", "Percent to Voir Dire"

def parse(tok):
    t = str(tok).replace(",", "").replace("%", "").strip()
    if t == "" or t.lower() in ("nan", "na", "none"):
        return None, None
    try:
        val = float(t)
    except ValueError:
        return None, None
    dec = len(t.split(".")[1]) if "." in t else 0
    return val, 0.5 * (10 ** -dec)

rows, fails = 0, []
for i, r in df.iterrows():
    a, ha = parse(r[APS]); p, hp = parse(r[PBI]); v, hv = parse(r[PVD])
    if a is None or p is None or v is None:
        continue
    rows += 1
    lo = max(0.0, (p - hp)) * max(0.0, (v - hv)) / 100.0
    hi = (p + hp) * (v + hv) / 100.0
    if (a + ha) < lo or (a - ha) > hi:
        fails.append((r["County"], r["Year"], r["Quarter"], a, p, v,
                      round(lo, 3), round(hi, 3), r.get("QA Flags", ""),
                      r.get("Data Status", "")))

print(f"testable records: {rows}")
print(f"identity failures outside the rounding envelope: {len(fails)}\n")
for f in fails:
    print(f"{f[0]:<14} {f[1]} {f[2]:<8} APS={f[3]:<8} PBI={f[4]:<8} "
          f"PVD={f[5]:<8} allowed=[{f[6]},{f[7]}]  flags={f[8]!r} status={f[9]!r}")

flagged = sum(1 for f in fails if str(f[8]).strip() not in ("", "nan"))
print(f"\nof those failures, already carried on QA Flags: {flagged} of {len(fails)}")
