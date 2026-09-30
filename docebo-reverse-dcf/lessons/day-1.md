# DAY 1: How things grow (and shrink), taught with Docebo's real story

**What you need:** a notebook, a calculator (turn your phone sideways to get the `xʸ` key), and your Excel file `Docebo_Reverse_DCF.xlsx`.

**Rules:**
- Copy every 📝 box by hand.
- Try each problem before you look at the answers.
- Every number has a tag that says where it came from:
  - **[R]** Reported by Docebo, with the document named.
  - **[M]** Market data (share price, exchange rate).
  - **[V]** From the video, not yet checked against a filing.
  - **[C]** Calculated by us from the numbers above it.

---

## Warm-up: Docebo's story in numbers

| When | What happened | Number | Tag |
|---|---|---|---|
| Oct 2019 | IPO on the TSX | C$16 a share, ~C$75M raised | [V] |
| Late 2021 | COVID remote-training boom, stock peaks | ~C$118 | [V] (insiders sold at C$112.00 in Sep 2021 [R]) |
| Recently | AI fears, higher interest rates | fell to ~C$22 | [V] (52-week low C$19.87 [M]) |
| 17 Sep 2026 | Price we use in the model | C$33.22 | [M] TSX close |
| FY2022 → FY2026 | Revenue | $143M → ~$268M | [V] / [R] original FY2026 guidance US$267.5–269.5M |
| FY2026 | Adjusted EBITDA margin | ~20% | [R] revised guidance, release of 17 Jul 2026 |

⚠️ **One number in the video is wrong.** It says 365Talents cost "$360 million". Docebo reported **US$61.3M** (acquisition release, 20 Jan 2026). The full check is in `lessons/video-fact-check.md`.

---

## Lesson 1: Percent change

**The idea:** a change only means something compared with where you started.

> 📝 **WRITE THIS DOWN**
> ```
> % change = (New − Old) ÷ Old
> ```
> *"How much it changed, divided by where it started."*

**Example: Docebo's revenue.** Q2-2025 was US$60.7M [R, Q2-2025 release] and Q2-2026 was US$68.7M [R, Q2-2026 release].
```
Step 1: New − Old = 68.7 − 60.7 = 8.0
Step 2: ÷ Old     = 8.0 ÷ 60.7 = 0.132
Step 3: × 100     = 13.2% growth [C]
```
Docebo's release says revenue was "up 13%". ✓

**Example: the crash.** From the ~C$118 peak [V] to ~C$22 [V]:
```
(22 − 118) ÷ 118 = −96 ÷ 118 = −0.814 → −81.4% [C]
```

## Lesson 2: The recovery trap

**The idea:** after a fall, you need a *bigger* percentage to get back, because you're climbing from a smaller number.

> 📝 **WRITE THIS DOWN**
> ```
> Gain needed to recover = drop ÷ (1 − drop)
> ```
> *Always ask: "percent of WHAT?"*

**Docebo example:** it fell 81.4% from the peak [C]. To get back to ~C$118:
```
(118 − 22) ÷ 22 = 96 ÷ 22 = 4.36 → +436% [C]
```
It fell 81% but needs +436% to recover. That's why investors fear big crashes.

## Lesson 3: Multiples, or "baggers"

**The idea:** investors say a stock was a "7-bagger" when it multiplied by 7.

> 📝 **WRITE THIS DOWN**
> ```
> Multiple = End ÷ Start           % gain = Multiple − 1
> ```

**Docebo:** C$16 IPO [V] → ~C$118 peak [V]: 118 ÷ 16 = **7.4×** [C]. That's the video's "seven bagger", a gain of about 638%.

## Lesson 4: CAGR (the average growth per year)

**The idea:** revenue didn't grow the same amount every year. CAGR (compound annual growth rate) is the single steady rate that gets you from the start to the end.

> 📝 **WRITE THIS DOWN**
> ```
> CAGR = (End ÷ Start)^(1/years) − 1
> ```

**Docebo:** revenue went from $143M in FY2022 [V] to ~$268M in FY2026 [V; matches the original guidance midpoint of US$268.5M, R].
```
Total growth: 268 ÷ 143 = 1.874 → +87.4% over 4 years [C]  (the video rounds to 88%)
CAGR:         1.874^(1/4) − 1 = 1.170 − 1 = 17.0% a year [C]
```
🧮 Calculator: `1.874` `xʸ` `0.25` `=`

Now compare that with **today**: revenue grew 13.2% in the latest quarter [C, Lesson 1] and ARR grew 9.5% [R, Q2-2026 release]. **The growth is slowing.** That's one of the bear-case points in the video.

## Lesson 5: Compounding works on losses too (this is your whole project)

**The idea:** if customers keep 99% of their spending each year, you multiply by 0.99 every year. If they keep 90.3%, you multiply by 0.903.

> 📝 **WRITE THIS DOWN**
> ```
> What's left = Today × (retention)^years
> ```

**Docebo's ARR is US$255.1M** [R, Q2-2026 release]. If Docebo signed no new customers, what's left of it?

| Years | At 99% retention [R, FY2025] | At 90.3% (what the price implies) [C, Excel Reverse DCF!H5] |
|---|---|---|
| 3 | 0.99³ = 0.970 → **US$247.5M** | 0.903³ = 0.736 → **US$187.8M** |
| 5 | 0.99⁵ = 0.951 → **US$242.6M** | 0.903⁵ = 0.600 → **US$153.2M** |
| 10 | 0.99¹⁰ = 0.904 → 90% left | 0.903¹⁰ = 0.360 → 36% left |

