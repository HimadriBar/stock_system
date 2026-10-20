"""
FastAPI Live Trading Web Server with Groww Auto-Order Bridge Support.
Serves an interactive trading terminal, provides real-time in-memory data,
and manages pending trade dispatching to Groww.
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
import uvicorn
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Add stock_system directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stock_system")))

from analyzer import scan_all_stocks_advanced, get_market_regime, calculate_comprehensive_indicators, flatten_dataframe
from risk_manager import generate_daily_trade_recommendations
from config import WATCHLIST, MAX_DAILY_INVESTMENT, GROWW_SLUGS
import yfinance as yf

app = FastAPI(title="Autonomous Stock Terminal")

# Enable CORS for Groww Extension integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Cache for ultra-fast <5ms responses on 2-second polling
STATE = {
    "market_regime": {
        "status": "CONSOLIDATION_PULLBACK",
        "desc": "Scanning live market data...",
        "nifty_close": 22610.0,
        "nifty_return_20d": -2.8
    },
    "budget": float(MAX_DAILY_INVESTMENT),
    "top_trade_plans": [],
    "watchlist_status": [],
    "high_safety_alerts": [],
    "high_safety_count": 0,
    "last_updated_time": datetime.now().strftime("%H:%M:%S"),
    "is_scanning": False,
    "pending_order": None,
    "pending_order_id": 0,
    "scored_stocks_cache": []
}

def recalculate_trade_plans_for_budget(new_budget: float):
    """Dynamically re-evaluates position sizing, exact shares, and risk for the specified budget."""
    STATE["budget"] = float(new_budget)
    scored = STATE.get("scored_stocks_cache")
    if scored:
        trade_plans = generate_daily_trade_recommendations(scored, max_trades=3, budget=STATE["budget"])
        STATE["top_trade_plans"] = trade_plans
        top_tickers = [p['ticker'] for p in trade_plans]
        for item in STATE.get("watchlist_status", []):
            item["is_top_pick"] = item["ticker"] in top_tickers
    return STATE.get("top_trade_plans", [])

def perform_deep_market_scan():
    """Runs the full quantitative multi-factor scan across all top 30 stocks and updates the in-memory state."""
    STATE["is_scanning"] = True
    try:
        print("[*] Background Worker: Performing full quantitative market scan across Top 30 stocks...")
        scored_stocks, market_regime = scan_all_stocks_advanced(WATCHLIST)
        STATE["scored_stocks_cache"] = scored_stocks
        trade_plans = generate_daily_trade_recommendations(scored_stocks, max_trades=3, budget=STATE.get("budget", 5000.0))

        # Detect any stock with Safe Percentage >= 90%
        high_safety_alerts = []
        for stock in scored_stocks:
            analysis = stock['analysis']
            safe_pct = analysis.get('safe_percentage', analysis.get('score', 0))
            if safe_pct >= 90:
                high_safety_alerts.append({
                    "ticker": stock['ticker'],
                    "name": stock['name'],
                    "slug": GROWW_SLUGS.get(stock['ticker'], ""),
                    "price": round(analysis['price'], 2),
                    "safe_percentage": safe_pct,
                    "is_high_safety": True,
                    "signals": analysis.get('signals', []),
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

        if high_safety_alerts:
            print("\n" + "!" * 70)
            print(f" [🚨 90%+ HIGH SAFETY ALERT] {len(high_safety_alerts)} stock(s) crossed 90% Safe Score!")
            for al in high_safety_alerts:
                print(f"  --> {al['name']} ({al['ticker']}): {al['safe_percentage']}% Safe | ₹{al['price']:.2f}")
            print("!" * 70 + "\n")

        # Build full watchlist radar data (All Top 30 Stocks)
        top_tickers = [p['ticker'] for p in trade_plans]
        watchlist_items = []
        for stock in scored_stocks:
            analysis = stock['analysis']
            ticker = stock['ticker']
            safe_pct = analysis.get('safe_percentage', analysis.get('score', 0))
            watchlist_items.append({
                "ticker": ticker,
                "slug": GROWW_SLUGS.get(ticker, ""),
                "name": stock['name'],
                "price": analysis['price'],
                "return_20d": float(stock['df']['Return_20d'].iloc[-1]) if 'Return_20d' in stock['df'] else 0.0,
                "relative_strength": analysis['relative_strength'],
                "adx": analysis['adx'],
                "trend_direction": "+DI Bullish" if analysis['plus_di'] > analysis['minus_di'] else "-DI Bearish",
                "vol_ratio": analysis['vol_ratio'],
                "score": safe_pct,
                "safe_percentage": safe_pct,
                "is_high_safety": safe_pct >= 90,
                "is_top_pick": ticker in top_tickers
            })

        STATE["market_regime"] = market_regime
        STATE["top_trade_plans"] = trade_plans
        STATE["watchlist_status"] = watchlist_items
        STATE["high_safety_alerts"] = high_safety_alerts
        STATE["high_safety_count"] = len(high_safety_alerts)
        STATE["last_updated_time"] = datetime.now().strftime("%H:%M:%S")
        print(f"[✓] Background Worker: Scan complete. Top pick: {trade_plans[0]['name'] if trade_plans else 'None'} | High-Safety Alerts: {len(high_safety_alerts)}")
    except Exception as e:
        print(f"[!] Error in deep market scan: {e}")
    finally:
        STATE["is_scanning"] = False

def background_price_streamer():
    """Continuously streams live price updates every 10 seconds without hammering external servers."""
    while True:
        try:
            time.sleep(10)
            if not STATE["top_trade_plans"]:
                continue

            tickers = [p['ticker'] for p in STATE["top_trade_plans"]]
            df = yf.download(tickers, period="1d", interval="1m", progress=False)
            
            if df is not None and not df.empty and 'Close' in df:
                close_df = df['Close']
                for plan in STATE["top_trade_plans"]:
                    t = plan['ticker']
                    if t in close_df.columns:
                        latest_val = float(close_df[t].dropna().iloc[-1])
                        if latest_val > 0:
                            plan['entry_price'] = round(latest_val, 2)
                            plan['invested_amount'] = round(plan['quantity'] * plan['entry_price'], 2)
                            plan['unallocated_cash'] = round(MAX_DAILY_INVESTMENT - plan['invested_amount'], 2)

                STATE["last_updated_time"] = datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            pass

@app.on_event("startup")
def startup_event():
    """Initializes market data on server start."""
    scan_thread = threading.Thread(target=perform_deep_market_scan, daemon=True)
    scan_thread.start()

    stream_thread = threading.Thread(target=background_price_streamer, daemon=True)
    stream_thread.start()

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    """Serves the live interactive trading web dashboard."""
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/live-data")
def get_live_data(budget: Optional[float] = None):
    """Returns latest in-memory market data instantly (< 5ms response time)."""
    if budget is not None and budget > 0 and budget != STATE.get("budget"):
        recalculate_trade_plans_for_budget(budget)

    # Return state omitting heavy cache objects
    payload = {k: v for k, v in STATE.items() if k != "scored_stocks_cache"}
    return JSONResponse(content=payload)

@app.post("/api/budget")
async def update_budget(request: Request):
    """Allows user to customize the daily investment budget and recalculate position sizing dynamically."""
    try:
        data = await request.json()
        b_val = float(data.get("budget", 5000.0))
        if b_val <= 0:
            return JSONResponse(status_code=400, content={"error": "Budget must be greater than 0"})
        plans = recalculate_trade_plans_for_budget(b_val)
        return JSONResponse(content={
            "status": "updated",
            "budget": b_val,
            "top_trade_plans": plans
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.get("/api/notifications")
def get_notifications():
    """Returns real-time high-safety notifications (stocks with Safe Score >= 90%)."""
    return JSONResponse(content={
        "alerts": STATE.get("high_safety_alerts", []),
        "count": STATE.get("high_safety_count", 0),
        "threshold": 90,
        "last_updated_time": STATE.get("last_updated_time")
    })

@app.post("/api/refresh")
def force_refresh(background_tasks: BackgroundTasks):
    """Triggers an immediate background deep scan."""
    if not STATE["is_scanning"]:
        background_tasks.add_task(perform_deep_market_scan)
        return {"status": "scanning_started"}
    return {"status": "already_scanning"}

# Groww Auto-Order Bridge Endpoints
@app.post("/api/set-pending-order")
async def set_pending_order(request: Request):
    """Sets a pending order dispatched by the user clicking on the terminal."""
    data = await request.json()
    STATE["pending_order"] = data
    STATE["pending_order_id"] += 1
    print(f"[*] Dispatched Order to Groww Bridge: {data.get('name')} x {data.get('quantity')} shares")
    return {"status": "dispatched", "order_id": STATE["pending_order_id"]}

@app.get("/api/pending-order")
def get_pending_order():
    """Polled by the Groww browser extension to detect pending orders."""
    return JSONResponse(content={
        "order": STATE.get("pending_order"),
        "order_id": STATE.get("pending_order_id", 0)
    })

@app.post("/api/clear-pending-order")
def clear_pending_order():
    """Called by the extension once the order is populated on Groww."""
    STATE["pending_order"] = None
    return {"status": "cleared"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9012))
    host = os.environ.get("HOST", "0.0.0.0")
    print("\n=======================================================")
    print("   AUTONOMOUS STOCK TERMINAL & GROWW BRIDGE SERVER     ")
    print(f"   Live URL: http://{host}:{port}                     ")
    print("=======================================================\n")
    uvicorn.run(app, host=host, port=port, log_level="info")

