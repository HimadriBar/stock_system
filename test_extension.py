import os
from playwright.sync_api import sync_playwright

with open("groww_extension/content.js", "r", encoding="utf-8") as f:
    js_code = f.read()

mock_file = os.path.abspath("mock_groww.html").replace(os.sep, "/")
test_url = f"file:///{mock_file}?quant_action=buy&qty=10&name=BHEL&sl=448.82&target=469.31&amount=4549"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.on("console", lambda msg: print(f"[Browser Console] {msg.type}: {msg.text}"))

    print(f"Navigating to: {test_url}")
    page.goto(test_url)

    # Inject the exact content.js code
    page.evaluate(js_code)
    page.wait_for_timeout(2000)

    qty_input = page.query_selector("#qty-input")
    val = qty_input.input_value() if qty_input else None
    print(f"--> Result Quantity value: '{val}'")

    sl_input = page.query_selector("#sl-input")
    sl_val = sl_input.input_value() if sl_input else None
    print(f"--> Result SL value: '{sl_val}'")

    browser.close()
