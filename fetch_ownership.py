#!/usr/bin/env python3
"""Fetch NSE quarterly shareholding-pattern history (promoter %) for every symbol in data/symbols.txt.

Promoter holding is INLINE in the shareholding-master JSON (`pr_and_prgrp`), so this
needs one call per symbol -- no XBRL. The finer breakdown (FII / DII / mutual fund /
retail / pledged) lives only in the linked SHP XBRL (~300 KB each, ~20 per symbol),
which is a separate and much heavier job (not needed here).

POINT-IN-TIME: `submissionDate` is when the filing hit the exchange. Always align
signals to submissionDate, never to the quarter-end `date` -- filings land 3-6 weeks
after quarter end and using `date` leaks the future.

Output: data/promoter_holding.csv  (symbol, quarter_end, submitted, promoter_pct, public_pct)

Run: python fetch_ownership.py [--limit N]   (symbols from data/symbols.txt; ~3 min, polite 0.25 s delay)
"""
import argparse, gzip, json, sys, time, urllib.request
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "data"; OUT.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
      "Accept": "*/*", "Referer": "https://www.nseindia.com/"}
API = "https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol={}"
DELAY = 0.25


def get(url, tries=3):
    for k in range(tries):
        try:
            d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()
            if d[:2] == b"\x1f\x8b":
                d = gzip.decompress(d)
            return json.loads(d.decode("utf-8", "replace"))
        except Exception as e:
            if k == tries - 1:
                return None
            time.sleep(1.5 * (k + 1))
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    syms = (OUT / "symbols.txt").read_text().split()  # NSE symbols with Yahoo .NS suffix
    if a.limit:
        syms = syms[:a.limit]

    rows, fails = [], []
    for i, s in enumerate(syms, 1):
        j = get(API.format(s.replace(".NS", "")))
        if not j or not isinstance(j, list):
            fails.append(s)
        else:
            for r in j:
                rows.append({"symbol": s, "quarter_end": r.get("date"),
                             "submitted": r.get("submissionDate"),
                             "promoter_pct": r.get("pr_and_prgrp"),
                             "public_pct": r.get("public_val")})
        if i % 50 == 0:
            print(f"  {i}/{len(syms)}  rows={len(rows)}  fails={len(fails)}", flush=True)
        time.sleep(DELAY)

    df = pd.DataFrame(rows)
    for c in ("quarter_end", "submitted"):
        df[c] = pd.to_datetime(df[c], format="%d-%b-%Y", errors="coerce")
    for c in ("promoter_pct", "public_pct"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["quarter_end", "submitted"]).sort_values(["symbol", "quarter_end"])
    df.to_csv(OUT / "promoter_holding.csv", index=False)

    lag = (df.submitted - df.quarter_end).dt.days
    print(f"\n{len(df):,} filings, {df.symbol.nunique()} symbols, "
          f"{df.quarter_end.min():%Y-%m} -> {df.quarter_end.max():%Y-%m}")
    print(f"filing lag after quarter end: median {lag.median():.0f}d, "
          f"p90 {lag.quantile(0.9):.0f}d  (why submissionDate matters)")
    print(f"quarters per symbol: median {df.groupby('symbol').size().median():.0f}")
    print(f"failed symbols: {len(fails)}")
    print(f"saved -> {OUT/'promoter_holding.csv'}")
