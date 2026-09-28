# Trinity Dollar Beer ticket bot

Grabs your tickets on Eventbrite the moment the Tuesday/Saturday 6 PM drop opens,
then gets you to the payment step. You confirm with Apple Pay yourself.

**What it does**

1. Waits until about a minute before the next drop. Your Mac stays awake while it waits.
2. Opens the event page in a Chrome window that's already logged in, and refreshes every 2 seconds.
3. When **Get tickets** appears, it clicks it, picks **4 tickets**, and clicks **Check out**.
4. It alerts you with a Mac notification, a sound, a spoken alert, and an optional phone push.
   Then you pay with Apple Pay.

It never stores your password. You log in once yourself, and the login is kept in
`~/.ticketbot/browser-profile` on your Mac.

## One-time setup (Mac)

You need Python 3 and Google Chrome. Chrome supports Apple Pay: you scan the QR code with your iPhone.

```bash
git clone <this repo> ticket-bot && cd ticket-bot
./setup.sh
./bot login          # a Chrome window opens: log in to Eventbrite, then press Enter
```

Edit `config.json`:

| key | what it is |
|---|---|
| `event_url` | the Eventbrite link for the next event (`https://www.eventbrite.com/e/...`) |
| `quantity` | tickets per order (max 4) |
| `ticket_name` | optional: part of the ticket type's name, if there's more than one type |
| `ntfy_topic` | optional: install the free **ntfy** app on your phone, subscribe to a hard-to-guess topic name, and put that name here to get a push notification |

## Every drop

```bash
./bot next           # shows when the next drop is
./bot run            # leave it running; it waits and then buys
```

If each drop is a new Eventbrite event, update `event_url` or pass it directly:
`./bot run --event-url https://www.eventbrite.com/e/...`

When the alert fires, go to the Chrome window and pay with Apple Pay. Eventbrite only holds the
tickets for a few minutes.

Other commands: `./bot test-alert` checks that notifications work. `./bot run --now` starts
refreshing right away, which is handy for a test run on an event that's already on sale.
Stop before paying if you don't want to buy.

## If something goes wrong

- **CAPTCHA or waiting room:** the bot alerts you and pauses. Solve it in the browser, then press Enter in the terminal.
- **It couldn't set the quantity or find Checkout:** Eventbrite changes its page layout sometimes. The bot still
  alerts you with the page open, so you can finish by hand. Then tell me what the page looked like and I'll fix it.
- Keep your Mac plugged in, and don't close the lid while it waits.

Heads up: Eventbrite's terms don't allow automated purchasing, and they can cancel orders or restrict accounts.
This bot buys the normal per-person amount on your own account and refreshes at a gentle rate. Use it at your own risk.
