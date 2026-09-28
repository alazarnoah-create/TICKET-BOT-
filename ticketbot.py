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
SIGNIN_URL = "https://www.eventbrite.com/signin/"

DEFAULTS = {
    "event_url": "",
    "quantity": 4,
    "ticket_name": "",
    "drop_days": ["tuesday", "saturday"],
    "drop_time": "18:00",
    "start_early_seconds": 60,
    "poll_seconds": 2.0,
    "give_up_minutes": 20,
    "ntfy_topic": "",
}
MAX_QUANTITY = 4  # the per-order limit for these events
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

GET_TICKETS = re.compile(r"^\s*(get tickets|buy tickets|reserve( a spot)?|register|tickets)\s*$", re.I)
CHECKOUT = re.compile(r"^\s*(check ?out|register|continue|reserve|place order)\s*$", re.I)
INCREASE = re.compile(r"(increase|add one|plus|\+)", re.I)
NOT_YET = re.compile(r"(sales start|sales begin|on sale|not yet available|sold out|sales ended|unavailable)", re.I)
BLOCKED = re.compile(r"(captcha|verify you are human|waiting room|you are in line|queue)", re.I)


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
    kwargs = dict(user_data_dir=str(PROFILE_DIR), headless=bool(os.environ.get("TICKETBOT_HEADLESS")), viewport=None)
    if browser == "chrome":
        try:
            # Real Google Chrome: supports Apple Pay (scan the QR code with your iPhone).
            return pw.chromium.launch_persistent_context(channel="chrome", **kwargs)
        except PlaywrightError:
            log("Google Chrome not found, falling back to Playwright's Chromium.")
    return pw.chromium.launch_persistent_context(**kwargs)


def first_visible(locator, timeout=0):
    """Return the first visible, enabled match of a locator, or None."""
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


def set_quantity(scope, cfg):
    """Pick the ticket quantity. Returns the quantity chosen (0 if nothing was found)."""
    want = min(int(cfg["quantity"]), MAX_QUANTITY)
    rows = scope.locator("[data-testid*=ticket], [class*=ticket-card], li, [role=listitem]")
    if cfg["ticket_name"]:
        rows = rows.filter(has_text=re.compile(re.escape(cfg["ticket_name"]), re.I))
        container = rows.first if rows.count() else scope
    else:
        container = scope

    selects = container.locator("select")
    select = first_visible(selects, timeout=8000)
    if select:
        values = [v for v in select.locator("option").evaluate_all("os => os.map(o => o.value)") if v.isdigit()]
        best = max((int(v) for v in values if int(v) <= want), default=0)
        if best:
            select.select_option(str(best))
            return best

    plus = first_visible(container.get_by_role("button", name=INCREASE), timeout=3000)
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
    button = first_visible(page.get_by_role("button", name=GET_TICKETS)) or first_visible(
        page.get_by_role("link", name=GET_TICKETS)
    )
    if not button:
        return False
    log("Tickets are live - clicking.")
    button.click()

    scope = checkout_scope(page)
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


def run(cfg, args):
    if not cfg["event_url"]:
        sys.exit("Set event_url in config.json (or pass --event-url).")

    drop = datetime.now() if args.now else next_drop(cfg)
    log(f"Target drop: {drop:%A %d %b %H:%M}, {cfg['quantity']} ticket(s), {cfg['event_url']}")
    wait_until(drop - timedelta(seconds=cfg["start_early_seconds"]))

    with sync_playwright() as pw:
        ctx = open_browser(pw, args.browser)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(cfg["event_url"], wait_until="domcontentloaded")
        give_up = drop + timedelta(minutes=cfg["give_up_minutes"])

        done = False
        while not done and datetime.now() < give_up:
            try:
                if check_blocked(page, cfg):
                    input("Press Enter here once you're past it... ")
                done = try_buy(page, cfg)
            except PlaywrightError as exc:
                log(f"Hiccup: {exc.__class__.__name__}: {str(exc).splitlines()[0]}")
            if not done:
                time.sleep(cfg["poll_seconds"])
                page.reload(wait_until="domcontentloaded")

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
        page.goto(SIGNIN_URL)
        input("Log in to Eventbrite in the browser window, then press Enter here... ")
        ctx.close()
    log(f"Saved. Your login lives in {PROFILE_DIR}")


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
