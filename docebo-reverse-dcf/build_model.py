"""Builds Docebo_Reverse_DCF.xlsx - "What is Docebo's stock price secretly betting on?"

A 10-year ARR -> revenue -> free cash flow -> DCF model of Docebo Inc. (TSX: DCBO),
run backwards: it solves for the net revenue retention (NRR) that makes the model's value per share
equal today's share price. Everything is a live formula; blue cells are inputs.
Run:  python build_model.py
"""
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

FONT = "Arial"
F = lambda color="000000", bold=False, size=10, italic=False: Font(
    name=FONT, size=size, bold=bold, italic=italic, color=color)
F_IN, F_CALC, F_LINK = F("0000FF"), F(), F("008000")
F_HDR = F("FFFFFF", True)
FILL_HDR = PatternFill("solid", fgColor="1F3864")
FILL_SEC = PatternFill("solid", fgColor="D9E1F2")
FILL_KEY = PatternFill("solid", fgColor="FFFF00")
FILL_ANS = PatternFill("solid", fgColor="E2EFDA")
TOP = Border(top=Side(style="thin"))
BOX = Border(*(Side(style="medium"),) * 4)

USDM = '#,##0.0;(#,##0.0);"-"'          # US$ millions, one decimal
USD2 = '$#,##0.00;($#,##0.00);"-"'
PCT = '0.0%;(0.0%);"-"'
MULT = '0.0x'
NUM2 = '0.00'

YEARS = 10
YC = [chr(ord("C") + i) for i in range(YEARS)]   # Year 1..10 -> C..L
Y1, Y10 = YC[0], YC[-1]

wb = Workbook()


def put(ws, ref, value, font=F_CALC, fmt=None, fill=None, bold=False, align=None, border=None):
    c = ws[ref]
    c.value = value
    c.font = Font(name=FONT, size=font.size, bold=bold or font.bold, color=font.color,
                  italic=font.italic)
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if align:
        c.alignment = Alignment(horizontal=align, wrap_text=False)
    if border:
        c.border = border
    return c


def header(ws, r, labels, start="A"):
    for i, t in enumerate(labels):
        c = ws.cell(r, ord(start) - 64 + i, t)
        c.font, c.fill = F_HDR, FILL_HDR
        c.alignment = Alignment(horizontal="left" if i == 0 else "center", wrap_text=True)


def section(ws, r, text, width):
    ws.cell(r, 1, text).font = F(bold=True)
    for i in range(1, width + 1):
        ws.cell(r, i).fill = FILL_SEC


def note(ws, ref, text):
    c = ws[ref]
    c.value = text
    c.font = F("595959", italic=True, size=9)


def widths(ws, spec):
    for k, v in spec.items():
        ws.column_dimensions[k].width = v


# Every hard-coded number below is either REPORTED by Docebo / the market (with its source),
# CALCULATED from reported numbers by a formula, a COMPANY TARGET, or a stated MARKET CONVENTION.
SRC = {
    "Q2-26": "Docebo Q2-2026 press release, 7 Aug 2026 (sec.gov 6-K docebo2026q2pr)",
    "Q1-26": "Docebo Q1-2026 press release, 8 May 2026 (sec.gov 6-K docebo2026q1pr)",
    "Q4-25": "Docebo Q4/FY2025 press release, 27 Feb 2026 (sec.gov 6-K docebo2025q4pr)",
    "Q3-25": "Docebo Q3-2025 press release, 7 Nov 2025 (sec.gov 6-K docebo2025q3pr)",
    "Q2-25": "Docebo Q2-2025 press release, 8 Aug 2025 (sec.gov 6-K docebo2025q2pr)",
    "Q1-25": "Docebo Q1-2025 press release, 9 May 2025 (sec.gov 6-K docebo2025q1pr)",
    "Q4-24": "Docebo Q4/FY2024 press release, 28 Feb 2025 (sec.gov 6-K docebo2024q4pr)",
    "Q3-24": "Docebo Q3-2024 press release, 8 Nov 2024 (sec.gov 6-K docebo2024q3pr)",
}

