#!/usr/bin/env python3
"""Eventbrite drop helper for the Tue/Sat 6 PM drop.

`run` (default): at the drop, opens the event in your own logged-in Safari, clicks Get
tickets, maxes out the quantity and clicks Check out; you pay with Apple Pay (Touch ID).

`auto`: the older fully automated mode in a separate Chrome window (log in with `login`).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"
PROFILE_DIR = Path(os.environ.get("TICKETBOT_PROFILE", Path.home() / ".ticketbot" / "browser-profile"))
# Eventbrite's login cookie is deleted when the browser closes, so we save it here and restore it.
LOGIN_FILE = PROFILE_DIR.parent / "eventbrite-login.json"
SIGNIN_URL = "https://www.eventbrite.ca/signin/"

DEFAULTS = {
    "organizer_url": "https://www.eventbrite.ca/o/trinity-social-38111092183",
    "event_keyword": "dollar beer",
    "event_url": "",
    "quantity": 4,
    "ticket_name": "",
    "drop_days": ["tuesday", "saturday"],
    "drop_time": "18:00",
    "start_early_seconds": 60,
    "poll_seconds": 1.0,
    "button_wait_seconds": 8,
    "give_up_minutes": 20,
    "ntfy_topic": "",
}
MAX_QUANTITY = 4  # the per-order limit for these events
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

GET_TICKETS = re.compile(r"^\s*(get tickets|buy tickets|reserve( a spot)?|register|check availability|select (a )?date)", re.I)
CHECKOUT = re.compile(r"^\s*(check ?out|register|continue|reserve|place order)", re.I)
TIME_SLOT = re.compile(r"^\s*\d{1,2}:\d{2}\s*(am|pm)?\s*$", re.I)
UNAVAILABLE = re.compile(r"(sold out|unavailable|sales ended|full)", re.I)
SIGN_IN = re.compile(r"^\s*(sign in|log in)\s*$", re.I)
INCREASE = re.compile(r"(increase|add one|plus|\+)", re.I)
BLOCKED = re.compile(r"(captcha|verify you are human|unusual activity|waiting room|you are (now )?in line)", re.I)


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def load_config(path):
    cfg = dict(DEFAULTS)
    if path.exists():
        cfg.update(json.loads(path.read_text()))
    return cfg


# ---------------------------------------------------------------- alerts

def alert(title, message, ntfy_topic=""):
    """Loud alert: console, macOS notification + sound, optional phone push."""
    log(f"*** {title}: {message}")
    if sys.platform == "darwin":
        # A pop-up box with an OK button (a notification would open Script Editor when clicked).
        script = f'display alert {json.dumps(title)} message {json.dumps(message)} giving up after 120'
        subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
        subprocess.Popen(["say", title])
    else:
        print("\a", end="", flush=True)
    if ntfy_topic:
        try:
            req = urllib.request.Request(
                f"https://ntfy.sh/{ntfy_topic}",
                data=message.encode(),
                headers={"Title": title, "Priority": "urgent"},
            )
            urllib.request.urlopen(req, timeout=5)
        except OSError as exc:
            log(f"Phone push failed: {exc}")


# ---------------------------------------------------------------- timing

def next_drop(cfg, now=None):
    """The drop currently in progress (within give_up_minutes) or the next one."""
    now = now or datetime.now()
    hour, minute = map(int, cfg["drop_time"].split(":"))
    weekdays = {DAYS.index(d.lower()) for d in cfg["drop_days"]}
    window = timedelta(minutes=cfg["give_up_minutes"])
    for offset in range(8):
        day = now + timedelta(days=offset)
        drop = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if drop.weekday() in weekdays and drop + window > now:
            return drop
    raise ValueError("drop_days is empty or invalid")


def wait_until(target):
    while True:
        remaining = (target - datetime.now()).total_seconds()
        if remaining <= 0:
            return
        if remaining > 60:
            log(f"Waiting {timedelta(seconds=int(remaining))} until {target:%a %H:%M:%S}...")
        time.sleep(min(remaining, 300 if remaining > 600 else 30 if remaining > 60 else 1))


# ---------------------------------------------------------------- browser

def open_browser(pw, browser):
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    kwargs = dict(
        user_data_dir=str(PROFILE_DIR),
        headless=bool(os.environ.get("TICKETBOT_HEADLESS")),
        viewport=None,
        chromium_sandbox=sys.platform == "darwin",
    )
    ctx = None
    if browser == "chrome":
        try:
            # Real Google Chrome: supports Apple Pay (scan the QR code with your iPhone).
            ctx = pw.chromium.launch_persistent_context(channel="chrome", **kwargs)
        except PlaywrightError:
            log("Google Chrome not found, falling back to Playwright's Chromium.")
    ctx = ctx or pw.chromium.launch_persistent_context(**kwargs)
    if LOGIN_FILE.exists():
        ctx.add_cookies(json.loads(LOGIN_FILE.read_text())["cookies"])
    return ctx


def save_login(ctx):
    LOGIN_FILE.write_text(json.dumps(ctx.storage_state()))
    LOGIN_FILE.chmod(0o600)


def looks_logged_out(page):
    return first_visible(page.get_by_role("link", name=SIGN_IN).or_(page.get_by_role("button", name=SIGN_IN))) is not None


def goto(page, url=None):
    """Open (or, with no url, reload) a page without waiting for it to fully finish loading.
    Eventbrite pages keep loading trackers in the background and can take ages to 'finish',
    but they're usable long before that, so a slow load is fine - we carry on."""
    try:
        if url:
            page.goto(url, wait_until="commit", timeout=30000)
        else:
            page.reload(wait_until="commit", timeout=30000)
        page.wait_for_load_state("domcontentloaded", timeout=15000)
    except PlaywrightTimeout:
        log("Page is loading slowly - carrying on anyway.")
    except PlaywrightError as exc:
        log(f"Couldn't load the page ({str(exc).splitlines()[0]}) - will retry.")


