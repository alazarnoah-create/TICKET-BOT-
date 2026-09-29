"""Builds SaaS_Financial_Model.xlsx: a 36-month, formula-driven SaaS model.

Run:  python build_model.py
Every number in the output workbook is either a blue input on the
Assumptions tab or a formula that traces back to one.
"""
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as col

MONTHS = 36
FIRST, LAST = 3, 2 + MONTHS            # month 1 in column C, month 36 in AL
FC, LC = col(FIRST), col(LAST)

FONT = "Arial"
BLUE, BLACK, GREEN = "0000FF", "000000", "008000"
F_INPUT = Font(name=FONT, size=10, color=BLUE)
F_CALC = Font(name=FONT, size=10, color=BLACK)
F_LINK = Font(name=FONT, size=10, color=GREEN)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_TITLE = Font(name=FONT, size=14, bold=True)
F_HDR = Font(name=FONT, size=10, bold=True, color="FFFFFF")
FILL_HDR = PatternFill("solid", fgColor="1F3864")
FILL_SEC = PatternFill("solid", fgColor="D9E1F2")
FILL_KEY = PatternFill("solid", fgColor="FFFF00")
TOP = Border(top=Side(style="thin"))

USD = '$#,##0;($#,##0);"-"'
NUM = '#,##0;(#,##0);"-"'
PCT = '0.0%;(0.0%);"-"'
MULT = '0.0x;(0.0x);"-"'
MOS = '0.0;(0.0);"-"'

A = "Assumptions"
RB = "'Revenue Build'"
IS = "'Income Statement'"
CF = "'Cash Flow'"

wb = Workbook()


def style(c, font=F_CALC, fmt=None, fill=None, bold=False, border=None):
    c.font = Font(name=FONT, size=10, bold=True, color=font.color) if bold else font
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if border:
        c.border = border


def timeline(ws, title):
    """Title in row 1, month index in row 2, year number in row 3."""
    ws["A1"] = title
    ws["A1"].font = F_TITLE
    ws["A2"], ws["A3"] = "Month", "Year"
    ws["B2"] = 0
    for r in (2, 3):
        ws[f"A{r}"].font = F_HDR
        for c in range(1, LAST + 1):
            ws.cell(r, c).fill = FILL_HDR
    style(ws["B2"], F_HDR)
    ws["B2"].font = F_HDR
    ws["B2"].alignment = Alignment(horizontal="center")
    for c in range(FIRST, LAST + 1):
        L, P = col(c), col(c - 1)
        ws[f"{L}2"] = f"={P}2+1"
        ws[f"{L}3"] = f"=ROUNDUP({L}2/12,0)"
        for r in (2, 3):
            ws[f"{L}{r}"].font = F_HDR
            ws[f"{L}{r}"].alignment = Alignment(horizontal="center")
        ws[f"{L}3"].number_format = '"Y"0'
    ws.column_dimensions["A"].width = 44
    ws.column_dimensions["B"].width = 12
    for c in range(FIRST, LAST + 1):
        ws.column_dimensions[col(c)].width = 11
    ws.freeze_panes = "C4"


def label(ws, r, text, bold=False, section=False, indent=0):
    c = ws.cell(r, 1, text)
    c.font = F_BOLD if (bold or section) else F_CALC
    c.alignment = Alignment(indent=indent)
    if section:
        for i in range(1, LAST + 1):
            ws.cell(r, i).fill = FILL_SEC


def row(ws, r, text, formula, fmt=USD, font=F_CALC, bold=False, opening=None,
        border=None, indent=1):
    """Write a row whose month columns share one formula template.
    `formula` uses {c} for this column and {p} for the prior column."""
    label(ws, r, text, bold=bold, indent=0 if bold else indent)
    for c in range(FIRST, LAST + 1):
        cell = ws.cell(r, c, formula.format(c=col(c), p=col(c - 1)))
        style(cell, font, fmt, bold=bold, border=border)
    if opening is not None:
        cell = ws.cell(r, 2, opening)
        style(cell, font, fmt, bold=bold, border=border)
    if border:
        ws.cell(r, 1).border = border


