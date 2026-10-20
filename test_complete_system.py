"""
Comprehensive Self-Test Suite for Autonomous Stock Quantitative System
Validates:
1. Top 30 Watchlist & Groww Slugs integrity
2. Multi-factor Scanner & 90%+ Safe Percentage detection
3. Risk Manager position sizing under ₹5,000 budget
4. FastAPI live endpoints (/api/live-data, /api/notifications, /api/pending-order)
5. Groww Chrome Extension content script auto-fill on mock DOM via Playwright
"""

import os
import sys
import json
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add stock_system and web_app to sys.path
sys.path.append(os.path.abspath("stock_system"))
sys.path.append(os.path.abspath("web_app"))

def test_1_config_and_watchlist():
    print("\n[TEST 1] Validating Top 30 Watchlist & Groww Slugs...")
    from config import WATCHLIST, GROWW_SLUGS, HIGH_SAFETY_THRESHOLD, MAX_DAILY_INVESTMENT
    
    assert len(WATCHLIST) == 30, f"Expected 30 stocks in WATCHLIST, found {len(WATCHLIST)}"
    print(f"  ✓ WATCHLIST contains exactly {len(WATCHLIST)} stocks.")
    
    missing_slugs = [t for t in WATCHLIST if t not in GROWW_SLUGS]
    assert len(missing_slugs) == 0, f"Missing Groww slugs for: {missing_slugs}"
    print(f"  ✓ All 30 stocks have corresponding Groww slugs.")
    
    assert HIGH_SAFETY_THRESHOLD == 90.0, f"Expected HIGH_SAFETY_THRESHOLD=90.0, got {HIGH_SAFETY_THRESHOLD}"
    print(f"  ✓ High-Safety Threshold configured at {HIGH_SAFETY_THRESHOLD}%.")
    assert MAX_DAILY_INVESTMENT == 5000.0, f"Expected budget ₹5000, got {MAX_DAILY_INVESTMENT}"
    print(f"  ✓ Daily Capital Limit capped at ₹{MAX_DAILY_INVESTMENT}.")
    print("[PASS] Test 1: Config & Watchlist Integrity Passed!\n")

def test_2_scanner_and_high_safety():
    print("[TEST 2] Running Multi-Factor Market Scanner across Top 30 Stocks...")
    from analyzer import scan_all_stocks_advanced
    from config import WATCHLIST
    
    scored_stocks, market_regime = scan_all_stocks_advanced(WATCHLIST)
    print(f"  ✓ Scan completed. Market Regime: {market_regime['status']} ({market_regime['desc']})")
    print(f"  ✓ Total stocks passing criteria: {len(scored_stocks)}")
    
    high_safety_stocks = []
    for s in scored_stocks:
        a = s['analysis']
        assert 'safe_percentage' in a, f"Missing safe_percentage in analysis for {s['name']}"
        assert 'is_high_safety' in a, f"Missing is_high_safety in analysis for {s['name']}"
        assert 'price' in a, f"Missing price for {s['name']}"
        assert a['price'] <= 5000.0, f"Stock price ₹{a['price']} exceeds ₹5,000 limit for {s['name']}"
        
        if a['safe_percentage'] >= 90:
            assert a['is_high_safety'] is True, f"is_high_safety must be True for {s['name']} (score {a['safe_percentage']})"
            high_safety_stocks.append((s['name'], a['safe_percentage'], a['price']))
        
        print(f"    - {s['name']:<12} | Safe: {a['safe_percentage']}% | High-Safety Alert: {a['is_high_safety']} | Price: ₹{a['price']:.2f}")

    print(f"\n  ✓ Found {len(high_safety_stocks)} stock(s) with Safe Percentage >= 90%:")
    for name, safe_pct, price in high_safety_stocks:
        print(f"    --> 🚨 ALERT TRIGGERED: {name} ({safe_pct}% Safe, Price: ₹{price:.2f})")
    
    assert len(high_safety_stocks) > 0, "Expected at least 1 stock with Safe Percentage >= 90% (e.g. TECHM or TCS)"
    print("[PASS] Test 2: Multi-Factor Scanner & High Safety Detection Passed!\n")
    return scored_stocks

def test_3_risk_manager(scored_stocks):
    print("[TEST 3] Validating Risk Manager & ₹5,000 Capital Cap...")
    from risk_manager import generate_daily_trade_recommendations
    
    plans = generate_daily_trade_recommendations(scored_stocks, max_trades=3)
    assert len(plans) > 0, "Expected at least 1 trade plan generated"
    print(f"  ✓ Generated {len(plans)} prioritized trade execution plans:")
    
    for plan in plans:
        assert plan['invested_amount'] <= 5000.0, f"Invested amount ₹{plan['invested_amount']} exceeds ₹5000"
        assert plan['quantity'] >= 1, f"Quantity must be >= 1 share"
        assert plan['stop_loss'] < plan['entry_price'], "Stop Loss must be lower than entry price"
        assert plan['target_2'] > plan['entry_price'], "Target must be higher than entry price"
        assert 'safe_percentage' in plan, "Missing safe_percentage in plan"
        assert 'is_high_safety' in plan, "Missing is_high_safety in plan"
        
        print(f"    - BUY {plan['quantity']} shares of {plan['name']} @ ₹{plan['entry_price']:.2f} "
              f"| Total: ₹{plan['invested_amount']:.2f} | Safe: {plan['safe_percentage']}% | High-Safety: {plan['is_high_safety']}")
    
    print("[PASS] Test 3: Risk Allocation & Position Sizing Passed!\n")