# =============================================================== START HERE
g = wb.active
g.title = "Start Here"
widths(g, {"A": 3, "B": 125})
lines = [
    ("What is Docebo's stock price secretly betting on?", F(bold=True, size=14)),
    ("Noah Alazar Research  |  Reverse DCF of Docebo Inc. (TSX: DCBO)  |  Built on reported numbers only", F(italic=True)),
    ("", None),
    ("THE IDEA", F(bold=True)),
    ("Normal model: assumptions -> value.  Reverse model: today's price -> the assumption the market must believe.", None),
    ("The lever we solve for is NET REVENUE RETENTION (NRR): of every $100 existing customers paid last year, how much they pay this year.", None),
    ("Docebo reports NRR of 99% (FY2025). We find the NRR that today's share price implies and compare the two.", None),
    ("", None),
    ("RULE FOR EVERY NUMBER", F(bold=True)),
    ("Each input is labelled: REPORTED (from Docebo filings or market data), CALCULATED (formula on reported numbers), COMPANY TARGET, or CONVENTION.", None),
    ("There are no analyst guesses. The 'Sources' tab lists every hard-coded number with the document it came from.", None),
    ("", None),
    ("HOW THE TABS FLOW", F(bold=True)),
    ("1. Inputs       - 8 quarters of reported ARR, revenue, adjusted EBITDA and free cash flow + price, shares, cash, debt.", None),
    ("2. Reverse DCF  - THE ANSWER: market-implied NRR vs. reported NRR (solved live, no macro).", None),
    ("3. Assumptions  - the forecast levers, each tagged with its type and source.", None),
    ("4. ARR Model    - 10 years: Starting ARR x NRR + new-customer ARR = Ending ARR -> revenue -> EBITDA -> free cash flow.", None),
    ("5. DCF          - discount each year's cash, add terminal value, add cash, subtract debt, divide by shares.", None),
    ("6. Sensitivity  - share price for every NRR (down) x discount rate (across).", None),
    ("7. Red Flags    - what looks sketchy about the company itself, each with a source.", None),
    ("8. Sources      - every hard-coded number and where it came from.", None),
    ("9. Tracker      - log each re-run (next: Q3-2026 results, early Nov 2026).", None),
    ("", None),
    ("COLOR CODE", F(bold=True)),
    ("Blue = hard-coded input (sourced)  |  Black = formula  |  Green = link from another tab  |  Yellow = key lever  |  Light green = answer", None),
    ("", None),
    ("EXCEL SKILLS TO PRACTISE", F(bold=True)),
    ("GOAL SEEK: Data -> What-If Analysis -> Goal Seek. Set cell DCF!C22, To value 33.22, By changing Assumptions!C5. Result should match Reverse DCF!H5.", None),
    ("   Afterwards type 99% back into Assumptions!C5.", None),
    ("DATA TABLE: put =DCF!C22 top-left, NRR values down the column, discount rates across the row, select the block, Data -> What-If -> Data Table.", None),
    ("   Row input cell: Assumptions!C10. Column input cell: Assumptions!C5. Compare with the Sensitivity tab.", None),
    ("", None),
    ("LIMITS YOU MUST STATE", F(bold=True)),
    ("- Figures were collected from Docebo releases via search results (the filing sites were blocked from the build environment). Links are on the Sources tab: open and tick them.", None),
    ("- Any 10-year forecast needs assumptions. Here they are only: today's reported levels held flat, management's own 24%-by-2028 margin target, a 10% discount rate and 2.5% terminal growth.", None),
    ("- New-customer ARR over the last 12 months includes ARR from the 365Talents acquisition (Jan 2026), which Docebo does not break out. Organic new ARR is therefore somewhat lower.", None),
    ("- Adjusted EBITDA excludes stock-based pay, restructuring (severance) and acquisition costs. Free cash flow conversion uses FY2025 actual cash, which does include cash severance.", None),
]
for i, (t, f) in enumerate(lines, start=1):
    c = g.cell(i, 2, t)
    c.font = f or F_CALC
    c.alignment = Alignment(wrap_text=True, vertical="top")

# =============================================================== INPUTS
inp = wb.create_sheet("Inputs")
widths(inp, {"A": 50, **{c: 11 for c in "BCDEFGHI"}, "J": 16, "K": 78})
put(inp, "A1", "Inputs - Docebo Inc. (TSX: DCBO) reported figures", F(bold=True, size=14))
note(inp, "A2", "US$ millions unless stated. Blue = typed from a source (hover a cell for the exact document). Black = formula.")
header(inp, 4, ["Market & balance sheet", "Value", "Unit", "", "", "", "", "", "", "Type", "Source"])
market = [
    (5, "Share price (TSX: DCBO)", 33.22, USD2, "C$", "REPORTED", "TSX close 17-Sep-2026 (Investing.com / TMX Money). Update on each run."),
    (6, "USD/CAD exchange rate (same day)", 1.3991, '0.0000', "C$ per US$", "REPORTED", "Mid-market rate 17-Sep-2026 (MTFX). Verify on Bank of Canada daily rates."),
    (7, "Shares held by Intercap", 15.9, NUM2, "millions", "REPORTED", "SIB final results, 11-Sep-2026: Intercap owns 15,900,000 shares"),
    (8, "Intercap ownership", 0.637, PCT, "%", "REPORTED", "SIB final results, 11-Sep-2026: approx. 63.7% of shares outstanding"),
    (9, "Shares outstanding (after buyback)", "=B7/B8", NUM2, "millions", "CALCULATED", "15.9M / 63.7%"),
    (10, "Market capitalization", "=B5*B9", USDM, "C$ m", "CALCULATED", "Price x shares"),
    (11, "Cash & equivalents, 30-Jun-2026", 45.7, USDM, "US$ m", "REPORTED", "Docebo release 17-Jul-2026 (SIB + preliminary Q2-2026 results)"),
    (12, "Cash paid in the buyback (Sep-2026)", 2.4833, USDM, "US$ m", "REPORTED", "SIB final results, 11-Sep-2026: 99,332 shares x US$25.00 = US$2,483,300"),
    (13, "Cash after buyback", "=B11-B12", USDM, "US$ m", "CALCULATED", "Matches the post-buyback share count"),
    (14, "Total borrowings, 30-Jun-2026", 88.0, USDM, "US$ m", "REPORTED", "Docebo release 17-Jul-2026"),
    (15, "Net debt", "=B14-B13", USDM, "US$ m", "CALCULATED", "Debt - cash"),
    (16, "Gross margin (Q2-2026)", 0.794, PCT, "%", "REPORTED", SRC["Q2-26"] + ": 79.4%"),
    (17, "Net revenue retention, FY2025", 0.99, PCT, "%", "REPORTED", "Q4-2025 earnings call: net dollar retention 99% (Globe and Mail coverage)"),
    (18, "Net revenue retention ex-AWS, FY2025", 1.01, PCT, "%", "REPORTED", "Q4-2025 earnings call: 101% excluding AWS"),
    (19, "Management target: adj. EBITDA margin by 2028", 0.24, PCT, "%", "COMPANY TARGET", "Docebo long-term model: >$80M adj. EBITDA by 2028 = 24% margin (Investing.com)"),
    (20, "Canada 10-year bond yield", 0.0399, PCT, "%", "REPORTED", "29-Sep-2026 (Trading Economics). Used only for the CAPM cross-check."),
]
for r, lab, v, fmt, unit, typ, src in market:
    put(inp, f"A{r}", lab)
    isf = isinstance(v, str)
    put(inp, f"B{r}", v, F_CALC if isf else F_IN, fmt, FILL_KEY if r in (5, 17) else None)
    put(inp, f"C{r}", unit, F("595959", size=9))
    put(inp, f"J{r}", typ, F("595959", bold=True, size=9))
    note(inp, f"K{r}", src)
    if not isf:
        inp[f"B{r}"].comment = Comment(src, "Source")