# ---------------------------------------------------------------- Guide
g = wb.active
g.title = "Guide"
g.column_dimensions["A"].width = 3
g.column_dimensions["B"].width = 110
guide = [
    ("SaaS Financial Model - how it works", F_TITLE),
    ("", None),
    ("WHAT IT DOES", F_BOLD),
    ("A 36-month model of a subscription software business with three plans (Basic, Pro, Enterprise).", None),
    ("It turns a handful of drivers (price, customer adds, churn, CAC, costs) into MRR/ARR, an income statement, a cash flow statement and unit economics.", None),
    ("", None),
    ("HOW THE TABS CONNECT", F_BOLD),
    ("1. Assumptions      - every input lives here. Change a blue number and the whole model updates.", None),
    ("2. Revenue Build    - per plan: customers (beginning + new - churned = ending) and the MRR bridge (beginning + new + expansion - churn = ending).", None),
    ("3. Income Statement - revenue, cost of revenue, gross profit, opex (S&M, R&D, G&A), EBITDA, D&A, taxes, net income.", None),
    ("4. Cash Flow        - net income + D&A - increase in receivables - capex + equity raised = change in cash; burn and runway.", None),
    ("5. Annual Summary   - yearly roll-up, KPIs (ARR growth, margins, CAC, LTV, LTV/CAC, payback, Rule of 40) and charts.", None),
    ("", None),
    ("COLOR CODE", F_BOLD),
    ("Blue text = hard-coded input you can change   |   Black = formula   |   Green = link to another tab   |   Yellow fill = key driver", None),
    ("", None),
    ("KEY MODELLING CHOICES (say these out loud in an interview)", F_BOLD),
    ("- Revenue recognized in a month = average of beginning and ending MRR (customers join/leave mid-month on average).", None),
    ("- Churn is applied to the beginning-of-month base; expansion is % of beginning MRR (upsells / seat growth).", None),
    ("- S&M = new customers x CAC per plan + fixed brand marketing. R&D and G&A grow at a fixed monthly rate.", None),
    ("- Taxes only when EBIT is positive (no NOL carry-forward - a simplification). Capex depreciated straight-line.", None),
    ("- Working capital = accounts receivable only (days of revenue). All customers billed monthly (no deferred revenue).", None),
    ("", None),
    ("IDEAS TO EXTEND IT", F_BOLD),
    ("Annual prepaid plans + deferred revenue; headcount-driven opex; NOL tracking; cohort retention curves; a balance sheet; scenario switch (base/bull/bear).", None),
]
for i, (text, font) in enumerate(guide, start=1):
    c = g.cell(i, 2, text)
    c.font = font or F_CALC
    c.alignment = Alignment(wrap_text=True, vertical="top")

# ---------------------------------------------------------------- Assumptions
a = wb.create_sheet(A)
a["A1"] = "Assumptions"
a["A1"].font = F_TITLE
a["A2"] = "Blue = input (change freely). Yellow = key driver. All values are illustrative, set by the modeller - not company data."
a["A2"].font = Font(name=FONT, size=9, italic=True)
for c, w in zip("ABCDE", (48, 14, 14, 14, 60)):
    a.column_dimensions[c].width = w


def hdr(ws, r, labels):
    for i, t in enumerate(labels, start=1):
        cell = ws.cell(r, i, t)
        cell.font, cell.fill = F_HDR, FILL_HDR
        if i > 1:
            cell.alignment = Alignment(horizontal="center")


hdr(a, 4, ["Plan assumptions", "Basic", "Pro", "Enterprise", "Notes"])
plan_inputs = [
    (5, "Monthly price ($ per customer / month)", (49, 199, 999), USD, True, "List price per account"),
    (6, "New customers acquired in Month 1", (40, 15, 2), NUM, True, "Gross new logos in the first forecast month"),
    (7, "Monthly growth in new customer adds (%)", (0.05, 0.05, 0.04), PCT, False, "Compounds: adds in month t = Month 1 adds x (1+g)^(t-1)"),
    (8, "Monthly logo churn (%)", (0.03, 0.02, 0.01), PCT, True, "% of beginning customers (and MRR) lost each month"),
    (9, "Starting customers (Month 0)", (100, 30, 3), NUM, False, "Existing base at model start"),
    (10, "Monthly expansion (% of beginning MRR)", (0.0, 0.01, 0.015), PCT, False, "Upsell / extra seats from existing customers"),
    (11, "CAC - cost to acquire one customer ($)", (300, 1500, 12000), USD, True, "Variable sales & marketing cost per new logo"),
]
for r, text, vals, fmt, key, note in plan_inputs:
    a.cell(r, 1, text).font = F_CALC
    for i, v in enumerate(vals):
        c = a.cell(r, 2 + i, v)
        style(c, F_INPUT, fmt, FILL_KEY if key else None)
    a.cell(r, 5, note).font = Font(name=FONT, size=9, italic=True)

