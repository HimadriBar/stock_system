"""
Main Entrypoint for the High-Accuracy Quantitative Stock Screener and Risk Allocation System.
Integrates Multi-Factor Trend Analysis, NIFTY Market Climate, and Sized Execution within ₹5,000.
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from analyzer import scan_all_stocks_advanced
from risk_manager import generate_daily_trade_recommendations
from backtester import run_advanced_portfolio_backtest
from report_generator import generate_terminal_report, generate_html_dashboard

def run_system():
    print("\n=======================================================")
    print("   HIGH-ACCURACY QUANTITATIVE STOCK SELECTION SYSTEM   ")
    print("=======================================================\n")

    # Step 1: Scan and score candidate stocks with Multi-Parameter Confluence & Market Climate
    scored_stocks, market_regime = scan_all_stocks_advanced()

    if not scored_stocks:
        print("[!] No stocks passed the strict multi-factor threshold today.")
        print("    Recommendation: Capital preservation mode. Sit out when edge is absent.")
        return

    # Step 2: Risk sizing and trade plan generation (strictly capped at ₹5,000 budget)
    print(f"[*] Analyzing top {len(scored_stocks)} candidates and computing position sizing...")
    top_trade_plans = generate_daily_trade_recommendations(scored_stocks, max_trades=3)

    # Step 3: Run advanced strategy backtest with Breakeven Trailing Stops
    backtest_summary = run_advanced_portfolio_backtest()

    # Step 4: Display terminal report
    generate_terminal_report(top_trade_plans, market_regime, backtest_summary)

    # Step 5: Save interactive HTML dashboard
    html_path = os.path.join(os.path.dirname(__file__), "report.html")
    generate_html_dashboard(top_trade_plans, market_regime, backtest_summary, html_path)
    print(f"[OK] Interactive visual dashboard generated at:\n    {os.path.abspath(html_path)}\n")

if __name__ == "__main__":
    run_system()