header(inp, 22, ["Quarterly history (US$ m)", "Q3-24", "Q4-24", "Q1-25", "Q2-25", "Q3-25",
                 "Q4-25", "Q1-26", "Q2-26", "Type", "Source"])
QS = ["Q3-24", "Q4-24", "Q1-25", "Q2-25", "Q3-25", "Q4-25", "Q1-26", "Q2-26"]
Q = "BCDEFGHI"
hist = {
    23: ("ARR (annual recurring revenue)", [214.1, 219.7, 225.1, 233.1, 235.6, 238.1, 248.9, 255.1]),
    24: ("Total revenue", [55.4, 57.0, 57.3, 60.7, 61.6, 63.0, 65.6, 68.7]),
    25: ("Adjusted EBITDA", [8.7, 9.5, 8.9, 9.2, 12.4, 13.3, 11.0, 11.2]),
    26: ("Free cash flow (company definition)", [4.5, 10.1, 9.0, 11.4, 5.7, 12.3, 27.6, 3.1]),
}
# Where each figure is printed: own quarter's release, or the prior-year comparison in the next year's release
prior_year = {("Q3-24", 25): "Q3-25", ("Q3-24", 26): "Q3-25", ("Q4-24", 25): "Q4-25", ("Q4-24", 26): "Q4-25"}
for r, (lab, vals) in hist.items():
    put(inp, f"A{r}", lab)
    for col, q, v in zip(Q, QS, vals):
        put(inp, f"{col}{r}", v, F_IN, USDM)
        where = prior_year.get((q, r))
        txt = SRC[where] + " (prior-year comparison)" if where else SRC[q]
        inp[f"{col}{r}"].comment = Comment(f"{lab}, {q}: {v}\nSource: {txt}", "Source")
    put(inp, f"J{r}", "REPORTED", F("595959", bold=True, size=9))
    note(inp, f"K{r}", "Each quarter's own press release (hover any cell for the exact document)")
put(inp, "A27", "FCF margin (%)")
put(inp, "A28", "Adj. EBITDA margin (%)")
put(inp, "A29", "ARR growth vs. same quarter last year (%)")
for col in Q:
    put(inp, f"{col}27", f"={col}26/{col}24", fmt=PCT)
    put(inp, f"{col}28", f"={col}25/{col}24", fmt=PCT)
for i, col in enumerate(Q[4:]):
    put(inp, f"{col}29", f"={col}23/{Q[i]}23-1", fmt=PCT)
for r in (27, 28, 29):
    put(inp, f"J{r}", "CALCULATED", F("595959", bold=True, size=9))

header(inp, 31, ["Derived from the reported figures", "Value", "Unit", "", "", "", "", "", "", "Type", "How"])
derived = [
    (32, "LTM revenue (Q3-25 to Q2-26)", "=SUM(F24:I24)", USDM, "Sum of last 4 quarters"),
    (33, "LTM adjusted EBITDA", "=SUM(F25:I25)", USDM, ""),
    (34, "LTM free cash flow", "=SUM(F26:I26)", USDM, ""),
    (35, "LTM adj. EBITDA margin", "=B33/B32", PCT, "Starting margin in the forecast"),
    (36, "LTM FCF margin", "=B34/B32", PCT, "Flattered by customer prepayments in Q1-26 (42% FCF margin)"),
    (37, "FY2025 adjusted EBITDA (Q1-25 to Q4-25)", "=SUM(D25:G25)", USDM, ""),
    (38, "FY2025 free cash flow", "=SUM(D26:G26)", USDM, "Matches the US$38.4M Docebo reported for FY2025"),
    (39, "FY2025 FCF conversion (FCF / adj. EBITDA)", "=B38/B37", PCT, "A full calendar year, so prepayment timing evens out"),
    (40, "ARR now (30-Jun-2026)", "=I23", USDM, "Forecast starting point"),
    (41, "ARR one year ago (30-Jun-2025)", "=E23", USDM, ""),
    (42, "Net new ARR, last 12 months", "=B40-B41", USDM, "Ending - starting"),
    (43, "New-customer ARR, last 12 months", "=B42+(1-B17)*B41", USDM,
     "Net new ARR + ARR lost at reported NRR. Includes acquired 365Talents ARR (not broken out by Docebo)"),
    (44, "Revenue per $1 of average ARR", "=B32/AVERAGE(B40,B41)", '0.000', "Revenue includes some services on top of ARR"),
    (45, "Enterprise value the market pays (US$ m)", "=B10/B6+B15", USDM, "Market cap in US$ + net debt"),
    (46, "EV / ARR", "=B45/B40", MULT, ""),
    (47, "EV / LTM free cash flow", "=B45/B34", MULT, ""),
]
for r, lab, f, fmt, how in derived:
    put(inp, f"A{r}", lab)
    put(inp, f"B{r}", f, fmt=fmt)
    put(inp, f"J{r}", "CALCULATED", F("595959", bold=True, size=9))
    note(inp, f"K{r}", how)
inp.freeze_panes = "B5"

