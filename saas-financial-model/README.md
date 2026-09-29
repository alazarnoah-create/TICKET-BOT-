# SaaS Financial Model

A 36-month, fully formula-driven Excel model of a subscription (SaaS) business.
Open `SaaS_Financial_Model.xlsx`, change any **blue** input on the *Assumptions* tab,
and every statement updates.

To rebuild the workbook from code: `pip install openpyxl && python build_model.py`.

## Tabs

| Tab | What it does |
|---|---|
| **Guide** | How the model works, the color code, and the key modelling choices |
| **Assumptions** | All inputs: price, new customers, growth, churn, expansion and CAC per plan; operating costs; cash and fundraising |
| **Annual Summary** | Year 1–3 roll-up: ARR, revenue, margins, cash, CAC, LTV, LTV/CAC, payback, Rule of 40, plus charts |
| **Revenue Build** | Per plan (Basic / Pro / Enterprise): customer roll-forward and MRR bridge, then totals, ARR, ARPA, recognized revenue |
| **Income Statement** | Revenue → cost of revenue → gross profit → S&M / R&D / G&A → EBITDA → D&A → taxes → net income |
| **Cash Flow** | Net income + D&A − change in receivables − capex + equity raised → ending cash; burn and runway |

## How the logic flows

```
Assumptions ─► Revenue Build ─► Income Statement ─► Cash Flow ─► Annual Summary
               customers          revenue & costs    cash, burn     KPIs
               MRR bridge                            runway
```

* **Customers:** beginning + new − churned = ending (churn = % of beginning customers).
* **MRR bridge:** beginning MRR + new + expansion − churned = ending MRR. ARR = MRR × 12.
* **Revenue** in a month = average of beginning and ending MRR.
* **S&M** = new customers × CAC (per plan) + fixed marketing.
* **Cash** = net income + D&A − increase in receivables − capex + equity raised.

## Base-case results (illustrative inputs)

| | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Ending ARR | $1.38M | $3.37M | $6.75M |
| Revenue | $0.73M | $2.29M | $4.91M |
| Gross margin | 78.5% | 79.0% | 79.2% |
| EBITDA margin | (223%) | (54%) | (10%) |
| Ending cash | $0.22M | $1.78M | $0.93M |
| LTV / CAC | 3.1x | 3.8x | 4.2x |
| CAC payback (months) | 11.9 | 10.0 | 9.0 |

Takeaway: the business nearly runs out of cash in Month 12, so the $3M raise in
Month 13 is essential. By Year 3 it is close to breakeven with healthy unit
economics, but at about $0.9M of cash it will need to cut burn or raise again.

## Simplifications (and next steps)

No deferred revenue (everyone billed monthly), no NOL carry-forward, no balance
sheet, opex grows at a flat rate rather than by headcount. Natural extensions:
annual prepaid plans, a headcount plan, cohort retention curves, a balance sheet,
and base/bull/bear scenarios.