def first_visible(locator, timeout=0):
    """Return the first visible, enabled match of a locator, or None. Waits up to timeout ms."""
    locator = locator.filter(visible=True)
    if timeout:
        try:
            locator.first.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeout:
            return None
    for i in range(locator.count()):
        item = locator.nth(i)
        try:
            if item.is_visible() and item.is_enabled():
                return item
        except PlaywrightError:
            continue
    return None


# The "Choose options" popup, found from its heading in case it isn't marked up as a dialog.
OPTIONS_POPUP = (
    "xpath=//*[normalize-space(text())='Choose options' or normalize-space(text())='Select tickets']"
    "/ancestor::*[@role='dialog' or @aria-modal='true' or contains(@class,'modal') or contains(@class,'Modal')][1]"
)


def checkout_scope(page, timeout_ms=4000):
    """Where the ticket options appear: a popup in the page ("Choose options"), an embedded
    checkout iframe, or a separate checkout page. Returns whichever shows up first, or None."""
    popup = page.locator("[role=dialog], [aria-modal=true]").or_(page.locator(OPTIONS_POPUP)).filter(visible=True)
    heading = page.get_by_text(re.compile(r"^\s*(choose options|select tickets)\s*$", re.I)).filter(visible=True)
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        for frame in page.frames:
            if frame is not page.main_frame and "checkout" in (frame.url or ""):
                return frame
        if popup.count():
            return popup.last
        if "checkout" in page.url or heading.count():
            return page
        page.wait_for_timeout(100)
    return None


def open_options(page, cfg):
    """Click the ticket button and make sure the ticket options actually open. A click that lands
    before the page is ready does nothing, so click again (trying each matching button)."""
    buttons = page.get_by_role("button", name=GET_TICKETS).or_(page.get_by_role("link", name=GET_TICKETS))
    if not first_visible(buttons, timeout=cfg["button_wait_seconds"] * 1000):
        return None
    log("Tickets are live - clicking.")
    buttons = buttons.filter(visible=True)
    for attempt in range(3):
        try:
            buttons.nth(attempt % max(buttons.count(), 1)).click(timeout=3000)
        except PlaywrightError:
            pass
        scope = checkout_scope(page, timeout_ms=2000 + 1500 * attempt)
        if scope is not None:
            return scope
        log("The ticket options didn't open yet - clicking again.")
    return page  # carry on and let the checks below report what's on screen


def captcha_on_screen(page):
    """True if a CAPTCHA challenge, 'unusual activity' notice or queue is showing.
    (Eventbrite loads hCaptcha invisibly on every page, so only a visible one counts.)"""
    for frame in page.frames:  # the CAPTCHA can sit inside the ticket options' own frame
        try:
            if frame.locator("iframe[src*=captcha], iframe[title*=captcha i]").filter(visible=True).count():
                return True
            if BLOCKED.search(frame.locator("body").inner_text(timeout=1000)):
                return True
        except PlaywrightError:
            continue
    return False