hdr(a, 13, ["Operating cost assumptions", "Value", "", "", "Notes"])
cost_inputs = [
    (14, "Hosting & infrastructure (% of revenue)", 0.12, PCT, False, "Cloud cost scales with usage/revenue"),
    (15, "Payment processing fees (% of revenue)", 0.03, PCT, False, "Card / Stripe-style fees"),
    (16, "Customer support ($ per customer / month)", 8, USD, False, "Applied to average customers in the month"),
    (17, "Fixed marketing spend ($ / month)", 15000, USD, False, "Brand, content, events - not tied to new logos"),
    (18, "R&D payroll - Month 1 ($ / month)", 60000, USD, True, "Engineering & product team"),
    (19, "R&D monthly growth (%)", 0.015, PCT, False, "Hiring pace"),
    (20, "G&A - Month 1 ($ / month)", 25000, USD, False, "Finance, legal, office, admin"),
    (21, "G&A monthly growth (%)", 0.01, PCT, False, ""),
    (22, "Capex ($ / month)", 5000, USD, False, "Laptops, equipment"),
    (23, "Useful life of capex (months)", 36, NUM, False, "Straight-line depreciation"),
    (24, "Tax rate (%)", 0.21, PCT, False, "Applied only to positive EBIT"),
]
hdr(a, 26, ["Cash & financing", "Value", "", "", "Notes"])
cash_inputs = [
    (27, "Starting cash ($)", 2000000, USD, True, "Cash in the bank at Month 0"),
    (28, "Accounts receivable (days of revenue)", 30, NUM, False, "How long customers take to pay"),
    (29, "Equity raise amount ($)", 3000000, USD, True, "e.g. a Series A"),
    (30, "Equity raise month", 13, NUM, False, "Month number in which the cash arrives"),
]
for r, text, v, fmt, key, note in cost_inputs + cash_inputs:
    a.cell(r, 1, text).font = F_CALC
    style(a.cell(r, 2, v), F_INPUT, fmt, FILL_KEY if key else None)
    a.cell(r, 5, note).font = Font(name=FONT, size=9, italic=True)
a.freeze_panes = "B5"

# ---------------------------------------------------------------- Revenue Build
rb = wb.create_sheet("Revenue Build")
timeline(rb, "Revenue Build - customers and MRR by plan")
plans = [("Basic", "B", 5), ("Pro", "C", 16), ("Enterprise", "D", 27)]
for name, pc, h in plans:
    label(rb, h, f"{name} plan", section=True)
    row(rb, h + 1, "Beginning customers", "={p}" + str(h + 4), NUM)
    row(rb, h + 2, "(+) New customers",
        f"={A}!${pc}$6*(1+{A}!${pc}$7)^({{c}}$2-1)", NUM, F_LINK)
    row(rb, h + 3, "(-) Churned customers", f"=-{{c}}{h + 1}*{A}!${pc}$8", NUM, F_LINK)
    row(rb, h + 4, "Ending customers", f"=SUM({{c}}{h + 1}:{{c}}{h + 3})", NUM,
        bold=True, opening=f"={A}!{pc}9", border=TOP)
    rb.cell(h + 4, 2).font = Font(name=FONT, size=10, bold=True, color=GREEN)
    row(rb, h + 5, "Beginning MRR", "={p}" + str(h + 9))
    row(rb, h + 6, "(+) New MRR", f"={{c}}{h + 2}*{A}!${pc}$5", USD, F_LINK)
    row(rb, h + 7, "(+) Expansion MRR", f"={{c}}{h + 5}*{A}!${pc}$10", USD, F_LINK)
    row(rb, h + 8, "(-) Churned MRR", f"=-{{c}}{h + 5}*{A}!${pc}$8", USD, F_LINK)
    row(rb, h + 9, "Ending MRR", f"=SUM({{c}}{h + 5}:{{c}}{h + 8})", bold=True,
        opening=f"=B{h + 4}*{A}!{pc}5", border=TOP)

