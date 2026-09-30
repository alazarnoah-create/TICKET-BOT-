# Simply Wall St fact-check: Docebo (TSX: DCBO)

**Pages:** https://simplywall.st/stocks/ca/software/tsx-dcbo/docebo-shares/health, plus its /past, /valuation and /news pages.

The site was blocked from the build environment, so these figures come from search results that quote its pages. **Simply Wall St updates automatically, and search results can show older snapshots.** Numbers from different dates got mixed together, so each one is checked against Docebo's own filings.

**Key:**
- ✅ **Matches:** agrees with a Docebo filing.
- ⚠️ **Can't date / unverified:** the snapshot date is unknown.
- ❌ **Out of date:** contradicts the latest filing.

## Financial health (the /health page)
| Simply Wall St says | Status | What Docebo's filings say |
|---|---|---|
| "Debt free", total debt $0, debt-to-equity 0% | ❌ **Out of date** | Borrowings of **US$88.0M** at 30 Jun 2026 (release, 17 Jul 2026). The debt began with a ~US$50M draw on 14 Jan 2026 (Q1-2026 MD&A). |
| Cash and short-term investments US$74.0M | ⚠️ Older snapshot | Probably end-2025; the video also says "net cash of $74M in 2025". Cash was **US$45.7M** at 30 Jun 2026 (release, 17 Jul 2026). |
| Shareholder equity US$74.1M; total assets US$206.6M; total liabilities US$132.6M | ⚠️ Older snapshot | Before the 2026 acquisition and borrowing. |
| Short-term assets US$151.5M exceed short-term liabilities US$123.8M | ⚠️ Older snapshot | Needs the 30 Jun 2026 balance sheet to update. |
| EBIT US$29.7M; interest coverage "−17.3" | ⚠️ Older snapshot | A negative number here means interest *income* exceeded interest expense, which is typical when a company is debt-free. That won't hold with US$88M of debt. |
| "6/6 financial health checks passing" | ❌ **Out of date** | The checks were run on a debt-free balance sheet. |
| Earlier snapshot: negative equity of −US$616k | ⚠️ Older snapshot | Shows how thin equity has been, after years of buybacks. |

## Earnings (the /past page and news)
| Simply Wall St says | Status | What we have |
|---|---|---|
| Q2-2026 revenue US$68.65M vs US$60.73M in Q2-2025 (~13% growth) | ✅ **Matches** | Our Excel uses the rounded 68.7 and 60.7 (Q2-2026 and Q2-2025 releases). |
| Q2-2026 basic earnings per share US$0.09, back to profit after a loss in Q1-2026 | ⚠️ Unverified | This fits the US$6.2M of severance in Q1-2026 (Q1-2026 financial statements). |
| Closing price C$31.09 on the Q2 results day | ⚠️ Market data, 7 Aug 2026 | Our model uses C$33.22 (17 Sep 2026). |
| P/E 16.5× | ⚠️ Depends on the date | P/E = price ÷ yearly profit per share, so it changes with the price. |
| Trailing net margin 13.0% (from 9.3%) | ⚠️ Conflicts with another snapshot | Another snapshot says 15.5% (from 12.3%). The dates differ, so we can't use either as fact. |
| Trailing net income US$37.5M; return on equity 50.6% | ⚠️ Older snapshot | Return on equity is high partly because equity is very small (see above), not only because profit is high. |
| Earnings grew 67.3% a year over 5 years; revenue grew 23.2% a year | ⚠️ Unverified | Needs 5 years of filings to check. |

## Valuation (the /valuation page and news)
| Simply Wall St says | Status | Comparison |
|---|---|---|
| DCF "fair value" estimates of CA$35.97, CA$62.50 and CA$65.10 (different dates) | ⚠️ Different dates and inputs | Our model gives **C$53.53** (Excel DCF!C18), inside that range. Every one of them is above the C$33.22 price. |
| Analysts forecast revenue growth of 18% a year for the next 3 years | ⚠️ An analyst forecast, not reported | Docebo's own FY2026 revenue guidance of US$274.5–276.5M implies about 13.6% growth on FY2025's US$242.6M. |

## Lessons
1. **Third-party sites go stale.** Simply Wall St still shows Docebo as "debt free", but the June 2026 filing shows US$88.0M of borrowings. Always check the date, and trust the company's latest filing over a website.
2. **Different websites build their DCF differently**, so their "fair value" jumps around (CA$36 to CA$65). What matters is being able to explain *your* inputs, which is why the reverse DCF is useful.
3. **A high return on equity can be an illusion.** It's profit ÷ equity, and Docebo's equity is tiny, so the ratio looks huge.