def check_blocked(page, cfg):
    if captcha_on_screen(page):
        alert("Action needed", "CAPTCHA or queue on screen - complete it in the browser.", cfg["ntfy_topic"])
        return True
    return False


def has_quantity_control(scope):
    return first_visible(scope.locator("select").or_(scope.get_by_role("button", name=INCREASE))) is not None


# Given a time label, find the whole slot box around it (stopping before the list that holds
# several slots) and report its text and whether it's disabled.
SLOT_INFO_JS = """el => {
  let box = el;
  for (let i = 0; i < 5 && box.parentElement; i++) {
    const up = box.parentElement;
    if ((up.innerText.match(/\\d{1,2}:\\d{2}/g) || []).length > 1) break;
    box = up;
  }
  const disabled = !!box.closest('[aria-disabled=true], [disabled], [data-disabled=true]');
  return {text: box.innerText, disabled};
}"""


def pick_time_slot(scope):
    """On multi-date events Eventbrite preselects the nearest available date, then lists time
    slots. Click the earliest slot that isn't sold out. Returns its label, or None."""
    slots = scope.get_by_text(TIME_SLOT).filter(visible=True)
    for i in range(slots.count()):
        slot = slots.nth(i)
        try:
            info = slot.evaluate(SLOT_INFO_JS)
            label = " ".join(info["text"].split())
            if info["disabled"] or UNAVAILABLE.search(label):
                log(f"Skipping {label}")
                continue
            slot.click(timeout=3000)
            return label
        except PlaywrightError:
            continue
    return None


def set_quantity(scope, cfg):
    """Max out the order: take as many tickets as allowed from the first ticket type that isn't
    sold out, and if it can't cover the full amount, top up from the next available types.
    Returns the total number of tickets chosen (0 if no ticket controls were found)."""
    want = min(int(cfg["quantity"]), MAX_QUANTITY)
    container = scope
    if cfg["ticket_name"]:
        rows = scope.locator("[data-testid*=ticket], [class*=ticket-card], li, [role=listitem]")
        rows = rows.filter(has_text=re.compile(re.escape(cfg["ticket_name"]), re.I))
        container = rows.first if rows.count() else scope

    # One control per ticket type, top to bottom: a dropdown or a "+" button.
    controls = container.locator("select").or_(container.get_by_role("button", name=INCREASE))
    first_visible(controls, timeout=8000)
    controls = controls.filter(visible=True)
    total = 0
    for i in range(controls.count()):
        if total >= want:
            break
        control = controls.nth(i)
        try:
            if not control.is_enabled():
                continue  # sold out
            if control.evaluate("e => e.tagName") == "SELECT":
                values = control.locator("option").evaluate_all("os => os.map(o => o.value)")
                best = max((int(v) for v in values if v.isdigit() and int(v) <= want - total), default=0)
                if best:
                    control.select_option(str(best))
                    total += best
            else:
                while total < want and control.is_enabled():
                    control.click()
                    total += 1
        except PlaywrightError:
            continue
    return total


def try_buy(page, cfg):
    """One attempt at the event page. Returns True once tickets are in checkout."""
    # The button is drawn by JavaScript a moment after the page loads, so give it time to appear.
    scope = open_options(page, cfg)
    if scope is None:
        return False
    # Multi-date events ("Choose options"): the nearest date is preselected, pick a time slot.
    options = scope.get_by_text(TIME_SLOT).or_(scope.locator("select")).or_(scope.get_by_role("button", name=INCREASE))
    first_visible(options, timeout=5000)
    if not has_quantity_control(scope):
        picked = pick_time_slot(scope)
        if picked:
            log(f"Picked the earliest available time: {picked}")
    qty = set_quantity(scope, cfg)
    if not qty:
        log(f"Couldn't find the ticket count. Buttons in the popup: {visible_buttons(scope)}")
        alert("Tickets are live!", "Couldn't set the quantity automatically - pick it in the browser NOW.", cfg["ntfy_topic"])
        return True
    log(f"Selected {qty} ticket(s).")

    go = first_visible(scope.get_by_role("button", name=CHECKOUT), timeout=5000)
    if go:
        go.click()
        # Eventbrite may ask you to prove you're human at this point. That's for you to solve.
        deadline = time.time() + 2
        while time.time() < deadline and not captcha_on_screen(page):
            page.wait_for_timeout(250)
        if captcha_on_screen(page):
            alert("Solve the CAPTCHA now!", f"{qty} ticket(s) chosen - Eventbrite wants you to verify. "
                  "Solve it in the browser, then pay with Apple Pay.", cfg["ntfy_topic"])
        else:
            alert("Tickets in your cart!", f"{qty} ticket(s) held - pay with Apple Pay in the browser now.", cfg["ntfy_topic"])
    else:
        alert("Tickets selected", f"{qty} ticket(s) chosen - click Checkout in the browser now.", cfg["ntfy_topic"])
    return True