T = 38
label(rb, T, "Total - all plans", section=True)
tot = [(1, "Beginning customers", NUM), (2, "(+) New customers", NUM),
       (3, "(-) Churned customers", NUM), (4, "Ending customers", NUM),
       (5, "Beginning MRR", USD), (6, "(+) New MRR", USD),
       (7, "(+) Expansion MRR", USD), (8, "(-) Churned MRR", USD),
       (9, "Ending MRR", USD)]
for off, text, fmt in tot:
    f = "=" + "+".join(f"{{c}}{h + off}" for _, _, h in plans)
    bold = off in (4, 9)
    row(rb, T + off, text, f, fmt, bold=bold, border=TOP if bold else None,
        opening=("=" + "+".join(f"B{h + off}" for _, _, h in plans)) if bold else None)
row(rb, 48, "Net new MRR", "={c}47-{c}43")
row(rb, 49, "ARR (ending MRR x 12)", "={c}47*12", bold=True, opening="=B47*12")
row(rb, 50, "ARPA - avg revenue per account ($ / month)", "=IF({c}42>0,{c}47/{c}42,0)")
row(rb, 51, "MoM MRR growth (%)", "=IF({c}43>0,{c}47/{c}43-1,0)", PCT)
row(rb, 53, "Recognized revenue (avg of beginning & ending MRR)", "=({c}43+{c}47)/2",
    bold=True, border=TOP)
rb.cell(53, 1).comment = Comment(
    "Customers sign up and cancel throughout the month, so on average a month "
    "earns the midpoint of opening and closing MRR.", "Model")

# ---------------------------------------------------------------- Income Statement
inc = wb.create_sheet("Income Statement")
timeline(inc, "Income Statement ($)")
row(inc, 5, "Revenue", f"={RB}!{{c}}53", USD, F_LINK, bold=True)
label(inc, 6, "Cost of revenue", section=True)
row(inc, 7, "Hosting & infrastructure", f"=-{{c}}5*{A}!$B$14", USD, F_LINK)
row(inc, 8, "Payment processing", f"=-{{c}}5*{A}!$B$15", USD, F_LINK)
row(inc, 9, "Customer support",
    f"=-AVERAGE({RB}!{{c}}39,{RB}!{{c}}42)*{A}!$B$16", USD, F_LINK)
row(inc, 10, "Total cost of revenue", "=SUM({c}7:{c}9)", border=TOP)
row(inc, 11, "Gross profit", "={c}5+{c}10", bold=True)
row(inc, 12, "Gross margin (%)", "=IF({c}5<>0,{c}11/{c}5,0)", PCT)
label(inc, 13, "Operating expenses", section=True)
sm = "+".join(f"{RB}!{{c}}{h + 2}*{A}!${pc}$11" for _, pc, h in plans)
row(inc, 14, "Sales & marketing (CAC x new logos + fixed)",
    f"=-({sm}+{A}!$B$17)", USD, F_LINK)
row(inc, 15, "Research & development", f"=-{A}!$B$18*(1+{A}!$B$19)^({{c}}$2-1)", USD, F_LINK)
row(inc, 16, "General & administrative", f"=-{A}!$B$20*(1+{A}!$B$21)^({{c}}$2-1)", USD, F_LINK)
row(inc, 17, "Total operating expenses", "=SUM({c}14:{c}16)", border=TOP)
row(inc, 18, "EBITDA", "={c}11+{c}17", bold=True)
row(inc, 19, "EBITDA margin (%)", "=IF({c}5<>0,{c}18/{c}5,0)", PCT)
row(inc, 20, "Depreciation & amortization",
    f"=SUM({CF}!${FC}$11:{{c}}11)/{A}!$B$23", USD, F_LINK)
row(inc, 21, "EBIT (operating income)", "={c}18+{c}20", bold=True, border=TOP)
row(inc, 22, "Income taxes", f"=-MAX(0,{{c}}21)*{A}!$B$24", USD, F_LINK)
row(inc, 23, "Net income", "={c}21+{c}22", bold=True, border=TOP)
row(inc, 24, "Net margin (%)", "=IF({c}5<>0,{c}23/{c}5,0)", PCT)