# =============================================================== ASSUMPTIONS
a = wb.create_sheet("Assumptions")
widths(a, {"A": 3, "B": 52, "C": 12, "D": 18, "E": 92})
put(a, "B1", "Assumptions - forecast levers", F(bold=True, size=14))
note(a, "B2", "No analyst guesses: each lever is reported, calculated from reported numbers, a company target, or a stated convention.")
header(a, 4, ["", "Lever", "Value", "Type", "Source / reason"])
levers = [
    (5, "Net revenue retention used in the DCF", 0.99, True, "REPORTED",
     "Docebo FY2025 NRR = 99%. This is the cell Goal Seek changes (the reverse-DCF lever)."),
    (6, "New-customer ARR added per year (US$ m)", "=Inputs!B43", False, "CALCULATED",
     "Last-12-months level from reported ARR and NRR, held flat (no growth assumed)."),
    (7, "Adj. EBITDA margin, long-term", "=Inputs!B19", True, "COMPANY TARGET",
     "Management's own model: >$80M adj. EBITDA by 2028 = 24%. Held flat after that."),
    (8, "Years to reach the target margin", 2, False, "COMPANY TARGET",
     "Target year 2028 is about 2 years after the Jun-2026 starting point. Straight-line from LTM margin."),
    (9, "FCF conversion (FCF / adj. EBITDA)", "=Inputs!B39", False, "CALCULATED",
     "FY2025 actual (a full year, so Q1 prepayment timing evens out). Held flat."),
    (10, "Discount rate (required return per year)", 0.10, True, "CONVENTION",
     "Standard starting rate for the project. CAPM cross-check below. Sensitivity tab covers 8-12%."),
    (11, "Terminal growth rate (after Year 10)", 0.025, False, "CONVENTION",
     "About the Bank of Canada 2% inflation target plus modest real growth. Must stay below the discount rate."),
    (12, "Gross margin (display only)", "=Inputs!B16", False, "REPORTED", "Q2-2026"),
]
for r, lab, v, key, typ, why in levers:
    put(a, f"B{r}", lab)
    isf = isinstance(v, str)
    fmt = '0' if r == 8 else (USDM if r == 6 else PCT)
    put(a, f"C{r}", v, F_LINK if isf else F_IN, fmt, FILL_KEY if key else None)
    put(a, f"D{r}", typ, F("595959", bold=True, size=9))
    note(a, f"E{r}", why)
put(a, "B14", "Net ARR lost from existing customers per year = 1 - NRR", bold=True)
put(a, "C14", "=1-C5", fmt=PCT, fill=FILL_ANS, bold=True)
put(a, "B16", "CAPM cross-check (not used in the model)", bold=True)
put(a, "B17", "Risk-free rate (Canada 10-year)")
put(a, "C17", "=Inputs!B20", F_LINK, PCT)
put(a, "B18", "Beta (sources disagree: 0.73 Yahoo 5y monthly, ~1.0 Google)")
put(a, "C18", 1.0, F_IN, '0.00')
put(a, "D18", "REPORTED RANGE", F("595959", bold=True, size=9))
put(a, "B19", "Equity risk premium")
put(a, "C19", 0.05, F_IN, PCT)
put(a, "D19", "CONVENTION", F("595959", bold=True, size=9))
put(a, "B20", "CAPM cost of equity = risk-free + beta x premium", bold=True)
put(a, "C20", "=C17+C18*C19", fmt=PCT, bold=True)
note(a, "E20", "About 9% - so the 10% used in the model is slightly conservative (a higher rate gives a lower value).")

# =============================================================== ARR MODEL
m = wb.create_sheet("ARR Model")
widths(m, {"A": 50, "B": 13, **{c: 11 for c in YC}})
put(m, "A1", "ARR Model - 10-year forecast (US$ m)", F(bold=True, size=14))
for c in ["A", "B"] + YC:
    m[f"{c}2"].fill = FILL_HDR
    m[f"{c}3"].fill = FILL_HDR
put(m, "A2", "Year", F_HDR)
put(m, "B2", 0, F_HDR, align="center")
put(m, "A3", "Period", F_HDR)
put(m, "B3", "LTM Jun-26", F_HDR, align="center")
for i, c in enumerate(YC):
    prev = "B" if i == 0 else YC[i - 1]
    put(m, f"{c}2", f"={prev}2+1", F_HDR, align="center")
    put(m, f"{c}3", f'="Yr "&{c}2', F_HDR, align="center")
m.freeze_panes = "C4"
A = "Assumptions"


def mrow(r, lab, formula, fmt=USDM, font=F_CALC, bold=False, opening=None, border=None):
    put(m, f"A{r}", lab, bold=bold)
    for i, c in enumerate(YC):
        p = "B" if i == 0 else YC[i - 1]
        put(m, f"{c}{r}", formula.format(c=c, p=p), font, fmt, bold=bold, border=border)
    if opening is not None:
        put(m, f"B{r}", opening, F_LINK, fmt, bold=bold, border=border)
    if border:
        m[f"A{r}"].border = border


section(m, 5, "Drivers", 12)
mrow(6, "Progress to target margin (0% = today, 100% = target)", f"=MIN({{c}}$2/{A}!$C$8,1)", PCT)
mrow(7, "Adj. EBITDA margin", f"=Inputs!$B$35+({A}!$C$7-Inputs!$B$35)*{{c}}6", PCT, F_LINK, opening="=Inputs!B35")
mrow(8, "FCF conversion (FCF / adj. EBITDA)", f"={A}!$C$9", PCT, F_LINK, opening="=Inputs!B39")
mrow(9, "FCF margin (EBITDA margin x conversion)", "={c}7*{c}8", PCT)

section(m, 11, "ARR bridge  (Starting ARR x NRR + new-customer ARR = Ending ARR)", 12)
mrow(12, "Starting ARR", "={p}15")
mrow(13, "(+) New-customer ARR", f"={A}!$C$6", font=F_LINK)
mrow(14, "(+/-) Existing customers: Starting ARR x (NRR - 1)", f"={{c}}12*({A}!$C$5-1)", font=F_LINK)
mrow(15, "Ending ARR", "=SUM({c}12:{c}14)", bold=True, border=TOP, opening="=Inputs!B40")
mrow(16, "ARR growth (%)", "={c}15/{p}15-1", PCT)