def date_pattern(day):
    """Matches how Eventbrite writes the date: "Sept 29", "Sep 29", "Tue, Sep 29", "September 29"."""
    return re.compile(rf"\b{day:%b}[a-z]*\.?\s+0?{day.day}\b", re.I)


def find_event(page, cfg, drop):
    """Look on the organizer page for this drop's event. Returns its URL or None."""
    goto(page, cfg["organizer_url"])
    page.wait_for_timeout(1500)  # the event list is rendered by JavaScript
    links = page.locator("a[href*='/e/']").evaluate_all(
        """els => els.map(a => [a.href.split('?')[0],
             [a.getAttribute('aria-label'), a.innerText,
              a.parentElement && a.parentElement.parentElement && a.parentElement.parentElement.innerText]
             .filter(Boolean).join(' ')])"""
    )
    return choose_event(links, cfg, drop)


def choose_event(links, cfg, drop):
    """From (url, text) pairs, pick this drop's event: the keyword plus the drop's date."""
    keyword = re.compile(re.escape(cfg["event_keyword"]), re.I)
    events = {}
    for href, text in links:
        if keyword.search(text) or keyword.search(href.replace("-", " ")):
            events[href] = events.get(href, "") + " " + text
    on_date = date_pattern(drop)
    dated = [h for h, t in events.items() if on_date.search(t) or on_date.search(h.replace("-", " "))]
    if dated:
        return dated[0]
    # Event names normally include the date; if none do, fall back to the first upcoming one
    # once the drop has started, so a naming change doesn't make us miss it.
    if events and datetime.now() >= drop + timedelta(minutes=2):
        return next(iter(events))
    return None


# ---------------------------------------------------------------- Safari mode

EVENT_LINK = re.compile(r"https://www\.eventbrite\.[a-z.]+/e/[a-z0-9-]+-\d+", re.I)


def find_event_http(cfg, drop):
    """Read the organizer page (one plain request, no browser) and pick this drop's event."""
    try:
        req = urllib.request.Request(cfg["organizer_url"], headers={"User-Agent": "ticketbot/1.0 (personal use)"})
        html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "replace")
    except OSError as exc:
        log(f"Couldn't read the organizer page ({exc}).")
        return None
    links = [(url, "") for url in dict.fromkeys(EVENT_LINK.findall(html))]
    return choose_event(links, cfg, drop)


STEP_JS = (HERE / "safari_step.js").read_text()

# Runs JavaScript in Safari's front tab. Needs Safari > Develop > "Allow JavaScript from Apple Events".
JXA_RUN = """function run(argv) {
  const safari = Application('Safari');
  return String(safari.doJavaScript(argv[0], {in: safari.windows[0].currentTab()}));
}"""


class SafariNotAllowed(Exception):
    pass


def safari_js(code):
    """Run JavaScript in the front Safari tab and return its result as text."""
    out = subprocess.run(["osascript", "-l", "JavaScript", "-e", JXA_RUN, code],
                         capture_output=True, text=True, timeout=15)
    if out.returncode:
        err = out.stderr.strip()
        if "Allow JavaScript from Apple Events" in err or "-1743" in err or "not allowed" in err.lower():
            raise SafariNotAllowed(err)
        raise RuntimeError(err or "osascript failed")
    return out.stdout.strip()


