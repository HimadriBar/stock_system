"""
Visual Dashboard and Terminal Output Generator.
Renders Market Regime, Multi-Factor Confluence badges, and execution sizing.
"""

import os
import sys
from typing import Dict, List

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def generate_terminal_report(trade_plans: List[Dict], market_regime: Dict, backtest_summary: Dict):
    """Prints a structured, high-accuracy analysis summary to the terminal."""
    print("\n" + "=" * 75)
    print("      HIGH-ACCURACY QUANTITATIVE STOCK SELECTION & RISK SYSTEM       ")
    print("=" * 75)
    print(f" Daily Capital Limit  : Rs. 5,000.00")
    print(f" NIFTY 50 Climate     : {market_regime['status']} ({market_regime['desc']})")
    print(f" Confluence Filters   : 200 SMA + ADX/DMI + OBV Flow + Connors Dip + BB Squeeze")
    print("-" * 75)

    if not trade_plans:
        print("\n [!] No stocks passed the strict multi-factor threshold today.")
        print("     Reason: Capital preservation. The algorithm avoids forced trades in uncertain conditions.")
    else:
        print(f"\n [+] TOP FINALIZED HIGH-PROBABILITY SETUPS:")
        for i, plan in enumerate(trade_plans, 1):
            print(f"\n {i}. {plan['name']} ({plan['ticker']}) - Confluence Score: {plan['score']}/100")
            print(f"    - Current Price   : Rs. {plan['entry_price']:.2f}")
            print(f"    - Quantity to Buy : {plan['quantity']} shares")
            print(f"    - Capital Required: Rs. {plan['invested_amount']:.2f} (Cash Buffer: Rs. {plan['unallocated_cash']:.2f})")
            print(f"    - Stop Loss       : Rs. {plan['stop_loss']:.2f} (-{plan['risk_pct']}%) -> Max Loss: Rs. {plan['total_risk_inr']:.2f}")
            print(f"    - Target 1 (1:1.5): Rs. {plan['target_1']:.2f}")
            print(f"    - Target 2 (1:2)  : Rs. {plan['target_2']:.2f} (+{plan['reward_pct']}%) -> Target Gain: Rs. {plan['total_reward_inr']:.2f}")
            print(f"    - Quantitative Triggers: {', '.join(plan['signals'][:4])}")

    print("\n" + "-" * 75)
    print(" VERIFIED HISTORICAL BACKTEST METRICS (2-Year Multi-Factor Validation):")
    print(f"  - Overall Win Rate             : {backtest_summary.get('overall_win_rate', 'N/A')}%")
    print(f"  - Capital Preservation (Win+BE): {backtest_summary.get('capital_preservation_rate', 'N/A')}%")
    print(f"  - Average Profit Factor        : {backtest_summary.get('average_profit_factor', 'N/A')}")
    print(f"  - Total Trades Simulated       : {backtest_summary.get('total_trades_simulated', 'N/A')}")
    print("=" * 75 + "\n")

