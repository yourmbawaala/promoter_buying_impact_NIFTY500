"""Every number in the video, from data/events.csv. pandas + numpy only, about 30 s.

Run: python analyze.py   -> prints and writes results/stats.json
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
THR = 0.5  # "promoters bought" = promoter stake up >= 0.5 percentage points vs the previous quarter
rng = np.random.default_rng(7)

ev = pd.read_csv(HERE / "data/events.csv", parse_dates=["quarter_end", "entry_date"])
ev["group"] = np.select([ev.promoter_chg_pp >= THR, ev.promoter_chg_pp <= -THR], ["bought", "sold"], "flat")
ex, ret = ev.excess_vs_nifty500tri_12m, ev.stock_ret_12m


def summary(m):
    return {"n": int(m.sum()),
            "mean_excess_pct": round(100 * ex[m].mean(), 1),
            "median_excess_pct": round(100 * ex[m].median(), 1),
            "beat_index_pct": round(100 * (ex[m] > 0).mean(), 1),
            "big_winner_pct": round(100 * (ret[m] >= 0.5).mean(), 1)}   # stock itself up 50%+ in 12 months


def block_ci(fn, n=3000):
    """95% CI by resampling whole quarters: filings in the same quarter share the same market, so they aren't independent."""
    by_q = [g for _, g in ev.groupby("quarter_end")]
    vals = [fn(pd.concat([by_q[i] for i in rng.integers(0, len(by_q), len(by_q))])) for _ in range(n)]
    return [round(100 * v, 1) for v in np.percentile(vals, [2.5, 97.5])]


def gap(metric, a="bought", b=None):
    def f(s):
        x = metric(s)
        return x[s.group == a].mean() - (x.mean() if b is None else x[s.group == b].mean())
    return f


beat = lambda s: (s.excess_vs_nifty500tri_12m > 0).astype(float)
big = lambda s: (s.stock_ret_12m >= 0.5).astype(float)
exc = lambda s: s.excess_vs_nifty500tri_12m

out = {
    "window": f"entries {ev.entry_date.min():%b %Y} to {ev.entry_date.max():%b %Y}; 12-month returns end by Jun 2026",
    "symbols": int(ev.symbol.nunique()),
    "threshold_pp": THR,
    "all": summary(ev.group.notna()),
    **{g: summary(ev.group == g) for g in ("bought", "flat", "sold")},
    "ci95_bought_minus_all": {
        "beat_index_pp": block_ci(gap(beat)),
        "big_winner_pp": block_ci(gap(big)),
        "mean_excess_pp": block_ci(gap(exc)),
    },
    "ci95_bought_minus_sold_beat_index_pp": block_ci(gap(beat, "bought", "sold")),
    "bought_events_by_year": {int(y): int(n) for y, n in ev[ev.group == "bought"].entry_date.dt.year.value_counts().sort_index().items()},
    "robustness": {f"stake_up_gt_{t}pp": summary(ev.promoter_chg_pp > t) for t in (0.0, 2.0)},
}
print(json.dumps(out, indent=2))
(HERE / "results").mkdir(exist_ok=True)
json.dump(out, open(HERE / "results/stats.json", "w"), indent=2)

# the video's on-screen numbers; fails loudly if the data or code drift
assert (out["all"]["n"], out["symbols"], out["bought"]["n"]) == (9487, 678, 179)
assert (out["bought"]["beat_index_pct"], out["all"]["beat_index_pct"], out["sold"]["beat_index_pct"]) == (55.3, 49.0, 48.4)
assert (out["bought"]["big_winner_pct"], out["all"]["big_winner_pct"]) == (29.6, 22.7)
