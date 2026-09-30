# DAY 1: How things grow (and shrink), taught with Docebo's real story

**Style for every lesson:** each idea is explained in plain words first. Only at the end do you get its name: 🏷️ **This is called: …**

**You need:** a notebook and a calculator (turn your phone sideways to get the `xʸ` key).

**Number tags:**
- **[R]** Reported by Docebo
- **[M]** Market data
- **[V]** From the video, not yet checked against a filing
- **[C]** Calculated by us

---

## The story first
- **Oct 2019:** Docebo's shares first went on sale to the public at **C$16** [V].
- **Late 2021:** everyone was training staff online during COVID, and the price shot up to about **C$118** [V]. Insiders sold shares at C$112 in Sep 2021 [R].
- **Then:** people got scared that AI would make training software unnecessary, and borrowing got more expensive. The price fell to about **C$22** [V]. Its lowest price in the past year was C$19.87 [M].
- **17 Sep 2026:** **C$33.22** [M]. This is the price in your model.
- **Sales:** about **$143M** in 2022 [V], heading to about **$268M** in 2026 [V]. That matches Docebo's original 2026 forecast of US$267.5–269.5M [R].

⚠️ The video says Docebo paid "$360 million" for a French company, 365Talents. **Docebo reported US$61.3M** [R, acquisition release, 20 Jan 2026]. Full check: `video-fact-check.md`.

---

## Idea 1: "It went up by how much, compared to what?"

Docebo sold **$60.7M** of software in one quarter of 2025 [R] and **$68.7M** in the same quarter of 2026 [R]. That's $8.0M more.

But is $8M a lot? That depends on where you started. $8M more on top of $60M is a big deal. $8M more on top of $10 billion is nothing. So you compare the change to the starting amount:

1. How much did it change? 68.7 − 60.7 = **8.0**
2. Compared to where it started: 8.0 ÷ 60.7 = **0.132**
3. Turn it into a percentage: × 100 = **13.2%** [C]

Docebo's own release says sales were "up 13%". ✓

The same steps work for the crash, from ~C$118 [V] to ~C$22 [V]: (22 − 118) ÷ 118 = **−81.4%** [C]

> 📝 **WRITE THIS DOWN**
> ```
> (New − Old) ÷ Old
> ```
> 🏷️ **This is called: percent change**

---

## Idea 2: "Why is climbing back so much harder than falling?"

After the crash, the stock was at C$22. To get back to C$118 it needs to gain C$96. But that C$96 is measured against the small number it's at now, C$22, not the big number it fell from:
```
96 ÷ 22 = 4.36 → +436% [C]
```
It **lost 81% on the way down** but **needs +436% to get back up.** Falling is measured from a big number; climbing back is measured from a small one.

> 📝 **WRITE THIS DOWN**
> ```
> Gain needed to get back = drop ÷ (1 − drop)
> ```
> *Always ask: "percent of WHAT?"*
> 🏷️ **This is called: the recovery problem** (investors also call a big fall a **drawdown**)

---

## Idea 3: "How many times bigger did it get?"

Say you bought at C$16 and it went to C$118 [V]. Instead of a percentage, just ask how many times your money multiplied:
```
118 ÷ 16 = 7.4 times [C]
```
Every $1 you put in became about $7.40.

> 📝 **WRITE THIS DOWN**
> ```
> End ÷ Start
> ```
> 🏷️ **This is called: a multiple.** Investors call a stock that multiplies 7 times a **"7-bagger"**, which is the word in the video.

---

## Idea 4: "On average, how fast did it grow each year?"

Sales went from $143M [V] to $268M [V/R] over 4 years. They didn't grow the same amount each year, so ask: **what one steady yearly growth rate would get you from $143M to $268M in 4 years?**

There's a catch: growth stacks. Each year grows on top of the last year's bigger number, so you can't just divide the total growth by 4.
```
Step 1: How many times bigger?      268 ÷ 143 = 1.874  (87.4% bigger in total) [C]
Step 2: Undo the stacking over 4 yrs: 1.874^(1/4) = 1.170
Step 3: Take away the 1:            1.170 − 1 = 0.170 → 17.0% a year [C]
```
🧮 Calculator: `1.874` `xʸ` `0.25` `=`

Today, sales grow about 13% [C] and recurring sales grow 9.5% a year [R]. **Growth is slowing.**

> 📝 **WRITE THIS DOWN**
> ```
> (End ÷ Start)^(1 ÷ years) − 1
> ```
> 🏷️ **This is called: CAGR, the compound annual growth rate.** The "stacking" in Step 2 is called **compounding**.

---

## Idea 5: "Stacking works on losses too" (this is your whole project)

Docebo customers currently pay a combined **$255.1M a year** for their subscriptions [R].

Imagine Docebo never signs another new customer. Each year the existing customers stay, cancel, downgrade or buy more. Suppose that, overall, for every $100 they paid last year, they pay **$99** this year. Then each year you multiply by 0.99.

Now suppose they only paid **$90.20** of every $100. Then you multiply by 0.902 each year.

| After | Keeping $99 of every $100 [R] | Keeping $90.20 of every $100 [C] |
|---|---|---|
| 3 years | $255.1M × 0.99³ = **$247.5M** | $255.1M × 0.902³ = **$187.2M** |
| 5 years | **$242.6M** | **$152.3M** |
| 10 years | **90%** still there | only **36%** still there |