section(m, 18, "Revenue to free cash flow", 12)
mrow(19, "Revenue (average ARR x revenue per $ of ARR)", "=AVERAGE({p}15,{c}15)*Inputs!$B$44", bold=True,
     opening="=Inputs!B32")
mrow(20, "Revenue growth (%)", "={c}19/{p}19-1", PCT)
mrow(21, "Gross profit", f"={{c}}19*{A}!$C$12")
mrow(22, "(-) Operating expenses (S&M, R&D, G&A)", "={c}23-{c}21")
mrow(23, "Adjusted EBITDA", "={c}19*{c}7", bold=True, border=TOP, opening="=Inputs!B33")
mrow(24, "(-) Cash taxes, capex, working capital & other", "=-{c}23*(1-{c}8)")
mrow(25, "Free cash flow", "={c}23+{c}24", bold=True, border=TOP, opening="=Inputs!B34")
m["B19"].comment = Comment("Column B = last-twelve-months actuals (Q3-25 to Q2-26).", "Model")

# =============================================================== DCF
d = wb.create_sheet("DCF")
widths(d, {"A": 46, "B": 13, **{c: 11 for c in YC}})
put(d, "A1", "DCF - what the future cash is worth today", F(bold=True, size=14))
for c in ["A", "B"] + YC:
    d[f"{c}3"].fill = FILL_HDR
put(d, "A3", "Year", F_HDR)
for c in YC:
    put(d, f"{c}3", f"='ARR Model'!{c}2", F_HDR, align="center")
put(d, "A4", "Free cash flow (US$ m)")
put(d, "A5", "Discount factor = 1 / (1 + discount rate)^year")
put(d, "A6", "Present value of FCF")
for c in YC:
    put(d, f"{c}4", f"='ARR Model'!{c}25", F_LINK, USDM)
    put(d, f"{c}5", f"=1/(1+{A}!$C$10)^{c}3", fmt='0.000')
    put(d, f"{c}6", f"={c}4*{c}5", fmt=USDM)
dcf = [
    (8, "Sum of PV of FCF, Years 1-10", f"=SUM({Y1}6:{Y10}6)", USDM, ""),
    (9, "Terminal value at Year 10", f"={Y10}4*(1+{A}!C11)/({A}!C10-{A}!C11)", USDM, "FCF Year 11 / (discount rate - growth)"),
    (10, "PV of terminal value", f"=C9*{Y10}5", USDM, ""),
    (11, "Enterprise value (US$ m)", "=C8+C10", USDM, ""),
    (12, "(+) Cash (after buyback)", "=Inputs!B13", USDM, ""),
    (13, "(-) Debt", "=-Inputs!B14", USDM, ""),
    (14, "Equity value (US$ m)", "=SUM(C11:C13)", USDM, ""),
    (15, "Shares outstanding (m)", "=Inputs!B9", NUM2, ""),
    (16, "Value per share (US$)", "=C14/C15", USD2, ""),
    (17, "USD/CAD", "=Inputs!B6", '0.0000', ""),
    (18, "Model value per share (C$)", "=C16*C17", USD2, "At reported NRR unless you change Assumptions!C5"),
    (19, "Market price today (C$)", "=Inputs!B5", USD2, ""),
    (20, "Upside / (downside) vs. market", "=C18/C19-1", PCT, ""),
    (21, "Terminal value as % of enterprise value", "=C10/C11", PCT, ""),
    (22, "GOAL SEEK TARGET -> model price (C$)", "=C18", USD2, "Set C22 to the market price by changing Assumptions!C5"),
]
for r, lab, f, fmt, why in dcf:
    bold = r in (11, 14, 18, 22)
    put(d, f"A{r}", lab, bold=bold)
    font = F_LINK if f.startswith("=Inputs") else F_CALC
    put(d, f"C{r}", f, font, fmt, bold=bold, fill=FILL_ANS if r in (18, 22) else None,
        border=TOP if r in (11, 14) else None)
    note(d, f"D{r}", why)

# =============================================================== REVERSE DCF
rv = wb.create_sheet("Reverse DCF")
widths(rv, {"A": 12, **{c: 9 for c in "BCDEFGHIJKL"}, "M": 11, "N": 11})
put(rv, "A1", "Reverse DCF - the retention rate today's price is betting on", F(bold=True, size=14))
note(rv, "A2", "Solved live: the price is computed for NRR from 120% down to 50% below, then interpolated at the market price.")
LAD0, STEP, NSTEP = 30, 0.005, 141
LAD1 = LAD0 + NSTEP - 1
res = [
    (4, "Market price today (C$)", "=Inputs!B5", USD2),
    (5, "MARKET-IMPLIED NET REVENUE RETENTION", None, PCT),
    (6, "Reported net revenue retention (FY2025)", "=Inputs!B17", PCT),
    (7, "Gap: reported minus implied (percentage points)", '=IFERROR(H6-H5,"n/a")', '+0.0%;-0.0%;0.0%'),
    (8, "Implied net ARR lost from existing customers per year", '=IFERROR(1-H5,"n/a")', PCT),
    (9, "Reported net ARR lost per year", "=1-H6", PCT),
    (10, "Model price at reported NRR (C$)", f"=N{LAD1 + 3}", USD2),
    (11, "Check: model price at implied NRR (C$) - should equal market", f"=N{LAD1 + 4}", USD2),
]
for r, lab, f, fmt in res:
    rv.merge_cells(f"A{r}:G{r}")
    put(rv, f"A{r}", lab, bold=r in (5, 7))
    if f:
        put(rv, f"H{r}", f, F_LINK if f.startswith("=Inputs") else F_CALC, fmt, bold=r in (5, 7))