def test_4_fastapi_endpoints():
    print("[TEST 4] Testing FastAPI Endpoints using httpx AsyncClient...")
    import asyncio
    import httpx
    from server import app, STATE, perform_deep_market_scan
    
    # Run deep scan to ensure STATE has live data
    perform_deep_market_scan()

    async def run_checks():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # 1. Test Dashboard HTML
            res_dash = await client.get("/")
            assert res_dash.status_code == 200
            assert "Autonomous Quant Terminal" in res_dash.text
            assert "Live Watchlist Technical Radar (Top 30 Stocks)" in res_dash.text
            assert "highSafetyBanner" in res_dash.text
            print("  ✓ GET / serves HTML dashboard with Top 30 stocks and High Safety alert banner.")
            
            # 2. Test Live Data API
            res_live = await client.get("/api/live-data")
            assert res_live.status_code == 200
            data = res_live.json()
            assert "watchlist_status" in data
            assert "high_safety_alerts" in data
            print(f"  ✓ GET /api/live-data returns {len(data['watchlist_status'])} stocks in watchlist radar.")
            print(f"  ✓ High-safety alerts in live data: {len(data['high_safety_alerts'])}")
            
            # 3. Test Notifications API
            res_notif = await client.get("/api/notifications")
            assert res_notif.status_code == 200
            notif = res_notif.json()
            assert "alerts" in notif
            assert notif["threshold"] == 90
            print(f"  ✓ GET /api/notifications returns {len(notif['alerts'])} alerts crossing 90% threshold.")
            for al in notif['alerts']:
                print(f"    --> Notification payload: {al['name']} - {al['safe_percentage']}% Safe @ ₹{al['price']}")
            
            # 4. Test Pending Order Dispatch Bridge
            test_order = {
                "ticker": "TCS.NS",
                "slug": "tata-consultancy-services-ltd",
                "name": "TCS",
                "quantity": 2,
                "entry_price": 2460.90,
                "stop_loss": 2420.00,
                "target_2": 2540.00,
                "invested_amount": 4921.80
            }
            res_dispatch = await client.post("/api/set-pending-order", json=test_order)
            assert res_dispatch.status_code == 200
            assert res_dispatch.json()["status"] == "dispatched"
            print("  ✓ POST /api/set-pending-order successfully dispatched order.")
            
            res_poll = await client.get("/api/pending-order")
            assert res_poll.status_code == 200
            polled = res_poll.json()
            assert polled["order"]["name"] == "TCS"
            assert polled["order"]["quantity"] == 2
            print("  ✓ GET /api/pending-order retrieved dispatched order successfully.")
            
            res_clear = await client.post("/api/clear-pending-order")
            assert res_clear.status_code == 200
            res_after = await client.get("/api/pending-order")
            assert res_after.json()["order"] is None
            print("  ✓ POST /api/clear-pending-order cleared pending order successfully.")
    
    asyncio.run(run_checks())
    print("[PASS] Test 4: All Backend Endpoints & Order Bridge Passed!\n")

def test_5_playwright_extension_autofill():
    print("[TEST 5] Testing Groww Extension content.js DOM injection in Playwright...")
    from playwright.sync_api import sync_playwright
    
    with open("groww_extension/content.js", "r", encoding="utf-8") as f:
        js_code = f.read()

    mock_file = os.path.abspath("mock_groww.html").replace(os.sep, "/")
    test_url = f"file:///{mock_file}?quant_action=buy&qty=14&name=TECHM&sl=1750.50&target=1830.00&amount=4900"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        console_logs = []
        page.on("console", lambda msg: console_logs.append(msg.text))
        
        page.goto(test_url)
        page.evaluate(js_code)
        page.wait_for_timeout(1000)
        
        # Verify Quantity was filled
        qty_val = page.eval_on_selector("#qty-input", "el => el.value")
        print(f"  ✓ Quantity input populated value: '{qty_val}' (Expected: '14')")
        assert qty_val == "14", f"Expected qty '14', got '{qty_val}'"
        
        # Verify Stop Loss was filled
        sl_val = page.eval_on_selector("#sl-input", "el => el.value")
        print(f"  ✓ Stop Loss input populated value: '{sl_val}' (Expected: '1750.50')")
        assert sl_val == "1750.50", f"Expected SL '1750.50', got '{sl_val}'"
        
        # Verify HUD was created
        hud_text = page.eval_on_selector("#quant-order-hud", "el => el.innerText")
        print(f"  ✓ Floating HUD notification active: '{hud_text.strip()}'")
        assert "14 Shares" in hud_text
        assert "TECHM" in hud_text
        
        # Verify Quick Fill button
        quick_btn = page.query_selector("#btn-quick-fill-quant")
        assert quick_btn is not None, "Quick Fill button was not injected"
        print(f"  ✓ Quick Fill floating button injected: '{quick_btn.inner_text()}'")
        
        browser.close()

    print("[PASS] Test 5: Browser Extension Auto-Fill & DOM Manipulation Passed!\n")

if __name__ == "__main__":
    print("=" * 70)
    print("   AUTONOMOUS QUANTITATIVE STOCK SYSTEM — VERIFICATION TEST SUITE   ")
    print("=" * 70)
    
    t0 = time.time()
    test_1_config_and_watchlist()
    scored = test_2_scanner_and_high_safety()
    test_3_risk_manager(scored)
    test_4_fastapi_endpoints()
    test_5_playwright_extension_autofill()
    
    elapsed = time.time() - t0
    print("=" * 70)
    print(f"🎉 ALL 5 COMPREHENSIVE TESTS PASSED SUCCESSFULLY in {elapsed:.2f}s!")
    print("=" * 70)
