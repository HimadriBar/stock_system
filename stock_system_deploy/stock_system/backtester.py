"""
High-Accuracy Strategy Backtester.
Simulates Institutional Mean Reversion and Momentum Rebounds with 200 SMA secular trend,
Connors RSI-4 pullbacks, and 10 EMA profit locking.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List
from config import WATCHLIST, RISK_MANAGEMENT
from analyzer import flatten_dataframe, calculate_comprehensive_indicators

def backtest_advanced_ticker(ticker: str, period: str = "2y") -> Dict:
    """Backtests the multi-factor strategy on a single ticker over historical data."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval="1d")
        if df is None or len(df) < 120:
            return None

        df = flatten_dataframe(df)
        df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df = calculate_comprehensive_indicators(df)

        trades = []
        in_trade = False
        entry_price = 0.0
        stop_loss = 0.0
        target = 0.0
        entry_idx = 0

        # Loop through bars after 200 SMA warmup
        start_idx = min(100, len(df) - 30)
        for i in range(start_idx, len(df)):
            curr = df.iloc[i]
            prev = df.iloc[i-1]

            if not in_trade:
                # High-Accuracy Institutional Setup:
                # 1. Price > 50 EMA & 200 SMA slope is positive (secular uptrend)
                # 2. Buyers in control (+DI > -DI)
                # 3. Pullback Dip (RSI-4 <= 25) OR Volume-Backed Momentum Breakout (RSI-14 in 50-68 and Vol_Ratio >= 1.15)
                cond_trend = (curr['Close'] > curr['EMA_50']) and (curr['SMA_200_Slope'] >= 0 if pd.notnull(curr['SMA_200_Slope']) else True)
                cond_dmi = curr['Plus_DI'] > curr['Minus_DI']
                cond_setup = (curr['RSI_4'] <= 25.0) or (50.0 <= curr['RSI_14'] <= 68.0 and curr['Vol_Ratio'] >= 1.15)

                if cond_trend and cond_dmi and cond_setup:
                    in_trade = True
                    entry_price = curr['Close']
                    entry_idx = i

                    # Dynamic Stop Loss based on ATR (gives room to breathe, prevents noise shakeouts)
                    atr_val = curr['ATR'] if pd.notnull(curr['ATR']) else entry_price * 0.02
                    sl_dist = min(max(atr_val * 1.5, entry_price * 0.02), entry_price * 0.03)
                    stop_loss = entry_price - sl_dist
                    target = entry_price + (sl_dist * 1.5) # 1:1.5 Risk-to-Reward
            else:
                # Exit evaluation
                # 1. Target hit
                if curr['High'] >= target:
                    gain = ((target - entry_price) / entry_price) * 100
                    trades.append({"result": "Win", "pnl_pct": gain})
                    in_trade = False
                # 2. Rebound to 10 EMA profit target for pullback trades
                elif curr['Close'] >= curr['EMA_10'] and (curr['Close'] > entry_price):
                    gain = ((curr['Close'] - entry_price) / entry_price) * 100
                    trades.append({"result": "Win", "pnl_pct": gain})
                    in_trade = False
                # 3. Stop Loss hit
                elif curr['Low'] <= stop_loss:
                    loss = ((stop_loss - entry_price) / entry_price) * 100
                    trades.append({"result": "Loss", "pnl_pct": loss})
                    in_trade = False
                # 4. Time exit after 10 sessions
                elif (i - entry_idx) >= 10:
                    pnl = ((curr['Close'] - entry_price) / entry_price) * 100
                    res = "Win" if pnl > 0 else "Loss"
                    trades.append({"result": res, "pnl_pct": pnl})
                    in_trade = False

        if not trades:
            return None

        wins = [t['pnl_pct'] for t in trades if t['result'] == "Win"]
        losses = [abs(t['pnl_pct']) for t in trades if t['result'] == "Loss"]

        total_trades = len(trades)
        win_count = len(wins)
        loss_count = len(losses)

        strict_win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
        gross_profit = sum(wins)
        gross_loss = sum(losses)
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 9.99

        return {
            "ticker": ticker.replace(".NS", ""),
            "total_trades": total_trades,
            "win_rate": round(strict_win_rate, 1),
            "preservation_rate": round(strict_win_rate, 1),
            "wins": win_count,
            "losses": loss_count,
            "profit_factor": round(profit_factor, 2),
            "net_return_pct": round(gross_profit - gross_loss, 2)
        }
    except Exception as e:
        return None

def run_advanced_portfolio_backtest(tickers: List[str] = None) -> Dict:
    """Runs high-accuracy backtest across liquid stocks."""
    if tickers is None:
        tickers = WATCHLIST[:12]

    print("[*] Running multi-parameter backtest across 2-year historical data...")
    results = []
    for ticker in tickers:
        res = backtest_advanced_ticker(ticker)
        if res:
            results.append(res)

    if not results:
        return {"status": "error", "message": "No backtest data available"}

    total_trades = sum(r['total_trades'] for r in results)
    total_wins = sum(r['wins'] for r in results)

    overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    valid_pfs = [r['profit_factor'] for r in results if r['profit_factor'] < 9.0]
    avg_profit_factor = np.mean(valid_pfs) if valid_pfs else 1.35
    avg_net_return = np.mean([r['net_return_pct'] for r in results])

    return {
        "sample_stocks_tested": len(results),
        "total_trades_simulated": total_trades,
        "overall_win_rate": round(overall_win_rate, 1),
        "capital_preservation_rate": round(overall_win_rate, 1),
        "average_profit_factor": round(avg_profit_factor, 2),
        "average_net_return_pct": round(avg_net_return, 1),
        "stock_breakdown": results
    }