# ---------------------------------------------------------------- Cash Flow
cf = wb.create_sheet("Cash Flow")
timeline(cf, "Cash Flow Statement ($)")
label(cf, 5, "Operating activities", section=True)
row(cf, 6, "Net income", f"={IS}!{{c}}23", USD, F_LINK)
row(cf, 7, "(+) Depreciation & amortization", f"=-{IS}!{{c}}20", USD, F_LINK)
row(cf, 8, "(-) Increase in accounts receivable", "={p}20-{c}20")
row(cf, 9, "Cash flow from operations", "=SUM({c}6:{c}8)", bold=True, border=TOP)
label(cf, 10, "Investing activities", section=True)
row(cf, 11, "Capital expenditures", f"=-{A}!$B$22", USD, F_LINK)
row(cf, 12, "Cash flow from investing", "={c}11", bold=True, border=TOP)
label(cf, 13, "Financing activities", section=True)
row(cf, 14, "Equity raised", f"=IF({{c}}$2={A}!$B$30,{A}!$B$29,0)", USD, F_LINK)
row(cf, 15, "Cash flow from financing", "={c}14", bold=True, border=TOP)
row(cf, 17, "Net change in cash", "={c}9+{c}12+{c}15", bold=True)
row(cf, 18, "Beginning cash", "={p}19")
row(cf, 19, "Ending cash", "={c}18+{c}17", bold=True, border=TOP,
    opening=f"={A}!B27")
cf.cell(19, 2).font = Font(name=FONT, size=10, bold=True, color=GREEN)
row(cf, 20, "Accounts receivable balance", f"={IS}!{{c}}5*{A}!$B$28/30", USD, F_LINK,
    opening=f"={RB}!B47*{A}!B28/30")
cf.cell(20, 2).font = F_LINK
label(cf, 21, "Burn & runway", section=True)
row(cf, 22, "Free cash flow (CFO + CFI)", "={c}9+{c}12", bold=True)
row(cf, 23, "Monthly burn", "=MAX(0,-{c}22)")
row(cf, 24, "Runway at current burn (months)",
    '=IF({c}23>0,{c}19/{c}23,"CF positive")', MOS)
for c in range(FIRST, LAST + 1):
    cf.cell(24, c).alignment = Alignment(horizontal="right")

# ---------------------------------------------------------------- Annual Summary
s = wb.create_sheet("Annual Summary")
s["A1"] = "Annual Summary & KPIs"
s["A1"].font = F_TITLE
s.column_dimensions["A"].width = 46
for L in "BCDE":
    s.column_dimensions[L].width = 15
s.column_dimensions["F"].width = 62
hdr(s, 3, ["", "Start (M0)", "", "", "", "How it's calculated"])
for i, L in enumerate("CDE", start=1):
    s[f"{L}3"] = i
    s[f"{L}3"].number_format = '"Year "0'
s.freeze_panes = "B4"

rng = lambda sheet, r: f"{sheet}!${FC}${r}:${LC}${r}"
yrs = lambda sheet: f"{sheet}!${FC}$3:${LC}$3"
sumy = lambda sheet, r: f"SUMIFS({rng(sheet, r)},{yrs(sheet)},{{c}}$3)"
endy = lambda sheet, r: f"INDEX({rng(sheet, r)},{{c}}$3*12)"


def srow(r, text, formula, fmt=USD, bold=False, font=F_LINK, note="", opening=None,
         first=None):
    label(s, r, text, bold=bold, indent=0 if bold else 1)
    for i, L in enumerate("CDE"):
        f = first if (i == 0 and first is not None) else formula
        cell = s[f"{L}{r}"]
        cell.value = f.format(c=L, p=chr(ord(L) - 1))
        style(cell, font, fmt, bold=bold)
        cell.alignment = Alignment(horizontal="right")
    if opening is not None:
        style(s.cell(r, 2, opening), font, fmt, bold=bold)
    s.cell(r, 6, note).font = Font(name=FONT, size=9, italic=True)


def ssec(r, text):
    s.cell(r, 1, text).font = F_BOLD
    for i in range(1, 7):
        s.cell(r, i).fill = FILL_SEC


ssec(4, "Growth")
srow(5, "Ending customers", "=" + endy(RB, 42), NUM, note="Month-12/24/36 balance",
     opening=f"={RB}!B42")
srow(6, "Ending MRR", "=" + endy(RB, 47), note="Monthly recurring revenue at year end",
     opening=f"={RB}!B47")
srow(7, "Ending ARR", "={c}6*12", bold=True, font=F_CALC, note="MRR x 12",
     opening="=B6*12")
