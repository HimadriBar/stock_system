"""
Configuration settings for the High-Accuracy Quantitative Stock System.
Includes Nifty Benchmark Regime, Multi-Factor Technical Thresholds, and ₹5,000 Capital Cap.
"""

# Maximum daily investment capital (INR)
MAX_DAILY_INVESTMENT = 5000.0

# Benchmark Index for Market Regime Detection
BENCHMARK_INDEX = "^NSEI"  # NIFTY 50

# Universe of top 30 high-volume, liquid Indian equities (NSE)
WATCHLIST = [
    # Top Nifty 50 Heavyweights & High-Liquid Leaders (Top 30 Universe)
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "INFY.NS",
    "BHARTIARTL.NS",
    "ITC.NS",
    "SBIN.NS",
    "LT.NS",
    "KOTAKBANK.NS",
    "AXISBANK.NS",
    "HINDUNILVR.NS",
    "SUNPHARMA.NS",
    "TITAN.NS",
    "TATASTEEL.NS",
    "NTPC.NS",
    "POWERGRID.NS",
    "ONGC.NS",
    "COALINDIA.NS",
    "HINDALCO.NS",
    "WIPRO.NS",
    "TECHM.NS",
    "BPCL.NS",
    "GAIL.NS",
    "IOC.NS",
    "BEL.NS",
    "VEDL.NS",
    "TATAPOWER.NS",
    "BHEL.NS",
    "IRFC.NS"
]

# Official Groww URL Slugs for seamless direct order navigation (All Top 30 Stocks)
GROWW_SLUGS = {
    "RELIANCE.NS": "reliance-industries-ltd",
    "TCS.NS": "tata-consultancy-services-ltd",
    "HDFCBANK.NS": "hdfc-bank-ltd",
    "ICICIBANK.NS": "icici-bank-ltd",
    "INFY.NS": "infosys-ltd",
    "BHARTIARTL.NS": "bharti-airtel-ltd",
    "ITC.NS": "itc-ltd",
    "SBIN.NS": "state-bank-of-india",
    "LT.NS": "larsen-toubro-ltd",
    "KOTAKBANK.NS": "kotak-mahindra-bank-ltd",
    "AXISBANK.NS": "axis-bank-ltd",
    "HINDUNILVR.NS": "hindustan-unilever-ltd",
    "SUNPHARMA.NS": "sun-pharmaceutical-industries-ltd",
    "TITAN.NS": "titan-company-ltd",
    "TATASTEEL.NS": "tata-steel-ltd",
    "NTPC.NS": "ntpc-ltd",
    "POWERGRID.NS": "power-grid-corporation-of-india-ltd",
    "ONGC.NS": "oil-natural-gas-corporation-ltd",
    "COALINDIA.NS": "coal-india-ltd",
    "HINDALCO.NS": "hindalco-industries-ltd",
    "WIPRO.NS": "wipro-ltd",
    "TECHM.NS": "tech-mahindra-ltd",
    "BPCL.NS": "bharat-petroleum-corporation-ltd",
    "GAIL.NS": "gail-india-ltd",
    "IOC.NS": "indian-oil-corporation-ltd",
    "BEL.NS": "bharat-electronics-ltd",
    "VEDL.NS": "vedanta-ltd",
    "TATAPOWER.NS": "tata-power-company-ltd",
    "BHEL.NS": "bharat-heavy-electricals-ltd",
    "IRFC.NS": "indian-railway-finance-corporation-ltd"
}

# High-Safety Notification Threshold (% Safe Score)
HIGH_SAFETY_THRESHOLD = 90.0

# Risk Management & Trade Sizing Rules
RISK_MANAGEMENT = {
    "risk_reward_ratio": 2.0,       # 1:2 Risk to Reward
    "stop_loss_pct": 0.015,         # 1.5% - 2.0% maximum risk
    "target_pct": 0.03,             # 3.0% primary target
    "atr_multiplier": 1.5,          # Dynamic ATR volatility factor
    "breakeven_trigger_pct": 0.015  # Move Stop Loss to breakeven once price moves +1.5%
}

# Advanced Quantitative Filter Thresholds
ADVANCED_CRITERIA = {
    "adx_trend_min": 20.0,          # ADX must be > 20 to confirm trend strength
    "rsi4_pullback_threshold": 25.0,# Connors short-term oversold dip threshold
    "rsi14_momentum_min": 48.0,     # Standard RSI bullish floor
    "rsi14_momentum_max": 68.0,     # Standard momentum range
    "min_vol_ratio": 1.1,           # Relative Volume (RVOL) > 1.1x 20-day SMA
    "mfi_oversold": 35.0,           # Money Flow Index accumulation floor
    "min_price": 20.0,              # Filter penny stocks below 20 INR
    "max_price": MAX_DAILY_INVESTMENT # Stock price must not exceed daily budget
}
