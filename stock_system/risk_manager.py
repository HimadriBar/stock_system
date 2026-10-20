"""
Risk Management and Position Sizing Engine.
Calculates exact share quantities, Stop Loss, Target, and rupee risk adhering to the ₹5,000 budget.
"""

import math
from typing import Dict, List
from config import MAX_DAILY_INVESTMENT, RISK_MANAGEMENT, GROWW_SLUGS

def calculate_trade_plan(stock_candidate: Dict, budget: float = MAX_DAILY_INVESTMENT) -> Dict:
    """
    Computes precise trade execution parameters:
    - Exact shares to buy within ₹5,000 budget
    - Exact Stop Loss price
    - Target 1 (1:1.5) & Target 2 (1:2 Risk:Reward)
    - Total Rupees at Risk vs Total Rupees of Expected Profit
    """
    analysis = stock_candidate['analysis']
    price = analysis['price']
    atr = analysis['atr']

    if price > budget:
        return {
            "valid": False,
            "reason": f"Stock price ₹{price:.2f} exceeds total budget of ₹{budget:.2f}"
        }

    # Position Sizing: Number of whole shares that can be bought
    quantity = math.floor(budget / price)
    if quantity < 1:
        return {
            "valid": False,
            "reason": "Cannot buy at least 1 share within budget"
        }

    invested_amount = round(quantity * price, 2)
    unallocated_cash = round(budget - invested_amount, 2)

    # Dynamic Stop Loss based on ATR and percentage guardrail
    sl_atr_dist = atr * RISK_MANAGEMENT['atr_multiplier']
    sl_pct_dist = price * RISK_MANAGEMENT['stop_loss_pct']
    # Use the tighter stop to strictly protect capital
    sl_distance = min(sl_atr_dist, sl_pct_dist)

    stop_loss = round(price - sl_distance, 2)
    risk_per_share = round(price - stop_loss, 2)

    # Target calculation with 1:2 Risk:Reward ratio
    target_1 = round(price + (risk_per_share * 1.5), 2)
    target_2 = round(price + (risk_per_share * RISK_MANAGEMENT['risk_reward_ratio']), 2)
    reward_per_share = round(target_2 - price, 2)

    total_risk_inr = round(quantity * risk_per_share, 2)
    total_reward_inr = round(quantity * reward_per_share, 2)
    reward_pct = round((reward_per_share / price) * 100, 2)
    risk_pct = round((risk_per_share / price) * 100, 2)

    return {
        "valid": True,
        "ticker": stock_candidate['ticker'],
        "slug": GROWW_SLUGS.get(stock_candidate['ticker'], ""),
        "name": stock_candidate['name'],
        "score": analysis['score'],
        "safe_percentage": analysis.get('safe_percentage', analysis['score']),
        "is_high_safety": analysis.get('is_high_safety', False),
        "entry_price": price,
        "quantity": quantity,
        "invested_amount": invested_amount,
        "unallocated_cash": unallocated_cash,
        "stop_loss": stop_loss,
        "target_1": target_1,
        "target_2": target_2,
        "risk_per_share": risk_per_share,
        "reward_per_share": reward_per_share,
        "total_risk_inr": total_risk_inr,
        "total_reward_inr": total_reward_inr,
        "risk_pct": risk_pct,
        "reward_pct": reward_pct,
        "risk_reward_ratio": f"1:{RISK_MANAGEMENT['risk_reward_ratio']}",
        "signals": analysis['signals']
    }

def generate_daily_trade_recommendations(scored_stocks: List[Dict], max_trades: int = 3, budget: float = MAX_DAILY_INVESTMENT) -> List[Dict]:
    """Generates execution-ready trade setups for the top ranked stocks."""
    trade_plans = []

    for stock in scored_stocks:
        plan = calculate_trade_plan(stock, budget=budget)
        if plan.get("valid", False):
            trade_plans.append(plan)
        if len(trade_plans) >= max_trades:
            break

    return trade_plans