def safari_auto(cfg, run_js, reload, give_up):
    """Drive the open event page: click Get tickets, max out the quantity, click Check out.
    run_js runs JavaScript in the page; reload refreshes it. Returns True once at checkout."""
    want = str(min(int(cfg["quantity"]), MAX_QUANTITY))
    step = STEP_JS.replace("__WANT__", want).replace("__CAPTCHA_ONLY__", "false")
    captcha_check = STEP_JS.replace("__WANT__", want).replace("__CAPTCHA_ONLY__", "true")
    last, since, captcha_alerted = None, time.time(), False
    while datetime.now() < give_up:
        try:
            status = run_js(step)
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            status = f"error: {str(exc).splitlines()[0] if str(exc) else exc}"
        if status != last:
            log(f"Safari: {status}")
            last, since = status, time.time()
        if status.startswith("checkout:"):
            qty = status.split(":")[1]
            # Eventbrite may ask you to prove you're human right after Check out. That's for you to solve.
            captcha, deadline = False, time.time() + 2.5
            while not captcha and time.time() < deadline:
                time.sleep(0.3)
                try:
                    captcha = run_js(captcha_check) == "captcha"
                except (RuntimeError, subprocess.TimeoutExpired):
                    pass
            if captcha:
                alert("Solve the CAPTCHA now!", f"{qty} ticket(s) chosen - solve the CAPTCHA in Safari, "
                      "then pay with Apple Pay.", cfg["ntfy_topic"])
            else:
                alert("Tickets in your cart!", f"{qty} ticket(s) - pay with Apple Pay in Safari now (Touch ID).", cfg["ntfy_topic"])
            return True
        if status == "captcha":
            if not captcha_alerted:
                alert("Solve the CAPTCHA now!", "Eventbrite wants you to verify - solve it in Safari. "
                      "The bot carries on after.", cfg["ntfy_topic"])
                captcha_alerted = True
        elif status in ("no-button", "") or status.startswith("error"):
            # Not on sale yet: give the page a few seconds to draw the button, then refresh.
            if time.time() - since > cfg["button_wait_seconds"]:
                reload()
                last = None
        elif status == "no-checkout" and time.time() - since > 10:
            alert("Tickets selected", "Click Check out in Safari now, then pay with Apple Pay.", cfg["ntfy_topic"])
            return True
        time.sleep(0.3)
    alert("No luck", "Tickets never became available in time.", cfg["ntfy_topic"])
    return False


def open_in_safari(url):
    log(f"Opening in Safari: {url}")
    if sys.platform == "darwin":
        subprocess.run(["open", "-a", "Safari", url], check=False)


def safari(cfg, args):
    """Open the event in your own Safari right at the drop and alert you to buy."""
    drop = datetime.now() if args.now else next_drop(cfg)
    log(f"Target drop: {drop:%A %d %b %H:%M}. Safari will open the event then and grab your tickets.")
    heads_up = drop - timedelta(minutes=2)

    wait_until(heads_up)
    url = cfg["event_url"] or find_event_http(cfg, drop)
    if not args.now:
        open_in_safari(url or cfg["organizer_url"])
        alert("2 minutes to go", "Safari has the event open. Check you're logged in to Eventbrite.", cfg["ntfy_topic"])

    wait_until(drop)
    # The event can be posted right at the drop, so keep checking for up to 2 minutes.
    deadline = datetime.now() + timedelta(minutes=2)
    while not url and datetime.now() < deadline:
        url = find_event_http(cfg, drop)
        if not url:
            time.sleep(5)
    if url and not args.manual:
        open_in_safari(url)
        time.sleep(1.5)
        give_up = datetime.now() + timedelta(minutes=cfg["give_up_minutes"])
        try:
            safari_auto(cfg, safari_js, lambda: safari_js("location.reload(); 'ok'"), give_up)
        except SafariNotAllowed:
            alert("GO NOW - buy it yourself!", "The bot isn't allowed to click in Safari yet (see Terminal). "
                  "Click Get tickets, choose 4, Check out, Apple Pay.", cfg["ntfy_topic"])
            log("To let the bot click for you next time: Safari > Settings > Advanced > tick "
                "'Show features for web developers', then in the Develop menu tick "
                "'Allow JavaScript from Apple Events'.")
    elif url:
        open_in_safari(url)
        alert("GO NOW!", "Click Get tickets, choose 4, Check out, pay with Apple Pay. "
              "No Get tickets button? Press Cmd+R.", cfg["ntfy_topic"])
    else:
        open_in_safari(cfg["organizer_url"])
        alert("GO NOW!", "Couldn't spot the event - click the newest Dollar Beers event in Safari.", cfg["ntfy_topic"])
    return 0


def visible_buttons(page):
    """Short list of button labels on the page, to help debug when the ticket button isn't found."""
    try:
        names = page.locator("button:visible, a[role=button]:visible").evaluate_all(
            "els => els.map(e => e.innerText.trim().split('\\n')[0]).filter(t => t && t.length < 40)"
        )
    except PlaywrightError:
        return "?"
    return ", ".join(dict.fromkeys(names)) or "none"


