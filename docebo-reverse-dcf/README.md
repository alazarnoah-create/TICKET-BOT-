# What is Docebo's stock price secretly betting on?

Noah Alazar Research. A reverse DCF of **Docebo Inc. (TSX: DCBO)** built on **reported numbers only**.
The model runs ARR → revenue → free cash flow → DCF → price per share, then works backwards to
solve for the **net revenue retention (NRR)** that makes the model's price equal today's share price.

| File | What it is |
|---|---|
| `Docebo_Reverse_DCF.xlsx` | The model. Every blue input is sourced (hover a cell, or see the Sources tab) |
| `build_model.py` | Regenerates the workbook (`pip install openpyxl && python build_model.py`) |
| `research-report.html` / `Docebo_Research_Report_Noah_Alazar.pdf` | The research note |
| `study-notes.html` | Plain-English notes, glossary, grid, red flags, pitch |

## Result (prices as of 17 Sep 2026)

| | |
|---|---|
| Market price | C$33.22 |
| Model value at reported numbers (10% discount rate) | C$53.56 (C$34.00 if valued on analysts' 2029 profit margin) |
| **Market-implied NRR** | **90.2%** (existing customers spend ~9.8% less each year) |
| Reported NRR (FY2025) | 99% (101% excluding AWS) |

## Input rules

Every input is one of:
- **REPORTED:** from Docebo filings or market data.
- **CALCULATED:** a formula on reported numbers.
- **COMPANY TARGET:** management's 24% adjusted EBITDA margin by 2028.
- **CONVENTION:** 10% discount rate and 2.5% terminal growth.

There are no analyst guesses. Quarterly figures come from each quarter's press release (SEC 6-K). The links are on the Sources tab.

## Red flags

The Red Flags tab and report Section 5 cover:
- a US$70M buyback that almost nobody sold into,
- debt-funded acquisitions (365Talents, US$61.3M),
- a 63.7% controlling shareholder,
- insider sales at much higher prices in 2021,
- adjusted EBITDA that excludes recurring severance.

## Limits

- Figures were collected through search results that quote Docebo's releases, because the filing sites were blocked from the build environment. Tick them against the links.
- New-customer ARR over the last 12 months includes acquired 365Talents ARR, which Docebo does not break out.
- Illustrative student analysis, not investment advice.