px = f"$N${LAD0}:$N${LAD1}"
nr = f"$A${LAD0}:$A${LAD1}"
k = f"MATCH(H4,{px},-1)"
implied = (f'=IF(H4>N{LAD0},"above 120%",IF(H4<N{LAD1},"below 50%",'
           f"INDEX({nr},{k})-(INDEX({px},{k})-H4)/(INDEX({px},{k})-INDEX({px},{k}+1))*{STEP}))")
put(rv, "H5", implied, fmt=PCT, fill=FILL_ANS, bold=True, border=BOX)
for r in (6, 7, 8, 9):
    rv[f"H{r}"].fill = FILL_ANS
rv.merge_cells("A13:N13")
verdict = ('=IF(ISNUMBER(H5),IF(H5<H6,"PESSIMISTIC: the price only makes sense if existing customers pay about "&TEXT(1-H5,"0%")'
           '&" less every year (NRR "&TEXT(H5,"0%")&"). Docebo reports NRR of "&TEXT(H6,"0%")&" - a loss of only "&TEXT(1-H6,"0%")&".",'
           '"OPTIMISTIC: the price needs NRR of "&TEXT(H5,"0.0%")&" - better than the "&TEXT(H6,"0%")&" Docebo reports."),'
           '"Implied NRR is outside 50-120%: check the inputs.")')
put(rv, "A13", verdict, F(bold=True, size=11, color="C00000"))
rv["A13"].alignment = Alignment(wrap_text=True, vertical="top")
rv.row_dimensions[13].height = 48
note(rv, "A15", "Implied NRR BELOW reported = market pessimistic (stock may be cheap if the reported number holds). ABOVE = market optimistic.")
note(rv, "A16", "Cross-check with Goal Seek (see Start Here). Both answers should agree to about 0.1 percentage point.")

put(rv, f"A{LAD0 - 3}", "Engine: price for each NRR (same maths as ARR Model + DCF, one row per NRR)", bold=True)
header(rv, LAD0 - 1, ["NRR"] + [f"ARR Y{i}" for i in range(11)] + ["EV (US$m)", "Price C$"])
ARRC = [chr(ord("B") + i) for i in range(11)]   # B..L


def engine_row(ws, r, nrr_value):
    put(ws, f"A{r}", nrr_value, F_CALC, PCT)
    put(ws, f"B{r}", "='ARR Model'!$B$15", F_LINK, '#,##0')
    for i in range(1, 11):
        c, p, ym = ARRC[i], ARRC[i - 1], YC[i - 1]
        put(ws, f"{c}{r}", f"={p}{r}*$A{r}+'ARR Model'!{ym}$13", fmt='#,##0')
    rev = f"(B{r}:K{r}+C{r}:L{r})/2*Inputs!$B$44"
    ev = (f"=SUMPRODUCT({rev},'ARR Model'!$C$9:$L$9,DCF!$C$5:$L$5)"
          f"+AVERAGE(K{r},L{r})*Inputs!$B$44*'ARR Model'!$L$9*(1+{A}!$C$11)/({A}!$C$10-{A}!$C$11)*DCF!$L$5")
    put(ws, f"M{r}", ev, fmt='#,##0')
    put(ws, f"N{r}", f"=(M{r}+Inputs!$B$13-Inputs!$B$14)/Inputs!$B$9*Inputs!$B$6", fmt=USD2)


for i in range(NSTEP):
    engine_row(rv, LAD0 + i, round(1.20 - i * STEP, 4))
put(rv, f"A{LAD1 + 2}", "Checks", bold=True)
engine_row(rv, LAD1 + 3, "=Inputs!B17")
engine_row(rv, LAD1 + 4, "=IF(ISNUMBER(H5),H5,0)")
engine_row(rv, LAD1 + 5, f"={A}!C5")
put(rv, f"O{LAD1 + 3}", "<- at reported NRR", F("595959", italic=True, size=9))
put(rv, f"O{LAD1 + 4}", "<- at implied NRR", F("595959", italic=True, size=9))
put(rv, f"O{LAD1 + 5}", "<- at Assumptions!C5 (must equal DCF!C18)", F("595959", italic=True, size=9))
put(rv, f"A{LAD1 + 6}", f'=IF(ABS(N{LAD1 + 5}-DCF!C18)<0.005,"CHECK OK: engine matches DCF tab","CHECK FAILED: engine differs from DCF tab")', bold=True)
rv.freeze_panes = "A4"

# =============================================================== SENSITIVITY
s = wb.create_sheet("Sensitivity")
widths(s, {"A": 30, **{c: 12 for c in "BCDEF"}})
put(s, "A1", "Sensitivity - model share price (C$): NRR x discount rate", F(bold=True, size=14))
note(s, "A2", "Green = at or above today's market price. Red = below. Blue headers are editable.")
put(s, "A3", "Market price (C$):")
put(s, "B3", "=Inputs!B5", F_LINK, USD2, bold=True)
rates = [0.08, 0.09, 0.10, 0.11, 0.12]
nrrs = [0.80, 0.85, 0.90, 0.95, 0.99, 1.01, 1.05]
put(s, "A5", "NRR ↓  /  Discount rate →", F_HDR, fill=FILL_HDR)
GC = "BCDEF"
for j, rt in enumerate(rates):
    put(s, f"{GC[j]}5", rt, F("FFFFFF", True), PCT, FILL_HDR, align="center")
E0 = 20
for i, nv in enumerate(nrrs):
    r = 6 + i
    put(s, f"A{r}", nv, F_IN, PCT, align="center")
    er = E0 + 2 + i
    for j in range(len(rates)):
        rt = f"{GC[j]}$5"
        f = (f"=(SUMPRODUCT($M{er}:$V{er},'ARR Model'!$C$9:$L$9,1/(1+{rt})^'ARR Model'!$C$2:$L$2)"
             f"+$V{er}*'ARR Model'!$L$9*(1+{A}!$C$11)/({rt}-{A}!$C$11)/(1+{rt})^10"
             f"+Inputs!$B$13-Inputs!$B$14)/Inputs!$B$9*Inputs!$B$6")
        put(s, f"{GC[j]}{r}", f, fmt=USD2, align="center")
