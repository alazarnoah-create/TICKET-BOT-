# Trinity Dollar Beer ticket bot

Grabs Dollar Beers tickets in **your own Safari** the second the Tuesday/Saturday 6 PM drop opens:
it clicks Get tickets, maxes out the order at 4, clicks Check out, and alerts you to pay with Apple Pay.

**What it does**

1. Waits for the next drop. Your Mac stays awake while it waits.
2. **2 minutes before:** finds this drop's event on the
   [Trinity Social organizer page](https://www.eventbrite.ca/o/trinity-social-38111092183)
   (the "Dollar Beers" event with the drop's date in its name), opens it in Safari, and alerts you
   so you can check you're logged in.
3. **At 6:00 PM on the dot:** opens the event fresh in Safari, refreshes until tickets are on sale,
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

Open Terminal, point it at this folder (`cd ` then drag the folder in and press Enter), and run
this any time before 6 PM:

```bash
bash bot run
```

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
