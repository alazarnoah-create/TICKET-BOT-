# Trinity Dollar Beer ticket bot

Gets you onto the Dollar Beers ticket page in **your own Safari** the second the Tuesday/Saturday
6 PM drop opens, and sets off an alert so you can grab 4 tickets and pay with Apple Pay.

**What it does**

1. Waits for the next drop. Your Mac stays awake while it waits.
2. **2 minutes before:** finds this drop's event on the
   [Trinity Social organizer page](https://www.eventbrite.ca/o/trinity-social-38111092183)
   (the "Dollar Beers" event with the drop's date in its name), opens it in Safari, and alerts you
   so you can check you're logged in.
3. **At 6:00 PM on the dot:** opens the event again, fresh, and alerts you: **GO NOW!**
4. **You** click **Get tickets**, pick **4**, **Check out**, and pay with **Apple Pay** (Touch ID).

You do the clicking in your normal, logged-in Safari, so Eventbrite sees a real person buying.
That's what avoids the "unusual activity" blocks the automated clicking triggered.

## One-time setup (Mac)

1. In **Safari**, go to eventbrite.ca and **log in**.
2. Make sure Apple Pay works in Safari: **System Settings → Wallet & Apple Pay** should have a card.
3. In Terminal, point it at this folder (type `cd `, drag the folder in, press Enter), then run:
   ```bash
   bash setup.sh
   ```

## Every drop

Open Terminal, point it at this folder (`cd ` then drag the folder in and press Enter), and run
this any time before 6 PM:

```bash
bash bot run
```

Leave it running. When **GO NOW!** goes off, click **Get tickets → 4 → Check out → Apple Pay**.
If the Get tickets button isn't there yet, press **Cmd + R** to refresh.

Other commands:

- `bash bot next`: shows when the next drop is.
- `bash bot test-alert`: checks the alert and sound work.
- `bash bot run --now --event-url "https://www.eventbrite.ca/e/..."`: opens a specific event right away (practice).

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
