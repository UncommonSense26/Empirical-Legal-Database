#!/usr/bin/env python3
"""
Extract the six Jury Management Indices from OSCA's quarterly
"Jury Management Indices Report" PDFs into a tidy unit-quarter CSV.

Structure of every edition (verified against the FY 2009-10 Q2 edition
and the quarter-ending-June-2024 edition, fifteen years apart):

  page 1        index definitions
  pages 2-88    one page per judicial circuit, followed by one page per
                county in that circuit; 20 circuits, 67 counties

Each page holds six charts in a 3x2 grid. Under each chart is a
quarterly table with two data rows: the unit itself, and the comparison
median (circuit median on circuit pages, state median on county pages).
The four quarter columns rotate between editions, so quarter labels and
years are read off the page rather than assumed.

The six indices, as OSCA defines them on page 1:
  summoning_yield             jurors available to serve on day one
                              divided by jurors summoned. FSC goal >= 40%.
  juror_days_per_trial        (jurors reporting daily + carry-overs)
                              divided by jury trials. FSC goal <= 30.5.
  people_brought_in_per_trial jurors reporting daily divided by jury
                              trials. FSC goal <= 18.3 (six-person).
  percent_to_voir_dire        persons sent to voir dire divided by
                              jurors reporting daily. FSC goal >= 100%.
  average_panel_size          prospective jurors sent to voir dire per
                              jury empaneled.
  number_of_trials            six-person plus twelve-person jury trials.

OSCA's own caveat, reproduced on page 1 of every edition: the data is
self reported by the clerk of court or the circuit court administrator,
and OSCA does not confirm its accuracy, validity, or reliability.

Usage:
    python3 extract_jury_indices.py report1.pdf [report2.pdf ...] -o out.csv
"""

import argparse
import csv
import re
import sys
from pathlib import Path

import pdfplumber

QUARTERS = ["Jan-Mar", "Apr-Jun", "Jul-Sep", "Oct-Dec"]

INDEX_BLOCKS = [
    ("summoning_yield", r"Summoning\s*Yield\s*-\s*Quarterly\s*Data"),
    ("juror_days_per_trial", r"Juror\s*Days\s*Per\s*Trial\s*-\s*Quarterly\s*Data"),
    ("people_brought_in_per_trial", r"People\s*Brought\s*In\s*Per\s*Trial\s*-\s*Quarterly\s*Data"),
    ("percent_to_voir_dire", r"Percent\s*to\s*Voir\s*Dire\s*-\s*Quarterly\s*Data"),
    ("average_panel_size", r"Average\s*Panel\s*Size\s*-\s*Quarterly\s*Data"),
    ("number_of_trials", r"Number\s*of\s*Trials\s*\(\s*6\s*\+\s*12\s*Person\s*\)\s*-\s*Quarterly\s*Data"),
]

PCT_INDICES = {"summoning_yield", "percent_to_voir_dire"}

NUM = re.compile(r"\d[\d,]*\.?\d*\s*%|\d[\d,]*\.?\d*")

CIRCUIT_WORDS = (
    "First Second Third Fourth Fifth Sixth Seventh Eighth Ninth Tenth Eleventh "
    "Twelfth Thirteenth Fourteenth Fifteenth Sixteenth Seventeenth Eighteenth "
    "Nineteenth Twentieth"
).split()
ORDINAL_TO_NUM = {w: i + 1 for i, w in enumerate(CIRCUIT_WORDS)}

QUARTER_START_MONTH = {"Jan-Mar": 1, "Apr-Jun": 4, "Jul-Sep": 7, "Oct-Dec": 10}


def _is_doubled(tok, min_len=4):
    return (len(tok) >= min_len and len(tok) % 2 == 0
            and all(tok[i] == tok[i + 1] for i in range(0, len(tok), 2)))


def undouble(line):
    """
    Some editions draw bold table rows twice, one glyph offset apart, so the
    text layer reads 'SSttaattee MMeeddiiaann 2222.33 2244.66'. Letters and
    digits get doubled; punctuation usually does not. Detect the condition
    from the row label, then halve each doubled run.
    """
    toks = [t for t in line.split(" ") if t]
    alpha = [t for t in toks if t.isalpha()]
    if not alpha or not any(_is_doubled(t) for t in alpha):
        return line

    def fix(tok):
        out, run = [], ""
        for ch in tok:
            if ch.isalnum():
                run += ch
            else:
                out.append(run[::2] if _is_doubled(run, 2) else run)
                out.append(ch)
                run = ""
        out.append(run[::2] if _is_doubled(run, 2) else run)
        return "".join(out)

    return " ".join(fix(t) for t in line.split(" "))


def clean_num(tok):
    tok = tok.replace(",", "").replace("%", "").strip()
    try:
        return float(tok)
    except ValueError:
        return None


def page_label(page):
    """The circuit or county name printed in the page's right-hand header."""
    b = page.bbox
    txt = page.crop((b[0], b[1], b[2], b[1] + (b[3] - b[1]) * 0.06)).extract_text() or ""
    for line in txt.split("\n"):
        lab = line.replace("Jury Management Indices Report", "").strip()
        if lab:
            return lab
    return ""


def half_lines(page, side, frac=0.50):
    """
    Split the page into left and right chart columns. The divider is not
    always at the exact midpoint: page bounding boxes are sometimes offset
    and column widths vary between editions, so the fraction is a parameter
    and parse_page tries several.
    """
    b = page.bbox
    mid = b[0] + (b[2] - b[0]) * frac
    x0, x1 = (b[0], mid) if side == "L" else (mid, b[2])
    txt = page.crop((x0, b[1], x1, b[3])).extract_text(layout=True) or ""
    return [l for l in txt.split("\n")]


