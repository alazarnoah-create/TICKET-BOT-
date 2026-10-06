# Trinity Dollar Beer ticket bot

Grabs Dollar Beers tickets in **your own Safari** the second the Tuesday/Saturday 6 PM drop opens:
it clicks Get tickets, maxes out the order at 4, clicks Check out, and alerts you to pay with Apple Pay.

**What it does**

1. Waits for the next drop. Your Mac stays awake while it waits.
2. **2 minutes before:** an alert to get ready, and the bot finds the next Dollar Beers event on the
   [Trinity Social organizer page](https://www.eventbrite.ca/o/trinity-social-38111092183)
   (the soonest upcoming one). Safari stays off Eventbrite until the drop.
3. **At 6:00 PM on the dot:** opens the event in Safari (it doesn't load Eventbrite before then), refreshes
   gently until tickets are on sale (after 3, 5, 8, 12, 20 seconds, then every 30),
   clicks **Get tickets**, picks **4** (skipping sold-out ticket types and topping up from the next
   one if needed), and clicks **Check out**.
4. Alerts you: **Tickets in your cart!** You pay with **Apple Pay** (Touch ID). Apple requires you to
   approve every payment yourself, so the bot can't do that step.

If Eventbrite shows a CAPTCHA, the bot alerts **Solve the CAPTCHA now!** Solve it in Safari, then pay.

## One-time setup (Mac)

1. In **Safari**, go to eventbrite.ca and **log in**.
2. Make sure Apple Pay works in Safari: **System Settings → Wallet & Apple Pay** should have a card.
3. Let the bot click in Safari (one time):
   - Safari menu → **Settings…** → **Advanced** → tick **Show features for web developers**.
   - Close Settings. A **Develop** menu appears at the top. Click it and tick
     **Allow JavaScript from Apple Events**.
   - The first time the bot runs, macOS asks whether **Terminal** may control **Safari**. Click **OK**.
4. In Terminal, point it at this folder (type `cd `, drag the folder in, press Enter), then run:
   ```bash
   bash setup.sh
   ```

## Every drop

Tickets go on sale at **6 PM**, often a day or more before the party. Trinity announces the day on
[Instagram (@trinityktown)](https://www.instagram.com/trinityktown/) (e.g. "Tickets for dollar beers go on
sale Friday at 6PM"). The bot grabs the **next upcoming** Dollar Beers event, whatever night it's for.

Open Terminal, point it at this folder (`cd ` then drag the folder in and press Enter), and run
this any time before 6 PM:

```bash
bash bot run
```

That waits for the next Tuesday or Saturday at 6 PM. If Trinity announces a different day, add it,
e.g. `bash bot run --day friday`.

Leave it running, and don't use Safari while it works. When **Tickets in your cart!** goes off,
pay with Apple Pay. If the bot can't click (the Safari setting above is off), it alerts
**GO NOW - buy it yourself!** and you click through by hand.

Other commands:

- `bash bot next`: shows when the next drop is.
- `bash bot check`: checks the bot can read the Trinity Social page and lists any Dollar Beers events it sees.
- `bash bot test-alert`: checks the alert and sound work.
- `bash bot run --now --event-url "https://www.eventbrite.ca/e/..."`: runs on a specific event right away (practice; don't pay).
- `bash bot run --manual`: only opens the event and alerts you; you do all the clicking.

## Optional: phone alert

Install the free **ntfy** app on your phone, subscribe to a hard-to-guess topic name, and put that
name in `ntfy_topic` in `config.json`. You'll get a push notification at the same time as the alert.

## Settings (`config.json`)

| key | what it is |
|---|---|
| `organizer_url` | where to look for new events (already set to Trinity Social) |
| `event_keyword` | text the event name must contain (default `dollar beer`) |
| `event_url` | leave empty to auto-find; set it to force one specific event |
| `drop_days`, `drop_time` | Tuesday/Saturday at 18:00 |

If the bot can't spot the event, it opens the Trinity Social page in Safari instead. Click the
newest Dollar Beers event there.

## Automated mode (not recommended)

`bash bot login` then `bash bot auto` runs the older fully automated mode in a separate Chrome
window. Eventbrite flags it with CAPTCHAs and "unusual activity", so use `run` instead.

## MLB betting model (`mlb_model/`)

A separate tool in this folder: it projects MLB games and prices bets and parlays against the odds.
No extra installs (plain Python 3.9+).

```bash
python3 -m mlb_model today                                  # today's games, live from MLB's free Stats API
python3 -m mlb_model today --date 2026-10-07 --bankroll 200
python3 -m mlb_model file mlb_model/games/2026-10-06.json   # a slate typed in by hand, works offline
python3 -m mlb_model backtest --season 2025                 # checks the model on last season
```

For live odds, get a free key at [the-odds-api.com](https://the-odds-api.com) and run
`ODDS_API_KEY=yourkey python3 -m mlb_model today`. Or pass `--odds odds.json` with
`{"Away Team @ Home Team": {"ml": {"away": -115, "home": -105}, "run_line": {"away": [-1.5, 161], "home": [1.5, -196]}, "total": {"line": 6, "over": -115, "under": -105}}}`.

**How it works**

1. **Expected runs** for each side = league runs per game × the batting team's offense × the other
   side's pitching (starter for the innings he's expected to throw, bullpen for the rest) × park.
   Season numbers are pulled toward league average by sample size, so a hot 40-inning starter
   doesn't look like an ace. Home teams get a small edge (about 53% for even teams, like real MLB).
2. **Score distribution**: each team's runs follow a negative binomial (real MLB scoring is
   lumpier than a simple bell curve). Ties go to extra innings. Every market comes off that one
   table: moneyline, run line, totals, and same-game combos with their true joint chance.
3. **Props**: starter strikeouts (strikeout rate × batters he'll face) and batter home runs.
4. **Bets**: each bet shows the book's no-vig chance, the model's chance, the expected profit
   per $1, and a quarter-Kelly stake (max 5% of bankroll). It also lists the best 3-leg
   same-game parlays per game and long-shot parlays near `--target` (default 50x).

**Read this before betting real money.** Betting markets are sharp. When this model disagrees
with the line, the line is right more often than not, especially on props, where the model is
roughest. Each parlay leg stacks the book's edge, and same-game parlays pay less than the legs'
product shown here. A 50x parlay that the model gives a 2-3% chance still loses about 97 times
in 100. Bet only what you can afford to lose.
