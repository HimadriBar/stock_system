"""
Advanced Multi-Factor Quantitative Market Data and Scoring Engine.
Features:
- NIFTY 50 Market Climate Detection
- Mansfield Relative Strength (RS) Outperformance Factor
- 200 SMA Secular Trend & Golden Alignment
- ADX & Directional Movement Index (DMI)
- On-Balance Volume (OBV) & Money Flow Index (MFI)
- Connors RSI-4 Deep Pullbacks & Bollinger Squeeze Releases
"""

import concurrent.futures
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from config import WATCHLIST, BENCHMARK_INDEX, ADVANCED_CRITERIA, HIGH_SAFETY_THRESHOLD

def flatten_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame columns are simple single-level Close, High, Low, Open, Volume."""
    if isinstance(df.columns, pd.MultiIndex):
        flat_cols = []
        for col in df.columns:
            if isinstance(col, tuple):
                flat_cols.append(col[0])
            else:
                flat_cols.append(col)
        df.columns = flat_cols
    return df

def get_market_regime() -> Dict:
    """
    Analyzes the NIFTY 50 Benchmark Index to determine market regime and 20-day benchmark return.
    """
    try:
        nifty = yf.Ticker(BENCHMARK_INDEX)
        df = nifty.history(period="1y", interval="1d")
        if df is None or len(df) < 50:
            return {"status": "NEUTRAL", "nifty_return_20d": 0.0, "desc": "Market data fallback"}

        df = flatten_dataframe(df)
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['SMA_200'] = df['Close'].rolling(200).mean()

        latest = df.iloc[-1]
        close = latest['Close']
        ema_21 = latest['EMA_21']
        ema_50 = latest['EMA_50']
        sma_200 = latest['SMA_200'] if pd.notnull(latest['SMA_200']) else ema_50

        nifty_ret_20d = float((close - df['Close'].iloc[-20]) / df['Close'].iloc[-20] * 100) if len(df) >= 20 else 0.0

        if close > ema_21 and ema_21 > ema_50 and close > sma_200:
            status = "BULLISH"
            desc = "NIFTY 50 in strong uptrend (Above 21 EMA & 200 SMA)"
        elif close > ema_50:
            status = "NEUTRAL_BULLISH"
            desc = "NIFTY 50 holding above 50 EMA"
        elif close > sma_200:
            status = "CAUTION"
            desc = "NIFTY 50 consolidating near 200 SMA support"
        else:
            status = "CONSOLIDATION_PULLBACK"
            desc = f"NIFTY 50 in intermediate correction (20D return: {nifty_ret_20d:.1f}%). Focus on Relative Strength Leaders"

        return {
            "status": status,
            "nifty_close": round(close, 2),
            "nifty_return_20d": round(nifty_ret_20d, 2),
            "desc": desc
        }
    except Exception as e:
        return {"status": "NEUTRAL", "nifty_return_20d": 0.0, "desc": "Market regime default"}

def calculate_comprehensive_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Computes full multi-parameter quantitative suite."""
    if len(df) < 35:
        return df

    # 1. Moving Averages
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['SMA_200'] = df['Close'].rolling(min(200, len(df))).mean()
    df['SMA_200_Slope'] = df['SMA_200'].diff(10)

    # 2. RSI (14 standard) & RSI (4 Connors dip)
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # RSI 14
    gain_14 = gain.rolling(14).mean()
    loss_14 = loss.rolling(14).mean()
    rs_14 = gain_14 / loss_14.replace(0, np.nan)
    df['RSI_14'] = 100 - (100 / (1 + rs_14))
    df['RSI_14'] = df['RSI_14'].fillna(50)

    # RSI 4
    gain_4 = gain.rolling(4).mean()
    loss_4 = loss.rolling(4).mean()
    rs_4 = gain_4 / loss_4.replace(0, np.nan)
    df['RSI_4'] = 100 - (100 / (1 + rs_4))
    df['RSI_4'] = df['RSI_4'].fillna(50)

    # 3. ADX & Directional Movement (+DI, -DI)
    high_diff = df['High'].diff()
    low_diff = -df['Low'].diff()
    plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0.0)
    minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0.0)
    tr = pd.concat([df['High']-df['Low'], np.abs(df['High']-df['Close'].shift()), np.abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
    tr_s = pd.Series(tr).ewm(span=14, adjust=False).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).ewm(span=14, adjust=False).mean() / tr_s)
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).ewm(span=14, adjust=False).mean() / tr_s)
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
    df['ADX'] = dx.ewm(span=14, adjust=False).mean()
    df['Plus_DI'] = plus_di.fillna(0)
    df['Minus_DI'] = minus_di.fillna(0)

    # 4. Volume SMA, RVOL, and OBV
    df['Vol_SMA_20'] = df['Volume'].rolling(20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA_20'].replace(0, np.nan)
    
    obv_dir = np.sign(df['Close'].diff()).fillna(0)
    df['OBV'] = (obv_dir * df['Volume']).cumsum()
    df['OBV_SMA_10'] = df['OBV'].rolling(10).mean()

    # 5. Money Flow Index (MFI 14)
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    mf = tp * df['Volume']
    pos_mf = np.where(tp > tp.shift(1), mf, 0)
    neg_mf = np.where(tp < tp.shift(1), mf, 0)
    mfr = pd.Series(pos_mf, index=df.index).rolling(14).sum() / pd.Series(neg_mf, index=df.index).rolling(14).sum().replace(0, np.nan)
    df['MFI'] = 100 - (100 / (1 + mfr))
    df['MFI'] = df['MFI'].fillna(50)

    # 6. Bollinger Bands & Volatility Squeeze
    df['BB_Mid'] = df['Close'].rolling(20).mean()
    df['BB_Std'] = df['Close'].rolling(20).std()
    df['BB_Upper'] = df['BB_Mid'] + 2 * df['BB_Std']
    df['BB_Lower'] = df['BB_Mid'] - 2 * df['BB_Std']
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Mid'].replace(0, np.nan)
    min_bw = df['BB_Width'].rolling(20).min()
    df['BB_Squeeze'] = df['BB_Width'] <= (min_bw.shift(1) * 1.15)

    # 7. ATR
    df['ATR'] = tr.rolling(14).mean()

    # 8. 20-Day Return for Relative Strength calculation
    df['Return_20d'] = df['Close'].pct_change(20) * 100

    return df

def score_advanced_stock(df: pd.DataFrame, market_regime: Dict) -> Dict:
    """
    Multi-Factor Confluence & Safe Percentage Scoring Engine (0-100%).
    Evaluates:
    - Mansfield Relative Strength (RS) vs Benchmark (up to 25 pts)
    - Trend Alignment & 200 SMA Secular Bullish Slope (up to 25 pts)
    - Directional Movement Index (+DI/-DI) & ADX Trend Dominance (up to 20 pts)
    - Institutional Volume Flow & On-Balance Volume Accumulation (up to 15 pts)
    - Timing & Momentum Confluence / Continuation Breakout (up to 15 pts)
    """
    if len(df) < 35:
        return {"eligible": False, "reason": "Insufficient data"}

    latest = df.iloc[-1]
    price = float(latest['Close'])
    atr = float(latest['ATR']) if pd.notnull(latest['ATR']) else (price * 0.015)
    rsi_14 = float(latest['RSI_14'])
    rsi_4 = float(latest['RSI_4'])
    adx = float(latest['ADX']) if pd.notnull(latest['ADX']) else 15.0
    plus_di = float(latest['Plus_DI']) if pd.notnull(latest['Plus_DI']) else 0.0
    minus_di = float(latest['Minus_DI']) if pd.notnull(latest['Minus_DI']) else 0.0
    vol_ratio = float(latest['Vol_Ratio']) if pd.notnull(latest['Vol_Ratio']) else 1.0
    obv_bullish = bool(latest['OBV'] > latest['OBV_SMA_10']) if pd.notnull(latest['OBV_SMA_10']) else False
    mfi = float(latest['MFI'])
    sma_200 = float(latest['SMA_200']) if pd.notnull(latest['SMA_200']) else float(latest['EMA_50'])
    sma_200_slope = float(latest['SMA_200_Slope']) if pd.notnull(latest['SMA_200_Slope']) else 0.0
    ema_21 = float(latest['EMA_21'])
    ema_50 = float(latest['EMA_50'])
    bb_squeeze = bool(latest['BB_Squeeze'])

    # Price Constraints
    if price < ADVANCED_CRITERIA['min_price'] or price > ADVANCED_CRITERIA['max_price']:
        return {
            "eligible": False,
            "reason": f"Price ₹{price:.2f} out of allowable range"
        }

    score = 0
    signals = []

    # 1. Relative Strength (RS) Outperformance Factor (up to 25 Points)
    stock_ret_20d = float(latest['Return_20d']) if pd.notnull(latest['Return_20d']) else 0.0
    nifty_ret_20d = market_regime.get("nifty_return_20d", 0.0)
    relative_strength = stock_ret_20d - nifty_ret_20d

    if relative_strength >= 5.0:
        score += 25
        signals.append(f"Super Relative Strength Leader (+{relative_strength:.1f}% vs NIFTY)")
    elif relative_strength >= 2.0:
        score += 18
        signals.append(f"Outperforming NIFTY (+{relative_strength:.1f}%)")
    elif relative_strength > 0:
        score += 10
        signals.append(f"Positive Relative Strength (+{relative_strength:.1f}%)")
    else:
        signals.append(f"Lagging Benchmark ({relative_strength:.1f}%)")

    # 2. Trend Structure & Secular Alignment (up to 25 Points)
    if price > ema_21 and ema_21 > ema_50:
        score += 20
        signals.append("Uptrend Alignment (Price > 21 EMA > 50 EMA)")
    elif price > ema_21:
        score += 15
        signals.append("Holding above 21 EMA Support")
    elif price > ema_50:
        score += 10
        signals.append("Above 50 EMA Baseline")

    # Secular 200 SMA golden alignment bonus (5 pts)
    if price > sma_200 and sma_200_slope >= 0:
        score += 5
        signals.append("Secular Bull Trend (Above Rising 200 SMA)")

    # 3. Trend Dominance: DMI & ADX (up to 20 Points)
    if plus_di > minus_di:
        if adx >= 25.0:
            score += 20
            signals.append(f"Strong Buyer Trend (ADX: {adx:.1f}, +DI > -DI)")
        elif adx >= 20.0:
            score += 16
            signals.append(f"Confirmed Bullish Trend (ADX: {adx:.1f})")
        else:
            score += 12
            signals.append("Buyer Dominance (+DI > -DI)")
    else:
        score -= 10
        signals.append("Seller Dominance (-DI > +DI)")

    # 4. Institutional Volume & Flow (up to 15 Points)
    if vol_ratio >= 1.2:
        score += 10
        signals.append(f"Volume Surge ({vol_ratio:.1f}x 20-SMA)")
    elif vol_ratio >= 1.0:
        score += 6
        signals.append(f"Active Volume ({vol_ratio:.1f}x avg)")
    elif vol_ratio >= 0.8:
        score += 3
    if obv_bullish:
        score += 5
        signals.append("Positive OBV Institutional Accumulation")

    # 5. Timing Trigger & Momentum Confluence (up to 15 Points)
    if price > ema_50 and rsi_4 <= 25.0:
        score += 15
        signals.append(f"High-Accuracy Dip Entry (RSI-4: {rsi_4:.1f} Oversold)")
    elif rsi_14 > 68.0 and adx >= 25.0 and plus_di > minus_di:
        score += 15
        signals.append(f"Powerful Bullish Continuation Breakout (RSI-14: {rsi_14:.1f}, ADX: {adx:.1f})")
    elif 50.0 <= rsi_14 <= 68.0:
        score += 12
        if bb_squeeze:
            score += 3
            signals.append("Volatility Squeeze Breakout Ready")
        signals.append(f"Momentum Expansion (RSI-14: {rsi_14:.1f})")
    elif rsi_4 <= 35.0 and plus_di > minus_di:
        score += 10
        signals.append(f"Rebound Momentum Setup (RSI-4: {rsi_4:.1f})")

    # Safe Percentage (0% to 100%)
    safe_percentage = int(max(0, min(100, score)))
    is_high_safety = bool(safe_percentage >= HIGH_SAFETY_THRESHOLD)

    if is_high_safety:
        signals.insert(0, f"🚨 HIGH SAFETY ALERT: {safe_percentage}% Safe Setup (>{HIGH_SAFETY_THRESHOLD:.0f}% Threshold Passed)")

    # Eligibility threshold: Requires Score >= 50, Plus_DI > Minus_DI (buyers in control), and RS > 0
    eligible = (safe_percentage >= 50) and (plus_di > minus_di) and (relative_strength > 0)

    return {
        "eligible": eligible,
        "score": safe_percentage,
        "safe_percentage": safe_percentage,
        "is_high_safety": is_high_safety,
        "price": price,
        "rsi_14": round(rsi_14, 2),
        "rsi_4": round(rsi_4, 2),
        "adx": round(adx, 2),
        "plus_di": round(plus_di, 2),
        "minus_di": round(minus_di, 2),
        "vol_ratio": round(vol_ratio, 2),
        "relative_strength": round(relative_strength, 2),
        "atr": round(atr, 2),
        "signals": signals
    }

def scan_all_stocks_advanced(tickers: Optional[List[str]] = None, return_all: bool = False) -> Union[Tuple[List[Dict], Dict], Tuple[List[Dict], Dict, List[Dict]]]:
    """Scans and analyzes all watchlist stocks using concurrent multi-threading for fast sub-5s execution."""
    if tickers is None:
        tickers = WATCHLIST

    market_regime = get_market_regime()
    print(f"[*] Starting high-speed concurrent screening across {len(tickers)} liquid stocks...")
    print(f"[*] Market Climate: {market_regime['status']} ({market_regime['desc']})")

    def process_ticker(ticker: str) -> Optional[Dict]:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="6mo", interval="1d")
            if df is None or len(df) < 35:
                df = stock.history(period="1y", interval="1d")
            if df is None or len(df) < 35:
                return None

            df = flatten_dataframe(df)
            df = calculate_comprehensive_indicators(df)
            analysis = score_advanced_stock(df, market_regime)

            clean_name = ticker.replace(".NS", "")
            return {
                "ticker": ticker,
                "name": clean_name,
                "analysis": analysis,
                "df": df
            }
        except Exception:
            return None

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {executor.submit(process_ticker, t): t for t in tickers}
        for future in concurrent.futures.as_completed(future_map):
            res = future.result()
            if res is not None:
                results.append(res)

    # Sort all results by safe score / score descending
    results.sort(key=lambda x: x['analysis']['score'], reverse=True)

    # Filter eligible stocks and sort by score descending
    valid_stocks = [r for r in results if r['analysis'].get('eligible', False)]
    valid_stocks.sort(key=lambda x: x['analysis']['score'], reverse=True)

    if return_all:
        return valid_stocks, market_regime, results
    return valid_stocks, market_regime