def parse_block(lines, hdr, unit_key):
    """
    Read one quarterly table beginning at line index `hdr`.
    Returns (header, unit_vals, median_vals) or None.
    header is [(quarter, year), ...] in printed left-to-right order.
    """
    window = lines[hdr + 1: hdr + 10]

    quarters = None
    years = None
    unit_vals = None
    median_vals = None
    fallback_vals = None
    fallback_label = None

    for line in window:
        line = undouble(line)
        # Editions published 2015-2022 letter-space some header tokens, e.g.
        # 'J a n - M ar' and 'Summoning Yield 2 0 14 2014 ...'. Match quarter
        # labels and years against a space-stripped copy of the line.
        d = line.replace(" ", "")
        found = [(d.find(q), q) for q in QUARTERS if q in d]
        if len(found) == 4 and quarters is None:
            quarters = [q for _, q in sorted(found)]
            continue

        if years is None and "%" not in line and "." not in line:
            ys = re.findall(r"(?:19|20)\d{2}", d)
            if len(ys) >= 4:
                cand = [int(y) for y in ys[-4:]]
                if max(cand) - min(cand) <= 1:
                    years = cand
                    continue

        toks = NUM.findall(line)
        if len(toks) < 4:
            continue
        # Row labels can themselves contain digits, e.g. "(6 + 12 Person)".
        # The four data columns are always the rightmost four numbers.
        vals = [clean_num(t) for t in toks[-4:]]
        if any(v is None for v in vals):
            continue

        low = line.lower()
        if "median" in low:
            if median_vals is None:
                median_vals = vals
        elif unit_key and unit_key in low:
            if unit_vals is None:
                unit_vals = vals
        elif re.match(r"\s*[A-Za-z(]", line) and fallback_vals is None:
            fallback_vals = vals
            fallback_label = line.strip()

    if quarters is None or years is None:
        return None

    # A few tables in OSCA's own template carry a stale row label from the
    # preceding page (the Second Circuit page labels its Average Panel Size
    # row "First Circuit" in every edition checked). The values are the
    # page's own; only the label is wrong. Fall back to the sole non-median
    # data row and flag it rather than dropping the observation.
    mislabeled = False
    if unit_vals is None and fallback_vals is not None:
        unit_vals = fallback_vals
        mislabeled = fallback_label
    return list(zip(quarters, years)), unit_vals, median_vals, mislabeled


def unit_key_for(label):
    """A short lowercase key that survives OCR: 'St. Lucie County' -> 'lucie'."""
    stripped = re.sub(r"\b(County|Judicial|Circuit)\b", "", label, flags=re.I)
    words = re.sub(r"[^A-Za-z ]", " ", stripped).split()
    return words[-1].lower() if words else ""


def parse_page(page):
    label = page_label(page)
    if not label or "Indices Report" in label:
        return []

    is_circuit = bool(re.search(r"Judicial\s+Circuit", label, re.I))
    if is_circuit:
        ordinal = label.split()[0]
        unit_type = "circuit"
        circuit_no = ORDINAL_TO_NUM.get(ordinal)
        county = None
    else:
        unit_type = "county"
        circuit_no = None
        county = re.sub(r"\s*County\s*$", "", label, flags=re.I).strip()

    key = unit_key_for(label)

    # Try several column-divider positions and keep whichever recovers the
    # most of the six index blocks. Editions differ in layout, and a divider
    # that clips one chart silently drops that index rather than erroring.
    best_lines, best_hits = None, -1
    for frac in (0.50, 0.47, 0.53, 0.44, 0.56):
        cand = half_lines(page, "L", frac) + half_lines(page, "R", frac)
        hits = sum(1 for _, p in INDEX_BLOCKS
                   if any(re.search(p, l, re.I) for l in cand))
        if hits > best_hits:
            best_lines, best_hits = cand, hits
        if hits == len(INDEX_BLOCKS):
            break
    lines = best_lines

    rows = []
    for idx_name, pattern in INDEX_BLOCKS:
        hdr = next((i for i, l in enumerate(lines) if re.search(pattern, l, re.I)), None)
        if hdr is None:
            continue
        parsed = parse_block(lines, hdr, key)
        if parsed is None:
            continue
        header, unit_vals, median_vals, mislabeled = parsed
        for pos, (quarter, year) in enumerate(header):
            rows.append({
                "unit_type": unit_type,
                "unit_name": label,
                "county": county,
                "circuit": circuit_no,
                "year": year,
                "quarter": quarter,
                "quarter_start": f"{year}-{QUARTER_START_MONTH[quarter]:02d}",
                "index": idx_name,
                "is_percent": idx_name in PCT_INDICES,
                "value": unit_vals[pos] if unit_vals else None,
                "comparison_median": median_vals[pos] if median_vals else None,
                "source_row_label_mismatch": mislabeled or "",
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("-o", "--out", default="jury_indices.csv")
    args = ap.parse_args()

    all_rows = []
    for p in args.pdfs:
        before = len(all_rows)
        with pdfplumber.open(p) as pdf:
            for page in pdf.pages:
                for r in parse_page(page):
                    r["source_file"] = Path(p).name
                    all_rows.append(r)
        got = len(all_rows) - before
        units = len({r["unit_name"] for r in all_rows[before:]})
        print(f"{Path(p).name}: {got} rows, {units} units", file=sys.stderr)

    if not all_rows:
        sys.exit("no rows extracted")

    fields = ["source_file", "unit_type", "unit_name", "county", "circuit",
              "year", "quarter", "quarter_start", "index", "is_percent",
              "value", "comparison_median", "source_row_label_mismatch"]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in all_rows:
            w.writerow({k: r.get(k) for k in fields})
    print(f"wrote {len(all_rows)} rows -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