last = 5 + len(nrrs)
rng = f"B6:F{last}"
s.conditional_formatting.add(rng, CellIsRule(operator="greaterThanOrEqual", formula=["$B$3"],
                                             fill=PatternFill("solid", fgColor="C6EFCE")))
s.conditional_formatting.add(rng, CellIsRule(operator="lessThan", formula=["$B$3"],
                                             fill=PatternFill("solid", fgColor="FFC7CE")))
note(s, f"A{last + 2}", "99% = Docebo's reported FY2025 NRR. 101% = reported NRR excluding AWS.")
put(s, f"A{E0}", "Engine (one row per NRR): ARR Y0-Y10, then revenue Y1-Y10", bold=True)
header(s, E0 + 1, ["NRR"] + [f"ARR Y{i}" for i in range(11)] + [f"Rev Y{i}" for i in range(1, 11)])
RC = [chr(ord("M") + i) for i in range(10)]
for i in range(len(nrrs)):
    er = E0 + 2 + i
    put(s, f"A{er}", f"=A{6 + i}", fmt=PCT)
    put(s, f"B{er}", "='ARR Model'!$B$15", F_LINK, '#,##0')
    for t in range(1, 11):
        c, p = ARRC[t], ARRC[t - 1]
        put(s, f"{c}{er}", f"={p}{er}*$A{er}+'ARR Model'!{YC[t - 1]}$13", fmt='#,##0')
        put(s, f"{RC[t - 1]}{er}", f"=AVERAGE({p}{er},{c}{er})*Inputs!$B$44", fmt='#,##0')
for c in "GHIJKLMNOPQRSTUV":
    s.column_dimensions[c].width = 9

# =============================================================== RED FLAGS
rf = wb.create_sheet("Red Flags")
widths(rf, {"A": 4, "B": 34, "C": 70, "D": 60})
put(rf, "A1", "Red flags - what looks sketchy about the company itself", F(bold=True, size=14))
note(rf, "A2", "Facts only, each with its source. Interpretation is in the research report.")
header(rf, 4, ["#", "Flag", "The facts", "Source"])
flags = [
    ("Buyback nobody wanted", "Announced a US$70M share buyback at US$20.40, citing an undervalued stock; raised the price to US$25.00; "
     "only 99,332 shares (US$2.48M) were tendered. Intercap tendered 13,351 shares.",
     "Docebo SIB announcement 17-Jul-2026; price increase 21-Aug-2026; final results 11-Sep-2026"),
    ("Planned to borrow for it", "The US$70M buyback was to be funded with ~US$10M cash and a US$60M draw on the credit facility.",
     "Docebo SIB announcement 17-Jul-2026"),
    ("Debt went up fast", "Credit facility raised from US$50M to US$100M (Feb-2026), then to US$150M. Drew ~US$50M on 14-Jan-2026. "
     "Borrowings US$88.0M vs cash US$45.7M at 30-Jun-2026.",
     "Q1/Q2-2026 MD&A; Docebo release 17-Jul-2026"),
    ("Growth partly bought", "Acquired 365Talents (France) on 20-Jan-2026 for US$61.3M (US$54.3M cash at closing). Expected ~US$9M revenue in 2026. "
     "2026 ARR includes acquired ARR, which Docebo does not break out.",
     "Docebo acquisition release 20-Jan-2026; Q1-2026 preliminary release 21-Apr-2026"),
    ("Controlled company", "Intercap owns 63.7% (15.9M shares). Outside shareholders cannot outvote it.",
     "SIB final results 11-Sep-2026"),
    ("Insiders sold near the top", "In 2021 Intercap, founder Claudio Erba and CEO Alessio Artuffo sold shares at C$112.00 and US$49.67 in secondary offerings. "
     "The stock is C$33.22 today.",
     "Docebo secondary offering releases, 2021"),
    ("Biggest customers leaving", "Largest OEM customer fell from 9.4% of ARR (Mar-2025) to 3.2% (Mar-2026) and 2.5% (Jun-2026). "
     "Management: AWS churn complete, Dayforce winding down.",
     "Q1-2026 preliminary release 21-Apr-2026; Q2-2026 release; Q2-2026 call"),
    ("'Adjusted' hides real costs", "Adjusted EBITDA excludes share-based pay, restructuring, acquisition compensation and transaction costs. "
     "Severance: US$5.2M in FY2025 and US$6.2M in Q1-2026 alone.",
     "Docebo MD&A (non-IFRS definitions); FY2025 and Q1-2026 financial statements"),
    ("Cash flow swings", "Free cash flow was US$27.6M (42% of revenue) in Q1-2026, then US$3.1M (4.5%) in Q2-2026.",
     "Q1-2026 and Q2-2026 press releases"),
    ("Growth slowed", "ARR growth fell from 17.8% (Q3-2024) to 8.4% (Q4-2025), then 9.5% (Q2-2026) including the acquisition.",
     "Q3-2024, Q4-2025 and Q2-2026 press releases"),
]
for i, (flag, facts, src) in enumerate(flags, start=1):
    r = 4 + i
    put(rf, f"A{r}", i)
    put(rf, f"B{r}", flag, bold=True)
    put(rf, f"C{r}", facts)
    note(rf, f"D{r}", src)
    for col in "BCD":
        rf[f"{col}{r}"].alignment = Alignment(wrap_text=True, vertical="top")
    rf.row_dimensions[r].height = 48

