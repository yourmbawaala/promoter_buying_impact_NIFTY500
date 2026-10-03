# When promoters buy, should you? A NIFTY 500 test

Code and data behind the [@yourMBAwaala](https://www.youtube.com/@yourMBAwaala) Short *"Promoters bought. Should you? I tested 9,487 filings."*

> **Educational only. Not investment advice.** I am not a SEBI-registered investment adviser or research analyst.
> Nothing here recommends buying or selling any security. Past results do not predict future returns.

## The question

Finfluencers often say "promoters increased their stake, so buy." When a company's promoters raise their
shareholding, do those stocks actually do better than the market over the next year?

## The test

| Step | Rule |
|---|---|
| Universe | 678 NSE stocks that have been in the NIFTY 500 (all currently listed) |
| Event | Every quarterly shareholding filing, compared with the previous quarter |
| "Promoters bought" | Promoter stake up **≥ 0.5 percentage points** quarter-on-quarter |
| "Promoters sold" | Promoter stake down ≥ 0.5 pp |
| Entry | Close of the first trading session **after** the filing's NSE submission date (no look-ahead) |
| Holding period | 252 sessions (≈ 12 months) |
| Benchmark | NIFTY 500 Total Return Index over the same window |
| Data window | Filings Apr 2016 – Jun 2025; every 12-month window ends by 30 Jun 2026 |

## Results

| Group | Filings | Beat NIFTY 500 TRI | Up 50%+ in 12 months | Median excess return |
|---|---:|---:|---:|---:|
| **Promoters bought** | 179 | **55.3%** | **29.6%** | +6.0% |
| Everyone (all filings) | 9,487 | 49.0% | 22.7% | −0.9% |
| Promoters sold | 566 | 48.4% | 23.9% | −1.5% |

**95% confidence intervals for "bought" minus "everyone"**, resampling whole quarters
(filings from the same quarter share one market, so they are not independent):

| Gap | Estimate | 95% CI |
|---|---:|---|
| Beat-the-index rate | +6.3 pp | −0.5 to +14.1 pp |
| Up-50%+ rate | +6.9 pp | +1.0 to +13.5 pp |

**Verdict: a small tilt, not a buy signal.**
- Promoter buying is rare: fewer than 2 in 100 filings.
- Those stocks beat the index 55% of the time against 49% for everyone, and the confidence interval for that gap still includes zero.
- They were somewhat more likely to become big winners. That is the only gap whose interval excludes zero, and I looked at several metrics, so treat it as a hint.
- Promoter *selling* was no red flag either: 48%, the same as everyone else.

Full output, including thresholds of >0 pp and >2 pp: [`results/stats.json`](results/stats.json).

### Why the signal is weak: one mechanism
A promoter's percentage can rise without the promoter buying a single share. If a company buys back
10% of its shares, all from the public, a promoter holding 50% ends up with 55.6%. Other events (warrants, preferential allotments,
mergers) also move the percentage. This data records the percentage, not *why* it changed.

Related evidence (US, not India): Cohen, Malloy & Pomorski (2012), *Decoding Inside Information*, Journal of Finance 67(3)
([NBER WP 16454](https://www.nber.org/papers/w16454)). They find that "routine" insider trades, over half of all insider trades,
earn abnormal returns that are "essentially zero"; all the predictive power sits in the "opportunistic" trades.
A raw promoter-percentage signal mixes both kinds, plus mechanical changes, which is one reason it would be noisy.

## Caveats (read these)
- **Short history.** NSE's shareholding history is thin before 2021: 173 of the 179 "bought" events are from 2022–2025,
  mostly a strong market for mid and small caps. This is not a full market cycle.
- **Survivorship.** The universe is stocks still listed today, so delisted losers are missing. That inflates
  absolute returns (look at the means). The *comparison* between groups is less affected, but not immune.
- **Small sample.** There are 179 events, and many cluster in the same few quarters.
- **No costs or taxes** are included. This is a statistical test, not a trading strategy.

## Reproduce

```bash
pip install -r requirements.txt
python analyze.py          # every number above, from data/events.csv (~30 s); asserts the video's figures
```

Rebuild from scratch:
```bash
python fetch_ownership.py  # NSE shareholding history -> data/promoter_holding.csv (~3 min)
python build_events.py     # + Yahoo Finance prices -> data/events_rebuilt.csv
```
`data/events.csv` was built from the author's cleaned price panel (Yahoo Finance, split/dividend-adjusted, holidays removed).
A fresh Yahoo download can differ slightly because Yahoo revises its history.
Checked on 3 Oct 2026: a from-scratch rebuild gave 9,459 events. Promoters bought: 178 events, 55.6% beat the index, 29.8% up 50%+.
Everyone: 48.9% beat the index. Promoters sold: 48.0%. Same conclusions.

## Files
| File | What it is |
|---|---|
| `data/promoter_holding.csv` | 13,708 quarterly filings: symbol, quarter end, **NSE submission date**, promoter %, public % |
| `data/events.csv` | 9,487 events: entry date, promoter change, 12-month stock return, excess vs NIFTY 500 TRI |
| `data/symbols.txt` | The 684 symbols queried (678 had usable price history) |
| `fetch_ownership.py` | NSE `corporate-share-holdings-master` fetcher (point-in-time submission dates) |
| `build_events.py` | Filings + prices → events |
| `analyze.py` | Events → results, confidence intervals, and checks against the video's numbers |

Shareholding data comes from public NSE filings. Price data is not redistributed here; `build_events.py` downloads it.

## License
Code: MIT. Data files are derived from public NSE disclosures and are provided for education only.