def generate_html_dashboard(trade_plans: List[Dict], market_regime: Dict, backtest_summary: Dict, filepath: str):
    """Creates a self-contained modern HTML dashboard report."""
    cards_html = ""
    for plan in trade_plans:
        signals_li = "".join([f"<li style='margin-bottom:5px;'>{sig}</li>" for sig in plan['signals']])
        cards_html += f"""
        <div class="card">
            <div class="card-header">
                <div>
                    <span class="stock-title">{plan['name']}</span>
                    <span class="stock-ticker">{plan['ticker']}</span>
                </div>
                <div class="score-badge">Confluence {plan['score']}/100</div>
            </div>
            
            <div class="price-grid">
                <div class="price-item">
                    <span class="label">Entry Price</span>
                    <span class="val highlight">₹{plan['entry_price']:.2f}</span>
                </div>
                <div class="price-item">
                    <span class="label">Allocation Qty</span>
                    <span class="val">{plan['quantity']} shares</span>
                </div>
                <div class="price-item">
                    <span class="label">Total Capital</span>
                    <span class="val">₹{plan['invested_amount']:.2f}</span>
                </div>
            </div>

            <div class="targets-container">
                <div class="box stop-loss">
                    <div class="box-title">STOP LOSS</div>
                    <div class="box-val">₹{plan['stop_loss']:.2f}</div>
                    <div class="box-sub">Max Risk: -₹{plan['total_risk_inr']:.2f} ({plan['risk_pct']}%)</div>
                </div>
                <div class="box target">
                    <div class="box-title">TARGET (1:2 R:R)</div>
                    <div class="box-val">₹{plan['target_2']:.2f}</div>
                    <div class="box-sub">Target Gain: +₹{plan['total_reward_inr']:.2f} ({plan['reward_pct']}%)</div>
                </div>
            </div>

            <div class="signals-list">
                <div style="font-weight:700; margin-bottom:8px; color:#38bdf8; font-size:11px; text-transform:uppercase; letter-spacing:0.5px;">Open-Source Quantitative Triggers</div>
                <ul style="padding-left:18px; margin:0; font-size:13px; color:#cbd5e1; line-height:1.5;">
                    {signals_li}
                </ul>
            </div>
        </div>
        """

    table_rows = ""
    for item in backtest_summary.get('stock_breakdown', []):
        table_rows += f"""
        <tr>
            <td style="font-weight:600;">{item['ticker']}</td>
            <td>{item['total_trades']}</td>
            <td><span class="tag-win">{item['win_rate']}%</span></td>
            <td><span class="tag-be">{item.get('preservation_rate', item['win_rate'])}%</span></td>
            <td>{item['profit_factor']}</td>
            <td style="color:{'#10b981' if item['net_return_pct'] > 0 else '#ef4444'}; font-weight:700;">+{item['net_return_pct']}%</td>
        </tr>
        """

    regime_color = "#10b981" if "BULLISH" in market_regime['status'] else ("#f59e0b" if "CAUTION" in market_regime['status'] else "#ef4444")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>High-Accuracy Quantitative Stock Analysis</title>
    <style>
        :root {{
            --bg: #0b0f19;
            --surface: #151d30;
            --border: #22304d;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-blue: #38bdf8;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 24px;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
        }}
        h1 {{ margin: 0; font-size: 24px; font-weight: 800; color: #fff; }}
        .header-badges {{ display: flex; gap: 12px; }}
        .badge {{
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
        }}
        .badge-budget {{ background: #0284c7; color: #fff; }}
        .badge-regime {{ background: {regime_color}22; color: {regime_color}; border: 1px solid {regime_color}; }}
        .section-title {{
            font-size: 15px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--text-muted);
            margin: 28px 0 16px 0;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 22px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }}
        .stock-title {{ font-size: 20px; font-weight: 800; display: block; }}
        .stock-ticker {{ font-size: 12px; color: var(--text-muted); }}
        .score-badge {{
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-blue);
            font-weight: 800;
            font-size: 12px;
            padding: 5px 12px;
            border-radius: 8px;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }}
        .price-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            background: #0d1322;
            padding: 12px;
            border-radius: 10px;
            gap: 8px;
            margin-bottom: 16px;
            border: 1px solid var(--border);
        }}
        .price-item {{ display: flex; flex-direction: column; }}
        .label {{ font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }}
        .val {{ font-size: 14px; font-weight: 700; }}
        .val.highlight {{ color: var(--accent-blue); }}
        .targets-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 16px;
        }}
        .box {{
            padding: 12px;
            border-radius: 10px;
            border: 1px solid transparent;
        }}
        .box.stop-loss {{
            background: rgba(239, 68, 68, 0.08);
            border-color: rgba(239, 68, 68, 0.3);
        }}
        .box.target {{
            background: rgba(16, 185, 129, 0.08);
            border-color: rgba(16, 185, 129, 0.3);
        }}
        .box-title {{ font-size: 10px; font-weight: 800; letter-spacing: 0.6px; margin-bottom: 4px; }}
        .stop-loss .box-title {{ color: var(--accent-red); }}
        .target .box-title {{ color: var(--accent-green); }}
        .box-val {{ font-size: 17px; font-weight: 800; }}
        .box-sub {{ font-size: 11px; margin-top: 4px; color: var(--text-muted); }}
        .stats-banner {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 16px;
            background: var(--surface);
            padding: 20px;
            border-radius: 14px;
            border: 1px solid var(--border);
            margin-bottom: 24px;
        }}
        .stat-box {{ text-align: center; }}
        .stat-value {{ font-size: 26px; font-weight: 800; color: var(--accent-green); }}
        .stat-desc {{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--surface);
            border-radius: 10px;
            overflow: hidden;
            font-size: 13px;
            border: 1px solid var(--border);
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{ background: #0d1322; color: var(--text-muted); font-size: 11px; text-transform: uppercase; }}
        .tag-win {{ background: rgba(16, 185, 129, 0.15); color: #10b981; padding: 3px 8px; border-radius: 4px; font-weight: 700; }}
        .tag-be {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 3px 8px; border-radius: 4px; font-weight: 700; }}
        .info-card {{
            background: #111a2e;
            border-left: 4px solid #38bdf8;
            padding: 18px;
            border-radius: 8px;
            margin-top: 24px;
            font-size: 13px;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>High-Accuracy Quantitative Screener</h1>
                <div style="font-size:13px; color:#94a3b8; margin-top:4px;">Multi-Parameter Institutional Confluence: 200 SMA + DMI + OBV Flow + Connors Dip</div>
            </div>
            <div class="header-badges">
                <span class="badge badge-regime">Market: {market_regime['status']}</span>
                <span class="badge badge-budget">Daily Budget: ₹5,000</span>
            </div>
        </header>

        <div class="stats-banner">
            <div class="stat-box">
                <div class="stat-value">{backtest_summary.get('overall_win_rate', 'N/A')}%</div>
                <div class="stat-desc">Pure Target Hit Rate</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" style="color:#38bdf8;">{backtest_summary.get('capital_preservation_rate', 'N/A')}%</div>
                <div class="stat-desc">Capital Preservation (Win + Breakeven)</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{backtest_summary.get('average_profit_factor', 'N/A')}</div>
                <div class="stat-desc">Strategy Profit Factor</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" style="color:#f8fafc;">{backtest_summary.get('total_trades_simulated', 'N/A')}</div>
                <div class="stat-desc">2-Year Simulated Trades</div>
            </div>
        </div>

        <div class="section-title">Final Selected High-Confluence Trades for Today</div>
        <div class="grid">
            {cards_html}
        </div>

        <div class="section-title">2-Year Backtest Verification Breakdown</div>
        <table>
            <thead>
                <tr>
                    <th>Stock</th>
                    <th>Simulated Trades</th>
                    <th>Win Rate</th>
                    <th>Preservation Rate</th>
                    <th>Profit Factor</th>
                    <th>Net Gain %</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>

        <div class="info-card">
            <strong>Execution Checklist for Groww:</strong><br>
            1. Search for the finalized stock above in Groww.<br>
            2. Enter the exact <strong>Quantity</strong> shown above (guarantees you never exceed your ₹5,000 budget).<br>
            3. Set a <strong>Stop-Loss (SL)</strong> order immediately upon purchase to guard against black-swan drops.<br>
            4. <em>Trailing Rule</em>: As soon as the stock hits +1.5% profit, move your stop-loss up to your entry price to lock in a risk-free trade!
        </div>
    </div>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
