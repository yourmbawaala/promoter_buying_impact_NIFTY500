"""Rebuild data/events.csv from scratch: promoter filings + Yahoo Finance prices.

Event   = one quarterly shareholding filing (with a previous quarter to compare against).
Signal  = change in promoter % vs the previous quarter, in percentage points.
Entry   = close of the first trading session AFTER the filing's NSE submission date (no look-ahead).
Outcome = 252-session (≈12-month) stock return minus the Nifty 500 TRI (^CRSLDX) over the same window.
Only windows that finish by 2026-06-30 are kept.

Run: python build_events.py [--out data/events_rebuilt.csv]
The published data/events.csv came from the author's cleaned price panel (also Yahoo, auto-adjusted).
A fresh download can differ slightly because Yahoo revises history; see README.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
START, END, H = "2015-01-01", "2026-06-30", 252

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=str(HERE / "data/events_rebuilt.csv"))
a = ap.parse_args()

ph = pd.read_csv(HERE / "data/promoter_holding.csv", parse_dates=["quarter_end", "submitted"]).sort_values(["symbol", "quarter_end"])
ph["promoter_chg_pp"] = ph.groupby("symbol")["promoter_pct"].diff()
ph = ph.dropna(subset=["promoter_chg_pp", "submitted"])

bench = yf.download("^CRSLDX", start=START, end=END, auto_adjust=True, progress=False)["Close"].squeeze().dropna()
cal = bench.index                                          # NSE sessions = days the index printed
close = yf.download(sorted(ph.symbol.unique()), start=START, end=END, auto_adjust=True, progress=False, threads=True)["Close"]
close = close.reindex(cal)

rows = []
for r in ph.itertuples():
    if r.symbol not in close.columns:
        continue
    i = cal.searchsorted(r.submitted, side="right")         # first session strictly after the filing went public
    if i + H >= len(cal):
        continue
    p0, p1 = close[r.symbol].iat[i], close[r.symbol].iat[i + H]
    if not (np.isfinite(p0) and np.isfinite(p1)) or p0 <= 0:
        continue
    stock = p1 / p0 - 1
    rows.append((r.symbol, r.quarter_end.date(), cal[i].date(), round(r.promoter_chg_pp, 3), round(stock, 5),
                 round(stock - (bench.iat[i + H] / bench.iat[i] - 1), 5)))
ev = pd.DataFrame(rows, columns=["symbol", "quarter_end", "entry_date", "promoter_chg_pp", "stock_ret_12m", "excess_vs_nifty500tri_12m"])
ev.to_csv(a.out, index=False)
print(f"{len(ev):,} events, {ev.symbol.nunique()} symbols -> {a.out}")