# =============================================================== SOURCES
so = wb.create_sheet("Sources")
widths(so, {"A": 40, "B": 14, "C": 18, "D": 70, "E": 70})
put(so, "A1", "Sources - every hard-coded number", F(bold=True, size=14))
note(so, "A2", "Open each link and tick the number. If a link fails, search the document title on Google or Business Wire.")
header(so, 4, ["Item", "Value", "Where in this file", "Document", "Link"])
links = {
    "Q2-26": "https://www.sec.gov/Archives/edgar/data/1829959/000162828026054559/docebo2026q2pr.htm",
    "Q1-26": "https://www.sec.gov/Archives/edgar/data/0001829959/000162828026032550/docebo2026q1pr.htm",
    "Q4-25": "https://www.sec.gov/Archives/edgar/data/1829959/000162828026012570/docebo2025q4pr.htm",
    "Q3-25": "https://www.sec.gov/Archives/edgar/data/1829959/000162828025050413/docebo2025q3pr.htm",
    "Q2-25": "https://www.sec.gov/Archives/edgar/data/1829959/000162828025039119/docebo2025q2pr.htm",
    "Q1-25": "https://www.sec.gov/Archives/edgar/data/1829959/000162828025024057/docebo2025q1pr.htm",
    "Q4-24": "https://www.sec.gov/Archives/edgar/data/1829959/000162828025008862/docebo2024q4pr.htm",
    "Q3-24": "https://www.sec.gov/Archives/edgar/data/1829959/000162828024046493/docebo2024q3pr.htm",
}
rows = []
for r, (lab, vals) in hist.items():
    for col, q, v in zip(Q, QS, vals):
        where = prior_year.get((q, r))
        docq = where or q
        rows.append((f"{lab}, {q}", v, f"Inputs!{col}{r}",
                     SRC[docq] + (" - prior-year comparison" if where else ""), links[docq]))
extra = [
    ("Share price (TSX), 17-Sep-2026", 33.22, "Inputs!B5", "TMX Money / Investing.com close", "https://money.tmx.com/en/quote/DCBO"),
    ("USD/CAD, 17-Sep-2026", 1.3991, "Inputs!B6", "MTFX historical rates (verify: Bank of Canada daily rates)", "https://www.bankofcanada.ca/rates/exchange/daily-exchange-rates/"),
    ("Intercap shares / ownership", "15.9M / 63.7%", "Inputs!B7:B8", "Docebo SIB final results, 11-Sep-2026", "https://finance.yahoo.com/markets/stocks/articles/docebo-inc-announces-final-results-110000945.html"),
    ("Buyback cash paid", 2.4833, "Inputs!B12", "Docebo SIB final results, 11-Sep-2026", "https://finance.yahoo.com/markets/stocks/articles/docebo-inc-announces-final-results-110000945.html"),
    ("Cash / borrowings, 30-Jun-2026", "45.7 / 88.0", "Inputs!B11, B14", "Docebo SIB + preliminary Q2-2026 release, 17-Jul-2026", "https://finance.yahoo.com/markets/stocks/articles/docebo-inc-announces-substantial-issuer-103000376.html"),
    ("Gross margin Q2-2026", 0.794, "Inputs!B16", SRC["Q2-26"], links["Q2-26"]),
    ("NRR FY2025 (and ex-AWS)", "99% / 101%", "Inputs!B17:B18", "Q4-2025 earnings call coverage, Globe and Mail", "https://www.theglobeandmail.com/investing/markets/stocks/DCBO/pressreleases/632787/docebo-earnings-call-bookings-strength-amid-cautious-outlook/"),
    ("EBITDA margin target 2028", 0.24, "Inputs!B19", "Docebo long-term model (Investing.com coverage)", "https://www.investing.com/news/analyst-ratings/needham-reiterates-docebo-stock-rating-on-efficiency-gains-93CH-4628763"),
    ("Canada 10-year yield", 0.0399, "Inputs!B20", "Trading Economics, 29-Sep-2026", "https://tradingeconomics.com/canada/government-bond-yield"),
]
for i, row in enumerate(rows + extra):
    r = 5 + i
    for j, v in enumerate(row):
        c = so.cell(r, j + 1, v)
        c.font = F_IN if j == 1 else F_CALC
        if j == 4:
            c.hyperlink = v
            c.font = F("0563C1", size=9)
        if j == 1 and isinstance(v, float):
            c.number_format = PCT if v < 1 else ('0.0000' if v < 2 else USDM)
so.freeze_panes = "A5"

# =============================================================== TRACKER
t = wb.create_sheet("Tracker")
widths(t, {"A": 13, "B": 40, "C": 11, "D": 10, "E": 11, "F": 12, "G": 14, "H": 14, "I": 60})
put(t, "A1", "Tracker - did the market's hidden bet change after news?", F(bold=True, size=14))
note(t, "A2", "After each earnings release: update Inputs, then add a row and PASTE AS VALUES the live results from Reverse DCF.")
header(t, 4, ["Date", "Event", "Price C$", "USD/CAD", "ARR US$m", "Reported NRR", "Implied NRR", "Model value C$", "What changed / my read"])
put(t, "A5", "2026-09-17", F_IN)
put(t, "B5", "Baseline (after Q2-2026 results)", F_IN)
for col, f, fmt in (("C", "=Inputs!B5", USD2), ("D", "=Inputs!B6", '0.0000'), ("E", "=Inputs!B40", USDM),
                    ("F", "=Inputs!B17", PCT), ("G", "='Reverse DCF'!H5", PCT), ("H", "='Reverse DCF'!H10", USD2)):
    put(t, f"{col}5", f, F_LINK, fmt)
put(t, "I5", "Live link for now - paste as values before adding the next row.", F("595959", italic=True, size=9))
put(t, "A6", "Nov-2026", F_IN)
put(t, "B6", "Q3-2026 results (expected early Nov 2026)", F_IN)

wb.move_sheet("Reverse DCF", offset=-3)
wb.calculation.fullCalcOnLoad = True
wb.save("Docebo_Reverse_DCF.xlsx")
print("Saved Docebo_Reverse_DCF.xlsx")
