import os
from playwright.sync_api import sync_playwright

mock_file = os.path.abspath("mock_groww.html").replace(os.sep, "/")
test_js = """
(() => {
    const qty = "10";
    const sl = "448.82";
    console.log("Starting auto-fill test...");

    // 1. Find Qty input
    const allNodes = document.querySelectorAll('*');
    let qtyInput = null;

    for (const node of allNodes) {
        if (node.children.length === 0) {
            const t = (node.textContent || '').trim().toUpperCase();
            if (t === 'QTY NSE' || t === 'QTY BSE' || t.startsWith('QTY')) {
                let parent = node.parentElement;
                for (let d = 0; d < 5 && parent; d++) {
                    const inp = parent.querySelector('input');
                    if (inp && inp.id !== 'globalSearch23') {
                        qtyInput = inp;
                        break;
                    }
                    parent = parent.parentElement;
                }
            }
        }
        if (qtyInput) break;
    }

    if (!qtyInput) {
        const inputs = Array.from(document.querySelectorAll('input')).filter(i => !i.placeholder?.toLowerCase().includes('search') && i.id !== 'globalSearch23');
        qtyInput = inputs[0];
    }

    // Set Quantity
    if (qtyInput) {
        qtyInput.focus();
        qtyInput.value = qty;
        qtyInput.dispatchEvent(new Event('input', { bubbles: true }));
        qtyInput.dispatchEvent(new Event('change', { bubbles: true }));
        qtyInput.blur();
        console.log("Qty input successfully filled with:", qty);
    }

    // 2. Click Add Stoploss
    for (const node of allNodes) {
        if (node.children.length === 0) {
            const t = (node.textContent || '').trim().toLowerCase();
            if (t.includes('add stoploss') || t.includes('stoploss / target')) {
                node.click();
                if (node.parentElement) node.parentElement.click();
                console.log("Add Stoploss clicked!");
                break;
            }
        }
    }

    // 3. Set Stop Loss input
    const inputs = Array.from(document.querySelectorAll('input')).filter(i => !i.placeholder?.toLowerCase().includes('search') && i.id !== 'globalSearch23');
    if (inputs.length >= 2) {
        const slInput = inputs[1];
        slInput.focus();
        slInput.value = sl;
        slInput.dispatchEvent(new Event('input', { bubbles: true }));
        slInput.dispatchEvent(new Event('change', { bubbles: true }));
        slInput.blur();
        console.log("Stop Loss filled with:", sl);
    }
    return true;
})()
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.on("console", lambda msg: print(f"[Console] {msg.text}"))
    page.goto(f"file:///{mock_file}")

    # Execute injection
    res = page.evaluate(test_js)
    page.wait_for_timeout(500)

    qty_val = page.eval_on_selector("#qty-input", "el => el.value")
    sl_val = page.eval_on_selector("#sl-input", "el => el.value")
    sl_display = page.eval_on_selector("#sl-container", "el => el.style.display")

    print("=" * 60)
    print(f"VERIFIED RESULT: Qty Value   = '{qty_val}' (Expected: '10')")
    print(f"VERIFIED RESULT: SL Display  = '{sl_display}' (Expected: 'flex')")
    print(f"VERIFIED RESULT: SL Value    = '{sl_val}' (Expected: '448.82')")
    print("=" * 60)
    browser.close()
