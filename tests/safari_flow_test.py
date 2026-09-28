"""Runs the Safari flow (safari_step.js + safari_auto) against the mock pages, using a test
browser in place of Safari. Start the mock server first: python3 tests/mock/slowserver.py"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ticketbot as t  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PAGES = ["stepper-event", "event", "tiers-event", "slow-event", "captcha-event"]

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for name in PAGES:
        page = browser.new_page()
        t.goto(page, f"http://localhost:8766/e/{name}.html")
        t.alert = lambda title, msg, topic="": t.log(f"ALERT {title}: {msg}")
        cfg = dict(t.DEFAULTS, button_wait_seconds=3)
        give_up = datetime.now() + timedelta(seconds=25 if name != "captcha-event" else 12)

        def run_js(code, page=page):
            try:
                return page.evaluate(code)
            except Exception as exc:  # like Safari: a failed script comes back as an error
                raise RuntimeError(str(exc)) from exc

        ok = t.safari_auto(cfg, run_js, lambda: t.goto(page), give_up)
        titles = [f.title() for f in page.frames if f.title().startswith("ORDER")]
        print(f"== {name}: at checkout={ok} order={titles}\n")
        page.close()
    browser.close()
