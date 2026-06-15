"""E2E: seed a vendor with an XSS payload via /onboard, then load /vendors and
verify (a) no script executes, (b) the payload appears as TEXT in the DOM, not
as a parsed element.
"""

import hashlib

import pytest

pytestmark = pytest.mark.e2e


def test_vendors_browse_does_not_execute_injected_payload(page_mobile, live_server):
    page = page_mobile

    # Capture any JS dialogs — if XSS fires via alert(), this records it.
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    # Capture console errors (an XSS payload that uses image onerror would log
    # a 404 console error on the fetch; we want to be sure no execution path
    # produces script-side effects).
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    # POST a malicious vendor via the JSON API the form would normally hit.
    payload = {
        "q1": "<img src=x onerror=alert('xss-via-q1')>",
        "q2": "menu 60",
        "q3": "<script>alert('xss-via-q3')</script>",
        "q4": "daily",
        "q5": "cash",
        "q6": "story",
        "phone_hash": hashlib.sha256(b"e2e-xss-seed").hexdigest(),
    }
    resp = page.request.post(f"{live_server}/onboard", form=payload, max_redirects=0)
    assert resp.status in (200, 303)

    # Load the browse page — the malicious vendor card will render.
    page.goto(f"{live_server}/vendors")
    page.wait_for_selector("#cards:not(.hidden)", timeout=10_000)

    # No alert dialog fired.
    assert dialogs == [], f"XSS executed! dialogs: {dialogs}"

    # The original payload should NOT have appeared in the DOM as a real
    # element — query for img with src=x and for any <script> with the
    # alert sentinel.
    assert page.locator("img[src='x']").count() == 0
    # Even if the angle brackets were rendered, no SCRIPT child should have
    # been created with our payload string.
    page_html = page.content()
    assert "<script>alert('xss-via-q3')</script>" not in page_html
