// One step of the ticket flow, run inside your Safari tab by ticketbot.py (several times a second).
// It looks at the page, does the next thing, and returns what it did:
//   "no-button"      tickets aren't on sale yet (no Get tickets button)
//   "clicked-get"    clicked Get tickets
//   "opening"        waiting for the ticket options to open
//   "qty:N"          chose N tickets
//   "checkout:N"     clicked Check out with N tickets - done
//   "no-checkout"    tickets chosen but no Check out button found yet
//   "captcha"        Eventbrite is asking you to prove you're human
//   "queue"          you're in Eventbrite's waiting room - wait, don't refresh
// With __CAPTCHA_ONLY__ true it only checks for a CAPTCHA and returns "captcha" or "ok".
(function () {
  const want = __WANT__;
  const state = (window.__ticketbot = window.__ticketbot || {});

  // The ticket options (and a CAPTCHA over them) often live in iframes on the same site,
  // sometimes nested, so look through every level we're allowed to read.
  const docs = [];
  const collect = (d) => {
    docs.push(d);
    for (const f of d.querySelectorAll("iframe")) {
      try { if (f.contentDocument) collect(f.contentDocument); } catch (e) { /* other site */ }
    }
  };
  collect(document);
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== "hidden";
  };
  const find = (sel) => docs.flatMap((d) => [...d.querySelectorAll(sel)]).filter(visible);
  const label = (el) => (el.getAttribute("aria-label") || el.innerText || "").trim();
  const enabled = (el) => !el.disabled && el.getAttribute("aria-disabled") !== "true";
  const pageText = docs.map((d) => (d.body ? d.body.innerText : "")).join("\n");

  if (find("iframe[src*='captcha'], iframe[title*='aptcha']").length ||
      /unusual activity|verify you are human/i.test(pageText)) {
    return "captcha";
  }
  if (__CAPTCHA_ONLY__) return "ok";

  // Eventbrite's waiting room on busy drops. Refreshing here would lose your place in line.
  if (/waiting room|you('|’| a)re (now )?in line|place in line|in the queue|you are in the queue/i.test(pageText)) {
    return "queue";
  }

  // Ticket quantity controls: a dropdown or a "+" button per ticket type.
  const selects = find("select").filter(enabled);
  const plus = find("button").filter((b) => /increase|add one|^\+$/i.test(label(b)));
  if (selects.length || plus.length) {
    if (state.qty === undefined) {
      // Max out: take as many as allowed from the first ticket type that isn't sold out,
      // then top up from the next ones until we reach `want`.
      let total = 0;
      for (const s of selects) {
        if (total >= want) break;
        const options = [...s.options].map((o) => parseInt(o.value, 10)).filter((v) => v >= 0 && v <= want - total);
        const best = Math.max(0, ...options);
        if (!best) continue;
        const setValue = Object.getOwnPropertyDescriptor(s.ownerDocument.defaultView.HTMLSelectElement.prototype, "value").set;
        setValue.call(s, String(best)); // works with React-controlled dropdowns
        s.dispatchEvent(new Event("input", { bubbles: true }));
        s.dispatchEvent(new Event("change", { bubbles: true }));
        total += best;
      }
      for (const b of plus) {
        while (total < want && enabled(b)) { b.click(); total++; }
      }
      state.qty = total;
      return "qty:" + total;
    }
    const checkout = find("button").find((b) =>
      /^\s*(check ?out|register|continue|reserve|place order)/i.test(label(b)) && enabled(b));
    if (checkout && state.qty > 0) {
      checkout.click();
      return "checkout:" + state.qty;
    }
    return "no-checkout";
  }

  const getTickets = find("button, a").find((b) =>
    /^\s*(get tickets|buy tickets|reserve( a spot)?|register|check availability)/i.test(label(b)));
  if (getTickets) {
    // Click again if nothing opened after 2 seconds (an early click can land before the page is ready).
    if (!state.clickedAt || Date.now() - state.clickedAt > 2000) {
      getTickets.click();
      state.clickedAt = Date.now();
      return "clicked-get";
    }
    return "opening";
  }
  return "no-button";
})();