📝 **The whole report in one line:** Docebo's numbers keep 90% of today's customer revenue after 10 years. The stock price assumes only 36% is left.

## Lesson 6: Percent vs percentage points (interviewers test this)

**The idea:** when a *percentage* changes, there are two ways to describe it, and mixing them up sounds amateur.

> 📝 **WRITE THIS DOWN**
> - **Percentage points (pp):** simple subtraction of two percentages.
> - **Percent (%):** the % change *of* the percentage.

**Docebo:** the EBITDA margin was 16.4% in Q2-2026 [R, Q2-2026 release] and is guided to about 20% for FY2026 [R, 17 Jul 2026 guidance].
```
Percentage points: 20 − 16.4 = +3.6 pp [C]
Percent:           (20 − 16.4) ÷ 16.4 = +22% [C]
```
Say: *"The margin rose 3.6 points."* Don't say *"the margin rose 3.6%."*

The video's bigger example: 0.9% margin in 2022 [V] → ~20% in 2026 = **+19.1 percentage points** [C].

## Lesson 7: Rule of 72 (head-math shortcut)

> 📝 **WRITE THIS DOWN**
> ```
> Years to double ≈ 72 ÷ growth rate
> ```

- At the 17.0% CAGR from 2022–26 [C]: 72 ÷ 17 ≈ **4.2 years** to double.
- At today's 9.5% ARR growth [R]: 72 ÷ 9.5 ≈ **7.6 years** to double.

The slowdown nearly doubles the time it takes to double.

---

## ✏️ Day 1 practice
1. Docebo's 52-week low was C$19.87 [M] and the price was C$33.22 on 17 Sep 2026 [M]. What's the % gain?
2. The 52-week high was C$45.24 [M]. From C$33.22, what % gain gets it back to the high?
3. ARR was US$219.7M at Dec 2024 [R, Q4-2024 release] and US$238.1M at Dec 2025 [R, Q4-2025 release]. What's the growth?
4. The IPO price was C$16 [V]. What's the % gain from the IPO to C$33.22?
5. **Fact-check drill:** 365Talents brings in ~US$9M of revenue [R]. Work out price ÷ revenue using the video's "$360M" and using Docebo's reported US$61.3M [R]. Which multiple is believable for a small software company?
6. With 90.3% retention and no new customers, how much of today's US$255.1M ARR is left after 5 years?
7. A margin goes from 18.5% [C, Excel Inputs!B35] to 24% [R, management's 2028 target]. How many percentage points is that? And what % increase?

🔍 **Expand on it (2 sentences):** the video says EV/ARR is ~1.9×, but your Excel says 2.5× (Inputs!B46). Why could both be "right"? Hint: what price did each use?

---

## ✅ Answers
1. (33.22 − 19.87) ÷ 19.87 = **+67.2%**
2. (45.24 − 33.22) ÷ 33.22 = **+36.2%**
3. (238.1 − 219.7) ÷ 219.7 = **+8.4%**. Docebo's Q4-2025 release also says 8.4%. ✓
4. (33.22 − 16) ÷ 16 = **+107.6%**, so the stock has roughly doubled since its IPO, even after the crash.
5. Video: 360 ÷ 9 = **40×** revenue. Reported: 61.3 ÷ 9 = **6.8×** revenue. Docebo itself trades at about 2.5× ARR [C], so 40× is not believable. **The video's number is wrong.**
6. 255.1 × 0.903⁵ = 255.1 × 0.600 = **US$153.2M**. Over 40% of it is gone.
7. 24 − 18.5 = **+5.5 percentage points**. As a %: 5.5 ÷ 18.5 = **+29.7%**.
- 🔍 EV/ARR depends on the share price on the day. At C$33.22 it's 2.5×. At C$24, the same maths gives about 1.85× [C], so the video was probably recorded when the stock was cheaper. **Always write down the date of the price you use.**

---

## 🧠 Index card (rewrite from memory tomorrow)
```
% CHANGE:  (New − Old) ÷ Old            Revenue +13.2% (60.7 → 68.7) [R]
RECOVER:   drop ÷ (1 − drop)            −81% crash needs +436% [C]
MULTIPLE:  End ÷ Start                  C$16 → C$118 = 7.4× "bagger" [V]
CAGR:      (End÷Start)^(1/n) − 1        $143M → $268M = 17%/yr [V]
LOSSES:    Today × retention^n          10 yrs: 90% left (99%) vs 36% (90.3%)
POINTS:    16.4% → 20% = +3.6 pp, not +3.6%
RULE 72:   72 ÷ growth = years to double
```

## 🧠 Report Recap
- **Headline:** the C$33.22 price [M] implies **90.3% retention** [C, Excel Reverse DCF!H5]; Docebo reports **99%** [R, Q4-2025 call].
- **Model value:** **C$53.53** at reported numbers [C, Excel DCF!C18].
- **New from the video, verified:** FY2026 guidance means about a **20% adjusted EBITDA margin** [R, 17 Jul 2026]. Organic growth excluding AWS and Dayforce is about **14%** [R].
- **Caught an error:** 365Talents cost **US$61.3M**, not $360M [R, 20 Jan 2026].