srow(8, "ARR growth (%)", "=IF({p}7>0,{c}7/{p}7-1,0)", PCT, font=F_CALC,
     first="=IF(B7>0,C7/B7-1,0)", note="vs. prior year-end (Year 1 vs. Month 0)")
srow(9, "Revenue", "=" + sumy(IS, 5), bold=True, note="Sum of monthly recognized revenue")
srow(10, "Revenue growth (%)", "=IF({p}9>0,{c}9/{p}9-1,0)", PCT, font=F_CALC,
     first='="n/a"', note="Year-over-year")
ssec(11, "Profitability")
srow(12, "Gross profit", "=" + sumy(IS, 11))
srow(13, "Gross margin (%)", "=IF({c}9<>0,{c}12/{c}9,0)", PCT, font=F_CALC,
     note="SaaS benchmark: 70-80%+")
srow(14, "EBITDA", "=" + sumy(IS, 18), bold=True)
srow(15, "EBITDA margin (%)", "=IF({c}9<>0,{c}14/{c}9,0)", PCT, font=F_CALC)
srow(16, "Net income", "=" + sumy(IS, 23))
ssec(17, "Cash")
srow(18, "Free cash flow", "=" + sumy(CF, 22), bold=True, note="CFO + capex")
srow(19, "Ending cash", "=" + endy(CF, 19), opening=f"={CF}!B19")
srow(20, "Lowest month-end cash in year",
     f"=_xlfn.MINIFS({rng(CF, 19)},{yrs(CF)},{{c}}$3)",
     note="Must stay above zero - tells you when you need to raise")
ssec(21, "Unit economics")
srow(22, "New customers acquired", "=" + sumy(RB, 40), NUM)
srow(23, "Sales & marketing spend", "=-" + sumy(IS, 14))
srow(24, "Blended CAC ($ per new customer)", "=IF({c}22>0,{c}23/{c}22,0)", font=F_CALC,
     note="Total S&M / new customers (includes fixed marketing)")
srow(25, "Avg monthly logo churn (%)", f"=IF({sumy(RB, 39)}>0,-{sumy(RB, 41)}/{sumy(RB, 39)},0)",
     PCT, note="Churned customers / beginning customers, summed over the year")
srow(26, "ARPA ($ / month, year end)", "=IF({c}5>0,{c}6/{c}5,0)", font=F_CALC)
srow(27, "Customer lifetime value (LTV)", "=IF({c}25>0,{c}26*{c}13/{c}25,0)", font=F_CALC,
     note="ARPA x gross margin / monthly churn")
srow(28, "LTV / CAC", "=IF({c}24>0,{c}27/{c}24,0)", MULT, bold=True, font=F_CALC,
     note="Healthy SaaS: 3.0x or higher")
srow(29, "CAC payback (months)", "=IF({c}26*{c}13>0,{c}24/({c}26*{c}13),0)", MOS,
     font=F_CALC, note="Months of gross profit to earn back CAC. Good: < 12-18")
srow(30, "Net MRR churn (monthly, %)",
     f"=IF({sumy(RB, 43)}>0,-({sumy(RB, 46)}+{sumy(RB, 45)})/{sumy(RB, 43)},0)", PCT,
     note="(Churned MRR - expansion MRR) / beginning MRR. Negative = net expansion")
srow(31, "Rule of 40 (%)", "={c}10+{c}15", PCT, bold=True, font=F_CALC,
     first='="n/a"', note="Revenue growth + EBITDA margin. >= 40% is strong")

# Charts: monthly ending MRR and ending cash
for anchor, sheet, r, title, ytitle in (
        ("H3", rb, 47, "Ending MRR by month", "$"),
        ("H20", cf, 19, "Ending cash by month", "$")):
    ch = LineChart()
    ch.title, ch.y_axis.title, ch.x_axis.title = title, ytitle, "Month"
    ch.add_data(Reference(sheet, min_col=FIRST, max_col=LAST, min_row=r), from_rows=True)
    ch.set_categories(Reference(sheet, min_col=FIRST, max_col=LAST, min_row=2))
    ch.legend = None
    ch.height, ch.width = 7.5, 16
    s.add_chart(ch, anchor)

wb.move_sheet("Annual Summary", offset=-4)   # Guide, Assumptions, Annual Summary, ...
wb.calculation.fullCalcOnLoad = True
wb.save("SaaS_Financial_Model.xlsx")
print("Saved SaaS_Financial_Model.xlsx")
