# Trinity Dollar Beer ticket bot

Grabs your tickets on Eventbrite the moment the Tuesday/Saturday 6 PM drop opens,
then gets you to the payment step. You confirm with Apple Pay yourself.

**What it does**

1. Waits until about a minute before the next drop. Your Mac stays awake while it waits.
2. Finds that drop's event on the [Trinity Social organizer page](https://www.eventbrite.ca/o/trinity-social-38111092183):
   the "Dollar Beers" event with the drop's date in its name. You don't paste a link each time.
3. Opens the event in its own logged-in browser window and refreshes every second.
4. When **Get tickets** appears, it clicks it and maxes out the order at **4 tickets**. It skips
   sold-out ticket types (and sold-out time slots), takes as many as it can from the next available
   one, and tops up from the one after if needed. Then it clicks **Check out**.
5. It alerts you with a Mac notification, a sound, a spoken alert, and an optional phone push.
   Then you pay with Apple Pay.

The bot uses its own Chrome profile, not your everyday one. It looks empty, like a fresh
window, but it isn't incognito: once you log in there, it stays logged in. (Chrome doesn't allow
automation tools to control your main profile.) When you log in, use your **email and password**
(or Eventbrite's emailed code), not "Continue with Google". Google often blocks sign-ins from
automated browsers.

It never stores your password. You log in once yourself, and the login is kept in
`~/.ticketbot/browser-profile` on your Mac.

## One-time setup (Mac)

You need Python 3. The bot drives its own browser window, separate from Arc, so keep using Arc
normally. If Google Chrome is installed, the bot uses it. Otherwise it uses a built-in Chromium.
Either way, Apple Pay shows a QR code that you scan with your iPhone. (Arc itself can't be
automated reliably.)

```bash
git clone -b claude/trinity-beer-ticket-autobuy-2y7kon https://github.com/alazarnoah-create/ticket-bot-.git ticket-bot
cd ticket-bot
./setup.sh
./bot login          # a browser window opens: log in to Eventbrite, then press Enter
```

`config.json` is created for you. The defaults are already set for Trinity Social:

| key | what it is |
|---|---|
| `organizer_url` | where to look for new events (already set to Trinity Social) |
| `event_keyword` | text the event name must contain (default `dollar beer`) |
| `event_url` | leave empty to auto-find; set it to force one specific event |
| `quantity` | tickets per order (max 4) |
| `ticket_name` | optional: part of the ticket type's name, if there's more than one type |
| `ntfy_topic` | optional: install the free **ntfy** app on your phone, subscribe to a hard-to-guess topic name, and put that name here to get a push notification |

## Every drop

```bash
./bot next           # shows when the next drop is
./bot run            # leave it running; it waits, finds the event, and buys
```

To force a specific event instead: `./bot run --event-url https://www.eventbrite.ca/e/...`

When the alert fires, go to the bot's browser window and pay with Apple Pay. Eventbrite only holds
the tickets for a few minutes.

`./bot test-alert` checks that notifications work.

**Practice run** on a free event that's on sale now. It stops after the first Register/Check out click,
before anything is completed:

```bash
./bot run --now --event-url "https://www.eventbrite.ca/e/queens-university-in-person-campus-tour-tickets-1995720814680"
```

## If something goes wrong

- **CAPTCHA or waiting room:** the bot alerts you and pauses. Solve it in the browser, then press Enter in the terminal.
- **It couldn't set the quantity or find Checkout:** Eventbrite changes its page layout sometimes. The bot still
  alerts you with the page open, so you can finish by hand. Then tell me what the page looked like and I'll fix it.
- **It never found the event:** Trinity may have named it differently. Set `event_url` by hand for that drop.
- Keep your Mac plugged in, and don't close the lid while it waits.

Heads up: Eventbrite's terms don't allow automated purchasing, and they can cancel orders or restrict accounts.
This bot buys the normal per-person amount on your own account and refreshes at a gentle rate. Use it at your own risk.
