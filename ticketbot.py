#!/usr/bin/env python3
"""Eventbrite drop helper: waits for the Tue/Sat 6 PM drop, grabs your tickets,
and gets you to the payment step so you can confirm with Apple Pay.

You log in yourself once (`python ticketbot.py login`); the login is kept in a
local browser profile, so no password is ever stored by this script.
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
# A date or time slot, e.g. "Tue, Sep 29", "September 29", "29", "10:00 AM".
DATE_OR_TIME = re.compile(
    r"\b(mon|tue|wed|thu|fri|sat|sun|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b|\b\d{1,2}:\d{2}\s*(am|pm)?\b",
    re.I,
)
UNAVAILABLE = re.compile(r"(sold out|unavailable|sales ended|full)", re.I)
SIGN_IN = re.compile(r"^\s*(sign in|log in)\s*$", re.I)
INCREASE = re.compile(r"(increase|add one|plus|\+)", re.I)
BLOCKED = re.compile(r"(captcha|verify you are human|waiting room|you are (now )?in line)", re.I)


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
        script = f'display notification {json.dumps(message)} with title {json.dumps(title)} sound name "Glass"'
        subprocess.run(["osascript", "-e", script], check=False)
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


def checkout_scope(page, timeout_ms=15000):
    """Eventbrite opens checkout in a modal iframe or on its own page; return whichever appears."""
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        for frame in page.frames:
            if frame is page.main_frame:
                continue
            if "checkout" in (frame.url or "") or "tickets" in (frame.name or ""):
                return frame
        if "checkout" in page.url or page.locator("select, [data-testid*=quantity]").count():
            return page
        page.wait_for_timeout(250)
    return page


def check_blocked(page, cfg):
    text = page.locator("body").inner_text(timeout=2000)
    if BLOCKED.search(text) or page.locator("iframe[src*=captcha], iframe[title*=captcha i]").count():
        alert("Action needed", "CAPTCHA or queue on screen - complete it in the browser.", cfg["ntfy_topic"])
        return True
    return False


def has_quantity_control(scope):
    return first_visible(scope.locator("select").or_(scope.get_by_role("button", name=INCREASE))) is not None


def pick_nearest_date(scope):
    """For events with several dates: click the first (soonest) available date or time slot.
    Returns its label, or None if there is nothing to pick."""
    options = scope.get_by_role("button").or_(scope.get_by_role("radio")).or_(scope.get_by_role("option"))
    options = options.filter(visible=True)
    for i in range(options.count()):
        opt = options.nth(i)
        try:
            label = (opt.get_attribute("aria-label") or opt.inner_text()).strip()
            if not DATE_OR_TIME.search(label) or UNAVAILABLE.search(label):
                continue
            if not opt.is_enabled() or opt.get_attribute("aria-disabled") == "true":
                continue
            opt.click()
            return label.replace("\n", " ")
        except PlaywrightError:
            continue
    return None


def set_quantity(scope, cfg):
    """Pick the ticket quantity. Returns the quantity chosen (0 if nothing was found)."""
    want = min(int(cfg["quantity"]), MAX_QUANTITY)
    rows = scope.locator("[data-testid*=ticket], [class*=ticket-card], li, [role=listitem]")
    if cfg["ticket_name"]:
        rows = rows.filter(has_text=re.compile(re.escape(cfg["ticket_name"]), re.I))
        container = rows.first if rows.count() else scope
    else:
        container = scope

    # Wait for either kind of quantity control (dropdown or + button), whichever Eventbrite shows.
    first_visible(container.locator("select").or_(container.get_by_role("button", name=INCREASE)), timeout=8000)
    select = first_visible(container.locator("select"))
    if select:
        values = [v for v in select.locator("option").evaluate_all("os => os.map(o => o.value)") if v.isdigit()]
        best = max((int(v) for v in values if int(v) <= want), default=0)
        if best:
            select.select_option(str(best))
            return best

    plus = first_visible(container.get_by_role("button", name=INCREASE))
    if plus:
        chosen = 0
        for _ in range(want):
            if not plus.is_enabled():
                break
            plus.click()
            chosen += 1
        return chosen
    return 0


def try_buy(page, cfg):
    """One attempt at the event page. Returns True once tickets are in checkout."""
    # The button is drawn by JavaScript a moment after the page loads, so give it time to appear.
    button = first_visible(
        page.get_by_role("button", name=GET_TICKETS).or_(page.get_by_role("link", name=GET_TICKETS)),
        timeout=cfg["button_wait_seconds"] * 1000,
    )
    if not button:
        return False
    log("Tickets are live - clicking.")
    button.click()

    scope = checkout_scope(page)
    # Events with several dates show a date (and maybe time) picker before the quantity.
    for _ in range(3):
        if has_quantity_control(scope):
            break
        page.wait_for_timeout(700)
        if has_quantity_control(scope):
            break
        picked = pick_nearest_date(scope)
        if not picked:
            break
        log(f"Picked the nearest available date: {picked}")
        page.wait_for_timeout(500)
        scope = checkout_scope(page, timeout_ms=5000)
    qty = set_quantity(scope, cfg)
    if not qty:
        alert("Tickets are live!", "Couldn't set the quantity automatically - pick it in the browser NOW.", cfg["ntfy_topic"])
        return True
    log(f"Selected {qty} ticket(s).")

    go = first_visible(scope.get_by_role("button", name=CHECKOUT), timeout=5000)
    if go:
        go.click()
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
    r = sub.add_parser("run", help="wait for the next drop and buy")
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