def run(cfg, args):
    if not (cfg["event_url"] or cfg["organizer_url"]):
        sys.exit("Set event_url or organizer_url in config.json (or pass --event-url).")

    drop = datetime.now() if args.now else next_drop(cfg)
    log(f"Target drop: {drop:%A %d %b %H:%M}, {cfg['quantity']} ticket(s)")
    wait_until(drop - timedelta(seconds=cfg["start_early_seconds"]))

    with sync_playwright() as pw:
        ctx = open_browser(pw, args.browser)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        give_up = drop + timedelta(minutes=cfg["give_up_minutes"])

        event_url = cfg["event_url"]
        while not event_url and datetime.now() < give_up:
            try:
                event_url = find_event(page, cfg, drop)
            except PlaywrightError as exc:
                log(f"Hiccup: {exc.__class__.__name__}: {str(exc).splitlines()[0]}")
            if not event_url:
                log(f"No {drop:%b %d} event posted yet, checking again...")
                time.sleep(max(cfg["poll_seconds"], 5))
        if not event_url:
            alert("No luck", "This drop's event never showed up on the organizer page.", cfg["ntfy_topic"])
            ctx.close()
            return 1
        log(f"Event: {event_url}")
        goto(page, event_url)
        page.wait_for_timeout(2000)
        if looks_logged_out(page):
            alert("Not logged in", "Eventbrite shows Sign in - stop with Ctrl+C and run: bash bot login", cfg["ntfy_topic"])

        done = False
        attempts = 0
        while not done and datetime.now() < give_up:
            attempts += 1
            try:
                if check_blocked(page, cfg):
                    input("Press Enter here once you're past it... ")
                done = try_buy(page, cfg)
            except PlaywrightError as exc:
                log(f"Hiccup: {exc.__class__.__name__}: {str(exc).splitlines()[0]}")
            if not done:
                if attempts % 5 == 1:
                    log(f"No ticket button yet. Buttons on the page: {visible_buttons(page)}")
                time.sleep(cfg["poll_seconds"])
                try:
                    goto(page)
                except PlaywrightError as exc:
                    log(f"Reload failed ({str(exc).splitlines()[0]}), retrying.")

        if not done:
            alert("No luck", "Tickets never became available in time.", cfg["ntfy_topic"])
        if args.keep_open:
            input("Browser stays open - finish checkout, then press Enter to close... ")
        ctx.close()
    return 0 if done else 1


def login(args):
    with sync_playwright() as pw:
        ctx = open_browser(pw, args.browser)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        goto(page, SIGNIN_URL)
        input("Log in to Eventbrite in the browser window, then press Enter here... ")
        save_login(ctx)
        goto(page, "https://www.eventbrite.ca/")
        page.wait_for_timeout(3000)
        logged_out = looks_logged_out(page)
        ctx.close()
    if logged_out:
        log("Hmm, Eventbrite still shows 'Sign in'. Run 'bash bot login' again and make sure you finish logging in.")
        return 1
    log(f"Saved. You're logged in (login kept in {LOGIN_FILE.parent}).")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--browser", choices=["chrome", "chromium"], default="chrome")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login", help="log in to Eventbrite once; the session is remembered")
    s = sub.add_parser("run", help="at the drop, open the event in Safari and alert you")
    s.add_argument("--event-url")
    s.add_argument("--now", action="store_true", help="don't wait for the drop; open it right away")
    s.add_argument("--manual", action="store_true", help="only open the page and alert; you do the clicking")
    r = sub.add_parser("auto", help="fully automated mode in a separate Chrome window")
    r.add_argument("--event-url")
    r.add_argument("--quantity", type=int)
    r.add_argument("--now", action="store_true", help="skip the wait and start polling immediately")
    r.add_argument("--no-keep-open", dest="keep_open", action="store_false")
    sub.add_parser("next", help="show when the next drop is")
    sub.add_parser("test-alert", help="fire a test notification")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.cmd == "run":
        if args.event_url:
            cfg["event_url"] = args.event_url
        return safari(cfg, args)
    if args.cmd == "auto":
        if args.event_url:
            cfg["event_url"] = args.event_url
        if args.quantity:
            cfg["quantity"] = args.quantity
        return run(cfg, args)
    if args.cmd == "login":
        return login(args)
    if args.cmd == "next":
        print(f"Next drop: {next_drop(cfg):%A %d %b %Y at %H:%M}")
        return 0
    if args.cmd == "test-alert":
        alert("Ticket bot", "Test alert - you'll get this when tickets are in your cart.", cfg["ntfy_topic"])
        return 0


if __name__ == "__main__":
    sys.exit(main())
