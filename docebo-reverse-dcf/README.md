# What is Docebo's stock price secretly betting on?

A reverse DCF of **Docebo Inc. (TSX: DCBO)** built at the customer level. The model runs
ARR → revenue → free cash flow → DCF → price per share, then works backwards: it solves
for the **annual ARR churn** that makes the model's price equal today's share price.

| File | What it is |
|---|---|
| `Docebo_Reverse_DCF.xlsx` | The model: every cell is a live formula, blue cells are inputs |
| `build_model.py` | Regenerates the workbook (`pip install openpyxl && python build_model.py`) |
| `study-notes.html` | Plain-English notes, glossary, sensitivity grid, one-page write-up, interview answers |

## Result (data as of 17 Sep 2026)

| | |
|---|---|
| Market price | C$33.22 |
| Model value at reported churn (10% discount rate) | C$69.83 |
| **Market-implied churn** | **24.5% of ARR per year** (≈ 83% net revenue retention) |
| Reported-equivalent churn | 9.0% (99% net revenue retention + 8% assumed expansion) |

The market is pricing in far worse retention than Docebo reports. Either it expects AI
disruption or customer losses (such as AWS) to hurt retention badly, or the stock is undervalued.

## Tabs

1. **Start Here**: how it works, plus Goal Seek and Data Table instructions
2. **Inputs**: 8 quarters of reported ARR, revenue, EBITDA and FCF; price, shares, cash and debt, each with a source
3. **Reverse DCF**: the answer. Implied churn is solved by a live formula (a 0–50% churn ladder interpolated at the market price), so it updates when inputs change
4. **Assumptions**: forecast levers (churn, expansion, new-ARR growth, margin ramp, discount rate, terminal growth)
5. **ARR Model**: 10-year ARR bridge, then revenue, EBITDA and FCF
6. **DCF**: discount factors, terminal value, EV, then equity value, then C$ per share
7. **Sensitivity**: price grid of churn × discount rate, built with plain formulas (also works in Google Sheets)
8. **Tracker**: log each re-run, e.g. after Q3-2026 results in early Nov 2026

## Caveats

- Figures were gathered from Docebo releases through news and search summaries. Several quarters were derived
  (for example, revenue = FCF ÷ FCF margin). Verify each blue input against the filings on sedarplus.ca.
- Docebo does not disclose gross churn. "Reported churn" = assumed expansion + (1 − reported NRR).
- Adjusted EBITDA excludes stock-based compensation, which makes the valuation somewhat generous.
- Illustrative student analysis, not investment advice.