The first column is what Docebo reports. **The second column is what today's share price assumes** (Excel: Reverse DCF!H5).

> 📝 **WRITE THIS DOWN**
> ```
> What's left = Today × (share kept each year)^years
> ```
> 🏷️ **This is called: net revenue retention**, the "$99 of every $100" number. The yearly subscription total ($255.1M) is called **ARR, annual recurring revenue**.

---

## Idea 6: "The margin went up 3.6… 3.6 what?"

Out of every $100 of sales, Docebo kept about **$16.40 as profit** in Q2-2026 [R]. For 2026 it expects to keep about **$20** of every $100 [R, guidance of 17 Jul 2026].

There are two honest ways to describe that change, and they give different numbers:
1. **Just subtract:** 20 − 16.4 = **3.6**. The share of profit went up by 3.6 "points".
2. **Compare to where it started:** 3.6 ÷ 16.4 = **+22%**. The share of profit grew by 22%.

Both are true, but they mean different things. If you say "it went up 3.6%" when you mean 3.6 points, a finance person will notice.

> 📝 **WRITE THIS DOWN**
> - Subtracting two percentages → say **"points"**.
> - % change of a percentage → say **"%"**.
>
> 🏷️ **This is called: percentage points vs percent.** "Profit per $100 of sales" is called the **margin**. The profit measure here is **adjusted EBITDA**, which you'll learn on Day 4.

---

## Idea 7: "How long until it doubles?" (a head-math trick)

Take 72 and divide it by the growth rate. The answer is roughly how many years it takes to double.
- Growing 17% a year (2022–26 average): 72 ÷ 17 ≈ **4.2 years** [C]
- Growing 9.5% a year (today's subscription growth): 72 ÷ 9.5 ≈ **7.6 years** [C]

> 📝 **WRITE THIS DOWN**
> ```
> 72 ÷ growth rate ≈ years to double
> ```
> 🏷️ **This is called: the Rule of 72**

---

## ✏️ Practice (try before you peek)
1. The lowest price in the past year was C$19.87 [M]; on 17 Sep 2026 it was C$33.22 [M]. How much did it go up, compared to where it started?
2. The highest price in the past year was C$45.24 [M]. From C$33.22, how much must it rise to get back there?
3. The subscription total was $219.7M at Dec 2024 [R] and $238.1M at Dec 2025 [R]. How much did it grow?
4. From the C$16 first sale price [V] to C$33.22: how much gain? How many times bigger?
5. **Fact-check:** 365Talents brings in about $9M of sales a year [R]. How many times its sales did Docebo pay, using the video's $360M? Using the reported $61.3M [R]? Which is believable?
6. If customers keep only $90.20 of every $100 each year and nobody new joins, what's left of $255.1M after 5 years?
7. Profit per $100 of sales goes from $18.50 [C, Excel Inputs!B35] to $24 [R, management's 2028 target]. How many points is that? And how many %?

🔍 **Think about it:** the video says investors pay 1.9 times Docebo's subscription total for the company. Your Excel says 2.5 times (Inputs!B46). How can both be right?

## ✅ Answers
1. (33.22 − 19.87) ÷ 19.87 = **+67.2%**
2. (45.24 − 33.22) ÷ 33.22 = **+36.2%**
3. (238.1 − 219.7) ÷ 219.7 = **+8.4%**. Docebo's release says 8.4% too. ✓
4. **+107.6%**, and 33.22 ÷ 16 = **2.1 times**. It's still double the first sale price, even after the crash.
5. 360 ÷ 9 = **40 times** vs 61.3 ÷ 9 = **6.8 times**. Investors pay only about 2.5 times for Docebo itself, so 40 times makes no sense. **The video is wrong.**
6. 255.1 × 0.902⁵ = **$152.3M**
7. **5.5 points** (24 − 18.5), which is **+29.7%** (5.5 ÷ 18.5)
- 🔍 They used share prices from different days. At C$24, the same maths gives about 1.85 times [C]. **Always write down the date of the price.**

---

## 🧠 Index card: say the idea, then the name
```
"Change vs where it started"        → percent change        (New−Old)÷Old
"Why climbing back is harder"       → recovery problem      drop÷(1−drop)
"How many times bigger"             → multiple ("bagger")   End÷Start
"One steady yearly growth rate"     → CAGR                  (End÷Start)^(1/n)−1
"$ kept from existing customers"    → net revenue retention Today×kept^years
"Subtract two percentages"          → percentage points     16.4%→20% = +3.6 pts
"Years to double"                   → Rule of 72            72÷growth
```

## 🧠 Report Recap
- **The hidden bet:** today's price assumes customers keep only **$90.20 of every $100** a year. Docebo reports **$99**. *(Excel: Reverse DCF!H5; 99% is from the Q4-2025 earnings call)*
- **The model's value:** **C$53.56** a share, vs a price of **C$33.22**. *(Excel: DCF!C18, Inputs!B5)*
- **Error caught in the video:** 365Talents cost **US$61.3M**, not $360M. *(Acquisition release, 20 Jan 2026)*
